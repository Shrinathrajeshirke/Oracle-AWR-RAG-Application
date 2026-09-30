"""
Embedding management using HuggingFace Inference API
"""

import os
import sys
from langchain_huggingface import HuggingFaceEndpointEmbeddings
from config.settings import EMBEDDING_MODEL_NAME
from utils.logger import logging
from utils.exception import CustomException

# Mapping common model names to their vector sizes
MODEL_DIMENSIONS = {
    "sentence-transformers/all-MiniLM-L6-v2": 384,
    "all-MiniLM-L6-v2": 384,
    "BAAI/bge-small-en-v1.5": 384,
    "BAAI/bge-base-en-v1.5": 768,
    "sentence-transformers/all-mpnet-base-v2": 768,
}


class EmbeddingManager:
    """
    Manages embedding model initialization via HuggingFace Hosted API
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(EmbeddingManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        if self._initialized:
            return
            
        logging.info("="*50)
        logging.info("Initializing Embedding Manager (HuggingFace API)")
        logging.info(f"Embedding model: {model_name}")
        
        self.model_name = model_name
        self.hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN") or os.getenv("HF_TOKEN")
        
        if not self.hf_token:
            raise ValueError(
                "HUGGINGFACEHUB_API_TOKEN or HF_TOKEN is required in .env for API embeddings."
            )
        
        # Determine vector size for Qdrant collection
        self.vector_size = MODEL_DIMENSIONS.get(model_name, 384)
        
        try:
            # Full Hugging Face repo name format
            repo_id = (
                model_name 
                if "/" in model_name 
                else f"sentence-transformers/{model_name}"
            )
            
            logging.info(f"Connecting to HuggingFace Inference API endpoint: {repo_id}")
            self.embeddings = HuggingFaceEndpointEmbeddings(
                model=repo_id,
                huggingfacehub_api_token=self.hf_token,
            )
            
            logging.info(f"HuggingFace API embeddings initialized. Dimension: {self.vector_size}")
            logging.info("="*50)
            self._initialized = True
            
        except Exception as e:
            logging.error(f"Failed to initialize HuggingFace embeddings API: {e}")
            raise CustomException(e, sys)
            
    def get_embeddings(self) -> HuggingFaceEndpointEmbeddings:
        """Returns the LangChain embeddings instance"""
        return self.embeddings
        
    def get_vector_size(self) -> int:
        """Returns vector dimension size for Qdrant"""
        return self.vector_size


def get_embedding_manager(model_name: str = EMBEDDING_MODEL_NAME) -> EmbeddingManager:
    """Singleton getter for EmbeddingManager"""
    return EmbeddingManager(model_name=model_name)