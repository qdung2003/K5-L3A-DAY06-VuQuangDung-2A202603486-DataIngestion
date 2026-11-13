"""Check the selected Chroma backend, or the optional original PostgreSQL stack."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "starter"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["chroma", "postgres"], default="chroma")
    args = parser.parse_args()
    if args.backend == "postgres":
        import psycopg
        from dotenv import load_dotenv
        load_dotenv(ROOT / "starter/.env")
        url = os.getenv("DATABASE_URL")
        if not url:
            raise SystemExit("DATABASE_URL missing; configure starter/.env")
        try:
            with psycopg.connect(url, connect_timeout=5) as connection:
                row = connection.execute("SELECT current_database(), current_setting('server_version'), extversion FROM pg_extension WHERE extname = 'vector'").fetchone()
                if not row:
                    raise SystemExit("pgvector extension missing")
                print(f"Database: {row[0]} | PostgreSQL: {row[1]} | pgvector: {row[2]}")
        except psycopg.Error:
            raise SystemExit("PostgreSQL connection failed; inspect Docker, port and DATABASE_URL")
    else:
        from src.validation import load_inputs, verify_model
        from src.embeddings import MyEmbedder
        from src.store import ChromaStore
        pages, questions, _ = load_inputs(ROOT)
        verify_model(ROOT)
        model = MyEmbedder()
        vector = model.embed_query("How are Python files closed?")
        store = ChromaStore(ROOT / "starter/vector_store", model.dimensions)
        store.create_schema()
        counts = {s: store.collection(s).count() for s in "ABC"}
        if len(vector) != 384 or not any(vector):
            raise ValueError("Invalid real embedding")
        output = {"backend": "Chroma PersistentClient", "dimensions": 384,
                  "units": len(pages), "questions": len(questions), "persisted_counts": counts,
                  "status": "Setup OK", "docker_required": False}
        (ROOT / "results").mkdir(exist_ok=True)
        (ROOT / "results/setup.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
        print(json.dumps(output, indent=2))
    print("Setup OK")


if __name__ == "__main__":
    main()
