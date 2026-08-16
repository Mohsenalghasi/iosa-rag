"""Tests for agent nodes. All LLM calls are mocked."""
from unittest.mock import patch

from src.iosa.agent.state import AgentState


def _base_state(**overrides) -> dict:
    """Create a minimal valid state dict."""
    state = {
        "query": "test question",
        "rewritten_query": "test question",
        "retries": 0,
        "retrieved_docs": [],
        "grade": "",
        "answer": "",
        "refused": False,
        "route": "",
        "sql_result": [],
        "sql_query": "",
    }
    state.update(overrides)
    return state


@patch("src.iosa.agent.nodes.chat", return_value="VECTOR")
def test_router_vector(mock_chat):
    from src.iosa.agent.nodes import router_node
    result = router_node(_base_state(query="what caused the explosion"))
    assert result["route"] == "vector"


@patch("src.iosa.agent.nodes.chat", return_value="SQL")
def test_router_sql(mock_chat):
    from src.iosa.agent.nodes import router_node
    result = router_node(_base_state(query="how many incidents on P-101"))
    assert result["route"] == "sql"


@patch("src.iosa.agent.nodes.chat", return_value="DIRECT")
def test_router_direct(mock_chat):
    from src.iosa.agent.nodes import router_node
    result = router_node(_base_state(query="hello"))
    assert result["route"] == "direct"


@patch("src.iosa.agent.nodes.chat", return_value="RELEVANT")
def test_grade_relevant(mock_chat):
    from src.iosa.agent.nodes import grade_node
    docs = [{"text": "some relevant text"}]
    result = grade_node(_base_state(retrieved_docs=docs))
    assert result["grade"] == "relevant"


@patch("src.iosa.agent.nodes.chat", return_value="NOT_RELEVANT")
def test_grade_not_relevant(mock_chat):
    from src.iosa.agent.nodes import grade_node
    docs = [{"text": "some text"}]
    result = grade_node(_base_state(retrieved_docs=docs))
    assert result["grade"] == "not_relevant"


def test_grade_empty_docs():
    from src.iosa.agent.nodes import grade_node
    result = grade_node(_base_state(retrieved_docs=[]))
    assert result["grade"] == "not_relevant"


@patch("src.iosa.agent.nodes.chat", return_value="rephrased query about explosions")
def test_rewrite_increments_retries(mock_chat):
    from src.iosa.agent.nodes import rewrite_node
    result = rewrite_node(_base_state(retries=0))
    assert result["retries"] == 1
    assert result["rewritten_query"] == "rephrased query about explosions"


def test_refuse_sets_refused():
    from src.iosa.agent.nodes import refuse_node
    result = refuse_node(_base_state())
    assert result["refused"] is True
    assert "don't have enough information" in result["answer"]
