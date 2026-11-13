"""Strict single-chunk evidence metrics, independent from qualitative labels."""
import re
import unicodedata
from collections import defaultdict
from typing import Any


def canonical(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", text)).strip()


def golds(question):
    return [{"source_id": question["gold_source_id"], "page": question["gold_page"],
             "evidence_quote": question["evidence_quote"]}, *question.get("alternative_gold", [])]


def evaluate_query(question: dict[str, Any], hits: list[dict[str, Any]]) -> dict[str, Any]:
    evidence_hits = []
    for hit in hits[:3]:
        meta = hit["metadata"]
        matched = any(meta.get("document_id") == g["source_id"] and
            meta.get("page") == g["page"] and
            canonical(g["evidence_quote"]) in canonical(hit["text"]) for g in golds(question))
        evidence_hits.append(matched)
    return {"question": question, "hits": hits[:3], "evidence_hits": evidence_hits,
            "hit_at_1": bool(evidence_hits and evidence_hits[0]), "hit_at_3": any(evidence_hits)}


def summarize(traces: list[dict[str, Any]]) -> dict[str, Any]:
    groups = defaultdict(list)
    for trace in traces:
        groups[(trace["strategy"], trace["question"]["split"])].append(trace)
    return {f"{s}/{split}": {"n": len(rows),
                "hit_at_1": sum(r["hit_at_1"] for r in rows),
                "hit_at_3": sum(r["hit_at_3"] for r in rows)}
            for (s, split), rows in sorted(groups.items())}
