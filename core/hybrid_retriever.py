"""
Hybrid Search: Combines semantic search with keyword-based BM25 search
Better retrieval for technical metrics (CPU%, wait events, SQL IDs, etc.)
"""

from typing import List
from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from utils.logger import logging


class HybridRetriever:
    """
    Combines vector search (semantic) with BM25 keyword search
    Uses reciprocal rank fusion to merge results
    """
    
    def __init__(self, documents: List[Document]):
        """
        Initialize hybrid retriever with documents
        
        Args:
            documents: List of document chunks for BM25 indexing
        """
        self.documents = documents
        
        if not documents:
            logging.warning("HybridRetriever initialized with 0 documents. BM25 is disabled.")
            self.bm25 = None
            self.tokenized_docs = []
            return

        # Tokenize documents for BM25
        self.tokenized_docs = [doc.page_content.lower().split() for doc in documents]
        
        # Initialize BM25 safely
        try:
            self.bm25 = BM25Okapi(self.tokenized_docs)
            logging.info(f"HybridRetriever initialized with {len(documents)} documents")
        except Exception as e:
            logging.error(f"Failed to initialize BM25Okapi: {e}")
            self.bm25 = None
    
    def bm25_search(self, query: str, k: int = 5) -> List[Document]:
        """
        BM25 keyword-based search
        """
        if not self.documents or not self.bm25:
            logging.warning("BM25 index is empty. Returning 0 results.")
            return []
            
        query_tokens = query.lower().split()
        if not query_tokens:
            return self.documents[:k]
            
        scores = self.bm25.get_scores(query_tokens)
        
        # Get top k indices
        top_indices = sorted(
            range(len(scores)),
            key=lambda i: scores[i],
            reverse=True
        )[:k]
        
        logging.info(f"BM25 search returned {len(top_indices)} results")
        return [self.documents[i] for i in top_indices]
    
    def hybrid_search(self, vector_results: List[Document], 
                     bm25_results: List[Document], k: int = 5) -> List[Document]:
        """
        Merge vector search and BM25 results using reciprocal rank fusion (RRF)
        """
        if not vector_results and not bm25_results:
            return []
        if not vector_results:
            return bm25_results[:k]
        if not bm25_results:
            return vector_results[:k]

        rrf_scores = {}
        
        # RRF formula: 1 / (rank + 60)
        for rank, doc in enumerate(vector_results, 1):
            doc_key = doc.page_content[:120]
            rrf_scores[doc_key] = rrf_scores.get(doc_key, 0.0) + (1.0 / (rank + 60))
        
        for rank, doc in enumerate(bm25_results, 1):
            doc_key = doc.page_content[:120]
            rrf_scores[doc_key] = rrf_scores.get(doc_key, 0.0) + (1.0 / (rank + 60))
        
        # Deduplicate
        all_docs = vector_results + bm25_results
        all_docs_unique = []
        seen = set()
        
        for doc in all_docs:
            key = doc.page_content[:120]
            if key not in seen:
                all_docs_unique.append(doc)
                seen.add(key)
        
        sorted_docs = sorted(
            all_docs_unique,
            key=lambda doc: rrf_scores.get(doc.page_content[:120], 0.0),
            reverse=True
        )[:k]
        
        logging.info(f"Hybrid search merged results: {len(sorted_docs)} final docs")
        return sorted_docs