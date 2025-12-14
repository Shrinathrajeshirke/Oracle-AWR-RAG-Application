"""
Configuration settings for AWR RAG Application
Centralized configuration for embeddings, vector store, and LLM models
"""

import os
from dotenv import load_dotenv

#load environment variables
load_dotenv()

## chunks settings
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

## embdding model settings
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

## vector store settings
QDRANT_COLLECTION_NAME = "multi_doc_comparison_rag"
QDRANT_LOCATION = os.getenv("QDRANT_LOCATION", ":memory:")

## LLM model choices
MODEL_CHOICES = {
    "openai":[
        "gpt-4o",
        "gpt-4-turbo",
        "gpt-3.5-turbo-0125"
    ],
    
    "groq": [
        "llama-3.1-8b-instant",
        
    ],
    
    "huggingface": [
        "HuggingFaceH4/zephyr-7b-beta",  # General purpose chat model
        "mistralai/Mixtral-8x7B-Instruct-v0.1" # Powerful model (requires token access)
    ],
    "default": {
        "openai": "gpt-4o",
        "groq": "llama-3.1-8b-instant",
        "huggingface": "HuggingFaceH4/zephyr-7b-beta"
    }
}

# LangSmith Configuration 
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", None)  
LANGSMITH_PROJECT = "rag-evaluation"  # Project name in LangSmith

# RAGAS Configuration
RAGAS_METRICS = [
    "faithfulness",
    "answer_relevancy", 
    "context_precision",
    "context_recall"
]

RAGAS_ENABLED = True  # Always True for background evaluation
RAGAS_OPENAI_KEY = os.getenv("RAGAS_OPENAI_KEY", None)
RAGAS_LOG_ONLY = True  # Don't show in UI, only log

# retriver configuration
RETRIEVER_K = 10  # Number of documents to retrieve

# Streamlit UI configuration
TEMP_DIR = "temp_files"
LOGS_DIR = "logs"

# SMTP Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")