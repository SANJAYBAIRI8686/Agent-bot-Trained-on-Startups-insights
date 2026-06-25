import logging
from app.agent.graph import graph

logger = logging.getLogger(__name__)


class ResearchService:
    @staticmethod
    async def run_research(query: str) -> dict:
        """
        Orchestrates and executes the research LangGraph flow.
        """
        logger.info(f"ResearchService starting workflow for query: {query}")
        
        # Prepare starting state
        initial_state = {
            "query": query,
            "search_results": [],
            "summary": ""
        }

        try:
            # Execute workflow asynchronously
            result = await graph.ainvoke(initial_state)
            logger.info("ResearchService workflow successfully completed.")
            return result
        except Exception as e:
            logger.error(f"Error during agent execution: {e}", exc_info=True)
            raise e
