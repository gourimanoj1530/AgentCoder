from typing import TypedDict, Annotated, List, Optional
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    # Full conversation history (LangGraph appends automatically with operator.add)
    messages: Annotated[List[BaseMessage], operator.add]

    # The user's original coding problem
    user_input: str

    # Planner's step-by-step breakdown of the task
    plan: List[str]

    # Which step we're currently executing
    current_step: int

    # Tool the agent decided to call: "code_executor" | "web_search" | "doc_lookup"
    selected_tool: Optional[str]

    # Raw input to the selected tool (e.g. code string, search query)
    tool_input: Optional[str]

    # Result returned by the tool
    tool_result: Optional[str]

    # Running log of errors seen this session (for memory / retry logic)
    error_log: List[str]

    # Number of ReAct iterations so far (used for loop termination)
    iteration_count: int

    # Final verified output to return to the user
    final_output: Optional[str]