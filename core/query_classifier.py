"""
Query Intent Classification
Classifies user queries into specific types for specialized handling
"""

from typing import Dict, List
from utils.logger import logging


class QueryClassifier:
    """
    Classifies queries into intent types
    Enables specialized retrieval and analysis per intent
    """
    
    # Keywords for each intent type
    INTENT_KEYWORDS = {
        "metrics_extraction": [
            "what", "how many", "how much", "what is", "what was",
            "total", "count", "number", "value", "size", "ratio",
            "percentage", "rate", "average", "sum", "bytes", "seconds",
            "database name", "instance", "elapsed", "cpu", "db time",
            "logical reads", "physical reads", "redo", "executions"
        ],
        "performance_analysis": [
            "analyze", "analyze performance", "identify issues", "problem",
            "bottleneck", "slow", "slow query", "performance", "issue",
            "degradation", "degraded", "contention", "wait", "latency",
            "why is", "root cause", "cause", "explain", "analyze"
        ],
        "sql_tuning": [
            "sql", "query", "sql statement", "optimization", "optimize",
            "index", "execution plan", "explain plan", "execution",
            "full scan", "missing index", "tune", "tuning", "rewrite"
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
        logging.info("QueryClassifier initialized")
    
    def classify(self, query: str) -> Dict[str, any]:
        """
        Classify query intent
        
        Args:
            query: User query
        
        Returns:
            Dict with intent type and confidence
        """
        query_lower = query.lower()
        
        # Score each intent type
        intent_scores = {}
        
        for intent_type, keywords in self.INTENT_KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            intent_scores[intent_type] = score
        
        # Get top intent
        if max(intent_scores.values()) == 0:
            # Default to metrics extraction
            top_intent = "metrics_extraction"
            confidence = 0.3
        else:
            top_intent = max(intent_scores, key=intent_scores.get)
            # Confidence based on keyword matches
            max_score = max(intent_scores.values())
            confidence = min(max_score / 5, 1.0)  # Normalize to 0-1
        
        logging.info(f"Query classified as: {top_intent} (confidence: {confidence:.2%})")
        
        return {
            "primary_intent": top_intent,
            "confidence": confidence,
            "all_scores": intent_scores
        }
    
    def get_retrieval_strategy(self, intent_type: str) -> Dict:
        """
        Get optimal retrieval strategy for intent type
        
        Args:
            intent_type: Type of query intent
        
        Returns:
            Strategy configuration (k, method, etc.)
        """
        strategies = {
            "metrics_extraction": {
                "k": 8,
                "method": "hybrid",  # Exact values matter
                "needs_reranking": True,
                "system_prompt_style": "Standard"
            },
            "performance_analysis": {
                "k": 12,
                "method": "multi_query",  # Need comprehensive context
                "needs_reranking": True,
                "system_prompt_style": "Issue-Focused"
            },
            "sql_tuning": {
                "k": 10,
                "method": "multi_query",  # Multiple SQL approaches
                "needs_reranking": True,
                "system_prompt_style": "Detailed Step-by-Step"
            },
            "comparison": {
                "k": 15,
                "method": "diversity",  # Need all perspectives
                "needs_reranking": True,
                "system_prompt_style": "Standard"
            },
            "capacity_planning": {
                "k": 12,
                "method": "multi_query",  # Need trends over time
                "needs_reranking": True,
                "system_prompt_style": "Detailed Step-by-Step"
            }
        }
        
        return strategies.get(intent_type, strategies["metrics_extraction"])
    
    def get_system_prompt_variation(self, intent_type: str, base_prompt: str) -> str:
        """
        Customize system prompt based on intent type
        
        Args:
            intent_type: Type of query
            base_prompt: Base system prompt
        
        Returns:
            Customized prompt for the intent
        """
        additions = {
            "metrics_extraction": (
                "\n\nFocus on extracting exact numerical values and metrics. "
                "Provide specific numbers with units."
            ),
            "performance_analysis": (
                "\n\nAnalyze the data to identify performance issues. "
                "Explain root causes and recommend solutions with priority levels."
            ),
            "sql_tuning": (
                "\n\nProvide SQL optimization recommendations. "
                "Include execution plan analysis and specific tuning steps."
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
    
    def classify_batch(self, queries: List[str]) -> List[Dict]:
        """
        Classify multiple queries
        
        Args:
            queries: List of queries
        
        Returns:
            List of classification results
        """
        return [self.classify(query) for query in queries]