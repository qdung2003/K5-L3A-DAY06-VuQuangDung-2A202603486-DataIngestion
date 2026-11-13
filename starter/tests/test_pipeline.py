"""Regression tests for provenance, chunk boundaries and evidence acceptance."""
import unittest
from src.chunking import by_paragraph, fixed_size
from src.evaluation import evaluate_query, summarize
from src.ingestion import normalize_text
from src.models import DocumentPage


class PipelineTests(unittest.TestCase):
    def test_normalization_preserves_structure_and_code_indentation(self):
        self.assertEqual(normalize_text("e\u0301  \r\n\r\n    x = 1  \r\n\r\n\r\nz"), "é\n\n    x = 1\n\nz")

    def test_chunks_retain_provenance_offsets_and_stable_ids(self):
        page = DocumentPage("doc", "source", "unit:001", "A" * 710 + "\n\n" + "B" * 2200, {"section": "real"})
        for chunks in [fixed_size(page, 500, 50), by_paragraph(page, 1000)]:
            for chunk in chunks:
                self.assertEqual(chunk.text, page.text[chunk.metadata["start_char"]:chunk.metadata["end_char"]])
                self.assertEqual((chunk.document_id, chunk.source, chunk.page, chunk.metadata["section"]),
                                 ("doc", "source", "unit:001", "real"))
            self.assertTrue(all(len(c.text) <= 1000 for c in chunks))
            covered = set(i for c in chunks for i in range(c.metadata["start_char"], c.metadata["end_char"]))
            self.assertTrue(all(i in covered for i, char in enumerate(page.text) if not char.isspace()))
        self.assertEqual(fixed_size(page, 500, 50), fixed_size(page, 500, 50))
        with self.assertRaises(ValueError):
            fixed_size(page, 50, 50)

    def test_evidence_requires_right_page_and_complete_condition(self):
        q = {"gold_source_id": "doc", "gold_page": 2, "evidence_quote": "only when no error"}
        def hit(text, page=2, doc="doc"):
            return {"text": text, "metadata": {"document_id": doc, "page": page}}
        self.assertFalse(evaluate_query(q, [hit("only when no error", page=3)])["hit_at_3"])
        self.assertFalse(evaluate_query(q, [hit("only when"), hit("no error")])["hit_at_3"])
        result = evaluate_query(q, [hit("only when"), hit("only when\n no error")])
        self.assertFalse(result["hit_at_1"])
        self.assertTrue(result["hit_at_3"])
        q["alternative_gold"] = [{"source_id": "other", "page": 9, "evidence_quote": "equivalent condition"}]
        self.assertTrue(evaluate_query(q, [hit("equivalent condition", page=9, doc="other")])["hit_at_1"])

    def test_summary_keeps_splits_and_strategies_separate(self):
        rows = [{"strategy": s, "question": {"split": split}, "hit_at_1": h1, "hit_at_3": h3}
                for s, split, h1, h3 in [("A", "dev", True, True), ("A", "test", False, True), ("B", "dev", False, False)]]
        actual = summarize(rows)
        self.assertEqual(actual["A/test"], {"n": 1, "hit_at_1": 0, "hit_at_3": 1})
        self.assertEqual(actual["B/dev"]["hit_at_3"], 0)


if __name__ == "__main__":
    unittest.main()
