"""Fail closed on inconsistent corpus, manifest, model or frozen benchmark."""
import hashlib
import json
from pathlib import Path
from .evaluation import canonical, golds
from .ingestion import normalize_text
from .models import DocumentPage


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_inputs(root):
    pages_path = root / "data/pages.jsonl"
    question_path = root / "benchmark/questions.json"
    freeze = json.loads((root / "benchmark/freeze.json").read_text(encoding="utf-8"))
    for key, path in [("pages_sha256", pages_path), ("benchmark_sha256", question_path)]:
        if freeze[key] != sha256(path):
            raise ValueError(f"Frozen input changed: {path}")
    pages = [DocumentPage(**json.loads(line)) for line in pages_path.read_text(encoding="utf-8").splitlines()]
    if len(pages) < 30 or any(len(normalize_text(p.text)) < 1500 for p in pages):
        raise ValueError("Require >=30 units, each >=1500 normalized characters")
    by_id = {(p.document_id, p.page): p for p in pages}
    if len(by_id) != len(pages):
        raise ValueError("Duplicate page identifiers")
    if len({p.metadata["section"] for p in pages}) < 2:
        raise ValueError("Need multiple filter scopes")
    manifest = json.loads((root / "data/manifest.json").read_text(encoding="utf-8"))
    expected_ids = set()
    for source in manifest["sources"]:
        if sha256(root / source["local_path"]) != source["sha256"]:
            raise ValueError(f"Raw source checksum mismatch: {source['source_id']}")
        text = (root / source["normalized_path"]).read_text(encoding="utf-8")
        previous_end = 0
        for entry in source["pages"]:
            page = by_id[(source["source_id"], entry["page"])]
            expected_ids.add((page.document_id, page.page))
            a, b = entry["start_char"], entry["end_char"]
            if a != previous_end or text[a:b] != page.text:
                raise ValueError(f"Source partition mismatch: {page.page}")
            if len(normalize_text(page.text)) != entry["normalized_char_count"]:
                raise ValueError("Character count mismatch")
            if page.source != source["source_path_or_url"]:
                raise ValueError("Source URL mismatch")
            if page.metadata["section"] != page.page.split(":")[0]:
                raise ValueError("Section provenance mismatch")
            previous_end = b
        if previous_end != len(text):
            raise ValueError("Incomplete source partition")
    if set(by_id) != expected_ids or manifest["total_counted_units"] != len(pages):
        raise ValueError("Manifest/page set mismatch")
    questions = json.loads(question_path.read_text(encoding="utf-8"))
    if len({q["id"] for q in questions}) != len(questions):
        raise ValueError("Duplicate question IDs")
    if sum(q["split"] == "dev" for q in questions) < 15 or sum(q["split"] == "test" for q in questions) < 5:
        raise ValueError("Need >=15 dev and >=5 test")
    if any(q["split"] not in {"dev", "test"} for q in questions):
        raise ValueError("Unknown split")
    if sum(bool(q["filter"]) for q in questions) < 3 or not any(q["filter"] for q in questions if q["split"] == "test"):
        raise ValueError("Insufficient filtered questions")
    for q in questions:
        for g in golds(q):
            page = by_id[(g["source_id"], g["page"])]
            if canonical(g["evidence_quote"]) not in canonical(page.text):
                raise ValueError(f"Gold evidence missing: {q['id']}")
            if q["filter"] and not all(page.metadata.get(k) == v for k, v in q["filter"].items()):
                raise ValueError(f"Gold violates input filter: {q['id']}")
        if not q["question"] or not q["expected_answer"]:
            raise ValueError("Empty question/answer")
    return pages, questions, freeze


def verify_model(root):
    manifest = json.loads((root / "data/model_manifest.json").read_text(encoding="utf-8"))
    folder = root / ".cache/all-MiniLM-L6-v2"
    for name, expected in manifest["sha256"].items():
        if sha256(folder / name) != expected:
            raise ValueError(f"Model file checksum mismatch: {name}")
    return manifest
