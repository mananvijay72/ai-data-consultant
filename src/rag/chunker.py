"""
chunker.py
----------
Splits a markdown document into overlapping chunks, paragraph-aware so we
never cut a sentence in half. Simple and dependency-free (no external NLP
libs) — appropriate for a 15-20 document demo corpus where chunk quality
matters more than throughput.

Strategy:
1. Split on blank lines -> paragraphs (this also naturally separates
   markdown headers, bullet lists, etc. into their own units).
2. Pack paragraphs into chunks up to `chunk_size` words.
3. Carry the last `chunk_overlap` words of a chunk into the next chunk, so
   a concept split across a paragraph boundary is still retrievable from
   either chunk.
"""
from dataclasses import dataclass
from typing import List
from src.config import CONFIG


@dataclass
class Chunk:
    text: str
    chunk_index: int
    source_file: str


def _split_paragraphs(text: str) -> List[str]:
    raw_paragraphs = [p.strip() for p in text.split("\n\n")]
    return [p for p in raw_paragraphs if p]


def chunk_document(text: str, source_file: str,
                    chunk_size: int = None, chunk_overlap: int = None) -> List[Chunk]:
    chunk_size = chunk_size or CONFIG["rag"]["chunk_size"]
    chunk_overlap = chunk_overlap or CONFIG["rag"]["chunk_overlap"]

    paragraphs = _split_paragraphs(text)
    chunks: List[Chunk] = []
    current_words: List[str] = []

    def flush():
        if current_words:
            chunks.append(Chunk(
                text=" ".join(current_words),
                chunk_index=len(chunks),
                source_file=source_file,
            ))

    for para in paragraphs:
        para_words = para.split()
        if len(current_words) + len(para_words) > chunk_size and current_words:
            flush()
            # carry overlap forward
            current_words = current_words[-chunk_overlap:] if chunk_overlap else []
        current_words.extend(para_words)

    flush()
    return chunks


def chunk_file(path: str) -> List[Chunk]:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    return chunk_document(text, source_file=path)
