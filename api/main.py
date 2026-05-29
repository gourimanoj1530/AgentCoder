import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from graph.graph import agent
from tracing.langsmith import setup_tracing
from db.database import init_db
from api.routes import router
from api.ws import ws_router

setup_tracing()
init_db()

app = FastAPI(
    title="AgentCoder API",
    description="Agentic coding assistant powered by LangGraph + Groq",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
app.include_router(ws_router)


class RunRequest(BaseModel):
    problem: str
    project_id: str = None


class RunResponse(BaseModel):
    answer: str
    steps_taken: int
    errors: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run", response_model=RunResponse)
async def run_agent(request: RunRequest):
    if not request.problem.strip():
        raise HTTPException(status_code=400, detail="Problem cannot be empty.")

    try:
        final_state = agent.invoke({
            "user_input": request.problem,
            "messages": [HumanMessage(content=request.problem)],
            "plan": [],
            "current_step": 0,
            "selected_tool": None,
            "tool_input": None,
            "tool_result": None,
            "error_log": [],
            "iteration_count": 0,
            "final_output": None,
        })

        messages = final_state.get("messages", [])
        answer = messages[-1].content if messages else "No response generated."

        return RunResponse(
            answer=answer,
            steps_taken=final_state.get("iteration_count", 0),
            errors=final_state.get("error_log", []),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))