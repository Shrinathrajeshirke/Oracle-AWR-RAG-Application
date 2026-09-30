"""
Tier 2 Retriever - Orchestrates Advanced RAG Techniques
Combines query classification, intelligent retrieval, and re-ranking
"""

from typing import List, Dict, Tuple
from langchain_core.documents import Document
from core.retriever import DocumentRetriever
from core.query_classifier import QueryClassifier
from core.multi_query_retriever import MultiQueryRetriever
from core.reranker import DocumentReranker
from core.fact_verifier import FactVerifier
from utils.logger import logging


class Tier2Retriever:
    """
    Advanced retriever combining:
    - Query intent classification
    - Intelligent retrieval based on intent
    - Cross-encoder re-ranking
    - Fact verification
    """
    
    def __init__(self, base_retriever: DocumentRetriever):
        """
        Initialize Tier 2 retriever
        
        Args:
            base_retriever: Base DocumentRetriever instance
        """
        self.retriever = base_retriever
        self.classifier = QueryClassifier()
        self.multi_retriever = MultiQueryRetriever(base_retriever)
        self.reranker = DocumentReranker()
        self.verifier = FactVerifier()
        
        logging.info("Tier2Retriever initialized")
    
    def retrieve_and_rerank(self, query: str, doc_ids: List[str], 
                           use_classification: bool = True) -> Tuple[List[Document], Dict]:
        """
        Main retrieval pipeline with classification and re-ranking
        
        Args:
            query: User query
            doc_ids: Document IDs to filter by
            use_classification: Whether to use query intent classification
        
        Returns:
            Tuple of (reranked documents, retrieval info dict)
        """
        logging.info("="*70)
        logging.info("TIER 2 RETRIEVAL PIPELINE")
        logging.info("="*70)
        
        info = {
            "query": query,
            "doc_ids": doc_ids,
            "classification": None,
            "retrieval_method": None,
            "initial_docs_count": 0,
            "reranked_docs_count": 0
        }
        
        # Step 1: Classify query intent
        if use_classification:
            classification = self.classifier.classify(query)
            info["classification"] = classification
            intent = classification["primary_intent"]
            confidence = classification["confidence"]
            
            logging.info(f"Query Intent: {intent} (confidence: {confidence:.2%})")
            
            # Get strategy for this intent
            strategy = self.classifier.get_retrieval_strategy(intent)
            k = strategy["k"]
            method = strategy["method"]
        else:
            intent = "default"
            k = 10
            method = "hybrid"
            logging.info("Using default retrieval strategy (classification disabled)")
        
        info["retrieval_method"] = method
        
        # Step 2: Retrieve using appropriate method
        if method == "hybrid":
            logging.info(f"Retrieving with Hybrid Search (k={k})")
            docs = self.retriever.retrieve_hybrid(query, doc_ids, k=k)
        
        elif method == "multi_query":
            logging.info(f"Retrieving with Multi-Query (k={k})")
            docs = self.multi_retriever.retrieve_multi_query(query, doc_ids, k=k)
        
        elif method == "diversity":
            logging.info(f"Retrieving with Diversity-Based (k={k})")
            docs = self.multi_retriever.retrieve_with_diversity(query, doc_ids, k=k)
        
        else:
            logging.info(f"Retrieving with standard Vector Search (k={k})")
            docs = self.retriever.retrieve_documents(query, doc_ids, k=k)
        
        info["initial_docs_count"] = len(docs)
        logging.info(f"Retrieved {len(docs)} documents")
        
        # Step 3: Re-rank documents
        if strategy.get("needs_reranking", True) and len(docs) > 5:
            logging.info("Re-ranking documents with cross-encoder")
            top_k = min(5, len(docs))
            docs = self.reranker.rerank(query, docs, top_k=top_k)
            info["reranked_docs_count"] = len(docs)
        else:
            info["reranked_docs_count"] = len(docs)
        
        logging.info(f"Final retrieved documents: {len(docs)}")
        logging.info("="*70)
        
        return docs, info
    
    def retrieve_with_verification(self, query: str, doc_ids: List[str],
                                  answer: str) -> Dict:
        """
        Retrieve documents and verify facts in given answer
        
        Args:
            query: User query
            doc_ids: Document IDs
            answer: LLM-generated answer to verify
        
        Returns:
            Dict with documents and verification report
        """
        # Retrieve documents
        docs, retrieval_info = self.retrieve_and_rerank(query, doc_ids)
        
        # Verify answer against retrieved documents
        verification_report = self.verifier.verify_response(answer, docs)
        
        return {
            "documents": docs,
            "retrieval_info": retrieval_info,
            "verification": verification_report,
            "badge": self.verifier.get_verification_badge(verification_report)
        }
    
    def get_system_prompt_for_query(self, query: str, base_prompt: str) -> str:
        """
        Get customized system prompt based on query intent
        
        Args:
            query: User query
            base_prompt: Base system prompt
        
        Returns:
            Customized system prompt
        """
        classification = self.classifier.classify(query)
        intent = classification["primary_intent"]
        
        # Get style for this intent
        strategy = self.classifier.get_retrieval_strategy(intent)
        style = strategy["system_prompt_style"]
        
        # Add customization to base prompt
        prompt = self.classifier.get_system_prompt_variation(intent, base_prompt)
        
        logging.info(f"Using system prompt style: {style}")
        
        return prompt
    
    def compare_retrieval_methods(self, query: str, doc_ids: List[str]) -> Dict:
        """
        Compare different retrieval methods on same query
        
        Args:
            query: User query
            doc_ids: Document IDs
        
        Returns:
            Comparison results
        """
        logging.info(f"Comparing retrieval methods for: {query[:80]}...")
        
        methods = {
            "vector": lambda: self.retriever.retrieve_documents(query, doc_ids, k=5),
            "hybrid": lambda: self.retriever.retrieve_hybrid(query, doc_ids, k=5),
            "multi_query": lambda: self.multi_retriever.retrieve_multi_query(query, doc_ids, k=5),
            "diversity": lambda: self.multi_retriever.retrieve_with_diversity(query, doc_ids, k=5),
        }
        
        results = {}
        for method_name, method_func in methods.items():
            try:
                docs = method_func()
                results[method_name] = {
                    "count": len(docs),
                    "success": True,
                    "top_doc_preview": docs[0].page_content[:100] if docs else "N/A"
                }
            except Exception as e:
                results[method_name] = {
                    "count": 0,
                    "success": False,
                    "error": str(e)
                }
        
        return results