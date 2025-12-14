"""
Embedding initialization and management
Handles SentenceTransformer and HuggingFace embeddings
"""

import sys
from sentence_transformers import SentenceTransformer
from langchain_huggingface import HuggingFaceEmbeddings
from config.settings import EMBEDDING_MODEL_NAME
from utils.logger import logging
from utils.exception import CustomException


class EmbeddingManager:
    """
    Manages embedding model initialization and caching
    Singleton pattern to avoid re-loading models
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.model_name = EMBEDDING_MODEL_NAME
        self.embeddings = None
        self.vector_size = None
        self.model_client = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize embedding models"""
        logging.info("="*50)
        logging.info("Initializing Embedding Manager")
        logging.info(f"Embedding model: {self.model_name}")
        
        try:
            logging.info("Loading SentenceTransformer model...")
            self.model_client = SentenceTransformer(self.model_name)
            self.vector_size = self.model_client.get_sentence_embedding_dimension()
            logging.info(f"SentenceTransformer loaded. Vector size: {self.vector_size}")
            
        except Exception as e:
            logging.error(f"SentenceTransformer initialization failed: {e}")
            raise CustomException(e, sys)
        
        try:
            logging.info("Initializing HuggingFace embeddings...")
            self.embeddings = HuggingFaceEmbeddings(model_name=self.model_name)
            logging.info("HuggingFace embeddings initialized")
            
        except Exception as e:
            logging.error(f"HuggingFace embeddings initialization failed: {e}")
            raise CustomException(e, sys)
        
        logging.info("="*50)
    
    def get_embeddings(self):
        """Get the embeddings object for LangChain"""
        if self.embeddings is None:
            raise RuntimeError("Embeddings not initialized")
        return self.embeddings
    
    def get_vector_size(self):
        """Get the vector dimension size"""
        if self.vector_size is None:
            raise RuntimeError("Vector size not initialized")
        return self.vector_size
    
    def get_model_client(self):
        """Get the SentenceTransformer model client"""
        if self.model_client is None:
            raise RuntimeError("Model client not initialized")
        return self.model_client


def get_embedding_manager():
    """Factory function to get embedding manager instance"""
    return EmbeddingManager()