"""
Query Intent Classification and Canonical Section Expansion
Classifies user queries into specific types for specialized handling
and enriches queries with official Oracle AWR section names.
"""

import re
from typing import Dict, List, Any
from utils.logger import logging

SQL_ID_PATTERN = re.compile(r'\b[0-9a-z]{13}\b', re.IGNORECASE)


class QueryClassifier:
    """
    Classifies queries into intent types and injects canonical Oracle AWR
    table/section names into keyword and dense retrieval pipelines.
    """

    # Keywords for each intent type
    INTENT_KEYWORDS = {
        "metrics_extraction": [
            "what", "how many", "how much", "what is", "what was",
            "total", "count", "number", "value", "size", "ratio",
            "percentage", "rate", "average", "sum", "bytes", "seconds",
            "database name", "instance", "elapsed", "cpu", "db time",
            "logical reads", "physical reads", "redo", "executions", "hit ratio"
        ],
        "performance_analysis": [
            "analyze", "analyze performance", "identify issues", "problem",
            "bottleneck", "slow", "slow query", "performance", "issue",
            "degradation", "degraded", "contention", "wait", "latency",
            "why is", "root cause", "cause", "explain"
        ],
        "sql_tuning": [
            "sql", "query", "sql statement", "optimization", "optimize",
            "index", "execution plan", "explain plan", "execution",
            "full scan", "missing index", "tune", "tuning", "rewrite", "sql_id"
        ],
        "comparison": [
            "compare", "comparison", "difference", "versus", "vs",
            "between", "trend", "change", "improved", "degraded",
            "before", "after", "then", "now", "increase", "decrease"
        ],
        "capacity_planning": [
            "capacity", "growth", "trend", "forecast", "projection",
            "peak", "peak usage", "resource", "allocation", "scaling",
            "limit", "threshold", "headroom", "utilization"
        ]
    }

    def __init__(self):
        """Initialize query classifier"""
        logging.info("QueryClassifier initialized with Canonical AWR Section Injector")

    def expand_query_with_canonical_sections(self, query: str) -> str:
        """
        Enriches query with targeted Oracle AWR section names.
        If a specific SQL_ID is identified, isolates it to avoid BM25 token dilution.
        """
        sql_match = SQL_ID_PATTERN.search(query)
        if sql_match:
            sql_id = sql_match.group(0)
            return f"{sql_id} SQL"

        q_lower = query.lower()

        if "hit ratio" in q_lower or "buffer cache" in q_lower or "library cache" in q_lower:
            return f"{query} Instance Efficiency Percentages"
        if "elapsed time" in q_lower and ("sql" in q_lower or "query" in q_lower):
            return f"{query} SQL ordered by Elapsed Time"
        if "buffer gets" in q_lower or ("gets" in q_lower and "sql" in q_lower):
            return f"{query} SQL ordered by Gets"
        if "db cpu" in q_lower or "cpu" in q_lower:
            return f"{query} Time Model Statistics"
        if "wait event" in q_lower or "foreground wait" in q_lower:
            return f"{query} Top 10 Foreground Events by Total Wait Time"
        if "redo" in q_lower:
            return f"{query} Load Profile redo size"
        if "logical read" in q_lower or "physical read" in q_lower:
            return f"{query} Load Profile logical reads physical reads"
        if "db time" in q_lower:
            return f"{query} Time Model Statistics"

        return query

    def classify(self, query: str) -> Dict[str, Any]:
        """
        Classify query intent.

        Args:
            query: User query

        Returns:
            Dict with intent type, confidence, and expanded query string
        """
        query_lower = query.lower()

        # Score each intent type
        intent_scores = {}
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            intent_scores[intent_type] = score

        # Determine top intent
        if max(intent_scores.values()) == 0:
            top_intent = "metrics_extraction"
            confidence = 0.3
        else:
            top_intent = max(intent_scores, key=intent_scores.get)
            max_score = max(intent_scores.values())
            confidence = min(max_score / 5.0, 1.0)

        # Generate targeted canonical section expansion
        expanded_query = self.expand_query_with_canonical_sections(query)

        logging.info(f"Query classified as: {top_intent} (confidence: {confidence:.2%})")

        return {
            "primary_intent": top_intent,
            "confidence": confidence,
            "all_scores": intent_scores,
            "expanded_query": expanded_query
        }

    def get_retrieval_strategy(self, intent_type: str) -> Dict[str, Any]:
        """
        Get optimal retrieval strategy for intent type.

        Args:
            intent_type: Type of query intent

        Returns:
            Strategy configuration (k, method, etc.)
        """
        strategies = {
            "metrics_extraction": {
                "k": 10,
                "method": "hybrid",
                "needs_reranking": True,
                "system_prompt_style": "Standard"
            },
            "performance_analysis": {
                "k": 12,
                "method": "multi_query",
                "needs_reranking": True,
                "system_prompt_style": "Issue-Focused"
            },
            "sql_tuning": {
                "k": 12,
                "method": "hybrid",
                "needs_reranking": True,
                "system_prompt_style": "Detailed Step-by-Step"
            },
            "comparison": {
                "k": 15,
                "method": "diversity",
                "needs_reranking": True,
                "system_prompt_style": "Standard"
            },
            "capacity_planning": {
                "k": 12,
                "method": "multi_query",
                "needs_reranking": True,
                "system_prompt_style": "Detailed Step-by-Step"
            }
        }

        return strategies.get(intent_type, strategies["metrics_extraction"])

    def get_system_prompt_variation(self, intent_type: str, base_prompt: str) -> str:
        """
        Customize system prompt based on intent type.

        Args:
            intent_type: Type of query
            base_prompt: Base system prompt

        Returns:
            Customized prompt for the intent
        """
        additions = {
            "metrics_extraction": (
                "\n\nFocus on extracting exact numerical values and metrics. "
                "Provide specific numbers with units directly from the tables."
            ),
            "performance_analysis": (
                "\n\nAnalyze the data to identify performance issues. "
                "Explain root causes and recommend solutions with priority levels."
            ),
            "sql_tuning": (
                "\n\nProvide SQL optimization recommendations. "
                "Include execution plan analysis, SQL_IDs, buffer gets, elapsed times, and specific tuning steps."
            ),
            "comparison": (
                "\n\nCompare the metrics and identify trends. "
                "Highlight what improved and what degraded between periods."
            ),
            "capacity_planning": (
                "\n\nAnalyze capacity trends and growth patterns. "
                "Provide forecasts and recommendations for resource allocation."
            )
        }

        return base_prompt + additions.get(intent_type, "")

    def classify_batch(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Classify multiple queries.

        Args:
            queries: List of queries

        Returns:
            List of classification results
        """
        return [self.classify(query) for query in queries]