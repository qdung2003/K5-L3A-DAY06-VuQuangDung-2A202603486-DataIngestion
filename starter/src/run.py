"""Reproducible A/B/C experiment; choose on dev before running test."""
import argparse
import csv
import importlib.metadata
import json
import logging
import platform
import statistics
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .chunking import by_paragraph, fixed_size
from .embeddings import MyEmbedder, MODEL_NAME, MODEL_REVISION
from .evaluation import canonical, evaluate_query, golds, summarize
from .store import ChromaStore
from .validation import load_inputs, sha256, verify_model

ROOT = Path(__file__).resolve().parents[2]


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def versions():
    return {name: importlib.metadata.version(name) for name in
            ["chromadb", "sentence-transformers", "torch", "transformers", "numpy", "pypdf", "python-dotenv"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "results")
    parser.add_argument("--store", type=Path, default=ROOT / "starter/vector_store")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(filename=args.output / "errors.log", level=logging.ERROR,
                        format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
    try:
        pages, questions, freeze = load_inputs(ROOT)
        model_manifest = verify_model(ROOT)
        if model_manifest["revision"] != MODEL_REVISION:
            raise ValueError("Model revision mismatch")
        if args.validate_only:
            print(f"Validation OK: {len(pages)} units, {len(questions)} questions, model hashes verified")
            return
        if (args.output / "run.json").exists():
            raise ValueError("Output already contains a run; use --output results/rerun_NAME to preserve evidence")
        started = datetime.now(timezone.utc).isoformat()
        total_clock = time.perf_counter()
        model_clock = time.perf_counter()
        embedder = MyEmbedder()
        model_load = time.perf_counter() - model_clock
        store = ChromaStore(args.store, embedder.dimensions)
        store.create_schema()
        all_chunks = {}
        stats = {}
        for strategy in "ABC":
            clock = time.perf_counter()
            chunks = [c for p in pages for c in
                      (fixed_size(p, 500, 50) if strategy == "A" else by_paragraph(p, 1000))]
            all_chunks[strategy] = chunks
            vectors = embedder.embed_documents([c.text for c in chunks])
            store.upsert(strategy, chunks, vectors)
            elapsed = time.perf_counter() - clock
            count_before = store.collection(strategy).count()
            reload_clock = time.perf_counter()
            store.upsert(strategy, chunks, vectors)
            count_after = store.collection(strategy).count()
            if count_before != len(chunks) or count_after != count_before:
                raise ValueError(f"Re-ingestion duplicated chunks: {strategy}")
            lengths = sorted(len(c.text) for c in chunks)
            token_counts = [len(embedder.model.tokenizer.encode(c.text, add_special_tokens=True, truncation=False))
                            for c in chunks]
            stats[strategy] = {"chunks": len(chunks), "characters": sum(lengths),
                "length_min": min(lengths), "length_max": max(lengths),
                "length_mean": statistics.mean(lengths), "length_median": statistics.median(lengths),
                "length_p95": lengths[min(int(len(lengths)*.95), len(lengths)-1)],
                "tokens_before_model_truncation": sum(token_counts),
                "chunks_exceeding_model_token_limit": sum(n > embedder.model.max_seq_length for n in token_counts),
                "ingest_seconds": elapsed, "reload_seconds": time.perf_counter() - reload_clock,
                "count_before_reload": count_before, "count_after_reload": count_after,
                "api_cost_usd": 0}
            with (args.output / f"chunks_{strategy}.jsonl").open("w", encoding="utf-8") as out:
                for chunk in chunks:
                    out.write(json.dumps(asdict(chunk), ensure_ascii=False) + "\n")
            print(f"{strategy}: {len(chunks)} chunks, ingest {elapsed:.3f}s, reload count {count_after}", flush=True)
        # B and C must contain identical data and embeddings; only query filters differ.
        if [asdict(c) for c in all_chunks["B"]] != [asdict(c) for c in all_chunks["C"]]:
            raise ValueError("B/C chunk mismatch")
        coherence = []
        for page in sorted(pages, key=lambda p: p.page)[:10]:
            anchor = len(page.text) // 2
            for strategy in "ABC":
                selected = next(c for c in all_chunks[strategy] if c.page == page.page
                                and c.metadata["start_char"] <= anchor < c.metadata["end_char"])
                coherence.append({"strategy": strategy, "page": page.page, "anchor": anchor,
                    "chunk": asdict(selected), "source_text": page.text,
                    "score": None, "reason": "", "reviewer": ""})
        write_json(args.output / "coherence_samples.json", coherence)
        traces = []
        search_seconds = {s: 0.0 for s in "ABC"}

        def run_split(split):
            for q in (q for q in questions if q["split"] == split):
                vector = embedder.embed_query(q["question"])
                for strategy in "ABC":
                    filters = q["filter"] if strategy == "C" else None
                    clock = time.perf_counter()
                    hits = store.search(strategy, vector, 3, filters)
                    search_seconds[strategy] += time.perf_counter() - clock
                    row = evaluate_query(q, hits)
                    row.update({"strategy": strategy, "applied_filter": filters,
                                "filter_mode": "filtered" if filters else "unfiltered"})
                    # Diagnose evidence splitting against all ingested chunks, without
                    # changing the mandatory single-chunk metric.
                    source_chunks = [c for c in all_chunks[strategy]
                                     if any(c.document_id == g["source_id"] and c.page == g["page"] for g in golds(q))]
                    row["gold_evidence_in_any_ingested_chunk"] = any(
                        c.document_id == g["source_id"] and c.page == g["page"] and
                        canonical(g["evidence_quote"]) in canonical(c.text)
                        for c in source_chunks for g in golds(q))
                    row["failure_kind"] = (None if row["hit_at_3"] else "ranking_or_filter"
                        if row["gold_evidence_in_any_ingested_chunk"] else "evidence_split_across_chunks")
                    traces.append(row)

        run_split("dev")
        dev = summarize(traces)
        preference = {"B": 2, "C": 1, "A": 0}
        selected = max("ABC", key=lambda s: (dev[f"{s}/dev"]["hit_at_3"],
                                            dev[f"{s}/dev"]["hit_at_1"], preference[s]))
        write_json(args.output / "selection.json", {"selected_strategy": selected, "dev_metrics": dev,
            "rule": freeze["selection_rule"], "selected_at": datetime.now(timezone.utc).isoformat(),
            "test_queries_executed_at_selection": 0})
        print(f"Selected on dev: {selected}; now evaluating frozen test", flush=True)
        run_split("test")
        with (args.output / "traces.jsonl").open("w", encoding="utf-8") as out:
            for row in traces:
                out.write(json.dumps(row, ensure_ascii=False) + "\n")
        metrics = summarize(traces)
        write_json(args.output / "metrics.json", metrics)
        with (args.output / "metrics.csv").open("w", encoding="utf-8", newline="") as out:
            writer = csv.writer(out)
            writer.writerow(["strategy", "split", "hit_at_1", "hit_at_3", "n"])
            for key, value in metrics.items():
                writer.writerow([*key.split("/"), value["hit_at_1"], value["hit_at_3"], value["n"]])
        write_json(args.output / "statistics.json", stats)
        metadata_samples = []
        grounding_samples = []
        page_map = {(p.document_id, p.page): p for p in pages}
        for row in traces:
            if row["question"]["split"] != "test":
                continue
            q = row["question"]
            grounding_samples.append({"strategy": row["strategy"], "question": q,
                "hits": row["hits"], "score": None, "reason": "", "reviewer": ""})
            for rank, hit in enumerate(row["hits"], 1):
                meta = hit["metadata"]
                page = page_map.get((meta.get("document_id"), meta.get("page")))
                metadata_samples.append({"strategy": row["strategy"], "question_id": q["id"],
                    "rank": rank, "chunk_id": hit["chunk_id"], "actual": meta,
                    "expected_source": page.source if page else None,
                    "expected_section": page.metadata["section"] if page else None,
                    "correct": None, "reason": "", "reviewer": ""})
        write_json(args.output / "grounding_samples.json", grounding_samples)
        write_json(args.output / "metadata_samples.json", metadata_samples)
        write_json(args.output / "run.json", {"started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": time.perf_counter() - total_clock,
            "model_load_seconds": model_load, "search_seconds": search_seconds,
            "python": platform.python_version(), "platform": platform.platform(),
            "libraries": versions(), "model": MODEL_NAME, "model_revision": MODEL_REVISION,
            "dimensions": embedder.dimensions, "device": "cpu", "threads": 4,
            "model_max_seq_length": embedder.model.max_seq_length,
            "query_document_processing": "Same tokenizer, mean pooling, L2 normalization; no prefixes; query text only.",
            "store": "Chroma PersistentClient", "store_path": str(args.store.resolve()),
            "collections": ["day06_a", "day06_b", "day06_c"],
            "metric": "cosine", "search": "approximate HNSW, search_ef=100; native where metadata filter",
            "benchmark_sha256": sha256(ROOT / "benchmark/questions.json"),
            "pages_sha256": sha256(ROOT / "data/pages.jsonl"),
            "traces_sha256": sha256(args.output / "traces.jsonl"),
            "seed": "No random split; frozen ordered questions. HNSW internal randomness not controlled.",
            "api_cost_usd": 0, "cost_scope": "No paid API used; electricity, hardware, network not monetized.",
            "config": {"A": {"method": "fixed", "size": 500, "overlap": 50, "filter": False},
                       "B": {"method": "paragraph", "max_size": 1000, "filter": False},
                       "C": {"method": "paragraph", "max_size": 1000, "filter": "only when supplied in question"}}})
        print(json.dumps(metrics, indent=2), flush=True)
    except Exception:
        logging.exception("Pipeline failed; no model/backend fallback was used")
        raise


if __name__ == "__main__":
    main()
