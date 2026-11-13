"""Fail-closed integrity check for the submission artifacts."""
import csv, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
required = ["STUDENT.md","README.md","data/manifest.json","data/pages.jsonl","benchmark/questions.json",
"benchmark/freeze.json","artifacts/experiment_log.csv","results/metrics.csv","results/traces.jsonl",
"results/run.json","results/statistics.json","results/storage_verification.json","results/audit_summary.json",
"report/individual/2A202603486_VuQuangDung.md","starter/src/ingestion.py","starter/src/chunking.py",
"starter/src/embeddings.py","starter/src/store.py","starter/src/evaluation.py","starter/src/run.py"]
for relative in required:
    path = ROOT / relative
    if not path.exists() or path.stat().st_size == 0:
        raise SystemExit(f"Missing or empty: {relative}")
pages = [json.loads(x) for x in (ROOT/"data/pages.jsonl").read_text(encoding="utf-8").splitlines()]
questions = json.loads((ROOT/"benchmark/questions.json").read_text(encoding="utf-8"))
assert len(pages) >= 30 and min(len(p["text"]) for p in pages) >= 1500
assert len(questions) >= 20 and sum(q["split"]=="dev" for q in questions) >= 15
assert sum(q["split"]=="test" for q in questions) >= 5 and sum(bool(q["filter"]) for q in questions) >= 3
metrics = json.loads((ROOT/"results/metrics.json").read_text(encoding="utf-8"))
assert set(metrics) == {"A/dev","A/test","B/dev","B/test","C/dev","C/test"}
assert sum(x["n"] for x in metrics.values()) == 60
for row in csv.DictReader((ROOT/"artifacts/experiment_log.csv").open(encoding="utf-8")):
    assert row["strategy"] in {"A","B","C"} and row["dev_hit3"] and row["test_hit3"]
traces = [json.loads(x) for x in (ROOT/"results/traces.jsonl").read_text(encoding="utf-8").splitlines()]
assert len(traces) == 60 and all(len(x["hits"]) == 3 for x in traces)
assert json.loads((ROOT/"results/storage_verification.json").read_text())["status"] == "passed"
for path in ROOT.rglob("*"):
    if ".venv" in path.parts or ".cache" in path.parts or "vector_store" in path.parts:
        continue
    if path.is_file() and ".git" not in path.parts and path.name not in {"model.safetensors","tokenizer.json"}:
        if path.stat().st_size > 2_000_000: continue
        text = path.read_text(errors="ignore")
        if ("s" + "k-") in text or ("AI" + "za") in text:
            raise SystemExit(f"Possible credential marker in {path}")
report = (ROOT/"report/individual/2A202603486_VuQuangDung.md").read_text(encoding="utf-8")
for forbidden in ["TODO:", "Hit@3: __", "placeholder"]:
    assert forbidden not in report
result = {"status":"passed","required_files":len(required),"units":len(pages),
          "questions":len(questions),"trace_rows":len(traces),"credentials_scan":"passed",
          "note":"External repo push, author audit and Docker are outside local verification."}
(ROOT/"results/submission_verification.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
