"""Wire all nodes into a LangGraph StateGraph.

This is the control flow of the agent. Nodes do the work,
this file just defines the order and branching logic.
"""
from langgraph.graph import StateGraph, END

from src.iosa.agent.state import AgentState
from src.iosa.agent.nodes import (
    router_node,
    retrieve_node,
    grade_node,
    rewrite_node,
    generate_node,
    refuse_node,
    sql_tool_node,
    direct_node,
    MAX_RETRIES,
)


def after_router(state: AgentState) -> str:
    """Branch based on the router's classification."""
    return state["route"]


def after_grade(state: AgentState) -> str:
    """Decide what to do after grading retrieved docs."""
    if state["grade"] == "relevant":
        return "generate"
    if state["retries"] < MAX_RETRIES:
        return "rewrite"
    return "refuse"


def build_graph():
    """Build and compile the agent graph."""
    graph = StateGraph(AgentState)

    # register all nodes
    graph.add_node("router", router_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("grade", grade_node)
    graph.add_node("rewrite", rewrite_node)
    graph.add_node("generate", generate_node)
    graph.add_node("refuse", refuse_node)
    graph.add_node("sql_tool", sql_tool_node)
    graph.add_node("direct", direct_node)

    # entry point
    graph.set_entry_point("router")

    # router branches into three paths
    graph.add_conditional_edges("router", after_router, {
        "vector": "retrieve",
        "sql": "sql_tool",
        "direct": "direct",
    })

    # vector path: retrieve -> grade -> (generate / rewrite / refuse)
    graph.add_edge("retrieve", "grade")
    graph.add_conditional_edges("grade", after_grade, {
        "generate": "generate",
        "rewrite": "rewrite",
        "refuse": "refuse",
    })
    graph.add_edge("rewrite", "retrieve")  # the retry loop

    # sql path: sql_tool -> generate
    graph.add_edge("sql_tool", "generate")

    # terminal nodes
    graph.add_edge("generate", END)
    graph.add_edge("refuse", END)
    graph.add_edge("direct", END)

    return graph.compile()
