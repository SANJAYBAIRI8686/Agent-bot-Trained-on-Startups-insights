import asyncio
import sys
import logging
from dotenv import load_dotenv

# Load local env
load_dotenv()

# Keep log output minimal for clean interactive prompt
logging.basicConfig(level=logging.WARNING)

from app.services.research_service import ResearchService


async def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"\nQuerying: {query}...")
        try:
            result = await ResearchService.run_research(query=query)
            print("\n" + "="*80)
            print("RESPONSE:")
            print("="*80)
            print(result['summary'])
            print("="*80)
        except Exception as e:
            print("Error running query:", e)
        return

    print("\n==================================================")
    print("         Startup Advisor Agent CLI")
    print("==================================================")
    print("Type your question and press Enter. Type 'exit' or 'quit' to end.\n")
    
    while True:
        try:
            query = input("Your Question: ").strip()
            if not query:
                continue
            if query.lower() in ("exit", "quit"):
                print("Goodbye!")
                break
            
            print("\nThinking...")
            result = await ResearchService.run_research(query=query)
            print("\n" + "="*80)
            print("RESPONSE:")
            print("="*80)
            print(result['summary'])
            print("="*80 + "\n")
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    asyncio.run(main())
