import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)


def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """
    Search the web for a query using Tavily (if configured) or DuckDuckGo.
    Returns a list of dicts with: 'title', 'url', 'content'.
    """
    results: List[Dict[str, str]] = []

    # 1. Try Tavily Search if API Key is configured
    if settings.TAVILY_API_KEY:
        try:
            logger.info("Using Tavily Search...")
            from langchain_community.tools.tavily_search import TavilySearchResults
            tool = TavilySearchResults(max_results=max_results)
            tavily_results = tool.invoke({"query": query})
            # Tavily returns a list of dicts: [{'url': '...', 'content': '...'}]
            for r in tavily_results:
                results.append({
                    "title": r.get("title", "Search Result"),
                    "url": r.get("url", ""),
                    "content": r.get("content", "")
                })
            if results:
                return results
        except Exception as e:
            logger.warning(f"Tavily Search failed, falling back to DuckDuckGo: {e}")

    # 2. Default/Fallback: DuckDuckGo Search
    try:
        logger.info("Using DuckDuckGo Search...")
        from ddgs import DDGS
        
        with DDGS() as ddgs:
            ddg_results = list(ddgs.text(query, max_results=max_results))
            for r in ddg_results:
                results.append({
                    "title": r.get("title", "Search Result"),
                    "url": r.get("href", ""),  # href contains URL in ddgs
                    "content": r.get("body", "")  # body contains content snippet
                })
    except Exception as e:
        logger.error(f"DuckDuckGo Search failed: {e}")
        # In case both fail, return empty list rather than crashing
        results = []

    return results
