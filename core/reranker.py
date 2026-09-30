"""
Intelligent Re-ranking using Cross-Encoder
Scores retrieved documents for relevance to the query
"""

from typing import List, Tuple
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from utils.logger import logging


class DocumentReranker:
    """
    Re-ranks documents using cross-encoder model
    Scores document-query pairs for relevance
    """
    
    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        """
        Initialize reranker with cross-encoder model
        
        Args:
            model_name: Cross-encoder model from HuggingFace
        """
        logging.info(f"Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name)
        logging.info("Cross-encoder model loaded successfully")
    
    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        """
        Re-rank documents by relevance to query
        
        Args:
            query: User query
            documents: Initial retrieved documents
            top_k: Number of top documents to return
        
        Returns:
            Re-ranked list of top_k documents
        """
        logging.info(f"Re-ranking {len(documents)} documents for query: {query[:80]}...")
        
        if not documents:
            logging.warning("No documents to re-rank")
            return []
        
        # Prepare document-query pairs
        doc_query_pairs = [(doc.page_content, query) for doc in documents]
        
        # Score all pairs
        scores = self.model.predict(doc_query_pairs)
        
        # Create list of (document, score) tuples
        doc_scores = list(zip(documents, scores))
        
        # Sort by score (descending)
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Extract top_k documents
        reranked_docs = [doc for doc, score in doc_scores[:top_k]]
        
        logging.info(f"Re-ranked documents. Top scores: {[score for _, score in doc_scores[:top_k]]}")
        
        return reranked_docs
    
    def score_documents(self, query: str, documents: List[Document]) -> List[Tuple[Document, float]]:
        """
        Score documents without re-ranking (returns all with scores)
        
        Args:
            query: User query
            documents: Documents to score
        
        Returns:
            List of (document, score) tuples
        """
        logging.info(f"Scoring {len(documents)} documents")
        
        if not documents:
            return []
        
        doc_query_pairs = [(doc.page_content, query) for doc in documents]
        scores = self.model.predict(doc_query_pairs)
        
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)
        
        return doc_scores