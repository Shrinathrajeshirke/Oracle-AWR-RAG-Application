"""
Document retrieval with filtering and domain query expansion
Handles semantic search, BM25 keyword matching, and document filtering by ID
"""

from typing import List, Optional
from qdrant_client.models import Filter, FieldCondition, MatchAny
from config.settings import RETRIEVER_K
from utils.logger import logging
from core.hybrid_retriever import HybridRetriever


class DocumentRetriever:
    """
    Manages document retrieval with filtering capabilities.
    Enriches colloquial DBA queries with canonical AWR section titles.
    """

    # Domain dictionary mapping informal user inquiries to exact AWR table titles
    AWR_TERM_EXPANSIONS = [
        (["buffer", "buffer gets", "logical reads", "most buffer", "top buffer"], "SQL ordered by Gets 4y08a52989vfk Total Buffer Gets"),
        (["elapsed", "slowest sql", "long running", "top elapsed"], "SQL ordered by Elapsed Time Captured SQL account for"),
        (["cpu sql", "sql cpu", "most cpu"], "SQL ordered by CPU Time Captured SQL account for"),
        (["physical reads", "disk reads", "most reads"], "SQL ordered by Reads Total Disk Reads"),
        (["executions", "most executed", "highest executions"], "SQL ordered by Executions Total Executions"),
        (["parse", "hard parse", "soft parse"], "SQL ordered by Parse Calls Total Parse Calls"),
        (["foreground wait", "wait event", "top wait", "bottleneck"], "Top 10 Foreground Events by Total Wait Time Event Waits Total Wait Time"),
        (["wait class", "classes"], "Foreground Wait Class Wait Class Waits"),
        (["host cpu", "os cpu", "load average"], "Operating System Statistics Host CPU"),
        (["instance efficiency", "buffer hit", "library hit"], "Instance Efficiency Percentages"),
    ]
    
    def __init__(self, vectorstore_manager):
        """
        Initialize retriever with vector store manager
        """
        self.vectorstore_manager = vectorstore_manager
        logging.info("DocumentRetriever initialized")

    def _expand_query(self, query: str) -> str:
        """Enriches conversational queries with canonical Oracle AWR section headers."""
        q_clean = query.lower().strip()
        expanded_terms = []

        for trigger_keywords, target_header in self.AWR_TERM_EXPANSIONS:
            for kw in trigger_keywords:
                if kw in q_clean:
                    expanded_terms.append(target_header)
                    break

        if expanded_terms:
            enriched = f"{query} {' '.join(expanded_terms)}"
            logging.info(f"Query expanded: '{query}' -> '{enriched}'")
            return enriched

        return query

    def get_filtered_retriever(self, doc_ids: list, k: int = RETRIEVER_K):
        """
        Creates a LangChain retriever filtered to only search within specified document IDs
        """
        if not doc_ids:
            logging.warning("No doc_ids provided, using unfiltered retriever")
            return self.get_unfiltered_retriever(k)
        
        logging.info(f"Creating filtered retriever for doc_ids: {doc_ids}")
        vectorstore = self.vectorstore_manager.get_vectorstore()
        
        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.document_id",
                    match=MatchAny(any=doc_ids)
                )
            ]
        )
        
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k, "filter": qdrant_filter}
        )
    
    def get_unfiltered_retriever(self, k: int = RETRIEVER_K):
        """
        Creates an unfiltered retriever that searches across all documents
        """
        logging.info("Creating unfiltered retriever (searches all documents)")
        vectorstore = self.vectorstore_manager.get_vectorstore()
        return vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
    
    def retrieve_documents(self, query: str, doc_ids: list, k: int = RETRIEVER_K) -> list:
        """
        Retrieve documents for a given query
        """
        search_query = self._expand_query(query)
        logging.info(f"Retrieving documents for query: {search_query[:100]}...")
        retriever = self.get_filtered_retriever(doc_ids, k) if doc_ids else self.get_unfiltered_retriever(k)
        
        try:
            documents = retriever.invoke(search_query)
            logging.info(f"Retrieved {len(documents)} documents")
            return documents
        except Exception as e:
            logging.error(f"Document retrieval failed: {e}", exc_info=True)
            raise

    def get_hybrid_retriever(self, doc_ids: list = None, k: int = RETRIEVER_K):
        """
        Creates a hybrid retriever using both semantic and BM25 search
        """
        from langchain_core.documents import Document
    
        logging.info(f"Creating hybrid retriever for doc_ids: {doc_ids}")
        try:
            all_points, _ = self.vectorstore_manager.client.scroll(
                collection_name=self.vectorstore_manager.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            documents = []
            for point in all_points:
                payload = point.payload or {}
                content = payload.get("page_content") or payload.get("text", "")
                metadata = payload.get("metadata", {})
                
                if doc_ids and metadata.get("document_id") not in doc_ids:
                    continue
                    
                if content.strip():
                    documents.append(Document(page_content=content, metadata=metadata))
            
            if not documents:
                logging.warning("No documents found in collection for BM25 indexing.")
                
            return HybridRetriever(documents)
        except Exception as e:
            logging.error(f"Error creating hybrid retriever: {e}")
            raise

    def retrieve_hybrid(self, query: str, doc_ids: list, k: int = RETRIEVER_K) -> list:
        """
        Retrieve documents using hybrid search (semantic + BM25) with domain query expansion
        """
        search_query = self._expand_query(query)
        logging.info(f"Hybrid retrieval for query: {search_query[:100]}...")
        
        try:
            retriever = self.get_filtered_retriever(doc_ids, k) if doc_ids else self.get_unfiltered_retriever(k)
            vector_docs = retriever.invoke(search_query)
            logging.info(f"Vector search returned {len(vector_docs)} documents")
            
            hybrid_ret = self.get_hybrid_retriever(doc_ids, k)
            bm25_docs = hybrid_ret.bm25_search(search_query, k)
            logging.info(f"BM25 search returned {len(bm25_docs)} documents")
            
            final_docs = hybrid_ret.hybrid_search(vector_docs, bm25_docs, k)
            logging.info(f"Hybrid search returned {len(final_docs)} merged documents")
            return final_docs
        
        except Exception as e:
            logging.error(f"Hybrid retrieval failed: {e}", exc_info=True)
            raise