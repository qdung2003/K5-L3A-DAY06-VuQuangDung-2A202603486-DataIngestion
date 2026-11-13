"""Freeze new holdout and fusion rule before any hybrid run."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "starter"))
from src.evaluation import canonical
ITEMS = [
("Which compact Python container stores homogeneous values?",
 "array.array stores homogeneous data compactly.",
 "The array module provides an array.array object that is like a list that stores only homogeneous data and stores it more compactly.", None),
("Which module checks tests embedded inside docstrings?",
 "doctest scans a module and validates tests in its docstrings.",
 "The doctest module provides a tool for scanning a module and validating tests embedded in a program's docstrings.", None),
("In errors, how can automatic exception chaining be disabled?",
 "Use raise ... from None.",
 "It also allows disabling automatic exception chaining using the from None idiom", {"section":"errors"}),
("In modules, what file normally marks a directory as a package, and what is the exception?",
 "__init__.py is required unless using a namespace package.",
 "The __init__.py files are required to make Python treat directories containing the file as packages (unless using a namespace package, a relatively advanced feature).", {"section":"modules"}),
("What generator state is automatically retained between calls?",
 "Local variables and execution state.",
 "Another key feature is that the local variables and execution state are automatically saved between calls.", None),
]
target = ROOT / "benchmark/hybrid_holdout.json"
if target.exists():
    raise SystemExit("Holdout exists; do not replace after viewing it.")
pages = [json.loads(line) for line in (ROOT / "data/pages.jsonl").read_text(encoding="utf-8").splitlines()]
questions = []
for index, (question, answer, quote, filters) in enumerate(ITEMS, 1):
    matches = [p for p in pages if canonical(quote) in canonical(p["text"])]
    if len(matches) != 1:
        raise ValueError(f"Need one verified source for H{index}: {len(matches)}")
    p = matches[0]
    questions.append({"id": f"H{index:02d}", "split":"test", "question": question,
        "expected_answer":answer, "gold_source_id":p["document_id"], "gold_page":p["page"],
        "evidence_quote":quote, "filter":filters, "alternative_gold":[]})
target.write_text(json.dumps(questions, indent=2) + "\n", encoding="utf-8")
freeze = {"frozen_at":datetime.now(timezone.utc).isoformat(),
    "holdout_sha256":hashlib.sha256(target.read_bytes()).hexdigest(),
    "original_dev_sha256":hashlib.sha256((ROOT/"benchmark/questions.json").read_bytes()).hexdigest(),
    "dense_weights":[0, .25, .5, .75, 1], "rrf_k":60, "bm25_k1":1.5, "bm25_b":.75,
    "selection_rule":"Max original dev Hit@3, then dev Hit@1, then higher dense weight. No original test used.",
    "design":"Created after main baseline test was viewed; new topics/questions frozen before first hybrid retrieval. Same corpus; not document-independent.",
    "fixed_data":"Exactly C chunks and question-provided section filters; only fusion changes."}
(ROOT/"benchmark/hybrid_freeze.json").write_text(json.dumps(freeze,indent=2),encoding="utf-8")
print("Frozen 5 new holdout questions and RRF grid; no hybrid retrieval executed.")
