import logging
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.state import ResearchState
from app.agent.llm import get_llm

logger = logging.getLogger(__name__)


def summarizer_node(state: ResearchState) -> dict:
    """
    Summarizer Node:
    Takes search results and user query, formats them, and calls the LLM to generate
    a comprehensive structured research report.
    """
    query = state.get("query")
    search_results = state.get("search_results", [])

    logger.info("Summarizer node started generating report...")

    if not search_results:
        logger.warning("No search results found. Generating fallback report.")
        return {"summary": f"Could not find any search results for query: '{query}'."}

    # Format search results for prompt context
    formatted_results = ""
    for idx, res in enumerate(search_results, start=1):
        formatted_results += f"Source [{idx}]:\n"
        formatted_results += f"Title: {res.get('title', 'Unknown')}\n"
        formatted_results += f"URL: {res.get('url', 'N/A')}\n"
        formatted_results += f"Content: {res.get('content', '')}\n"
        formatted_results += "-" * 40 + "\n\n"

    # Define prompts
    system_prompt = (
        "You are an expert Startup Advisor specializing in Paul Graham's wisdom and teachings. "
        "Your task is to write a detailed, well-structured answer in Markdown based on the provided "
        "essay chunks from Paul Graham's writings.\n\n"
        "Requirements:\n"
        "1. Write a professional, comprehensive answer addressing the user's query directly.\n"
        "2. Include clear headings, bullet points, and structure where appropriate.\n"
        "3. Use inline citations pointing to the source essay index (e.g., [1], [2]) based on the sources provided.\n"
        "4. Create a 'Sources' section at the end listing the unique essays referenced (Title and File Name).\n"
        "5. Keep the tone insightful, clear, and direct (similar to Paul Graham's style).\n"
        "6. Only answer based on the provided sources. Do NOT make up information that cannot be referenced back to the sources.\n"
        "7. Ensure the output is polished and ready to read."
    )

    user_content = (
        f"User Question: {query}\n\n"
        f"Relevant Essay Chunks:\n{formatted_results}\n"
        "Generate the response:"
    )

    # Call LLM
    try:
        llm = get_llm()
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
        ]
        response = llm.invoke(messages)
        report_content = response.content
    except Exception as e:
        logger.error(f"Error calling LLM in summarizer node: {e}")
        report_content = f"Failed to generate report due to LLM error: {e}"

    return {"summary": report_content}
