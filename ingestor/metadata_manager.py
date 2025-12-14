"""
Document metadata management
Handles document tracking, versioning, and metadata operations
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from utils.logger import logging


class MetadataManager:
    """
    Manages document metadata including ingestion history and statistics
    Stores metadata in JSON for persistence
    """
    
    def __init__(self, metadata_file: str = "documents_metadata.json"):
        """
        Initialize metadata manager
        
        Args:
            metadata_file: Path to JSON file storing metadata
        """
        self.metadata_file = metadata_file
        self.metadata = self._load_metadata()
        logging.info(f"MetadataManager initialized with file: {metadata_file}")
    
    def _load_metadata(self) -> dict:
        """Load metadata from file if it exists"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                    logging.info(f"Loaded metadata for {len(data.get('documents', {}))} documents")
                    return data
            except Exception as e:
                logging.error(f"Error loading metadata: {e}")
                return self._create_empty_metadata()
        
        return self._create_empty_metadata()
    
    def _create_empty_metadata(self) -> dict:
        """Create empty metadata structure"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "documents": {},
            "statistics": {
                "total_documents": 0,
                "total_chunks": 0,
                "total_size_bytes": 0
            }
        }
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logging.info("Metadata saved to file")
        except Exception as e:
            logging.error(f"Error saving metadata: {e}")
    
    def register_document(self, doc_id: str, filename: str, chunk_count: int, 
                         file_size: int = 0) -> bool:
        """
        Register a new document in metadata
        
        Args:
            doc_id: Unique document identifier
            filename: Original filename
            chunk_count: Number of chunks created from this document
            file_size: Size of file in bytes
        
        Returns:
            bool: True if registration successful
        """
        logging.info(f"Registering document: {filename} (ID: {doc_id})")
        
        try:
            self.metadata['documents'][doc_id] = {
                "filename": filename,
                "chunk_count": chunk_count,
                "file_size": file_size,
                "ingested_at": datetime.now().isoformat(),
                "status": "indexed"
            }
            
            # Update statistics
            self.metadata['statistics']['total_documents'] = len(self.metadata['documents'])
            self.metadata['statistics']['total_chunks'] += chunk_count
            self.metadata['statistics']['total_size_bytes'] += file_size
            
            self._save_metadata()
            logging.info(f"Document registered: {doc_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error registering document: {e}")
            return False
    
    def unregister_document(self, doc_id: str) -> bool:
        """
        Unregister a document (when deleting from vector store)
        
        Args:
            doc_id: Document identifier to remove
        
        Returns:
            bool: True if unregistration successful
        """
        logging.info(f"Unregistering document: {doc_id}")
        
        try:
            if doc_id in self.metadata['documents']:
                doc = self.metadata['documents'][doc_id]
                
                # Update statistics
                self.metadata['statistics']['total_documents'] -= 1
                self.metadata['statistics']['total_chunks'] -= doc['chunk_count']
                self.metadata['statistics']['total_size_bytes'] -= doc['file_size']
                
                del self.metadata['documents'][doc_id]
                self._save_metadata()
                logging.info(f"Document unregistered: {doc_id}")
                return True
            else:
                logging.warning(f"Document not found: {doc_id}")
                return False
                
        except Exception as e:
            logging.error(f"Error unregistering document: {e}")
            return False
    
    def get_document_info(self, doc_id: str) -> Optional[dict]:
        """
        Get information about a specific document
        
        Args:
            doc_id: Document identifier
        
        Returns:
            dict: Document metadata or None if not found
        """
        return self.metadata['documents'].get(doc_id)
    
    def get_all_documents(self) -> dict:
        """Get all documents metadata"""
        return self.metadata['documents']
    
    def get_statistics(self) -> dict:
        """Get overall statistics"""
        return self.metadata['statistics']
    
    def document_exists(self, doc_id: str) -> bool:
        """Check if document is registered"""
        return doc_id in self.metadata['documents']
    
    def get_documents_by_filename(self, filename: str) -> List[str]:
        """Find all doc_ids with a given filename"""
        return [
            doc_id for doc_id, info in self.metadata['documents'].items()
            if info['filename'] == filename
        ]
    
    def update_document_status(self, doc_id: str, status: str) -> bool:
        """
        Update document status
        
        Args:
            doc_id: Document identifier
            status: New status (e.g., 'indexed', 'processing', 'error')
        
        Returns:
            bool: True if update successful
        """
        try:
            if doc_id in self.metadata['documents']:
                self.metadata['documents'][doc_id]['status'] = status
                self.metadata['documents'][doc_id]['last_updated'] = datetime.now().isoformat()
                self._save_metadata()
                return True
            return False
        except Exception as e:
            logging.error(f"Error updating document status: {e}")
            return False
    
    def get_ingestion_history(self, doc_id: str) -> dict:
        """Get detailed ingestion history for a document"""
        if doc_id not in self.metadata['documents']:
            return {}
        
        doc = self.metadata['documents'][doc_id]
        return {
            "doc_id": doc_id,
            "filename": doc['filename'],
            "chunk_count": doc['chunk_count'],
            "file_size": doc['file_size'],
            "ingested_at": doc['ingested_at'],
            "status": doc['status'],
            "last_updated": doc.get('last_updated', doc['ingested_at'])
        }
    
    def clear_all_metadata(self):
        """Clear all metadata (use with caution)"""
        logging.warning("Clearing all metadata...")
        self.metadata = self._create_empty_metadata()
        self._save_metadata()
        logging.info("Metadata cleared")