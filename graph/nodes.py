from langchain_core.messages import HumanMessage, AIMessage
from graph.state import AgentState
from llm.client import get_llm, PLANNER_PROMPT, REASON_PROMPT, ACT_PROMPT, OUTPUT_PROMPT
from tools.executor import run_code
from tools.search import web_search
from tools.docs import doc_lookup
from memory.store import load_memory, save_memory
import json


# ─── Node 1: Planner ──────────────────────────────────────────────────────────

def planner_node(state: AgentState) -> dict:
    llm = get_llm()
    memory_context = load_memory()

    prompt = PLANNER_PROMPT.format(
        user_input=state["user_input"],
        memory_context=memory_context or "No previous context."
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        plan = json.loads(response.content)
        if not isinstance(plan, list):
            plan = [response.content]
    except json.JSONDecodeError:
        plan = [response.content]

    return {
        "plan": plan,
        "current_step": 0,
        "iteration_count": 0,
        "error_log": [],
        "messages": [HumanMessage(content=state["user_input"]), AIMessage(content=f"Plan: {plan}")]
    }


# ─── Node 2: Reason ───────────────────────────────────────────────────────────

def reason_node(state: AgentState) -> dict:
    llm = get_llm()
    current_step = state["plan"][state["current_step"]] if state["plan"] else "Solve the problem."
    tool_result = state.get("tool_result", "No result yet.")
    error_log = state.get("error_log", [])

    prompt = REASON_PROMPT.format(
        user_input=state["user_input"],
        current_step=current_step,
        tool_result=tool_result,
        error_log="\n".join(error_log) if error_log else "None so far.",
        iteration=state["iteration_count"]
    )

    response = llm.invoke(state["messages"] + [HumanMessage(content=prompt)])

    return {
        "messages": [AIMessage(content=response.content)]
    }


# ─── Node 3: Act ──────────────────────────────────────────────────────────────

def act_node(state: AgentState) -> dict:
    llm = get_llm()
    prompt = ACT_PROMPT.format(
        last_reasoning=state["messages"][-1].content
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    try:
        decision = json.loads(response.content)
        selected_tool = decision.get("tool", "code_executor")
        tool_input = decision.get("input", "")
    except json.JSONDecodeError:
        selected_tool = "code_executor"
        tool_input = response.content

    return {
        "selected_tool": selected_tool,
        "tool_input": tool_input,
        "messages": [AIMessage(content=f"[Act] Using tool: {selected_tool}")]
    }


# ─── Node 4a: Code executor tool ──────────────────────────────────────────────

def code_executor_node(state: AgentState) -> dict:
    result = run_code(state["tool_input"])
    error_log = state.get("error_log", [])

    if result.get("error"):
        error_log = error_log + [result["error"]]
        save_memory(error_log)

    return {
        "tool_result": result.get("output") or result.get("error", "No output."),
        "error_log": error_log,
        "iteration_count": state["iteration_count"] + 1,
        "current_step": min(state["current_step"] + 1, len(state["plan"]) - 1),
        "messages": [AIMessage(content=f"[Code executor] {result}")]
    }


# ─── Node 4b: Web search tool ─────────────────────────────────────────────────

def web_search_node(state: AgentState) -> dict:
    result = web_search(state["tool_input"])
    return {
        "tool_result": result,
        "iteration_count": state["iteration_count"] + 1,
        "messages": [AIMessage(content=f"[Web search] {result[:300]}...")]
    }


# ─── Node 4c: Doc lookup tool ─────────────────────────────────────────────────

def doc_lookup_node(state: AgentState) -> dict:
    result = doc_lookup(state["tool_input"])
    return {
        "tool_result": result,
        "iteration_count": state["iteration_count"] + 1,
        "messages": [AIMessage(content=f"[Doc lookup] {result[:300]}...")]
    }


# ─── Node 5: Observe ──────────────────────────────────────────────────────────

def observe_node(state: AgentState) -> dict:
    all_steps_done = state["current_step"] >= len(state["plan"]) - 1
    no_errors = not state.get("error_log")

    if all_steps_done and no_errors:
        return {
            "final_output": state["tool_result"],
            "messages": [AIMessage(content="[Observe] Task complete.")]
        }

    return {
        "final_output": None,
        "messages": [AIMessage(content=f"[Observe] Step {state['current_step']} done. Continuing...")]
    }


# ─── Node 6: Output ───────────────────────────────────────────────────────────

def output_node(state: AgentState) -> dict:
    llm = get_llm()
    prompt = OUTPUT_PROMPT.format(
        user_input=state["user_input"],
        final_output=state.get("final_output", "No verified output produced."),
        error_log="\n".join(state.get("error_log", [])) or "None."
    )

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "messages": [AIMessage(content=response.content)]
    }