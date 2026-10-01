"""
Tier 2 Retriever - Orchestrates Advanced RAG Techniques
Combines query classification, canonical AWR section injection, intelligent retrieval,
cross-encoder re-ranking, fact verification, and header chunk metadata pinning.
"""

from typing import List, Dict, Tuple
from langchain_core.documents import Document
from core.retriever import DocumentRetriever
from core.query_classifier import QueryClassifier
from core.multi_query_retriever import MultiQueryRetriever
from core.reranker import DocumentReranker
from core.fact_verifier import FactVerifier
from utils.logger import logging


class Tier2Retriever:
    """
    Advanced retriever combining:
    - Query intent classification & canonical section expansion
    - Intelligent retrieval routing (Hybrid vs Multi-Query vs Diversity)
    - Cross-encoder re-ranking aligned to search query
    - Fact verification
    - Metadata header chunk pinning
    """

    def __init__(self, base_retriever: DocumentRetriever):
        """
        Initialize Tier 2 retriever

        Args:
            base_retriever: Base DocumentRetriever instance
        """
        self.retriever = base_retriever
        self.classifier = QueryClassifier()
        self.multi_retriever = MultiQueryRetriever(base_retriever)
        self.reranker = DocumentReranker()
        self.verifier = FactVerifier()

        logging.info("Tier2Retriever initialized with canonical section expansion and header pinning")

    def _is_metadata_query(self, query: str) -> bool:
        """
        Identifies whether a query targets general database or host specifications
        such that the pinned header chunk should be prioritized.
        """
        meta_keywords = [
            "database name", "instance name", "db name", "elapsed time",
            "cpus", "cpu cores", "cores", "sockets", "host name", "snapshot",
            "host system", "platform", "release", "cache size"
        ]
        q_lower = query.lower()
        return any(kw in q_lower for kw in meta_keywords)

    def _get_pinned_header_chunk(self, doc_ids: List[str]) -> List[Document]:
        """
        Retrieves the pinned chunk 0 (is_header=True) from the active Qdrant vector store.
        """
        try:
            client = self.retriever.vectorstore_manager.client
            collection_name = self.retriever.vectorstore_manager.collection_name

            all_points, _ = client.scroll(
                collection_name=collection_name,
                limit=150,
                with_payload=True,
                with_vectors=False
            )

            for point in all_points:
                payload = point.payload or {}
                meta = payload.get("metadata", {})

                # Filter by doc_ids if specified
                if doc_ids and meta.get("document_id") not in doc_ids:
                    continue

                if meta.get("is_header") is True or meta.get("chunk_id") == 0:
                    content = payload.get("page_content") or payload.get("text", "")
                    if content:
                        return [Document(page_content=content, metadata=meta)]
        except Exception as e:
            logging.error(f"Error fetching pinned header chunk: {e}")

        return []

    def retrieve_and_rerank(self, query: str, doc_ids: List[str],
                           use_classification: bool = True) -> Tuple[List[Document], Dict]:
        """
        Main retrieval pipeline with classification, section-expanded retrieval,
        aligned cross-encoder re-ranking, and metadata pinning guardrails.

        Args:
            query: User query
            doc_ids: Document IDs to filter by
            use_classification: Whether to use query intent classification

        Returns:
            Tuple of (reranked documents, retrieval info dict)
        """
        logging.info("=" * 70)
        logging.info("TIER 2 RETRIEVAL PIPELINE")
        logging.info("=" * 70)

        info = {
            "query": query,
            "doc_ids": doc_ids,
            "classification": None,
            "retrieval_method": None,
            "initial_docs_count": 0,
            "reranked_docs_count": 0
        }

        # Step 1: Classify query intent and expand with canonical AWR table headers
        if use_classification:
            classification = self.classifier.classify(query)
            info["classification"] = classification
            intent = classification["primary_intent"]
            confidence = classification["confidence"]
            search_query = classification.get("expanded_query", query)

            logging.info(f"Query Intent: {intent} (confidence: {confidence:.2%})")
            logging.info(f"Search Query for Retriever: {search_query}")

            # Get strategy for this intent
            strategy = self.classifier.get_retrieval_strategy(intent)
            k = strategy["k"]
            method = strategy["method"]
        else:
            intent = "default"
            strategy = {"needs_reranking": True}
            k = 10
            method = "hybrid"
            search_query = query
            logging.info("Using default retrieval strategy (classification disabled)")

        info["retrieval_method"] = method

        # Step 2: Retrieve candidate documents using the expanded query
        if method == "hybrid":
            logging.info(f"Retrieving with Hybrid Search (k={k})")
            docs = self.retriever.retrieve_hybrid(search_query, doc_ids, k=k)

        elif method == "multi_query":
            logging.info(f"Retrieving with Multi-Query (k={k})")
            docs = self.multi_retriever.retrieve_multi_query(search_query, doc_ids, k=k)

        elif method == "diversity":
            logging.info(f"Retrieving with Diversity-Based (k={k})")
            docs = self.multi_retriever.retrieve_with_diversity(search_query, doc_ids, k=k)

        else:
            logging.info(f"Retrieving with standard Vector Search (k={k})")
            docs = self.retriever.retrieve_documents(search_query, doc_ids, k=k)

        info["initial_docs_count"] = len(docs)
        logging.info(f"Retrieved {len(docs)} initial documents")

        # Step 3: Re-rank candidate documents using Cross-Encoder against search_query
        if strategy.get("needs_reranking", True) and len(docs) > 5:
            logging.info("Re-ranking documents with cross-encoder")
            top_k = min(5, len(docs))
            docs = self.reranker.rerank(search_query, docs, top_k=top_k)
            info["reranked_docs_count"] = len(docs)
        else:
            info["reranked_docs_count"] = len(docs)
            if len(docs) > 5:
                docs = docs[:5]

        # Step 4: Metadata Header Pinning Guardrail
        if self._is_metadata_query(query):
            header_docs = self._get_pinned_header_chunk(doc_ids)
            if header_docs:
                logging.info("Metadata query pattern detected: Prepending Pinned Chunk 0 to context")
                header_text_key = header_docs[0].page_content[:100]
                docs = [
                    d for d in docs
                    if d.page_content[:100] != header_text_key and not d.metadata.get("is_header")
                ]
                docs.insert(0, header_docs[0])
                if len(docs) > 5:
                    docs = docs[:5]

        logging.info(f"Final retrieved documents: {len(docs)}")
        logging.info("=" * 70)

        return docs, info

    def retrieve_with_verification(self, query: str, doc_ids: List[str],
                                  answer: str) -> Dict:
        """
        Retrieve documents and verify facts in given answer

        Args:
            query: User query
            doc_ids: Document IDs
            answer: LLM-generated answer to verify

        Returns:
            Dict with documents, retrieval info, and verification report
        """
        docs, retrieval_info = self.retrieve_and_rerank(query, doc_ids)
        verification_report = self.verifier.verify_response(answer, docs)

        return {
            "documents": docs,
            "retrieval_info": retrieval_info,
            "verification": verification_report,
            "badge": self.verifier.get_verification_badge(verification_report)
        }

    def get_system_prompt_for_query(self, query: str, base_prompt: str) -> str:
        """
        Get customized system prompt based on query intent

        Args:
            query: User query
            base_prompt: Base system prompt

        Returns:
            Customized system prompt
        """
        classification = self.classifier.classify(query)
        intent = classification["primary_intent"]

        strategy = self.classifier.get_retrieval_strategy(intent)
        style = strategy["system_prompt_style"]

        prompt = self.classifier.get_system_prompt_variation(intent, base_prompt)
        logging.info(f"Using system prompt style: {style}")

        return prompt

    def compare_retrieval_methods(self, query: str, doc_ids: List[str]) -> Dict:
        """
        Compare different retrieval methods on the same query

        Args:
            query: User query
            doc_ids: Document IDs

        Returns:
            Comparison results
        """
        logging.info(f"Comparing retrieval methods for: {query[:80]}...")

        methods = {
            "vector": lambda: self.retriever.retrieve_documents(query, doc_ids, k=5),
            "hybrid": lambda: self.retriever.retrieve_hybrid(query, doc_ids, k=5),
            "multi_query": lambda: self.multi_retriever.retrieve_multi_query(query, doc_ids, k=5),
            "diversity": lambda: self.multi_retriever.retrieve_with_diversity(query, doc_ids, k=5),
        }

        results = {}
        for method_name, method_func in methods.items():
            try:
                docs = method_func()
                results[method_name] = {
                    "count": len(docs),
                    "success": True,
                    "top_doc_preview": docs[0].page_content[:100] if docs else "N/A"
                }
            except Exception as e:
                results[method_name] = {
                    "count": 0,
                    "success": False,
                    "error": str(e)
                }

        return results