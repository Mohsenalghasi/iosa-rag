"""Build the FAISS index from all parsed documents.

Reads every parsed JSON in data/processed/, chunks each into
parent/child pairs, embeds every child chunk via Ollama, and writes
two files to data/index/: the FAISS vector index, and a JSON sidecar
mapping each vector's position to its child and parent metadata.

Re-run this whenever the document corpus changes; at this corpus size
a full rebuild is cheap and simpler than incremental updates.
"""

import json
import os
from pathlib import Path

import faiss
import numpy as np
from dotenv import load_dotenv

from src.iosa.embedding.chunker import chunk_document
from src.iosa.embedding.embedder import embed_text

load_dotenv()

PROCESSED_DIR = Path("data/processed")
INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/index/faiss.index")
METADATA_PATH = os.getenv("FAISS_METADATA_PATH", "data/index/metadata.json")


def build_index():
    all_children = []
    all_parents = {}  # parent_id -> parent dict, deduplicated across documents

    json_files = sorted(PROCESSED_DIR.glob("*.json"))
    print(f"Found {len(json_files)} parsed documents")

    for path in json_files:
        with open(path) as f:
            parsed = json.load(f)

        parents, children = chunk_document(parsed)
        for p in parents:
            all_parents[p.parent_id] = {
                "parent_id": p.parent_id,
                "text": p.text,
                "source": p.source,
                "page_number": p.page_number,
            }
        all_children.extend(children)
        print(f"  {path.name}: {len(parents)} parents, {len(children)} children")

    print(f"\nTotal children to embed: {len(all_children)}")

    vectors = []
    child_metadata = []
    for i, child in enumerate(all_children):
        vec = embed_text(child.embedding_text)
        vectors.append(vec)
        child_metadata.append({
            "child_id": child.child_id,
            "parent_id": child.parent_id,
            "text": child.text,
            "source": child.source,
            "page_number": child.page_number,
        })
        if (i + 1) % 10 == 0 or (i + 1) == len(all_children):
            print(f"  embedded {i + 1}/{len(all_children)}")

    vectors_array = np.array(vectors, dtype="float32")
    faiss.normalize_L2(vectors_array)  # required for IndexFlatIP to behave as cosine similarity

    dimension = vectors_array.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(vectors_array)

    Path(INDEX_PATH).parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, INDEX_PATH)

    with open(METADATA_PATH, "w") as f:
        json.dump({
            "children": child_metadata,
            "parents": list(all_parents.values()),
        }, f, indent=2)

    print(f"\nSaved FAISS index to {INDEX_PATH} ({index.ntotal} vectors, dim {dimension})")
    print(f"Saved metadata to {METADATA_PATH}")


if __name__ == "__main__":
    build_index()
