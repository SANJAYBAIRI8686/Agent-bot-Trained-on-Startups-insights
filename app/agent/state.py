from typing import TypedDict, List, Dict, Any


class ResearchState(TypedDict):
    """
    Represents the state of our personal research agent workflow.
    """
    query: str
    search_results: List[Dict[str, str]]
    summary: str
