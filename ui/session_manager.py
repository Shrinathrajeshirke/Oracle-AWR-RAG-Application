"""
Streamlit session state management
Manages application state across user interactions
"""

import streamlit as st
from core.vector_store import VectorStoreManager
from utils.logger import logging


class SessionManager:
    """Manages Streamlit session state"""
    
    @staticmethod
    def initialize():
        """Initialize all session state variables"""
        logging.info("Initializing session state...")
        
        # RAG Manager
        if 'rag_manager' not in st.session_state:
            st.session_state.rag_manager = None
            logging.info("Initialized: rag_manager")
        
        # Vector Store Manager
        if 'vector_store_manager' not in st.session_state:
            try:
                st.session_state.vector_store_manager = VectorStoreManager()
                logging.info("Initialized: vector_store_manager")
            except Exception as e:
                logging.error(f"Failed to initialize vector_store_manager: {e}")
                st.session_state.vector_store_manager = None
        
        # Ingested Documents
        if 'ingested_docs' not in st.session_state:
            st.session_state.ingested_docs = {}
            logging.info("Initialized: ingested_docs")
        
        # Processed Files
        if 'processed_files' not in st.session_state:
            st.session_state.processed_files = set()
            logging.info("Initialized: processed_files")
        
        # Query Results
        if 'query_results' not in st.session_state:
            st.session_state.query_results = None
            logging.info("Initialized: query_results")
        
        # Evaluation Results
        if 'evaluation_results' not in st.session_state:
            st.session_state.evaluation_results = None
            logging.info("Initialized: evaluation_results")
        
        logging.info("Session initialization complete")
    
    @staticmethod
    def get_vector_store_manager():
        """Get vector store manager, initializing if needed"""
        if st.session_state.vector_store_manager is None:
            try:
                st.session_state.vector_store_manager = VectorStoreManager()
            except Exception as e:
                logging.error(f"Failed to initialize vector store: {e}")
                return None
        return st.session_state.vector_store_manager
    
    @staticmethod
    def add_ingested_document(doc_id: str, filename: str):
        """Add document to ingested documents list"""
        st.session_state.ingested_docs[doc_id] = filename
        logging.info(f"Added document to session: {doc_id} - {filename}")
    
    @staticmethod
    def remove_ingested_document(doc_id: str):
        """Remove document from ingested documents list"""
        if doc_id in st.session_state.ingested_docs:
            del st.session_state.ingested_docs[doc_id]
            logging.info(f"Removed document from session: {doc_id}")
    
    @staticmethod
    def get_ingested_documents():
        """Get all ingested documents"""
        return st.session_state.ingested_docs
    
    @staticmethod
    def add_processed_file(filename: str):
        """Track processed file"""
        st.session_state.processed_files.add(filename)
    
    @staticmethod
    def is_file_processed(filename: str) -> bool:
        """Check if file was already processed"""
        return filename in st.session_state.processed_files
    
    @staticmethod
    def store_query_results(results: dict):
        """Store query results in session"""
        st.session_state.query_results = results
        logging.info("Query results stored in session")
    
    @staticmethod
    def get_query_results():
        """Retrieve stored query results"""
        return st.session_state.query_results
    
    @staticmethod
    def clear_query_results():
        """Clear query results"""
        st.session_state.query_results = None
        logging.info("Query results cleared")
    
    @staticmethod
    def store_evaluation_results(results: dict):
        """Store evaluation results in session"""
        st.session_state.evaluation_results = results
        logging.info("Evaluation results stored in session")
    
    @staticmethod
    def get_evaluation_results():
        """Retrieve stored evaluation results"""
        return st.session_state.evaluation_results
    
    @staticmethod
    def clear_all():
        """Clear all session data"""
        logging.warning("Clearing all session state...")
        st.session_state.rag_manager = None
        st.session_state.ingested_docs = {}
        st.session_state.processed_files = set()
        st.session_state.query_results = None
        st.session_state.evaluation_results = None
        logging.info("Session cleared")