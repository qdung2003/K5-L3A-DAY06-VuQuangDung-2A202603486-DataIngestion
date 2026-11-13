"""Verify disk persistence, snapshot replacement and validation using REAL saved vectors."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "starter"))
from src.store import ChromaStore
from src.models import Chunk


def main():
    run = json.loads((ROOT / "results/run.json").read_text(encoding="utf-8"))
    store = ChromaStore(run["store_path"], run["dimensions"])
    counts = {}
    for strategy in "ABC":
        collection = store.collection(strategy)
        stored = collection.get(include=["documents", "metadatas"])
        expected = [json.loads(line) for line in (ROOT / f"results/chunks_{strategy}.jsonl").read_text(encoding="utf-8").splitlines()]
        mapping = {r["chunk_id"]: r for r in expected}
        if set(stored["ids"]) != set(mapping):
            raise AssertionError(f"Persisted ID set differs: {strategy}")
        for cid, text, meta in zip(stored["ids"], stored["documents"], stored["metadatas"]):
            expected_chunk = mapping[cid]
            assert text == expected_chunk["text"]
            assert meta == {**expected_chunk["metadata"], "document_id": expected_chunk["document_id"],
                            "source": expected_chunk["source"], "page": expected_chunk["page"]}
        counts[strategy] = len(stored["ids"])
    # Actual neural vectors already persisted by the experiment, never mock vectors.
    data = store.collection("B").get(limit=2, include=["embeddings", "documents", "metadatas"])
    chunks = []
    for cid, text, meta in zip(data["ids"], data["documents"], data["metadatas"]):
        extra = {k:v for k,v in meta.items() if k not in {"document_id", "source", "page"}}
        chunks.append(Chunk(cid, meta["document_id"], meta["source"], meta["page"], text, extra))
    vectors = data["embeddings"].tolist()
    test = ChromaStore(ROOT / "results/verification_store", run["dimensions"])
    test.create_schema()
    test.upsert("A", chunks, vectors)
    before = test.collection("A").count()
    test.upsert("A", chunks, vectors)
    assert test.collection("A").count() == before == 2
    test.upsert("A", chunks[1:], vectors[1:])
    assert test.collection("A").count() == 1
    assert test.collection("A").get(include=[])["ids"] == [chunks[1].chunk_id]
    checks = []
    for label, action in [
        ("mismatched_lengths", lambda: test.upsert("A", chunks, vectors[:1])),
        ("wrong_dimension", lambda: test.upsert("A", chunks[:1], [vectors[0][:-1]])),
        ("duplicate_ids", lambda: test.upsert("A", [chunks[0], chunks[0]], vectors)),
        ("unsupported_filter", lambda: test.search("A", vectors[0], filters={"document_id": "x"})),
        ("nonfinite_vector", lambda: test.search("A", [float("nan")] * run["dimensions"]))]:
        try:
            action()
        except ValueError:
            checks.append(label)
        else:
            raise AssertionError(f"Expected validation failure: {label}")
    assert test.search("A", vectors[1], filters={"section": "not-a-real-section"}) == []
    filtered = test.search("A", vectors[1], filters={"section": chunks[1].metadata["section"]})
    assert len(filtered) == 1 and filtered[0]["chunk_id"] == chunks[1].chunk_id
    output = {"status": "passed", "separate_process_persisted_counts": counts,
        "all_persisted_text_metadata_match_export": True, "same_snapshot_count": [2, 2],
        "changed_snapshot_count": [2, 1], "obsolete_id_removed": chunks[0].chunk_id,
        "invalid_input_rejections": checks, "native_filter_checks": 2,
        "vector_origin": "Actual B embeddings persisted by src.run; no mock/random vectors"}
    (ROOT / "results/storage_verification.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
