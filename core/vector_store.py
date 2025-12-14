"""
Vector store management using Qdrant
Handles collection creation, document indexing, and basic operations
"""

import sys
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient, models
from config.settings import QDRANT_COLLECTION_NAME, QDRANT_LOCATION
from core.embeddings import get_embedding_manager
from utils.logger import logging
from utils.exception import CustomException


class VectorStoreManager:
    """
    Manages Qdrant vector store operations
    Handles collection creation, indexing, and retrieval
    """
    
    def __init__(self, collection_name=QDRANT_COLLECTION_NAME, location=QDRANT_LOCATION):
        logging.info("="*50)
        logging.info("Initializing Vector Store Manager")
        logging.info(f"Qdrant location: {location}")
        logging.info(f"Collection name: {collection_name}")
        
        self.collection_name = collection_name
        self.location = location
        
        try:
            # Get embedding manager (singleton)
            self.embedding_manager = get_embedding_manager()
            self.embeddings = self.embedding_manager.get_embeddings()
            self.vector_size = self.embedding_manager.get_vector_size()
            
            logging.info("Embeddings obtained from EmbeddingManager")
            
            # Initialize Qdrant client
            logging.info(f"Connecting to Qdrant at: {location}")
            self.client = QdrantClient(location=location)
            logging.info("Qdrant client connected")
            
            # Ensure collection exists
            self._ensure_collection_exists()
            
            logging.info("="*50)
            
        except Exception as e:
            logging.error(f"VectorStoreManager initialization failed: {e}")
            raise CustomException(e, sys)
    
    def _ensure_collection_exists(self):
        """Creates the Qdrant collection if it does not exist"""
        logging.info(f"Checking if collection '{self.collection_name}' exists...")
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            logging.info(f"Collection '{self.collection_name}' exists with {collection_info.points_count} points")
            
        except Exception as e:
            logging.info(f"Collection not found. Creating new collection...")
            logging.info(f"Vector config: size={self.vector_size}, distance=COSINE")
            
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    )
                )
                logging.info(f"Created collection '{self.collection_name}' with vector size {self.vector_size}")
                
            except Exception as create_error:
                logging.error(f"Failed to create collection: {create_error}")
                raise CustomException(create_error, sys)
    
    def get_vectorstore(self) -> QdrantVectorStore:
        """
        Returns the LangChain Qdrant vectorstore object for retrieval
        
        Returns:
            QdrantVectorStore: Configured vectorstore instance
        """
        logging.info("Creating QdrantVectorStore instance...")
        
        try:
            vectorstore = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.embeddings,
            )
            logging.info("QdrantVectorStore created successfully")
            return vectorstore
            
        except Exception as e:
            logging.error(f"Failed to create QdrantVectorStore: {e}")
            raise CustomException(e, sys)
    
    def index_documents(self, documents: list):
        """
        Indexes documents into the vector store
        
        Args:
            documents: List of LangChain Document objects
        
        Returns:
            list: IDs of indexed documents
        """
        logging.info("="*50)
        logging.info("INDEXING DOCUMENTS")
        
        try:
            if not documents:
                logging.warning("No documents provided for indexing")
                return []
            
            logging.info(f"Received {len(documents)} documents to index")
            logging.info(f"Document: {documents[0].metadata.get('filename', 'Unknown')}")
            logging.info(f"Document ID: {documents[0].metadata.get('document_id', 'Unknown')}")
            
            # Get collection stats before
            collection_before = self.client.get_collection(self.collection_name)
            points_before = collection_before.points_count
            logging.info(f"Collection has {points_before} points before indexing")
            
            # Index documents
            logging.info("Adding documents to vectorstore...")
            vectorstore = self.get_vectorstore()
            ids = vectorstore.add_documents(documents=documents)
            logging.info(f"add_documents returned {len(ids)} IDs")
            
            # Verify indexing
            collection_after = self.client.get_collection(self.collection_name)
            points_after = collection_after.points_count
            points_added = points_after - points_before
            
            logging.info(f"Collection now has {points_after} points (added {points_added} points)")
            
            if points_added == 0:
                logging.error("NO POINTS WERE ADDED! Documents were not indexed!")
                raise Exception("Documents were not indexed - no points added to collection!")
            
            if points_added != len(documents):
                logging.warning(f"Expected to add {len(documents)} points but added {points_added}")
            
            logging.info(f"Successfully indexed {points_added} documents")
            logging.info("="*50)
            
            return ids
            
        except Exception as e:
            logging.error(f"Document indexing failed: {e}", exc_info=True)
            logging.info("="*50)
            raise CustomException(e, sys)
    
    def get_collection_stats(self) -> dict:
        """
        Get statistics about the current collection
        
        Returns:
            dict: Collection statistics including point count and sample metadata
        """
        try:
            collection_info = self.client.get_collection(self.collection_name)
            points_count = collection_info.points_count
            
            # Get sample points
            sample_points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=5,
                with_payload=True,
                with_vectors=False
            )
            
            return {
                "points_count": points_count,
                "sample_metadata": [p.payload for p in sample_points] if sample_points else []
            }
            
        except Exception as e:
            logging.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self):
        """Clear all documents from the collection"""
        try:
            logging.info(f"Clearing collection '{self.collection_name}'...")
            self.client.delete_collection(self.collection_name)
            self._ensure_collection_exists()
            logging.info("Collection cleared successfully")
            
        except Exception as e:
            logging.error(f"Failed to clear collection: {e}")
            raise CustomException(e, sys)