"""
Pure unit tests for chunker.py — no Gemini API key required, run these
first to sanity-check the chunking logic in isolation.
"""
from src.rag.chunker import chunk_document


def test_short_document_is_single_chunk():
    text = "This is a short paragraph.\n\nAnd another short one."
    chunks = chunk_document(text, source_file="test.md", chunk_size=400, chunk_overlap=50)
    assert len(chunks) == 1
    assert "short paragraph" in chunks[0].text


def test_long_document_splits_into_multiple_chunks():
    paragraph = " ".join(["word"] * 300)
    text = f"{paragraph}\n\n{paragraph}\n\n{paragraph}"
    chunks = chunk_document(text, source_file="test.md", chunk_size=400, chunk_overlap=50)
    assert len(chunks) > 1


def test_overlap_carries_words_into_next_chunk():
    paragraph_a = " ".join([f"wordA{i}" for i in range(300)])
    paragraph_b = " ".join([f"wordB{i}" for i in range(300)])
    text = f"{paragraph_a}\n\n{paragraph_b}"
    chunks = chunk_document(text, source_file="test.md", chunk_size=300, chunk_overlap=50)
    assert len(chunks) >= 2
    # last 50 words of chunk 0 should reappear at the start of chunk 1
    tail_of_first = chunks[0].text.split()[-10:]
    start_of_second = chunks[1].text.split()[:60]
    assert any(word in start_of_second for word in tail_of_first)


def test_chunk_index_and_source_are_set():
    text = "Just one paragraph here."
    chunks = chunk_document(text, source_file="my_doc.md")
    assert chunks[0].source_file == "my_doc.md"
    assert chunks[0].chunk_index == 0
