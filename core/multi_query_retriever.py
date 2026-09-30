"""
Multi-Query Retrieval: Generates multiple query variations and retrieves from all
Catches different perspectives on the same topic
"""

from typing import List
from langchain_core.documents import Document
from core.retriever import DocumentRetriever
from core.query_processor import QueryProcessor
from utils.logger import logging


class MultiQueryRetriever:
    """
    Uses query expansion to retrieve documents for multiple query variations
    Combines results using reciprocal rank fusion
    """
    
    def __init__(self, document_retriever: DocumentRetriever):
        """
        Initialize multi-query retriever
        
        Args:
            document_retriever: Base DocumentRetriever instance
        """
        self.retriever = document_retriever
        self.query_processor = QueryProcessor()
        logging.info("MultiQueryRetriever initialized")
    
    def retrieve_multi_query(self, query: str, doc_ids: List[str], k: int = 10) -> List[Document]:
        """
        Retrieve documents using multiple query variations
        
        Args:
            query: Original user query
            doc_ids: List of document IDs to filter by
            k: Final number of results to return
        
        Returns:
            List of deduplicated, merged documents
        """
        logging.info(f"Starting multi-query retrieval for: {query[:80]}...")
        
        # Generate query variations
        query_variations = self.query_processor.expand_query(query)
        logging.info(f"Generated {len(query_variations)} query variations")
        
        # Retrieve for each variation
        all_results = {}
        
        for i, variant in enumerate(query_variations, 1):
            logging.info(f"Retrieving for variation {i}: {variant[:60]}...")
            
            try:
                docs = self.retriever.retrieve_documents(variant, doc_ids, k=k)
                
                # Store with RRF scores
                for rank, doc in enumerate(docs, 1):
                    doc_key = doc.page_content[:100]  # Use content as key
                    
                    if doc_key not in all_results:
                        all_results[doc_key] = {
                            "document": doc,
                            "rrf_score": 0,
                            "source_queries": []
                        }
                    
                    # Add RRF score: 1 / (rank + 60)
                    all_results[doc_key]["rrf_score"] += (1 / (rank + 60))
                    all_results[doc_key]["source_queries"].append(variant)
                
                logging.info(f"  Retrieved {len(docs)} documents")
            
            except Exception as e:
                logging.error(f"Error retrieving for variation '{variant}': {e}")
                continue
        
        # Merge and sort by combined RRF score
        merged_docs = sorted(
            all_results.values(),
            key=lambda x: x["rrf_score"],
            reverse=True
        )[:k]
        
        # Extract documents only
        result_docs = [item["document"] for item in merged_docs]
        
        logging.info(f"Multi-query retrieval returned {len(result_docs)} unique documents")
        
        return result_docs
    
    def retrieve_with_diversity(self, query: str, doc_ids: List[str], k: int = 10) -> List[Document]:
        """
        Retrieve documents with diversity emphasis
        Ensures results cover different aspects of the query
        
        Args:
            query: User query
            doc_ids: Document IDs to filter by
            k: Number of results to return
        
        Returns:
            Diverse set of relevant documents
        """
        logging.info(f"Retrieving with diversity for: {query[:80]}...")
        
        # Get key search terms
        search_terms = self.query_processor.get_search_terms(query)
        logging.info(f"Search terms: {search_terms}")
        
        # Retrieve for each important term
        term_results = {}
        
        for term in search_terms[:5]:  # Limit to 5 terms
            try:
                docs = self.retriever.retrieve_documents(term, doc_ids, k=k)
                term_results[term] = docs
                logging.info(f"  Retrieved {len(docs)} docs for term '{term}'")
            except Exception as e:
                logging.error(f"Error retrieving for term '{term}': {e}")
                continue
        
        # Combine with diversity: one from each term
        diverse_docs = []
        doc_content_seen = set()
        
        # Round-robin through term results
        max_docs_per_term = k // max(len(term_results), 1)
        
        for term, docs in term_results.items():
            count = 0
            for doc in docs:
                if count >= max_docs_per_term:
                    break
                
                doc_content_hash = hash(doc.page_content[:100])
                if doc_content_hash not in doc_content_seen:
                    diverse_docs.append(doc)
                    doc_content_seen.add(doc_content_hash)
                    count += 1
        
        logging.info(f"Diversity-based retrieval returned {len(diverse_docs)} documents")
        
        return diverse_docs[:k]