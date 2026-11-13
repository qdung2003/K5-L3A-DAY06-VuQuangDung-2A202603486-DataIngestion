"""Download only required model files at an immutable upstream commit."""
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
BASE = f"https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/{REVISION}/"
FILES = ["README.md", "config.json", "config_sentence_transformers.json", "modules.json",
         "sentence_bert_config.json", "special_tokens_map.json", "tokenizer.json",
         "tokenizer_config.json", "vocab.txt", "1_Pooling/config.json", "model.safetensors"]


def main():
    folder = ROOT / ".cache" / "all-MiniLM-L6-v2"
    hashes = {}
    for name in FILES:
        path = folder / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            print(f"Downloading {name}", flush=True)
            temporary = path.with_suffix(path.suffix + ".part")
            with urllib.request.urlopen(BASE + name, timeout=180) as response, temporary.open("wb") as out:
                shutil.copyfileobj(response, out)
            temporary.replace(path)
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    output = {"model": "sentence-transformers/all-MiniLM-L6-v2", "revision": REVISION,
              "license": "Apache-2.0 (upstream model card)", "sha256": hashes}
    (ROOT / "data" / "model_manifest.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print("Model download and hash inventory complete")


if __name__ == "__main__":
    main()
