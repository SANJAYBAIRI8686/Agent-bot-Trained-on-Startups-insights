import asyncio
import logging
from dotenv import load_dotenv

# Load local .env
load_dotenv()

from app.services.research_service import ResearchService

# Configure logging to console
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_agent")


async def main():
    query = "What is Founder Mode and how does it differ from Manager Mode?"
    logger.info(f"Starting test agent with query: '{query}'")
    
    try:
        result = await ResearchService.run_research(query=query)
        print("\n" + "="*80)
        print(f"QUESTION: {result['query']}")
        print("="*80)
        print(f"RETRIEVED {len(result['search_results'])} ESSAY CHUNKS:")
        for idx, res in enumerate(result['search_results'], 1):
            print(f"[{idx}] {res['title']} (File: {res['url']})")
        print("="*80)
        print("GENERATED ADVISOR RESPONSE:")
        print(result['summary'])
        print("="*80)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(main())
