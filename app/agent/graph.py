from langgraph.graph import StateGraph, START, END
from app.agent.state import ResearchState
from app.agent.nodes.research import research_node
from app.agent.nodes.generator import summarizer_node


def create_agent():
    """
    Constructs and compiles the LangGraph research agent.
    """
    # 1. Initialize the StateGraph with our ResearchState schema
    workflow = StateGraph(ResearchState)

    # 2. Add nodes
    workflow.add_node("research", research_node)
    workflow.add_node("summarize", summarizer_node)

    # 3. Define transitions/edges
    workflow.add_edge(START, "research")
    workflow.add_edge("research", "summarize")
    workflow.add_edge("summarize", END)

    # 4. Compile the graph
    return workflow.compile()


# Export compiled graph
graph = create_agent()
