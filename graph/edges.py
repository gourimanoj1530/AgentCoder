from graph.state import AgentState

MAX_ITERATIONS = 6  # Safety cap — agent won't loop forever


def should_continue(state: AgentState) -> str:
    """
    After the Observe node reads the tool result, decide:
    - If final_output is set → we're done, go to output node
    - If we've hit the iteration cap → force output (avoid infinite loop)
    - Otherwise → loop back to Reason for the next step
    """
    if state.get("final_output"):
        return "output"

    if state["iteration_count"] >= MAX_ITERATIONS:
        return "output"  # Graceful exit even without a perfect answer

    return "reason"


def route_tool(state: AgentState) -> str:
    """
    After the Act node picks a tool, route to the right tool node.
    Defaults to code_executor if the agent returns something unexpected.
    """
    tool = state.get("selected_tool", "code_executor")

    if tool == "web_search":
        return "web_search"
    elif tool == "doc_lookup":
        return "doc_lookup"
    else:
        return "code_executor"  # Default — most common for a coding assistant