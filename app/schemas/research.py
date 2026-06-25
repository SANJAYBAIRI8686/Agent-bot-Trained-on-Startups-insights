from pydantic import BaseModel, Field
from typing import List, Optional


class ResearchRequest(BaseModel):
    query: str = Field(
        ..., 
        description="The research query or topic to search and summarize.",
        examples=["What are the latest breakthroughs in fusion energy in 2026?"]
    )


class SearchSource(BaseModel):
    title: str = Field(..., description="Title of the web source.")
    url: str = Field(..., description="URL of the web source.")
    content: str = Field(..., description="Extracted snippet content from the search result.")


class ResearchResponse(BaseModel):
    query: str = Field(..., description="The original query requested.")
    search_results: List[SearchSource] = Field(
        default=[], 
        description="List of search result sources used for synthesis."
    )
    summary: str = Field(..., description="The generated research report/summary in Markdown.")
