"""
Oracle AWR RAG Application - Main Entry Point
Refactored to use modular UI components
"""

import os
import streamlit as st
from config.settings import TEMP_DIR
from ui.session_manager import SessionManager
from ui.components.document_uploader import render_upload_section
from ui.components.query_interface import render_query_section
from utils.logger import logging

# ============================================================================
# STREAMLIT PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Oracle AWR RAG Application",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# INITIALIZE APPLICATION
# ============================================================================

def initialize_app():
    """Initialize application on startup"""
    # Create temp directory
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)
    
    # Initialize session
    SessionManager.initialize()
    
    logging.info("Application initialized")


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application function"""
    
    # Initialize
    initialize_app()
    
    # Title
    st.title("📊 Oracle AWR RAG Application")
    st.markdown(
        "Analyze AWR reports using advanced AI and semantic search. "
        "Upload multiple reports, ask questions in natural language, and receive intelligent insights."
    )
    
    # Sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Application Settings")
        
        # Clear session option
        if st.button("🔄 Clear All Data"):
            SessionManager.clear_all()
            st.success("✅ Session cleared!")
            st.rerun()
        
        st.divider()
        
        # Info
        st.markdown("### 📖 About")
        st.info(
            """
            **Oracle AWR RAG Application**
            
            • Upload AWR reports (PDF, TXT, DOCX, HTML)
            • Ask performance analysis questions
            • Get AI-powered insights with evidence
            • Generate and email reports
            
            **Features:**
            • Multi-document comparison
            • 3 analysis styles (Standard, Detailed, Issue-Focused)
            • Quality evaluation (RAGAS metrics)
            • Email delivery (PDF/HTML/Text)
            """
        )
    
    # Main Content
    render_upload_section()
    
    if render_query_section():
        pass
    
    # Footer
    st.markdown("---")
    st.caption(
        "Oracle AWR RAG Application | "
        "Powered by LangChain, Qdrant & Advanced LLMs"
    )


if __name__ == "__main__":
    main()