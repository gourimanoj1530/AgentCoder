from fastapi import WebSocket, WebSocketDisconnect
from fastapi import APIRouter
import pyflakes.api
import pyflakes.messages
import io
import sys
import json

ws_router = APIRouter()


def analyze_code(code: str, filename: str = "main.py") -> list[dict]:
    """
    Runs pyflakes on the code and returns a list of diagnostics.
    Each diagnostic has: line, col, message, severity
    """
    diagnostics = []

    # Capture pyflakes output
    old_stderr = sys.stderr
    sys.stderr = io.StringIO()

    try:
        # pyflakes returns warning count
        result = pyflakes.api.check(code, filename)
    except SyntaxError as e:
        # Syntax errors come back as exceptions
        diagnostics.append({
            "line": e.lineno or 1,
            "col": e.offset or 1,
            "message": f"SyntaxError: {e.msg}",
            "severity": "error",
        })
        sys.stderr = old_stderr
        return diagnostics
    except Exception:
        sys.stderr = old_stderr
        return diagnostics

    stderr_output = sys.stderr.getvalue()
    sys.stderr = old_stderr

    # Parse pyflakes output lines
    # Format: filename:line:col: message
    for line in stderr_output.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split(":")
        if len(parts) >= 4:
            try:
                lineno = int(parts[1].strip())
                col = int(parts[2].strip()) if parts[2].strip().isdigit() else 1
                message = ":".join(parts[3:]).strip()
                severity = "error" if "Error" in message or "error" in message else "warning"
                diagnostics.append({
                    "line": lineno,
                    "col": col,
                    "message": message,
                    "severity": severity,
                })
            except (ValueError, IndexError):
                continue

    # Also do basic syntax check
    try:
        compile(code, filename, "exec")
    except SyntaxError as e:
        # Avoid duplicate if already caught
        already = any(d["line"] == e.lineno for d in diagnostics)
        if not already:
            diagnostics.append({
                "line": e.lineno or 1,
                "col": e.offset or 1,
                "message": f"SyntaxError: {e.msg}",
                "severity": "error",
            })

    return diagnostics


@ws_router.websocket("/ws/lint")
async def lint_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for live code linting.

    Client sends: {"code": "...", "filename": "main.py"}
    Server returns: {"diagnostics": [...]}

    Each diagnostic:
    {
        "line": 5,
        "col": 1,
        "message": "undefined name 'x'",
        "severity": "error" | "warning"
    }
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                code = payload.get("code", "")
                filename = payload.get("filename", "main.py")

                # Only lint Python files
                if not filename.endswith(".py"):
                    await websocket.send_text(json.dumps({"diagnostics": []}))
                    continue

                diagnostics = analyze_code(code, filename)
                await websocket.send_text(json.dumps({"diagnostics": diagnostics}))

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"diagnostics": [], "error": "Invalid JSON"}))

    except WebSocketDisconnect:
        pass