"""
embedder.py
-----------
Thin wrapper around Gemini's embedding API. Kept separate from
indexer/retriever so the embedding backend can be swapped later (e.g. to a
local sentence-transformers model) without touching indexing/retrieval
logic.
"""
from typing import List
from google import genai
from src.config import GEMINI_API_KEY, CONFIG

_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Copy .env.example to .env and "
                "add your free key from https://aistudio.google.com/apikey"
            )
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def embed_texts(texts: List[str], task_type: str = "retrieval_document") -> List[List[float]]:
    """
    Embed a batch of texts with Gemini's embedding model.

    task_type: "retrieval_document" when embedding corpus chunks for
               storage, "retrieval_query" when embedding a user's question.
               Gemini's embedding model uses this to optimize the vector
               space for asymmetric search (short query vs. long doc).
    """
    client = _get_client()
    model = CONFIG["llm"]["embedding_model"]
    embeddings = []
    # Gemini's embed_content API accepts one text at a time in the stable
    # SDK surface; batch in a simple loop (fine for a 15-20 doc corpus).
    for text in texts:
        result = client.models.embed_content(
            model=model,
            contents=text,
            config={"task_type": task_type},
        )
        embeddings.append(result.embeddings[0].values)
    return embeddings


def embed_query(text: str) -> List[float]:
    return embed_texts([text], task_type="retrieval_query")[0]
