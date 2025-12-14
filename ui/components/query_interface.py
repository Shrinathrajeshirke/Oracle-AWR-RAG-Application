"""
Query interface UI component
Handles query configuration and execution
"""

import streamlit as st
from config.settings import MODEL_CHOICES
from config.prompts import get_system_prompt
from core.vector_store import VectorStoreManager
from core.retriever import DocumentRetriever
from llm.factory import get_llm, get_openai_eval_llm
from evaluation.ragas_evaluator import RAGASEvaluator
from evaluation.metrics import CustomMetrics
from reporting.report_builder import ReportBuilder
from ui.session_manager import SessionManager
from utils.logger import logging


def render_query_section():
    """Render query configuration and execution section"""
    st.header("2️⃣ Configure & Query")
    
    ingested_docs = SessionManager.get_ingested_documents()
    
    if not ingested_docs:
        st.warning("⚠️ Please upload and index documents in step 1 to enable querying.")
        return False
    
    # LLM Configuration
    col1, col2 = st.columns(2)
    
    with col1:
        api_choice = st.selectbox(
            "Select LLM provider",
            list(MODEL_CHOICES.keys())[:-1],
            key='api_choice_select'
        )
    
    with col2:
        api_key = st.text_input(
            f"Enter {api_choice.upper()} API key",
            type="password",
            key='api_key_input'
        )
    
    # Model Selection
    available_models = MODEL_CHOICES.get(api_choice, [])
    
    if available_models:
        model_name = st.selectbox(
            f"Select model for {api_choice.upper()}",
            options=available_models,
            key="model_name_select"
        )
    else:
        model_name = st.text_input("Enter model name manually")
    
    # Document Selection
    ingested_doc_ids = list(ingested_docs.keys())
    selected_doc_ids = st.multiselect(
        "Select document(s) for Query/Comparison",
        options=ingested_doc_ids,
        format_func=lambda x: ingested_docs[x],
        default=ingested_doc_ids,
        help="Select two or more documents to compare",
        key='doc_select'
    )
    
    # Query Input
    user_query = st.text_area(
        "Ask your question or request a comparison",
        height=100,
        placeholder="e.g., 'Analyze this AWR report and identify performance issues'"
    )
    
    st.markdown("---")
    
    # Analysis Style
    col_style1, col_style2 = st.columns([2, 1])
    
    with col_style1:
        prompt_style = st.selectbox(
            "🎨 Analysis Style",
            options=["Standard", "Detailed Step-by-Step", "Issue-Focused"],
            index=0,
            help="Choose how the AI analyzes the documents"
        )
    
    with col_style2:
        st.markdown("#### Style Guide")
        if prompt_style == "Standard":
            st.info("📝 Balanced analysis with clear structure")
        elif prompt_style == "Detailed Step-by-Step":
            st.info("🔍 Deep dive with reasoning at each step")
        elif prompt_style == "Issue-Focused":
            st.info("🎯 Executive summary with prioritized issues")
    
    st.markdown("---")
    
    # RAGAS Evaluation Toggle
    col_ragas1, col_ragas2 = st.columns([3, 1])
    
    with col_ragas1:
        ragas_enabled = st.toggle(
            "📊 Enable Background Quality Evaluation (RAGAS)",
            value=True,
            help="Evaluates answer quality in background. Scores are logged for internal tracking."
        )
    
    with col_ragas2:
        if ragas_enabled:
            st.success("✅ Active")
        else:
            st.info("⏸️ Disabled")
    
    if ragas_enabled:
        st.caption("ℹ️ Quality metrics will be logged for internal analysis. No impact on response time.")
    
    st.markdown("---")
    
    # Email Report Options
    st.subheader("📧 Email Report (Optional)")
    
    col_email1, col_email2 = st.columns(2)
    
    with col_email1:
        recipient_email = st.text_input(
            "Recipient Email Address",
            placeholder="user@example.com",
            help="Enter email address to receive the report",
            key='recipient_email'
        )
    
    with col_email2:
        report_format = st.selectbox(
            "Report Format",
            options=["pdf", "html", "text"],
            index=0,
            help="Choose the format for the email report",
            key='report_format'
        )
    
    if recipient_email:
        st.info(f"📨 Report will be sent to: {recipient_email} as {report_format.upper()}")
    
    # Run Query Button
    if st.button("🚀 Run RAG Query", type="primary", use_container_width=True):
        if not api_key or not model_name or not user_query:
            st.error("⚠️ Please ensure API key, model name and query are filled out.")
        else:
            execute_query(
                query=user_query,
                doc_ids=selected_doc_ids,
                api_choice=api_choice,
                api_key=api_key,
                model_name=model_name,
                prompt_style=prompt_style,
                ragas_enabled=ragas_enabled,
                recipient_email=recipient_email if recipient_email else "",
                report_format=report_format if recipient_email else "pdf"
            )
    
    return True


def execute_query(query, doc_ids, api_choice, api_key, model_name, prompt_style,
                  ragas_enabled, recipient_email, report_format):
    """Execute RAG query"""
    
    try:
        with st.spinner(f"Running query with {api_choice.upper()}..."):
            # Get vector store and retriever
            vs_manager = SessionManager.get_vector_store_manager()
            retriever = DocumentRetriever(vs_manager)
            
            # Retrieve documents
            docs = retriever.retrieve_documents(query, doc_ids)
            
            if not docs:
                st.warning("⚠️ No relevant documents found. Try refining your query.")
                return
            
            contexts = [doc.page_content for doc in docs]
            
            # Get LLM
            llm = get_llm(api_choice, api_key, model_name)
            
            # Get system prompt
            system_prompt = get_system_prompt(doc_ids, prompt_style)
            
            # Build and execute RAG chain
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.runnables import RunnablePassthrough
            from langchain_core.output_parsers import StrOutputParser
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt + "\n\nContext: {context}"),
                ("user", "{question}")
            ])
            
            def format_docs(docs):
                return "\n---\n".join([
                    f"Document ID: {doc.metadata.get('document_id', 'Unknown')}\n"
                    f"Filename: {doc.metadata.get('filename', 'Unknown')}\n"
                    f"Content: {doc.page_content}"
                    for doc in docs
                ])
            
            rag_chain = (
                {"context": retriever.get_filtered_retriever(doc_ids) | format_docs, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            answer = rag_chain.invoke(query)
            
            # Store results
            results = {
                "answer": answer,
                "contexts": contexts,
                "retrieved_docs_count": len(docs),
                "error": False
            }
            
            SessionManager.store_query_results(results)
        
        # Display results
        display_query_results(results, ragas_enabled, api_key, recipient_email, report_format, query)
        
    except Exception as e:
        st.error(f"Query execution failed: {e}")
        logging.error(f"Query failed: {e}")


def display_query_results(results, ragas_enabled, api_key, recipient_email, report_format, query):
    """Display query results"""
    
    st.markdown("---")
    st.markdown("### 🤖 RAG Answer")
    
    answer = results.get("answer", "")
    contexts = results.get("contexts", [])
    
    st.success("Query successful!")
    st.markdown(f"**Answer:**\n{answer}")
    
    st.caption(f"📚 Retrieved {results.get('retrieved_docs_count', 0)} relevant chunks")
    
    # RAGAS Evaluation
    if ragas_enabled and api_key:
        with st.spinner("📊 Running quality evaluation..."):
            try:
                evaluator = RAGASEvaluator()
                eval_llm = get_openai_eval_llm(api_key)
                
                ragas_scores = evaluator.evaluate_response(
                    question=query,
                    answer=answer,
                    contexts=contexts,
                    llm=eval_llm
                )
                
                if ragas_scores and "error" not in ragas_scores:
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Faithfulness", f"{ragas_scores.get('faithfulness', 0):.2f}")
                    with col2:
                        st.metric("Answer Relevancy", f"{ragas_scores.get('answer_relevancy', 0):.2f}")
                    with col3:
                        st.metric("Context Precision", f"{ragas_scores.get('context_precision', 0):.2f}")
                    with col4:
                        st.metric("Context Recall", f"{ragas_scores.get('context_recall', 0):.2f}")
                    
                    SessionManager.store_evaluation_results(ragas_scores)
            
            except Exception as e:
                st.warning(f"⚠️ Evaluation failed: {e}")
    
    # Custom Metrics
    if contexts:
        custom_scores = CustomMetrics.compute_overall_quality_score(answer, contexts)
        with st.expander("📊 Custom Quality Metrics"):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Completeness", f"{custom_scores.get('completeness', 0):.2%}")
                st.metric("Specificity", f"{custom_scores.get('specificity', 0):.2%}")
            with col2:
                st.metric("Actionability", f"{custom_scores.get('actionability', 0):.2%}")
                st.metric("Overall Quality", f"{custom_scores.get('overall_quality', 0):.2%}")
    
    # Email Report
    if recipient_email:
        with st.spinner(f"Generating {report_format.upper()} report and sending email..."):
            try:
                builder = ReportBuilder()
                success = builder.generate_and_send_report(
                    user_query=query,
                    answer=answer,
                    contexts=contexts,
                    to_email=recipient_email,
                    report_format=report_format
                )
                
                if success:
                    st.success(f"✅ Report sent successfully to {recipient_email} as {report_format.upper()}!")
                else:
                    st.warning(f"⚠️ Email sending failed. Please check SMTP configuration.")
            
            except Exception as e:
                st.error(f"Error generating/sending report: {e}")
                logging.error(f"Report generation failed: {e}")