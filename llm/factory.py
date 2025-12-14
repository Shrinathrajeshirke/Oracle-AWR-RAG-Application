"""
LLM provider factory
Creates and manages LLM instances for different providers
"""

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatHuggingFace
from huggingface_hub import InferenceClient
from langchain.chat_models.base import BaseChatModel
from utils.logger import logging


def get_llm(api_choice: str, api_key: str, model_name: str) -> BaseChatModel:
    """
    Returns the appropriate LangChain chat model instance based on provider choice
    
    Args:
        api_choice: LLM provider ("openai", "groq", or "huggingface")
        api_key: API key for the provider
        model_name: Model name to use
    
    Returns:
        BaseChatModel: Initialized LLM instance
    
    Raises:
        ValueError: If API key is missing or provider is invalid
    """
    
    logging.info(f"Initializing LLM: {api_choice}/{model_name}")
    
    if not api_key:
        raise ValueError(f"API key for {api_choice.upper()} is required.")
    
    if api_choice.lower() == "openai":
        logging.info("Creating OpenAI chat model")
        return ChatOpenAI(api_key=api_key, model=model_name)
    
    elif api_choice.lower() == "groq":
        logging.info("Creating Groq chat model")
        return ChatGroq(api_key=api_key, model=model_name)
    
    elif api_choice.lower() == "huggingface":
        logging.info("Creating HuggingFace chat model")
        client = InferenceClient(token=api_key)
        return ChatHuggingFace(inference_client=client, llm=model_name)
    
    else:
        raise ValueError(
            f"Invalid API choice: {api_choice}. "
            "Must be 'openai', 'groq', or 'huggingface'"
        )


def get_openai_eval_llm(api_key: str, model_name: str = "gpt-4-turbo-preview") -> BaseChatModel:
    """
    Returns a dedicated ChatOpenAI instance for RAGAS evaluation
    Uses a powerful model for best evaluation results
    
    Args:
        api_key: OpenAI API key
        model_name: Model to use for evaluation (default: gpt-4-turbo-preview)
    
    Returns:
        BaseChatModel: OpenAI chat model for evaluation
    
    Raises:
        ValueError: If API key is missing
    """
    if not api_key:
        raise ValueError("OpenAI API key for RAGAS evaluation is required.")
    
    logging.info(f"Creating OpenAI evaluation LLM: {model_name}")
    return ChatOpenAI(api_key=api_key, model=model_name)