"""
Tier 2 Advanced RAG Examples
Demonstrates re-ranking, query classification, and fact verification
"""

import sys
import os
import glob

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.vector_store import VectorStoreManager
from core.retriever import DocumentRetriever
from core.tier2_retriever import Tier2Retriever
from core.query_classifier import QueryClassifier
from core.reranker import DocumentReranker
from core.fact_verifier import FactVerifier
from ingestor.processor import DocumentProcessor
from utils.logger import logging


def setup_sample_data(vs_manager: VectorStoreManager):
    """Ingests baseline AWR report into the in-memory Qdrant store."""
    data_dir = "data"
    candidate_files = (
        glob.glob(os.path.join(data_dir, "*.html")) 
        + glob.glob(os.path.join(data_dir, "*.htm")) 
        + glob.glob(os.path.join(data_dir, "*.txt"))
    )
    if not candidate_files:
        print("No AWR report files found in data/ to ingest.")
        return

    file_path = candidate_files[0]
    filename = os.path.basename(file_path)
    print(f"\nIngesting '{filename}' into memory for Tier 2 examples...")
    
    processor = DocumentProcessor()
    chunks = processor.load_and_split_document(
        file_path=file_path, 
        doc_id="ebscdb_baseline_report", 
        filename=filename
    )
    vs_manager.index_documents(chunks)
    print(f"Indexed {len(chunks)} chunks into Qdrant.\n")


def example_query_classification():
    """Example 1: Query Intent Classification"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Query Intent Classification")
    print("="*70)
    
    classifier = QueryClassifier()
    test_queries = [
        "What was the total DB Time?",
        "Analyze performance issues and identify root causes",
        "Which SQL needs optimization?",
        "Compare CPU usage between two reports",
        "What is the capacity utilization trend?"
    ]
    
    for query in test_queries:
        result = classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"  Intent: {result['primary_intent']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Strategy: {classifier.get_retrieval_strategy(result['primary_intent'])['method']}")


def example_document_reranking(vs_manager: VectorStoreManager):
    """Example 2: Document Re-ranking"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Document Re-ranking with Cross-Encoder")
    print("="*70)
    
    retriever = DocumentRetriever(vs_manager)
    reranker = DocumentReranker()
    query = "What are the top wait events?"
    
    initial_docs = retriever.retrieve_documents(query, [], k=10)
    print(f"\nInitial retrieval: {len(initial_docs)} documents")
    
    if initial_docs:
        reranked_docs = reranker.rerank(query, initial_docs, top_k=5)
        print(f"After re-ranking: {len(reranked_docs)} documents")
        print("\nTop document (after re-ranking):")
        print(f"  {reranked_docs[0].page_content[:200]}...")


def example_fact_verification():
    """Example 3: Fact Verification"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Fact Verification")
    print("="*70)
    
    verifier = FactVerifier()
    sample_answer = (
        "The database has 32 CPUs and 16 cores. "
        "The total DB Time was 121 minutes. "
        "The top wait event was 'CPU' accounting for 77% of time."
    )
    sample_context = [
        "The host system has 32 CPUs and 16 CPU cores.",
        "Total elapsed time was 121.57 minutes with 9,260 seconds of DB Time.",
        "Foreground wait events: DB CPU (77.3%), Concurrency (15%), IO (5%)"
    ]
    
    from langchain_core.documents import Document
    context_docs = [Document(page_content=c) for c in sample_context]
    report = verifier.verify_response(sample_answer, context_docs)
    
    print(f"\nAnswer: {sample_answer}")
    print(f"\nVerification Report:")
    print(f"  Total Claims: {report['total_claims']}")
    print(f"  Supported: {report['supported_claims']}")
    print(f"  Support Ratio: {report['support_ratio']:.1%}")
    print(f"  Badge: {verifier.get_verification_badge(report)}")


def example_tier2_full_pipeline(vs_manager: VectorStoreManager):
    """Example 4: Full Tier 2 Pipeline"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Full Tier 2 Pipeline")
    print("="*70)
    
    retriever = DocumentRetriever(vs_manager)
    tier2 = Tier2Retriever(retriever)
    query = "Analyze the top wait events and their impact on performance"
    
    docs, info = tier2.retrieve_and_rerank(query, [], use_classification=True)
    
    print(f"\nQuery: {query}")
    print(f"\nClassification:")
    if info['classification']:
        print(f"  Intent: {info['classification']['primary_intent']}")
        print(f"  Confidence: {info['confidence' if 'confidence' in info else 'classification']['confidence']:.2%}")
    
    print(f"\nRetrieval:")
    print(f"  Method: {info['retrieval_method']}")
    print(f"  Initial: {info['initial_docs_count']} documents")
    print(f"  Final: {info['reranked_docs_count']} documents")
    
    if docs:
        print(f"\nTop Result:")
        print(f"  {docs[0].page_content[:300]}...")


def example_retrieval_comparison(vs_manager: VectorStoreManager):
    """Example 5: Compare Tier 1 vs Tier 2"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Tier 1 vs Tier 2 Comparison")
    print("="*70)
    
    retriever = DocumentRetriever(vs_manager)
    tier2 = Tier2Retriever(retriever)
    query = "What are the critical performance issues?"
    
    print(f"\nQuery: {query}\n")
    print("TIER 1 (Hybrid Search):")
    try:
        tier1_docs = retriever.retrieve_hybrid(query, [], k=5)
        print(f"  Retrieved: {len(tier1_docs)} documents")
        if tier1_docs:
            print(f"  Preview: {tier1_docs[0].page_content[:150]}...")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\nTIER 2 (Classification + Re-ranking):")
    try:
        tier2_docs, info = tier2.retrieve_and_rerank(query, [], use_classification=True)
        print(f"  Intent: {info['classification']['primary_intent']}")
        print(f"  Retrieved: {len(tier2_docs)} documents")
        if tier2_docs:
            print(f"  Preview: {tier2_docs[0].page_content[:150]}...")
    except Exception as e:
        print(f"  Error: {e}")


def example_system_prompt_customization(vs_manager: VectorStoreManager):
    """Example 6: Intent-Based System Prompt Customization"""
    print("\n" + "="*70)
    print("EXAMPLE 6: System Prompt Customization by Intent")
    print("="*70)
    
    retriever = DocumentRetriever(vs_manager)
    tier2 = Tier2Retriever(retriever)
    base_prompt = "You are an expert Oracle DBA analyzing AWR reports."
    
    test_queries = [
        "What is the total DB Time?",
        "Analyze performance issues",
        "Optimize this SQL query"
    ]
    
    for query in test_queries:
        custom_prompt = tier2.get_system_prompt_for_query(query, base_prompt)
        print(f"\nQuery: {query}")
        print(f"Customized prompt preview:\n  {custom_prompt[-150:]}")


if __name__ == "__main__":
    shared_vs_manager = VectorStoreManager()
    setup_sample_data(shared_vs_manager)

    example_query_classification()
    example_document_reranking(shared_vs_manager)
    example_fact_verification()
    example_tier2_full_pipeline(shared_vs_manager)
    example_retrieval_comparison(shared_vs_manager)
    example_system_prompt_customization(shared_vs_manager)
    
    print("\n" + "="*70)
    print("All examples completed!")
    print("="*70)