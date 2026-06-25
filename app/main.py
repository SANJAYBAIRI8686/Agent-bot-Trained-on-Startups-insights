import logging
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load local environment variables
load_dotenv()

from app.schemas.research import ResearchRequest, ResearchResponse
from app.services.research_service import ResearchService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("app.main")

app = FastAPI(
    title="Personal Research Agent API",
    description="Backend API for personal AI research agent using LangGraph and FastAPI.",
    version="1.0.0"
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Simple health check endpoint.
    """
    return {"status": "healthy", "service": "personal-research-agent"}


@app.post("/api/research", response_model=ResearchResponse, status_code=status.HTTP_200_OK)
async def run_research(request: ResearchRequest):
    """
    Takes a research question, performs web searches, and returns a structured markdown summary.
    """
    logger.info(f"Received research request: '{request.query}'")
    try:
        result = await ResearchService.run_research(query=request.query)
        return ResearchResponse(
            query=result["query"],
            search_results=result.get("search_results", []),
            summary=result["summary"]
        )
    except Exception as e:
        logger.error(f"Error handling research request: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred executing research: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
