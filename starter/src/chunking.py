"""Character windows and paragraph-aware chunks with exact source offsets."""
import hashlib
import re
from .models import Chunk, DocumentPage


def make_chunk(page: DocumentPage, start: int, end: int, method: str) -> Chunk:
    text = page.text[start:end]
    key = f"{page.document_id}|{page.page}|{method}|{start}|{end}|{text}"
    return Chunk(hashlib.sha256(key.encode()).hexdigest(), page.document_id,
                 page.source, page.page, text,
                 {**page.metadata, "start_char": start, "end_char": end})


def fixed_size(page: DocumentPage, size: int = 500, overlap: int = 50) -> list[Chunk]:
    if not 0 <= overlap < size:
        raise ValueError("Require 0 <= overlap < size")
    chunks = []
    for start in range(0, len(page.text), size - overlap):
        end = min(start + size, len(page.text))
        chunks.append(make_chunk(page, start, end, f"fixed:{size}:{overlap}"))
        if end == len(page.text):
            break
    return chunks


def by_paragraph(page: DocumentPage, max_size: int = 1000) -> list[Chunk]:
    if max_size < 1:
        raise ValueError("max_size must be positive")
    spans = [(m.start(), m.end()) for m in re.finditer(r"\S[\s\S]*?(?=\n\n|\Z)", page.text)]
    ranges = []
    for start, end in spans:
        while end - start > max_size:
            window = page.text[start:start + max_size]
            boundaries = [m.end() for m in re.finditer(r"[.!?](?:\s+)|\n| +", window)]
            cut = start + (max(boundaries) if boundaries else max_size)
            ranges.append((start, cut))
            start = cut
        if start < end:
            ranges.append((start, end))
    grouped = []
    for start, end in ranges:
        if grouped and end - grouped[-1][0] <= max_size:
            grouped[-1] = (grouped[-1][0], end)
        else:
            grouped.append((start, end))
    return [make_chunk(page, start, end, f"paragraph:{max_size}") for start, end in grouped]
