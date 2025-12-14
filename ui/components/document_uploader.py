"""
Document upload and ingestion UI component
Handles file uploads and document indexing
"""

import uuid
import os
import streamlit as st
from ingestor.processor import DocumentProcessor
from ingestor.metadata_manager import MetadataManager
from ui.session_manager import SessionManager
from config.settings import TEMP_DIR
from utils.logger import logging


def render_upload_section():
    """Render document upload section"""
    st.header("1️⃣ Upload & Index Documents")
    
    uploaded_files = st.file_uploader(
        "Upload AWR Reports (PDF, TXT, DOCX, HTML)",
        type=["pdf", "txt", "docx", "html"],
        accept_multiple_files=True,
        help="Documents will be automatically indexed upon upload"
    )
    
    # Auto-index on upload
    if uploaded_files:
        new_files = [
            f for f in uploaded_files
            if not SessionManager.is_file_processed(f.name)
        ]
        
        if new_files:
            with st.spinner(f"🔄 Auto-indexing {len(new_files)} new document(s)..."):
                handle_ingestion(new_files)
    
    # Display indexed documents
    display_indexed_documents()
    
    return uploaded_files


def handle_ingestion(uploaded_files):
    """Process and index uploaded files"""
    processor = DocumentProcessor()
    metadata_mgr = MetadataManager()
    vs_manager = SessionManager.get_vector_store_manager()
    
    if vs_manager is None:
        st.error("❌ Vector store not initialized. Cannot index documents.")
        return
    
    progress_bar = st.progress(0)
    status_placeholder = st.empty()
    
    for idx, uploaded_file in enumerate(uploaded_files):
        try:
            doc_id = str(uuid.uuid4())[:8]
            file_path = os.path.join(TEMP_DIR, uploaded_file.name)
            
            # Save file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Update status
            status_placeholder.info(f"Processing {uploaded_file.name}...")
            
            # Process document
            chunks = processor.load_and_split_document(
                file_path=file_path,
                doc_id=doc_id,
                filename=uploaded_file.name
            )
            
            status_placeholder.info(f"Split into {len(chunks)} chunks. Indexing...")
            
            # Index chunks
            vs_manager.index_documents(chunks)
            
            # Register metadata
            metadata_mgr.register_document(
                doc_id=doc_id,
                filename=uploaded_file.name,
                chunk_count=len(chunks),
                file_size=len(uploaded_file.getbuffer())
            )
            
            # Update session
            SessionManager.add_ingested_document(doc_id, uploaded_file.name)
            SessionManager.add_processed_file(uploaded_file.name)
            
            st.success(f"✅ Indexed {uploaded_file.name} (ID: {doc_id})")
            
            # Cleanup
            if os.path.exists(file_path):
                os.remove(file_path)
            
        except Exception as e:
            st.error(f"Failed to process {uploaded_file.name}: {e}")
            logging.error(f"Document processing failed: {e}")
        
        # Update progress
        progress_bar.progress((idx + 1) / len(uploaded_files))
    
    progress_bar.empty()
    status_placeholder.empty()


def display_indexed_documents():
    """Display list of indexed documents"""
    ingested_docs = SessionManager.get_ingested_documents()
    
    if ingested_docs:
        st.markdown("### 📚 Currently Indexed Documents")
        
        doc_list = [
            (doc_id, filename)
            for doc_id, filename in ingested_docs.items()
        ]
        
        st.dataframe(
            doc_list,
            column_config={
                0: st.column_config.TextColumn("Document ID", help="Unique 8-char identifier"),
                1: st.column_config.TextColumn("Filename", help="Original uploaded file name")
            },
            hide_index=True,
            use_container_width=True
        )
        
        st.divider()
        
        # Delete option
        with st.expander("🗑️ Delete Documents"):
            doc_to_delete = st.selectbox(
                "Select document to delete",
                options=list(ingested_docs.keys()),
                format_func=lambda x: ingested_docs[x]
            )
            
            if st.button("Delete Selected Document"):
                SessionManager.remove_ingested_document(doc_to_delete)
                st.success(f"✅ Document deleted: {ingested_docs[doc_to_delete]}")
                st.rerun()
    else:
        st.info("📄 No documents indexed yet. Upload documents to get started.")