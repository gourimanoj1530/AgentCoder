from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
import os


def get_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=api_key,
        temperature=0.2,
        max_tokens=2048,
    )


# ─── Prompt Templates ─────────────────────────────────────────────────────────

PLANNER_PROMPT = """
You are a senior software engineer planning how to solve a coding problem step by step.

User's problem:
{user_input}

Past context / errors from memory:
{memory_context}

Break this problem into an ordered list of concrete steps.
Each step should be one clear action (e.g. "Write a Python function to...", "Search for...", "Look up docs for...").

Respond ONLY with a valid JSON array of strings. No explanation. No markdown.
Example: ["Step 1: ...", "Step 2: ...", "Step 3: ..."]
"""


REASON_PROMPT = """
You are an AI coding agent working through a problem step by step.

Original problem: {user_input}
Current step: {current_step}
Iteration: {iteration}

Last tool result:
{tool_result}

Errors so far:
{error_log}

Think through what you know so far and what needs to happen next.
Be concise. This is your internal reasoning — do not write code yet.
"""


ACT_PROMPT = """
Based on this reasoning:
{last_reasoning}

Decide which tool to call and what input to give it.

Available tools:
- code_executor: runs Python code. Use when you need to write or test code.
- web_search: searches the web. Use when you need external information or docs.
- doc_lookup: fetches Python/library documentation. Use when you need API reference.

Respond ONLY with a valid JSON object. No explanation. No markdown.
Example:
{{"tool": "code_executor", "input": "print('hello world')"}}
or
{{"tool": "web_search", "input": "how to reverse a linked list in Python"}}
"""


OUTPUT_PROMPT = """
You are a helpful coding assistant presenting a final answer to the user.

Original problem: {user_input}

Final output from execution:
{final_output}

Errors encountered (if any):
{error_log}

Write a clean, friendly response that:
1. Shows the working code solution
2. Briefly explains how it works
3. Mentions any errors that were encountered and how they were resolved (if any)

Format the code in markdown code blocks.
"""