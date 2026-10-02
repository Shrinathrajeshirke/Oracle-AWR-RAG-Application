"""
Semantic Solution Cache using Qdrant
Stores masked issue diagnostic signatures and resolutions for fast retrieval.
"""

import uuid
from typing import Dict, List, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from utils.logger import logging


class SolutionCacheManager:
    """Manages semantic caching of masked Oracle performance diagnoses."""

    COLLECTION_NAME = "awr_solution_cache"

    def __init__(self, client: QdrantClient = None):
        from config.settings import EMBEDDING_MODEL
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.client = client or QdrantClient(":memory:")
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if self.COLLECTION_NAME not in collections:
                self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
                logging.info(f"Created dedicated Qdrant collection: {self.COLLECTION_NAME}")
        except Exception as e:
            logging.error(f"Failed to verify/create solution cache collection: {e}")

    def lookup_similar_solution(self, symptom_text: str, similarity_threshold: float = 0.88) -> Optional[Dict]:
        """Finds if this issue pattern has already been solved."""
        try:
            vector = self.embeddings.embed_query(symptom_text)
            results = self.client.search(
                collection_name=self.COLLECTION_NAME,
                query_vector=vector,
                limit=1,
                score_threshold=similarity_threshold
            )
            if results:
                top = results[0]
                return {
                    "matched_symptom": top.payload.get("symptom"),
                    "cached_solution": top.payload.get("solution"),
                    "similarity": top.score
                }
        except Exception as e:
            logging.error(f"Error during solution cache lookup: {e}")
        return None

    def store_solution(self, masked_symptom: str, masked_solution: str):
        """Saves a masked diagnostic solution for future reuse."""
        try:
            vector = self.embeddings.embed_query(masked_symptom)
            point_id = str(uuid.uuid4())
            self.client.upsert(
                collection_name=self.COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "symptom": masked_symptom,
                            "solution": masked_solution
                        }
                    )
                ]
            )
            logging.info("Successfully cached masked solution in Qdrant")
        except Exception as e:
            logging.error(f"Failed to cache solution: {e}")