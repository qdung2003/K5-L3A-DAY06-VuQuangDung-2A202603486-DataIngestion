"""Optional dense+BM25 weighted RRF on unchanged C chunks and filters."""
import json
import math
import re
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from .embeddings import MyEmbedder
from .evaluation import evaluate_query
from .run import write_json
from .store import ChromaStore
from .validation import load_inputs, sha256

ROOT = Path(__file__).resolve().parents[2]


def tokenize(text):
    return re.findall(r"[a-z_][a-z_0-9]*", text.lower())


def bm25_scores(chunks, question, k1=1.5, b=.75):
    documents = [Counter(tokenize(chunk["text"])) for chunk in chunks]
    query = set(tokenize(question))
    lengths = [sum(doc.values()) for doc in documents]
    avg = sum(lengths)/len(lengths)
    n = len(documents)
    dfs = {term: sum(term in doc for doc in documents) for term in query}
    result = []
    for chunk, doc, length in zip(chunks, documents, lengths):
        score = sum(math.log(1 + (n - dfs[term] + .5)/(dfs[term] + .5)) *
                    doc[term]*(k1+1)/(doc[term] + k1*(1-b+b*length/avg))
                    for term in query if doc[term])
        result.append((chunk["chunk_id"], score))
    return sorted(result, key=lambda row: (-row[1], row[0]))


def totals(rows):
    return {"n":len(rows), "hit_at_1":sum(r["hit_at_1"] for r in rows),
            "hit_at_3":sum(r["hit_at_3"] for r in rows)}


def main():
    output = ROOT/"results/hybrid"
    output.mkdir(exist_ok=True)
    if (output/"summary.json").exists():
        raise ValueError("Preserve completed hybrid run; do not overwrite")
    started = time.perf_counter()
    load_inputs(ROOT)
    freeze = json.loads((ROOT/"benchmark/hybrid_freeze.json").read_text(encoding="utf-8"))
    if sha256(ROOT/"benchmark/hybrid_holdout.json") != freeze["holdout_sha256"]:
        raise ValueError("Hybrid holdout changed")
    if sha256(ROOT/"benchmark/questions.json") != freeze["original_dev_sha256"]:
        raise ValueError("Original dev changed")
    chunks = [json.loads(line) for line in (ROOT/"results/chunks_C.jsonl").read_text(encoding="utf-8").splitlines()]
    lookup = {c["chunk_id"]:c for c in chunks}
    questions = json.loads((ROOT/"benchmark/questions.json").read_text(encoding="utf-8"))
    dev = [q for q in questions if q["split"]=="dev"]
    holdout = json.loads((ROOT/"benchmark/hybrid_holdout.json").read_text(encoding="utf-8"))
    for q in holdout:
        c = next(c for c in chunks if c["document_id"]==q["gold_source_id"] and c["page"]==q["gold_page"])
        if q["filter"] and not all(c["metadata"].get(k)==v for k,v in q["filter"].items()):
            raise ValueError("Invalid holdout filter")
    model = MyEmbedder()
    store = ChromaStore(ROOT/"starter/vector_store", model.dimensions)

    def candidates(q, vector):
        dense = store.search("C", vector, len(chunks), q["filter"])
        # Same filtered candidate universe for both rankers.
        eligible = [lookup[hit["chunk_id"]] for hit in dense]
        lexical = bm25_scores(eligible,q["question"],freeze["bm25_k1"],freeze["bm25_b"])
        dense_ranks = {hit["chunk_id"]:i for i,hit in enumerate(dense,1)}
        lexical_ranks = {cid:i for i,(cid,_) in enumerate(lexical,1)}
        return dense, dense_ranks, lexical_ranks

    def fused(q, candidate, alpha):
        dense, dr, lr = candidate
        by_id = {hit["chunk_id"]:hit for hit in dense}
        order = sorted(dr,key=lambda cid: (-(alpha/(freeze["rrf_k"]+dr[cid])+
                        (1-alpha)/(freeze["rrf_k"]+lr[cid])), dr[cid], cid))
        hits = [{**by_id[cid], "dense_score":by_id[cid]["score"],
            "score":alpha/(freeze["rrf_k"]+dr[cid])+(1-alpha)/(freeze["rrf_k"]+lr[cid]),
            "dense_rank":dr[cid], "bm25_rank":lr[cid]} for cid in order[:3]]
        return {**evaluate_query(q,hits), "dense_weight":alpha, "applied_filter":q["filter"]}

    vectors = model.embed_documents([q["question"] for q in dev])
    dev_candidates = [candidates(q,v) for q,v in zip(dev,vectors)]
    by_weight = {alpha:[fused(q,candidate,alpha) for q,candidate in zip(dev,dev_candidates)]
                 for alpha in freeze["dense_weights"]}
    dev_metrics = {str(alpha):totals(rows) for alpha,rows in by_weight.items()}
    selected = max(freeze["dense_weights"],
        key=lambda alpha:(dev_metrics[str(alpha)]["hit_at_3"],dev_metrics[str(alpha)]["hit_at_1"],alpha))
    write_json(output/"selection.json", {"dense_weight":selected, "dev_metrics":dev_metrics,
        "rule":freeze["selection_rule"],"selected_at":datetime.now(timezone.utc).isoformat(),
        "holdout_queries_executed_at_selection":0})
    test_rows, dense_rows = [], []
    vectors = model.embed_documents([q["question"] for q in holdout])
    for q, vector in zip(holdout,vectors):
        candidate = candidates(q,vector)
        test_rows.append(fused(q,candidate,selected))
        dense_rows.append({**evaluate_query(q,candidate[0][:3]),"dense_weight":1,"applied_filter":q["filter"]})
    with (output/"traces.jsonl").open("w",encoding="utf-8") as out:
        for stage, rows in [("dev_selected",by_weight[selected]),("holdout_hybrid",test_rows),("holdout_dense",dense_rows)]:
            for row in rows:
                out.write(json.dumps({"stage":stage,**row})+"\n")
    regressions = [q["id"] for q, hybrid, dense in zip(holdout,test_rows,dense_rows)
                   if dense["hit_at_3"] and not hybrid["hit_at_3"]]
    dev_regressions = [q["id"] for q,hybrid,dense in zip(dev,by_weight[selected],by_weight[1])
                       if dense["hit_at_1"] and not hybrid["hit_at_1"]]
    summary = {"selected_dense_weight":selected,"dev_grid":dev_metrics,
        "new_holdout_hybrid":totals(test_rows),"new_holdout_dense":totals(dense_rows),
        "holdout_hit3_regressions":regressions,"dev_hit1_regressions":dev_regressions,
        "elapsed_seconds":time.perf_counter()-started,"api_cost_usd":0,
        "caveat":"5 new questions authored after baseline test; same corpus, reused dev; no independent human audit.",
        "fixed":"Same C chunks, same model/store, same section filters. RRF score is not cosine score."}
    write_json(output/"summary.json",summary)
    print(json.dumps(summary,indent=2))


if __name__=="__main__":
    main()
