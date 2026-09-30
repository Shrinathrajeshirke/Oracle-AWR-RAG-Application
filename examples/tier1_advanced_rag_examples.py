"""
Tier 1 Advanced RAG Integration Example
Shows how to use Hybrid Search, Query Processing, and Multi-Query Retrieval together
"""

import os
import glob
from core.vector_store import VectorStoreManager
from core.retriever import DocumentRetriever
from core.query_processor import QueryProcessor
from core.multi_query_retriever import MultiQueryRetriever
from core.hybrid_retriever import HybridRetriever
from ingestor.processor import DocumentProcessor
from utils.logger import logging


def setup_sample_data(vs_manager: VectorStoreManager):
    """Ensures test AWR data is ingested into the in-memory Qdrant instance."""
    data_dir = "data"
    candidate_files = (
        glob.glob(os.path.join(data_dir, "*.html")) 
        + glob.glob(os.path.join(data_dir, "*.htm")) 
        + glob.glob(os.path.join(data_dir, "*.txt"))
    )
    if not candidate_files:
        print("No files found in data/ directory to ingest.")
        return

    file_path = candidate_files[0]
    filename = os.path.basename(file_path)
    print(f"\nIngesting '{filename}' into in-memory store for demo...")
    
    processor = DocumentProcessor()
    chunks = processor.load_and_split_document(
        file_path=file_path, 
        doc_id="sample_doc", 
        filename=filename
    )
    vs_manager.index_documents(chunks)
    print(f"Indexed {len(chunks)} chunks into Qdrant.\n")


def example_basic_hybrid_search(vs_manager: VectorStoreManager):
    """Example 1: Basic Hybrid Search"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Hybrid Search")
    print("="*70)
    
    retriever = DocumentRetriever(vs_manager)
    query = "What are the top wait events?"
    doc_ids = []
    
    docs = retriever.retrieve_hybrid(query, doc_ids, k=5)
    
    print(f"\nQuery: {query}")
    print(f"Retrieved {len(docs)} documents using hybrid search")
    for i, doc in enumerate(docs, 1):
        print(f"\n{i}. {doc.page_content[:200]}...")


def example_query_rewriting():
    """Example 2: Query Rewriting and Expansion"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Query Rewriting & Expansion")
    print("="*70)
    
    processor = QueryProcessor()
    original_query = "What is the CPU issue in this AWR report?"
    
    rewritten = processor.rewrite_query(original_query)
    print(f"\nOriginal: {original_query}")
    print(f"Rewritten: {rewritten}")
    
    variations = processor.expand_query(original_query)
    print(f"\nQuery variations ({len(variations)}):")
    for i, var in enumerate(variations, 1):
        print(f"  {i}. {var}")
    
    terms = processor.get_search_terms(original_query)
    print(f"\nExtracted search terms: {terms}")


def example_multi_query_retrieval(vs_manager: VectorStoreManager):
    """Example 3: Multi-Query Retrieval"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Multi-Query Retrieval")
    print("="*70)
    
    retriever = DocumentRetriever(vs_manager)
    multi_retriever = MultiQueryRetriever(retriever)
    
    query = "Analyze performance issues and provide solutions"
    doc_ids = []
    
    docs = multi_retriever.retrieve_multi_query(query, doc_ids, k=5)
    
    print(f"\nQuery: {query}")
    print(f"Retrieved {len(docs)} documents using multi-query retrieval")
    for i, doc in enumerate(docs, 1):
        print(f"\n{i}. {doc.page_content[:200]}...")


def example_diversity_based_retrieval(vs_manager: VectorStoreManager):
    """Example 4: Diversity-Based Retrieval"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Diversity-Based Retrieval")
    print("="*70)
    
    retriever = DocumentRetriever(vs_manager)
    multi_retriever = MultiQueryRetriever(retriever)
    
    query = "What are the top wait events and how does CPU usage affect performance?"
    doc_ids = []
    
    docs = multi_retriever.retrieve_with_diversity(query, doc_ids, k=5)
    
    print(f"\nQuery: {query}")
    print(f"Retrieved {len(docs)} documents with diversity emphasis")
    for i, doc in enumerate(docs, 1):
        print(f"\n{i}. {doc.page_content[:200]}...")


def compare_retrieval_methods(vs_manager: VectorStoreManager, query: str):
    """Compare different retrieval methods on the same query"""
    print("\n" + "="*70)
    print("COMPARISON: Different Retrieval Methods")
    print("="*70)
    
    retriever = DocumentRetriever(vs_manager)
    multi_retriever = MultiQueryRetriever(retriever)
    
    print(f"\nQuery: {query}")
    print(f"\n{'Method':<30} | {'Results':<10}")
    print("-" * 45)
    
    try:
        vector_docs = retriever.retrieve_documents(query, [], k=5)
        print(f"{'Vector Search':<30} | {len(vector_docs):<10}")
    except Exception as e:
        print(f"{'Vector Search':<30} | Error: {e}")
    
    try:
        hybrid_docs = retriever.retrieve_hybrid(query, [], k=5)
        print(f"{'Hybrid Search':<30} | {len(hybrid_docs):<10}")
    except Exception as e:
        print(f"{'Hybrid Search':<30} | Error: {e}")
    
    try:
        multi_docs = multi_retriever.retrieve_multi_query(query, [], k=5)
        print(f"{'Multi-Query':<30} | {len(multi_docs):<10}")
    except Exception as e:
        print(f"{'Multi-Query':<30} | Error: {e}")
    
    try:
        diversity_docs = multi_retriever.retrieve_with_diversity(query, [], k=5)
        print(f"{'Diversity-Based':<30} | {len(diversity_docs):<10}")
    except Exception as e:
        print(f"{'Diversity-Based':<30} | Error: {e}")


if __name__ == "__main__":
    vs_manager = VectorStoreManager()
    setup_sample_data(vs_manager)

    example_query_rewriting()
    example_basic_hybrid_search(vs_manager)
    example_multi_query_retrieval(vs_manager)
    example_diversity_based_retrieval(vs_manager)
    compare_retrieval_methods(vs_manager, "What are the top wait events causing performance issues?")