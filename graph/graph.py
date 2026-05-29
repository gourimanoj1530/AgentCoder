from langgraph.graph import StateGraph, END
from graph.state import AgentState
from graph.nodes import (
    planner_node,
    reason_node,
    act_node,
    code_executor_node,
    web_search_node,
    doc_lookup_node,
    observe_node,
    output_node,
)
from graph.edges import should_continue, route_tool


def build_graph() -> StateGraph:
    """
    Wires all nodes and edges into the LangGraph StateGraph.

    Flow:
        planner → reason → act → [tool] → observe → reason (loop)
                                                   ↘ output → END
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    graph.add_node("planner",       planner_node)
    graph.add_node("reason",        reason_node)
    graph.add_node("act",           act_node)
    graph.add_node("code_executor", code_executor_node)
    graph.add_node("web_search",    web_search_node)
    graph.add_node("doc_lookup",    doc_lookup_node)
    graph.add_node("observe",       observe_node)
    graph.add_node("output",        output_node)

    # ── Entry point ───────────────────────────────────────────────────────────
    graph.set_entry_point("planner")

    # ── Fixed edges ───────────────────────────────────────────────────────────
    graph.add_edge("planner", "reason")
    graph.add_edge("reason",  "act")

    # ── Conditional: Act → which tool? ────────────────────────────────────────
    graph.add_conditional_edges(
        "act",
        route_tool,
        {
            "code_executor": "code_executor",
            "web_search":    "web_search",
            "doc_lookup":    "doc_lookup",
        }
    )

    # ── All tools feed into observe ───────────────────────────────────────────
    graph.add_edge("code_executor", "observe")
    graph.add_edge("web_search",    "observe")
    graph.add_edge("doc_lookup",    "observe")

    # ── Conditional: Observe → loop back or finish ────────────────────────────
    graph.add_conditional_edges(
        "observe",
        should_continue,
        {
            "reason": "reason",  # Keep looping
            "output": "output",  # Done
        }
    )

    # ── Output is the terminal node ───────────────────────────────────────────
    graph.add_edge("output", END)

    return graph.compile()


# Compiled graph — import this in your FastAPI app
agent = build_graph()
