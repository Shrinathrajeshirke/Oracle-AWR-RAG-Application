"""
Oracle AWR AI Tuning Assistant - Production Chatbot Interface
Features: Auto-Summary, Interactive Chat, Semantic Solution Cache, PII Masking, Fact Verification, and MOS Links.
"""

import os
import uuid
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from config.prompts import get_system_prompt
from config.settings import TEMP_DIR
from core.vector_store import VectorStoreManager
from core.retriever import DocumentRetriever
from core.sanitizer import AwrSanitizer
from core.oracle_kb import OracleDocResolver
from core.solution_cache import SolutionCacheManager
from core.fact_verifier import FactVerifier
from ingestor.processor import DocumentProcessor
from llm.factory import get_llm
from utils.logger import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Streamlit Page Config
st.set_page_config(
    page_title="Oracle AWR Performance Copilot",
    page_icon="⚡",
    layout="wide"
)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vs_manager" not in st.session_state:
    st.session_state.vs_manager = VectorStoreManager()
if "cache_manager" not in st.session_state:
    st.session_state.cache_manager = SolutionCacheManager(st.session_state.vs_manager.client)
if "active_doc_ids" not in st.session_state:
    st.session_state.active_doc_ids = []
if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()


def get_llm_chain():
    """Initializes LLM using the server-side environment key and gpt-4o-mini."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY is missing in your .env file.")
        st.stop()
    return get_llm("openai", api_key, "gpt-4o-mini")


def process_report_silently(uploaded_file):
    """Silently parses, splits, and indexes the AWR report without cluttering the UI."""
    if not os.path.exists(TEMP_DIR):
        os.makedirs(TEMP_DIR)

    file_path = os.path.join(TEMP_DIR, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    doc_id = str(uuid.uuid4())[:8]
    processor = DocumentProcessor()
    chunks = processor.load_and_split_document(file_path, doc_id, uploaded_file.name)
    st.session_state.vs_manager.index_documents(chunks)

    if os.path.exists(file_path):
        os.remove(file_path)

    st.session_state.active_doc_ids.append(doc_id)
    st.session_state.processed_files.add(uploaded_file.name)
    return doc_id


def generate_rag_response(user_query: str) -> str:
    """Executes Tier 1 Hybrid search, runs LLM, and performs dual-pass fact verification."""
    retriever = DocumentRetriever(st.session_state.vs_manager)
    docs = retriever.retrieve_hybrid(user_query, st.session_state.active_doc_ids, k=10)

    context_str = "\n\n---\n\n".join([doc.page_content for doc in docs]) if docs else "No specific context found."
    system_prompt = get_system_prompt(st.session_state.active_doc_ids)

    llm = get_llm_chain()
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + "\n\nRetrieved Context:\n{context}"),
        ("user", "{question}")
    ])
    chain = prompt | llm | StrOutputParser()
    raw_answer = chain.invoke({"context": context_str, "question": user_query})

    # Dual-pass Fact Verification
    verified_answer, is_valid = FactVerifier.verify_response(raw_answer, docs)

    # Append Clickable Oracle MOS / Documentation Links if matching issues detected
    oracle_refs = OracleDocResolver.get_references_for_text(verified_answer)
    if oracle_refs:
        ref_block = "\n\n---\n**📚 Official Oracle Reference & Support Links:**\n"
        for ref in oracle_refs:
            ref_block += f"- [{ref['title']} ({ref['doc_id']})]({ref['url']}) | [Documentation Guide]({ref['free_doc']})\n"
        verified_answer += ref_block

    # Mask sensitive details and store in Solution Cache
    masked_query = AwrSanitizer.sanitize(user_query)
    masked_answer = AwrSanitizer.sanitize(verified_answer)
    st.session_state.cache_manager.store_solution(masked_query, masked_answer)

    return verified_answer


# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.title("⚡ AWR Copilot")
    st.markdown("Automated Oracle Workload & Performance Tuning Engine")

    st.divider()

    uploaded_files = st.file_uploader(
        "Upload AWR Report (HTML / TXT)",
        type=["html", "txt", "pdf"],
        accept_multiple_files=True,
        help="Upload an AWR report to receive an automatic performance diagnosis."
    )

    # Auto-Analyze upon file upload
    if uploaded_files:
        new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
        if new_files:
            for nf in new_files:
                with st.spinner(f"Analyzing {nf.name}..."):
                    doc_id = process_report_silently(nf)
                    initial_query = "Provide a comprehensive performance diagnosis and executive summary of this AWR report."
                    auto_summary = generate_rag_response(initial_query)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"### 📊 Initial Diagnosis for `{nf.name}`\n\n" + auto_summary
                    })
            st.rerun()

    st.divider()

    if st.button("🧹 Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("### 📖 About")
    st.info(
        """
        **Oracle AWR Performance Copilot**
        
        • **Automatic Ingestion:** Instant analysis with tabular parsing.
        • **Tier 1 Hybrid Engine:** BM25 lexical + dense semantic retrieval.
        • **Anti-Hallucination:** Fact verification & zero-temperature sampling.
        • **Privacy Masking:** PII sanitization for enterprise data.
        • **Solution Memory:** Semantic issue caching for recurring bottlenecks.
        • **Oracle KB Linking:** Clickable MOS Note IDs and documentation.
        """
    )


# ============================================================================
# MAIN CHAT INTERFACE
# ============================================================================
st.title("💬 Oracle AWR Interactive Tuning Assistant")

if not st.session_state.active_doc_ids:
    st.info("👈 Please upload an Oracle AWR report from the sidebar to begin the analysis.")
else:
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if user_prompt := st.chat_input("Ask a follow-up question (e.g., 'What SQL statement caused the most buffer gets?')"):
        # Display user message
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        # Check Semantic Solution Cache first
        cached = st.session_state.cache_manager.lookup_similar_solution(user_prompt)
        with st.chat_message("assistant"):
            if cached:
                response_text = f"⚡ *(Retrieved from Solution Cache - {cached['similarity']:.1%} match)*\n\n" + cached["cached_solution"]
                st.markdown(response_text)
            else:
                with st.spinner("Analyzing performance data..."):
                    response_text = generate_rag_response(user_prompt)
                    st.markdown(response_text)

        st.session_state.messages.append({"role": "assistant", "content": response_text})