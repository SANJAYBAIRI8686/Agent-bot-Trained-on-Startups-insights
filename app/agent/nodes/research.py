import logging
from app.agent.state import ResearchState
from app.agent.tools.docx_search import docx_search

logger = logging.getLogger(__name__)


def research_node(state: ResearchState) -> dict:
    """
    Research Node:
    Queries the local docx search tool and returns the collected chunks to update the state.
    """
    query = state.get("query")
    logger.info(f"Research node started searching docx for query: {query}")

    if not query:
        logger.warning("Empty query in state. Skipping search.")
        return {"search_results": []}

    # Execute search (retrieving top 10 chunks)
    results = docx_search(query=query, max_results=10)
    logger.info(f"Research node gathered {len(results)} docx chunks.")

    return {"search_results": results}
