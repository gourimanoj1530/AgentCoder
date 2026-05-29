import os
from dotenv import load_dotenv

load_dotenv()


def setup_tracing() -> None:
    """
    Enables LangSmith tracing by setting the required environment variables.
    Call this once at app startup (in main.py) before the agent runs.

    LangSmith automatically intercepts all LangChain/LangGraph calls
    once these env vars are set — no code changes needed in nodes.
    """
    api_key = os.getenv("LANGSMITH_API_KEY")

    if not api_key:
        print("[Tracing] LANGSMITH_API_KEY not set — tracing disabled.")
        return

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = api_key
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "agentcoder")

    print(f"[Tracing] LangSmith tracing enabled → project: {os.environ['LANGCHAIN_PROJECT']}")