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
        "You are an expert Startup Advisor speaking in the exact tone and style of Paul Graham: "
        "direct, conversational, clear, insightful, and concise. Your goal is to provide a "
        "highly focused, structured answer in Markdown based solely on the provided essay chunks.\n\n"
        "Writing Guidelines:\n"
        "1. Answer the user's query directly and concisely. Avoid generic introductory fluff (e.g. 'As startups grow...').\n"
        "2. Use headings, bullet points, and bold text for clarity and readability.\n"
        "3. Synthesize information across chunks. Avoid repeating similar points.\n"
        "4. Use inline citations to point to the source essay indices (e.g. [1], [2]).\n"
        "5. Create a clean 'Sources' section at the end of your response, listing the unique source essays used.\n"
        "6. Do NOT invent or extrapolate facts. If the information isn't in the provided chunks, state that it isn't covered."
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
