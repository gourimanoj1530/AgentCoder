import subprocess
import tempfile
import os
import re


# Dangerous patterns we block before execution
BLOCKED_PATTERNS = [
    r"import\s+os.*system",
    r"subprocess\.call",
    r"__import__\s*\(\s*['\"]os['\"]",
    r"open\s*\(.*['\"]w['\"]",   # No writing files
    r"shutil\.(rmtree|move|copy)",
]

TIMEOUT_SECONDS = 10


def is_safe(code: str) -> tuple[bool, str]:
    """Basic static check before executing user-supplied code."""
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, code):
            return False, f"Blocked pattern detected: {pattern}"
    return True, ""


def run_code(code: str) -> dict:
    """
    Executes Python code in a subprocess with a timeout.

    Returns:
        {"output": str} on success
        {"error": str}  on failure / timeout
    """
    safe, reason = is_safe(code)
    if not safe:
        return {"error": f"Code blocked for safety: {reason}"}

    # Write code to a temp file so we don't shell-inject anything
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", delete=False
    ) as tmp:
        tmp.write(code)
        tmp_path = tmp.name

    try:
        result = subprocess.run(
            ["python", tmp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )

        if result.returncode == 0:
            return {"output": result.stdout.strip() or "(no output)"}
        else:
            return {"error": result.stderr.strip()}

    except subprocess.TimeoutExpired:
        return {"error": f"Code execution timed out after {TIMEOUT_SECONDS}s"}

    except Exception as e:
        return {"error": str(e)}

    finally:
        os.unlink(tmp_path)  # Always clean up the temp file