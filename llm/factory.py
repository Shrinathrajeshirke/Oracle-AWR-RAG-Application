"""
LLM provider factory
Creates and manages deterministic ChatOpenAI instances for gpt-4o-mini.
"""

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from utils.logger import logging


def get_llm(api_choice: str, api_key: str, model_name: str = "gpt-4o-mini") -> BaseChatModel:
    """
    Returns a strictly deterministic ChatOpenAI instance configured with zero temperature.
    """
    if not api_key:
        raise ValueError(f"API key for {api_choice.upper()} is required.")

    choice = api_choice.lower()
    if choice == "openai":
        logging.info(f"Initializing deterministic ChatOpenAI ({model_name}) with temperature=0.0, top_p=0.01")
        return ChatOpenAI(
            api_key=api_key,
            model=model_name,
            temperature=0.0,
            model_kwargs={"top_p": 0.01}
        )

    raise ValueError(f"Invalid API choice: {api_choice}. Only 'openai' is supported.")