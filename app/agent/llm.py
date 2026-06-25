import logging
from langchain_openai import ChatOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_llm() -> ChatOpenAI:
    """
    Instantiate and return the LLM based on configuration settings.
    Supports OpenAI and NVIDIA NIM (using OpenAI compatible API).
    """
    if settings.LLM_PROVIDER == "nvidia":
        logger.info(f"Configuring ChatOpenAI for NVIDIA NIM with model: {settings.LLM_MODEL}")
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.NVIDIA_API_KEY,
            base_url="https://integrate.api.nvidia.com/v1",
            temperature=0.2
        )
    else:
        logger.info(f"Configuring ChatOpenAI for OpenAI with model: {settings.LLM_MODEL}")
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.2
        )
