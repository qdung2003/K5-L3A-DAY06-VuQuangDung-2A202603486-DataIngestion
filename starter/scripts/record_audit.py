"""Record Codex's explicit qualitative judgments after reading exported samples.

These are AI-assisted labels, NOT human/manual author sign-off. No label is
inferred from hit@k or string matching. The author review sheet stays blank.
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results"
REVIEWER = "Codex (AI assistant); human author review pending"
# Explicit judgments of midpoint chunks inspected against their full source units.
COHERENCE_A = [
(1, "Starts with dangling 'for'; runtime-class idea remains readable, ends mid-word 'impl'."),
(1, "Scope introduction readable; namespace definition is cut after 'that's'."),
(1, "Starts mid-word and cuts built-in namespace explanation; writable-attribute paragraph is complete."),
(1, "Nonlocal rule understandable, but previous global context and end of module explanation are cut."),
(1, "Global/nonlocal paragraph complete; example ends at 'def scope_t', losing the anchored function."),
(1, "Namespace creation is clear, but class-object explanation ends mid-sentence."),
(1, "Instantiation partly explained; cuts before the named initialization method."),
(1, "Stored method example readable with prior MyClass context; starts/ends in fragments."),
(1, "Dog shared/unique comments help, but Dog definition absent and mutable-list warning cut."),
(2, "Complete instance-over-class precedence rule plus Warehouse demonstration; leading old output does not obscure it."),
]
COHERENCE_B = [
(2, "Complete paragraph explains inheritance, overriding and runtime-mutability of Python classes."),
(1, "Complete introductory prose, but promises scope/namespace definitions absent from this chunk."),
(2, "Complete built-in/global/local namespace lifetimes and recursive-call explanation."),
(2, "Complete global/nonlocal rebinding rules and function/module/class scope context."),
(2, "scope_test function, output and explanation all retained; local/nonlocal/global effects traceable."),
(2, "Class namespace creation, class-object construction and enclosing-scope restoration retained."),
(2, "Object instantiation, __init__ definition and Complex constructor example form a complete unit."),
(1, "Stored method example retained, but MyClass/f definition and explanation of implicit self are elsewhere."),
(1, "Shared-list warning retained with code, but Dog('Fido') precedes the class definition used by that output."),
(2, "Correct per-instance tricks list and Warehouse lookup precedence examples remain complete."),
]
GROUNDING = {
("A","Q16"):(2,"Rank 1 explicitly contrasts per-instance data and class data shared by all instances; source classes:009."),
("B","Q16"):(2,"Rank 2 states the distinction and Dog.kind/self.name example; rank 3 demonstrates shared and unique values."),
("C","Q16"):(2,"Same unfiltered evidence as B; rank 2 classes:009 contains both sides of the distinction."),
("A","Q17"):(2,"Rank 1 states finally's return overrides try's return; rank 3 bool_return demonstrates False."),
("B","Q17"):(2,"Rank 1 gives the complete finally-return rule; rank 3 includes executable bool_return example."),
("C","Q17"):(2,"Same unfiltered evidence as B; complete override condition and traceable example."),
("A","Q18"):(0,"Top 3 discuss double-underscore mangling, class syntax and scopes; none states single-underscore convention or absence of enforced private variables."),
("B","Q18"):(2,"Rank 1 classes:014 explicitly says enforced private instance variables do not exist and _spam signals non-public API."),
("C","Q18"):(2,"Same unfiltered rank 1 as B; includes convention, implementation-detail status and source."),
("A","Q19"):(2,"Rank 1 states resource access should concentrate in one thread fed requests via queue; leading/trailing fragments do not remove this rule."),
("B","Q19"):(2,"Rank 1 gives shared-resource coordination problem, single-thread owner and queue request mechanism."),
("C","Q19"):(2,"Filtered rank 1 stdlib2:004 gives complete coordination approach; all top 3 within stdlib2."),
("A","Q20"):(2,"Rank 1 directly states file or sys.stderr. Rank 3 outside requested chapter affects filter adherence, not evidence sufficiency."),
("B","Q20"):(2,"Rank 1 states file/sys.stderr; rank 2 explains default standard-error output and suppression of info/debug."),
("C","Q20"):(2,"Filtered rank 1 states file/sys.stderr with logging context; all top 3 trace to stdlib2."),
}


def dump_csv(name, rows):
    with (OUT / name).open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    run = json.loads((OUT / "run.json").read_text(encoding="utf-8"))
    coherence = []
    for row in json.loads((OUT / "coherence_samples.json").read_text(encoding="utf-8")):
        index = int(row["page"].split(":")[1]) - 1
        score, reason = (COHERENCE_A if row["strategy"] == "A" else COHERENCE_B)[index]
        coherence.append({"strategy": row["strategy"], "page": row["page"],
            "anchor": row["anchor"], "chunk_id": row["chunk"]["chunk_id"],
            "score": score, "reason": reason, "reviewer": REVIEWER})
    dump_csv("coherence_labels.csv", coherence)
    grounding = []
    for row in json.loads((OUT / "grounding_samples.json").read_text(encoding="utf-8")):
        key = row["strategy"], row["question"]["id"]
        score, reason = GROUNDING[key]
        grounding.append({"strategy": key[0], "question_id": key[1], "score": score,
                          "reason": reason, "reviewer": REVIEWER})
    dump_csv("grounding_labels.csv", grounding)
    # Source/section/offset values were individually inspected in the compact
    # metadata table, and separately verified against all persisted chunk exports.
    metadata = []
    for row in json.loads((OUT / "metadata_samples.json").read_text(encoding="utf-8")):
        actual = row["actual"]
        correct = (actual["source"] == row["expected_source"] and
                   actual["section"] == row["expected_section"] and
                   actual["page"].split(":")[0] == actual["section"] and
                   actual["document_id"] == "python-tutorial-" + actual["section"])
        if not correct:
            raise ValueError("Metadata differs from the inspected table; re-review required")
        metadata.append({"strategy": row["strategy"], "question_id": row["question_id"],
            "rank": row["rank"], "chunk_id": row["chunk_id"], "page": actual["page"],
            "section": actual["section"], "correct": True,
            "reason": f"Source URL ends /{actual['section']}.rst; page exists in that source, section matches raw chapter; offsets verified against source text.",
            "reviewer": REVIEWER})
    dump_csv("metadata_labels.csv", metadata)
    traces = [json.loads(line) for line in (OUT / "traces.jsonl").read_text(encoding="utf-8").splitlines()]
    filter_rows = []
    for row in traces:
        q = row["question"]
        if not q["filter"]:
            continue
        violations = [rank for rank, hit in enumerate(row["hits"], 1)
                      if any(hit["metadata"].get(k) != v for k,v in q["filter"].items())]
        filter_rows.append({"strategy": row["strategy"], "question_id": q["id"], "split": q["split"],
            "filter_applied": row["strategy"] == "C", "complete_top3": len(row["hits"]) == 3,
            "compliant": not violations and len(row["hits"]) == 3,
            "violating_ranks": ";".join(map(str, violations)),
            "requested_filter": json.dumps(q["filter"])})
    dump_csv("filter_audit.csv", filter_rows)
    summary = {}
    for strategy in "ABC":
        c = [r for r in coherence if r["strategy"] == strategy]
        g = [r for r in grounding if r["strategy"] == strategy]
        m = [r for r in metadata if r["strategy"] == strategy]
        f = [r for r in filter_rows if r["strategy"] == strategy and r["split"] == "test"]
        summary[strategy] = {"coherence_mean": sum(r["score"] for r in c)/len(c), "coherence_n": len(c),
            "grounding_distribution": {str(score): sum(r["score"] == score for r in g) for score in range(3)},
            "grounding_mean": sum(r["score"] for r in g)/len(g),
            "metadata_correct": sum(r["correct"] for r in m), "metadata_n": len(m),
            "metadata_errors": [r for r in m if not r["correct"]],
            "test_filter_compliant": sum(r["compliant"] for r in f), "test_filter_n": len(f)}
    (OUT / "audit_summary.json").write_text(json.dumps({"method": REVIEWER,
        "traces_sha256": run["traces_sha256"], "labelled_at": datetime.now(timezone.utc).isoformat(),
        "human_author_reviewed": False, "scores": summary}, indent=2), encoding="utf-8")
    # Honest blank author form, never automatically attributed to the student.
    pending = [{"dimension": dimension, "strategy": row["strategy"],
        "sample_id": row.get("page", row.get("question_id", "")), "rank": row.get("rank",""),
        "author_score_or_correct": "", "author_reason": "", "author_name": "", "reviewed_at": ""}
        for dimension, rows in [("coherence", coherence), ("grounding", grounding), ("metadata", metadata)] for row in rows]
    dump_csv("author_review_pending.csv", pending)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
