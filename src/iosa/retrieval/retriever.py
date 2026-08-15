"""Search the FAISS index for a query and return parent chunks with metadata.

Embeds the query with the same model used at indexing time, searches FAISS
for the closest child chunks, then expands each hit to its parent chunk for
generation (children give precise matching, parents give the LLM more
context to work with). Deduplicates by parent so a well-matched parent
with multiple strong child hits is only returned once.
"""
import json
import os
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv

from src.iosa.embedding.embedder import embed_text

load_dotenv()

INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/index/faiss.index")
METADATA_PATH = os.getenv("FAISS_METADATA_PATH", "data/index/metadata.json")

_index = None
_children = None
_parents = None


def _load():
    """Load the FAISS index and metadata sidecar once, cache in module state."""
    global _index, _children, _parents
    if _index is None:
        _index = faiss.read_index(INDEX_PATH)
        with open(METADATA_PATH) as f:
            metadata = json.load(f)
        _children = metadata["children"]
        _parents = {p["parent_id"]: p for p in metadata["parents"]}


def retrieve(query: str, k: int = 5) -> list[dict]:
    """Return up to k parent chunks ranked by their best matching child's score.

    Each result dict has: text, source, page_number, score (0-1 cosine
    similarity of the best matching child chunk), parent_id.
    """
    _load()

    query_vector = np.array([embed_text(query)], dtype="float32")
    faiss.normalize_L2(query_vector)

    scores, indices = _index.search(query_vector, k)

    results = []
    seen_parent_ids = set()
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        child = _children[idx]
        parent_id = child["parent_id"]
        if parent_id in seen_parent_ids:
            continue
        seen_parent_ids.add(parent_id)

        parent = _parents.get(parent_id)
        if parent is None:
            continue

        results.append({
            "text": parent["text"],
            "source": parent["source"],
            "page_number": parent["page_number"],
            "score": float(score),
            "parent_id": parent_id,
        })

    return results