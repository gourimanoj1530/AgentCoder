import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

_client = None


def _get_client() -> TavilyClient:
    global _client
    if _client is None:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY not set in .env")
        _client = TavilyClient(api_key=api_key)
    return _client


def web_search(query: str, max_results: int = 3) -> str:
    """
    Searches the web using Tavily and returns a formatted string
    of the top results (title + snippet + url).

    Args:
        query: Natural language search query
        max_results: How many results to return (default 3)

    Returns:
        Formatted string with search results
    """
    if not query or not query.strip():
        return "Empty search query provided."

    try:
        client = _get_client()
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="basic",   # Use "advanced" for deeper results (costs more credits)
        )

        results = response.get("results", [])
        if not results:
            return "No results found for this query."

        formatted = []
        for i, r in enumerate(results, 1):
            formatted.append(
                f"[{i}] {r.get('title', 'No title')}\n"
                f"    {r.get('content', 'No snippet')[:300]}...\n"
                f"    URL: {r.get('url', '')}"
            )

        return "\n\n".join(formatted)

    except Exception as e:
        return f"Web search failed: {str(e)}"