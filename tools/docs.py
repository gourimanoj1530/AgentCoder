import requests
import pydoc
import io
from contextlib import redirect_stdout


def _lookup_builtin(query: str) -> str | None:
    """
    Try Python's built-in pydoc for standard library lookups.
    Returns None if not found.
    """
    try:
        f = io.StringIO()
        with redirect_stdout(f):
            pydoc.render_doc(query, renderer=pydoc.plaintext)
        result = f.getvalue()
        # pydoc returns "no Python documentation found" for unknown modules
        if "no Python documentation found" in result.lower():
            return None
        return result[:2000]  # Trim — pydoc can be very verbose
    except Exception:
        return None


def _lookup_pypi(package: str) -> str:
    """
    Fetch package metadata from PyPI as a fallback.
    """
    try:
        url = f"https://pypi.org/pypi/{package}/json"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return f"Package '{package}' not found on PyPI."

        data = resp.json()
        info = data.get("info", {})

        return (
            f"Package: {info.get('name')}\n"
            f"Version: {info.get('version')}\n"
            f"Summary: {info.get('summary')}\n"
            f"Home page: {info.get('home_page') or info.get('project_url')}\n"
            f"Docs URL: {info.get('docs_url') or 'Not listed'}\n"
        )
    except Exception as e:
        return f"PyPI lookup failed: {str(e)}"


def doc_lookup(query: str) -> str:
    """
    Looks up Python documentation for a module, class, or function.

    Strategy:
    1. Try pydoc (works for stdlib and installed packages)
    2. Fall back to PyPI metadata

    Args:
        query: Module or function name e.g. "os.path.join", "requests", "pandas.DataFrame"

    Returns:
        Documentation string
    """
    if not query or not query.strip():
        return "Empty doc lookup query."

    query = query.strip()

    # Try pydoc first
    result = _lookup_builtin(query)
    if result:
        return result

    # Fall back to PyPI (use top-level package name only)
    top_level = query.split(".")[0]
    return _lookup_pypi(top_level)