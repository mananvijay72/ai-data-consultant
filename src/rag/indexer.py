"""
indexer.py
----------
Builds (or rebuilds) a persistent Chroma collection from a folder of
markdown documents. Used for:
  - the static domain corpus (restaurant / ecommerce), Phase 1
  - per-client memory collections (Phase 6), via memory_indexer.py which
    calls the same `get_or_create_collection` + `.add()` pattern directly
    on already-chunked artifact text (no folder of files involved there).
"""
import glob
import os
import chromadb
from src.config import CONFIG
from src.rag.chunker import chunk_file
from src.rag.embedder import embed_texts


def get_client(persist_dir: str = None) -> chromadb.PersistentClient:
    persist_dir = persist_dir or CONFIG["rag"]["vectorstore_dir"]
    os.makedirs(persist_dir, exist_ok=True)
    return chromadb.PersistentClient(path=persist_dir)


def build_domain_collection(domain: str) -> int:
    """
    Reads all .md files under data/rag_corpus/{domain}/, chunks + embeds
    them, and writes them into a Chroma collection named after the domain.
    Returns the number of chunks indexed.
    """
    corpus_dir = os.path.join(CONFIG["rag"]["domain_corpus_dir"], domain)
    md_files = sorted(glob.glob(os.path.join(corpus_dir, "*.md")))
    if not md_files:
        raise FileNotFoundError(f"No .md files found in {corpus_dir}")

    client = get_client()
    # Fresh rebuild each time keeps the demo simple and reproducible.
    try:
        client.delete_collection(domain)
    except Exception:
        pass
    collection = client.create_collection(name=domain)

    all_texts, all_ids, all_metadatas = [], [], []
    for path in md_files:
        chunks = chunk_file(path)
        for c in chunks:
            chunk_id = f"{os.path.basename(path)}::{c.chunk_index}"
            all_texts.append(c.text)
            all_ids.append(chunk_id)
            all_metadatas.append({"source_file": os.path.basename(path)})

    embeddings = embed_texts(all_texts, task_type="retrieval_document")
    collection.add(
        ids=all_ids,
        documents=all_texts,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )
    return len(all_texts)


def add_texts_to_collection(collection_name: str, texts: list, metadatas: list,
                             ids: list, persist_dir: str = None) -> None:
    """
    Generic add used by memory_indexer.py to write client-artifact chunks
    into a per-client Chroma collection (created if it doesn't exist).
    """
    client = get_client(persist_dir)
    collection = client.get_or_create_collection(name=collection_name)
    embeddings = embed_texts(texts, task_type="retrieval_document")
    collection.add(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
