"""
Configuration settings for AWR RAG Application
Centralized configuration for embeddings, vector store, and LLM models
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

## Chunking settings (Optimized for wide Oracle Markdown tables)
CHUNK_SIZE = 2500
CHUNK_OVERLAP = 400

## Embedding model settings
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_MODEL = EMBEDDING_MODEL_NAME

## Vector store settings
QDRANT_COLLECTION_NAME = "awr_reports_hybrid"
QDRANT_LOCATION = os.getenv("QDRANT_LOCATION", ":memory:")

## Dedicated LLM Model
DEFAULT_LLM_MODEL = "gpt-4o-mini"

## Retrieval Configuration
RETRIEVER_K = 10  # Tier 1 Hybrid search top-k

## Directories
TEMP_DIR = "temp_files"
LOGS_DIR = "logs"

## SMTP Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")