"""Shared state passed between every node in the IOSA agent graph.

LangGraph threads this dict through the whole run, each node reads the
fields it needs and returns a partial update that gets merged in.
"""
from typing import TypedDict


class AgentState(TypedDict):
    query: str  # original user question, never modified
    rewritten_query: str  # current query used for retrieval, may change on retry
    retries: int  # number of rewrite attempts so far, capped at MAX_RETRIES
    retrieved_docs: list[dict]  # output of retrieve(), parent chunks with scores
    grade: str  # "relevant" or "not_relevant", set by the grade node
    answer: str  # final generated answer, set by the generate node
    refused: bool  # True if we gave up after max retries without a good match
    route: str  # "vector", "sql", or "direct", set by the router node
    sql_result: list[dict]  # rows returned by the SQL tool node
    sql_query: str  # the SQL query the LLM generated, for logging/debugging
