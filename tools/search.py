from duckduckgo_search import DDGS
from duckduckgo_search.exceptions import DuckDuckGoSearchException
from agents import function_tool


@function_tool
def web_search(query: str) -> str:
    """Search the web for current travel information and return a few snippets."""
    query = query.strip()
    if not query:
        return "Please provide a topic or search query."

    try:
        results = DDGS(timeout=10).text(query, max_results=5)
    except (DuckDuckGoSearchException, TimeoutError, OSError) as exc:
        return f"Sorry, web search is unavailable right now ({exc}). Please try again later."

    if not results:
        return f"No web results were found for '{query}'. Try a more specific search."

    lines = [f"Web results for: {query}"]
    for item in results:
        title = item.get("title", "Untitled result")
        url = item.get("href", "")
        snippet = item.get("body", "No summary available.")
        lines.append(f"- {title}\n  {snippet}\n  Source: {url}")
    lines.append("Search snippets can be incomplete or out of date; verify important details with the official source.")
    return "\n".join(lines)
