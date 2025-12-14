"""
Document chunk processing and preparation
Handles document loading, splitting, and metadata management
"""

import sys
import os
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from config.settings import CHUNK_SIZE, CHUNK_OVERLAP
from utils.logger import logging
from utils.exception import CustomException


class DocumentProcessor:
    """
    Handles document loading and chunk processing
    Splits documents into chunks with proper metadata
    """
    
    def __init__(self):
        """Initialize document processor with text splitter"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )
        logging.info("DocumentProcessor initialized")
    
    def load_and_split_document(self, file_path: str, doc_id: str, filename: str) -> list[Document]:
        """
        Loads a document from a file path, adds metadata, and splits into chunks
        
        Args:
            file_path: Path to the uploaded file
            doc_id: Unique identifier for the document
            filename: Original filename
        
        Returns:
            list[Document]: List of split and processed LangChain Document objects
        
        Raises:
            CustomException: If document loading or processing fails
        """
        logging.info("="*60)
        logging.info("LOADING AND PROCESSING DOCUMENT")
        logging.info(f"File: {filename}")
        logging.info(f"Document ID: {doc_id}")
        logging.info(f"File path: {file_path}")
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            logging.info("Loading document using UnstructuredFileLoader...")
            loader = UnstructuredFileLoader(file_path)
            documents = loader.load()
            
            if not documents:
                raise ValueError(f"No content loaded from {filename}")
            
            logging.info(f"Loaded {len(documents)} document(s) from file")
            
        except Exception as e:
            logging.error(f"Document loading failed: {e}")
            logging.info("="*60)
            raise CustomException(e, sys)
        
        # Add crucial metadata to each document
        logging.info("Adding metadata to documents...")
        for doc in documents:
            doc.metadata['document_id'] = doc_id
            doc.metadata['filename'] = filename
            doc.metadata['source_path'] = file_path
        
        # Split documents into chunks
        logging.info(f"Splitting document into chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
        chunks = self.text_splitter.split_documents(documents)
        
        logging.info(f"Split into {len(chunks)} chunks")
        
        if chunks:
            logging.info(f"Sample chunk metadata: {chunks[0].metadata}")
            logging.info(f"Sample content (first 200 chars): {chunks[0].page_content[:200]}")
        
        logging.info("="*60)
        return chunks
    
    def process_multiple_documents(self, file_info_list: list) -> dict:
        """
        Process multiple documents at once
        
        Args:
            file_info_list: List of dicts with keys: file_path, doc_id, filename
        
        Returns:
            dict: Results with keys 'successful' and 'failed'
        """
        logging.info(f"Processing {len(file_info_list)} document(s)...")
        
        results = {
            "successful": [],
            "failed": []
        }
        
        for file_info in file_info_list:
            try:
                chunks = self.load_and_split_document(
                    file_path=file_info['file_path'],
                    doc_id=file_info['doc_id'],
                    filename=file_info['filename']
                )
                
                results["successful"].append({
                    "doc_id": file_info['doc_id'],
                    "filename": file_info['filename'],
                    "chunk_count": len(chunks),
                    "chunks": chunks
                })
                
            except Exception as e:
                logging.error(f"Failed to process {file_info['filename']}: {e}")
                results["failed"].append({
                    "doc_id": file_info['doc_id'],
                    "filename": file_info['filename'],
                    "error": str(e)
                })
        
        logging.info(f"Processing complete: {len(results['successful'])} successful, {len(results['failed'])} failed")
        return results
    
    def validate_chunks(self, chunks: list[Document]) -> bool:
        """
        Validate that chunks have proper metadata
        
        Args:
            chunks: List of document chunks to validate
        
        Returns:
            bool: True if all chunks are valid
        """
        if not chunks:
            logging.warning("No chunks to validate")
            return False
        
        required_fields = ['document_id', 'filename', 'source_path']
        
        for i, chunk in enumerate(chunks):
            for field in required_fields:
                if field not in chunk.metadata:
                    logging.error(f"Chunk {i} missing metadata field: {field}")
                    return False
            
            if not chunk.page_content or len(chunk.page_content.strip()) == 0:
                logging.error(f"Chunk {i} has empty content")
                return False
        
        logging.info(f"✓ All {len(chunks)} chunks are valid")
        return True