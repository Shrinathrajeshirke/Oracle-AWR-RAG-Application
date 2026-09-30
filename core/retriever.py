"""
Document retrieval with filtering
Handles semantic search and document filtering by ID
"""

from qdrant_client.models import Filter, FieldCondition, MatchAny
from config.settings import RETRIEVER_K
from utils.logger import logging
from core.hybrid_retriever import HybridRetriever


class DocumentRetriever:
    """
    Manages document retrieval with filtering capabilities
    Supports both filtered and unfiltered semantic search
    """
    
    def __init__(self, vectorstore_manager):
        """
        Initialize retriever with vector store manager
        
        Args:
            vectorstore_manager: VectorStoreManager instance
        """
        self.vectorstore_manager = vectorstore_manager
        logging.info("DocumentRetriever initialized")
    
    def get_filtered_retriever(self, doc_ids: list, k: int = RETRIEVER_K):
        """
        Creates a LangChain retriever filtered to only search within specified document IDs
        
        Args:
            doc_ids: List of document IDs to filter by
            k: Number of documents to retrieve
        
        Returns:
            Retriever object filtered to specified documents
        """
        if not doc_ids:
            logging.warning("No doc_ids provided, using unfiltered retriever")
            return self.get_unfiltered_retriever(k)
        
        logging.info(f"Creating filtered retriever for doc_ids: {doc_ids}")
        
        vectorstore = self.vectorstore_manager.get_vectorstore()
        
        # Build Qdrant filter
        qdrant_filter = Filter(
            must=[
                FieldCondition(
                    key="metadata.document_id",
                    match=MatchAny(any=doc_ids)
                )
            ]
        )
        
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k, "filter": qdrant_filter}
        )
        
        logging.info(f"Filtered retriever created for {len(doc_ids)} document(s)")
        return retriever
    
    def get_unfiltered_retriever(self, k: int = RETRIEVER_K):
        """
        Creates an unfiltered retriever that searches across all documents
        
        Args:
            k: Number of documents to retrieve
        
        Returns:
            Retriever object with no document ID filtering
        """
        logging.info("Creating unfiltered retriever (searches all documents)")
        
        vectorstore = self.vectorstore_manager.get_vectorstore()
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        
        return retriever
    
    def retrieve_documents(self, query: str, doc_ids: list, k: int = RETRIEVER_K) -> list:
        """
        Retrieve documents for a given query
        
        Args:
            query: Search query
            doc_ids: Document IDs to filter by (empty list = all documents)
            k: Number of documents to retrieve
        
        Returns:
            List of retrieved documents
        """
        logging.info(f"Retrieving documents for query: {query[:100]}...")
        logging.info(f"Using {len(doc_ids) if doc_ids else 'all'} document(s)")
        
        retriever = self.get_filtered_retriever(doc_ids, k) if doc_ids else self.get_unfiltered_retriever(k)
        
        try:
            documents = retriever.invoke(query)
            logging.info(f"Retrieved {len(documents)} documents")
            
            if documents:
                logging.info("Sample retrieved document:")
                logging.info(f"  - Doc ID: {documents[0].metadata.get('document_id', 'Unknown')}")
                logging.info(f"  - Filename: {documents[0].metadata.get('filename', 'Unknown')}")
                logging.info(f"  - Content preview: {documents[0].page_content[:200]}")
            
            return documents

        except Exception as e:
                    logging.error(f"Document retrieval failed: {e}", exc_info=True)
                    raise

    def get_hybrid_retriever(self, doc_ids: list = None, k: int = RETRIEVER_K):
        """
        Creates a hybrid retriever using both semantic and BM25 search
        """
        from core.hybrid_retriever import HybridRetriever
        from langchain_core.documents import Document
    
        logging.info(f"Creating hybrid retriever for doc_ids: {doc_ids}")
        
        try:
            # Scroll points from Qdrant collection
            all_points, _ = self.vectorstore_manager.client.scroll(
                collection_name=self.vectorstore_manager.collection_name,
                limit=10000,
                with_payload=True,
                with_vectors=False
            )
            
            documents = []
            for point in all_points:
                payload = point.payload or {}
                # Support Langchain Qdrant storage conventions
                content = payload.get("page_content") or payload.get("text", "")
                metadata = payload.get("metadata", {})
                
                # Filter by doc_ids if specified
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
        Retrieve documents using hybrid search (semantic + BM25)
        
        Args:
            query: Search query
            doc_ids: Document IDs to filter by
            k: Number of documents to retrieve
        
        Returns:
            List of retrieved documents
        """

        logging.info(f"Hybrid retrieval for query: {query[:100]}...")
        logging.info(f"Using {len(doc_ids) if doc_ids else 'all'} document(s)")
        
        try:
            # Get semantic search results
            retriever = self.get_filtered_retriever(doc_ids, k) if doc_ids else self.get_unfiltered_retriever(k)
            vector_docs = retriever.invoke(query)
            
            logging.info(f"Vector search returned {len(vector_docs)} documents")
            
            # Get BM25 search results
            hybrid_ret = self.get_hybrid_retriever(doc_ids, k)
            bm25_docs = hybrid_ret.bm25_search(query, k)
            
            logging.info(f"BM25 search returned {len(bm25_docs)} documents")
            
            # Merge results using reciprocal rank fusion
            final_docs = hybrid_ret.hybrid_search(vector_docs, bm25_docs, k)
            
            logging.info(f"Hybrid search returned {len(final_docs)} merged documents")
            
            return final_docs
        
        except Exception as e:
            logging.error(f"Hybrid retrieval failed: {e}", exc_info=True)
            raise


                
            