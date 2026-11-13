"""Fetch licensed, versioned CPython tutorial and create disjoint text units."""
import hashlib
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "starter"))
from src.ingestion import normalize_text

CHAPTERS = ["controlflow", "datastructures", "modules", "inputoutput", "errors", "classes", "stdlib", "stdlib2"]
BASE = "https://raw.githubusercontent.com/python/cpython/v3.13.0/"


def fetch(url, path):
    if not path.exists():
        with urllib.request.urlopen(url, timeout=90) as response:
            content = response.read()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return path.read_bytes()


def clean_rst(raw):
    raw = re.sub(r"(?m)^(\s*)\.\. (?:method|function|class):: (.+)$", r"\1\2", raw)
    lines = [line for line in raw.splitlines()
             if not re.match(r"^\s*\.\. (?:_|[a-zA-Z-]+::)", line)
             and not re.match(r"^\s*(?::(?:noindex|class|name):|(?:single|pair):)", line)
             and not re.fullmatch(r"[\s*=-]{3,}", line)]
    text = "\n".join(lines)
    tick = chr(96)
    text = re.sub(r":[\w:]+:" + tick + "([^" + tick + "]+)" + tick,
                  lambda m: m[1].lstrip("!~"), text)
    return normalize_text(text.replace(tick * 2, ""))


def units(text):
    cuts = [0]
    for match in re.finditer(r"\n\n", text):
        if match.start() - cuts[-1] >= 1800:
            cuts.append(match.end())
    if len(text) - cuts[-1] < 1500 and len(cuts) > 1:
        cuts.pop()
    cuts.append(len(text))
    return [(a, b, text[a:b]) for a, b in zip(cuts, cuts[1:])]


def main():
    corpus = ROOT / "data" / "python_tutorial"
    accessed = datetime.now(timezone.utc).isoformat()
    pages, manifest = [], []
    fetch(BASE + "LICENSE", corpus / "LICENSE.txt")
    fetch(BASE + "Doc/license.rst", corpus / "documentation-license.rst")
    for chapter in CHAPTERS:
        relative = f"Doc/tutorial/{chapter}.rst"
        raw = fetch(BASE + relative, corpus / "raw" / f"{chapter}.rst")
        normalized = clean_rst(raw.decode("utf-8"))
        (corpus / f"{chapter}.txt").write_text(normalized, encoding="utf-8")
        title = next(line for line in normalized.splitlines() if line.strip())
        source_id = f"python-tutorial-{chapter}"
        source = BASE + relative
        source_pages = []
        for index, (start, end, content) in enumerate(units(normalized), 1):
            page_id = f"{chapter}:{index:03d}"
            if len(normalize_text(content)) < 1500:
                raise ValueError(f"Short content unit: {page_id}")
            pages.append({"document_id": source_id, "source": source, "page": page_id,
                "text": content, "metadata": {"section": chapter, "version": "3.13.0",
                "language": "en", "unit_start": start, "unit_end": end}})
            source_pages.append({"page": page_id, "start_char": start, "end_char": end,
                                 "normalized_char_count": len(normalize_text(content))})
        manifest.append({"source_id": source_id, "title": title, "source_path_or_url": source,
            "local_path": f"data/python_tutorial/raw/{chapter}.rst",
            "normalized_path": f"data/python_tutorial/{chapter}.txt",
            "license_or_permission": "PSF License Version 2 covers software and documentation; documentation examples/recipes/code additionally Zero-Clause BSD from Python 3.8.6. Copyright notices retained.",
            "license_path": "data/python_tutorial/LICENSE.txt", "accessed_at": accessed,
            "snapshot": "CPython v3.13.0", "sha256": hashlib.sha256(raw).hexdigest(),
            "physical_pages": None, "counted_units": len(source_pages), "pages": source_pages,
            "normalized_char_count": len(normalized)})
    if len(pages) < 30:
        raise ValueError("Need >=30 source units")
    (ROOT / "data" / "pages.jsonl").write_text("".join(json.dumps(p, ensure_ascii=False) + "\n" for p in pages), encoding="utf-8")
    (ROOT / "data" / "manifest.json").write_text(json.dumps({"counting_rule":
        "Non-overlapping sequential text units at paragraph boundaries, each >=1500 normalized characters; short tail merged. Source offsets [start,end) refer to normalized chapter text. No physical PDF pages, no OCR, no duplicated content.",
        "total_counted_units": len(pages), "sources": manifest}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Prepared {len(pages)} source units; {sum(len(p['text']) for p in pages)} characters")


if __name__ == "__main__":
    main()
