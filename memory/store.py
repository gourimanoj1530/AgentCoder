import json
import os

MEMORY_FILE = "agentcoder_memory.json"
MAX_ERRORS_STORED = 20  # Keep memory lean


def load_memory() -> str:
    """
    Loads past error logs from disk and returns them as a formatted string
    for the planner node to use as context.

    Returns:
        Formatted string of past errors, or empty string if none.
    """
    if not os.path.exists(MEMORY_FILE):
        return ""

    try:
        with open(MEMORY_FILE, "r") as f:
            data = json.load(f)
        errors = data.get("error_log", [])
        if not errors:
            return ""
        return "Past errors seen:\n" + "\n".join(f"- {e}" for e in errors)
    except (json.JSONDecodeError, IOError):
        return ""


def save_memory(error_log: list[str]) -> None:
    """
    Persists the current session's error log to disk.
    Merges with existing errors and trims to MAX_ERRORS_STORED.

    Args:
        error_log: List of error strings from current session
    """
    existing = []

    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                data = json.load(f)
            existing = data.get("error_log", [])
        except (json.JSONDecodeError, IOError):
            existing = []

    # Merge, deduplicate, and trim
    merged = list(dict.fromkeys(existing + error_log))  # Preserves order, removes dupes
    trimmed = merged[-MAX_ERRORS_STORED:]               # Keep only the most recent

    with open(MEMORY_FILE, "w") as f:
        json.dump({"error_log": trimmed}, f, indent=2)


def clear_memory() -> None:
    """Wipes all stored memory. Useful for testing or user reset."""
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)