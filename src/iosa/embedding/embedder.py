"""Call Ollama's embedding endpoint to turn text into vectors.

Used both at indexing time (embedding child chunks) and query time
(embedding the user's question), so retrieval and indexing always
share the same embedding space.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")


def embed_text(text: str) -> list[float]:
    """Embed a single string of text, returns a vector as a list of floats."""
    response = httpx.post(
        f"{OLLAMA_HOST}/api/embeddings",
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()["embedding"]
