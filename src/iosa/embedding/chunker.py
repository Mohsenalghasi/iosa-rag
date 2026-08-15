"""Structure-aware parent-child chunking for parsed documents.

Splits page text into large parent chunks (for LLM generation context)
and smaller child chunks nested inside each parent (for retrieval
precision), linked by parent_id. Each child is prefixed with source
and page metadata before embedding.
"""

import uuid
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class ParentChunk:
    parent_id: str
    text: str
    source: str
    page_number: int


@dataclass
class ChildChunk:
    child_id: str
    parent_id: str
    text: str
    embedding_text: str
    source: str
    page_number: int


def _make_splitter(chunk_size_words: int, overlap_words: int) -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_words,
        chunk_overlap=overlap_words,
        length_function=lambda text: len(text.split()),
        separators=["\n\n", "\n", ". ", " ", ""],
    )


def chunk_document(
    parsed_json: dict,
    parent_size: int = 800,
    parent_overlap: int = 100,
    child_size: int = 300,
    child_overlap: int = 50,
) -> tuple[list[ParentChunk], list[ChildChunk]]:
    """Split a parsed document's pages into parent and child chunks."""
    parent_splitter = _make_splitter(parent_size, parent_overlap)
    child_splitter = _make_splitter(child_size, child_overlap)

    source = parsed_json["source"]
    parents: list[ParentChunk] = []
    children: list[ChildChunk] = []

    for page in parsed_json["pages"]:
        page_text = page["text"].strip()
        if not page_text:
            continue

        for parent_text in parent_splitter.split_text(page_text):
            parent_id = str(uuid.uuid4())
            parents.append(
                ParentChunk(
                    parent_id=parent_id,
                    text=parent_text,
                    source=source,
                    page_number=page["page_number"],
                )
            )

            for child_text in child_splitter.split_text(parent_text):
                prefix = f"Doc: {source}. Page: {page['page_number']}. Text: "
                children.append(
                    ChildChunk(
                        child_id=str(uuid.uuid4()),
                        parent_id=parent_id,
                        text=child_text,
                        embedding_text=prefix + child_text,
                        source=source,
                        page_number=page["page_number"],
                    )
                )

    return parents, children
