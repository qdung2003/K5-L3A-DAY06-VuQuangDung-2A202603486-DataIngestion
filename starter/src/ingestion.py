"""Traceable PDF extraction and conservative text normalization."""
import logging
import re
import unicodedata
from pathlib import Path
from pypdf import PdfReader
from .models import DocumentPage


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    lines = [re.sub(r"[ \t]+$", "", line.expandtabs(4)) for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    pages = []
    for number, page in enumerate(PdfReader(path).pages, 1):
        text = normalize_text(page.extract_text() or "")
        if not text:
            logging.error("PDF page has no text: %s page %s; OCR required", path, number)
        pages.append(DocumentPage(document_id, source, number, text, {"empty_text": not bool(text)}))
    return pages
