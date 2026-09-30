"""
Document chunk processing and preparation
Handles document loading, splitting, and metadata management
"""

import sys
import os
from langchain_community.document_loaders import BSHTMLLoader, TextLoader
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
        """
        logging.info("="*60)
        logging.info("LOADING AND PROCESSING DOCUMENT")
        logging.info(f"File: {filename}")
        logging.info(f"Document ID: {doc_id}")
        logging.info(f"File path: {file_path}")
        
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Select loader based on file extension
            if file_path.lower().endswith((".html", ".htm")):
                logging.info("Loading HTML document using BSHTMLLoader...")
                loader = BSHTMLLoader(file_path, open_encoding="utf-8")
            else:
                logging.info("Loading text document using TextLoader...")
                loader = TextLoader(file_path, encoding="utf-8")

            documents = loader.load()
            
            if not documents:
                raise ValueError(f"No content loaded from {filename}")
            
            logging.info(f"Loaded {len(documents)} document(s) from file")
            
        except Exception as e:
            logging.error(f"Document loading failed: {e}")
            logging.info("="*60)
            raise CustomException(e, sys)
        
        logging.info("Adding metadata to documents...")
        for doc in documents:
            doc.metadata['document_id'] = doc_id
            doc.metadata['filename'] = filename
            doc.metadata['source_path'] = file_path
        
        logging.info(f"Splitting document into chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
        chunks = self.text_splitter.split_documents(documents)
        
        logging.info(f"Split into {len(chunks)} chunks")
        logging.info("="*60)
        return chunks
    
    def process_multiple_documents(self, file_info_list: list) -> dict:
        results = {"successful": [], "failed": []}
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
        return results
    
    def validate_chunks(self, chunks: list[Document]) -> bool:
        if not chunks:
            return False
        required_fields = ['document_id', 'filename', 'source_path']
        for i, chunk in enumerate(chunks):
            for field in required_fields:
                if field not in chunk.metadata:
                    return False
            if not chunk.page_content or len(chunk.page_content.strip()) == 0:
                return False
        return True