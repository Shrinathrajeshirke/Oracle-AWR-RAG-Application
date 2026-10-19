"""
Embedding management using local HuggingFace / SentenceTransformers models.
Runs entirely on CPU in-memory, avoiding hosted API rate limits and paid quotas.
"""

import sys
from langchain_huggingface import HuggingFaceEmbeddings
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
    Manages local embedding model initialization via SentenceTransformers.
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
            
        logging.info("=" * 50)
        logging.info("Initializing Local In-Memory Embedding Manager")
        logging.info(f"Embedding model: {model_name}")
        
        self.model_name = (
            model_name 
            if "/" in model_name 
            else f"sentence-transformers/{model_name}"
        )
        
        # Determine vector size for Qdrant collection
        self.vector_size = MODEL_DIMENSIONS.get(model_name, 384)
        
        try:
            logging.info(f"Loading local embedding model: {self.model_name} on CPU...")
            self.embeddings = HuggingFaceEmbeddings(
                model_name=self.model_name,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True}
            )
            
            logging.info(f"Local embeddings loaded successfully. Dimension: {self.vector_size}")
            logging.info("=" * 50)
            self._initialized = True
            
        except Exception as e:
            logging.error(f"Failed to load local HuggingFace embeddings: {e}")
            raise CustomException(e, sys)
            
    def get_embeddings(self) -> HuggingFaceEmbeddings:
        """Returns the LangChain embeddings instance"""
        return self.embeddings
        
    def get_vector_size(self) -> int:
        """Returns vector dimension size for Qdrant"""
        return self.vector_size


def get_embedding_manager(model_name: str = EMBEDDING_MODEL_NAME) -> EmbeddingManager:
    """Singleton getter for EmbeddingManager"""
    return EmbeddingManager(model_name=model_name)