"""
Custom evaluation metrics for AWR RAG
Metrics specific to Oracle database performance analysis
"""

from typing import List
from utils.logger import logging


class CustomMetrics:
    """
    Custom evaluation metrics tailored for AWR report analysis
    Assesses quality of database performance insights
    """
    
    @staticmethod
    def metric_completeness(answer: str) -> float:
        """
        Check if answer covers key AWR sections
        
        Args:
            answer: Generated answer text
        
        Returns:
            float: Score from 0-1 indicating completeness
        """
        key_sections = [
            "wait events",
            "cpu",
            "db time",
            "sql",
            "performance",
            "metrics"
        ]
        
        answer_lower = answer.lower()
        covered = sum(1 for section in key_sections if section in answer_lower)
        score = covered / len(key_sections)
        
        logging.info(f"Completeness score: {score:.2%} ({covered}/{len(key_sections)} sections covered)")
        return score
    
    @staticmethod
    def metric_actionability(answer: str) -> float:
        """
        Check if answer provides actionable recommendations
        
        Args:
            answer: Generated answer text
        
        Returns:
            float: Score from 0-1 indicating actionability
        """
        action_keywords = [
            "recommend",
            "should",
            "implement",
            "add index",
            "optimize",
            "increase",
            "decrease",
            "modify",
            "enable",
            "disable",
            "action",
            "step",
            "priority",
            "solution"
        ]
        
        answer_lower = answer.lower()
        action_count = sum(1 for keyword in action_keywords if keyword in answer_lower)
        
        # Score based on action keywords found
        score = min(1.0, action_count / 5)  # 5+ keywords = perfect score
        
        logging.info(f"Actionability score: {score:.2%} ({action_count} action keywords found)")
        return score
    
    @staticmethod
    def metric_specificity(answer: str, contexts: List[str]) -> float:
        """
        Check if answer includes specific metrics and values
        
        Args:
            answer: Generated answer text
            contexts: Retrieved context chunks
        
        Returns:
            float: Score from 0-1 indicating specificity
        """
        metric_patterns = [
            "%",
            "ms",
            "sec",
            "hours",
            "count",
            "=",
            ">",
            "<"
        ]
        
        specific_count = sum(1 for pattern in metric_patterns if pattern in answer)
        context_references = answer.lower().count("document") + answer.lower().count("context")
        
        # Score based on metric values and context references
        score = min(1.0, (specific_count + context_references) / 10)
        
        logging.info(f"Specificity score: {score:.2%}")
        return score
    
    @staticmethod
    def metric_structure(answer: str) -> float:
        """
        Check if answer is well-structured with clear sections
        
        Args:
            answer: Generated answer text
        
        Returns:
            float: Score from 0-1 indicating structure quality
        """
        structure_indicators = [
            "##",  # Headers
            "###",
            "**",  # Bold
            "-",   # Lists
            "1.",  # Numbered lists
            ":",   # Colons for sections
        ]
        
        structure_count = sum(answer.count(indicator) for indicator in structure_indicators)
        
        # More structure indicators = better structured
        score = min(1.0, structure_count / 20)
        
        logging.info(f"Structure score: {score:.2%} (structure indicators found: {structure_count})")
        return score
    
    @staticmethod
    def metric_relevance_to_context(answer: str, contexts: List[str]) -> float:
        """
        Check if answer is relevant to the contexts
        
        Args:
            answer: Generated answer text
            contexts: Retrieved context chunks
        
        Returns:
            float: Score from 0-1 indicating relevance
        """
        if not contexts:
            return 0.0
        
        # Extract key terms from contexts
        context_text = " ".join(contexts).lower()
        context_words = set(context_text.split())
        
        # Check how many context words appear in answer
        answer_lower = answer.lower()
        answer_words = set(answer_lower.split())
        
        overlap = len(context_words.intersection(answer_words))
        score = min(1.0, overlap / max(len(context_words), 1) * 0.5)  # Scale appropriately
        
        logging.info(f"Relevance to context score: {score:.2%} ({overlap} overlapping terms)")
        return score
    
    @staticmethod
    def compute_overall_quality_score(answer: str, contexts: List[str]) -> dict:
        """
        Compute overall quality score combining all metrics
        
        Args:
            answer: Generated answer text
            contexts: Retrieved context chunks
        
        Returns:
            dict: All metric scores and overall score
        """
        logging.info("-"*60)
        logging.info("COMPUTING CUSTOM QUALITY METRICS")
        logging.info("-"*60)
        
        scores = {
            "completeness": CustomMetrics.metric_completeness(answer),
            "actionability": CustomMetrics.metric_actionability(answer),
            "specificity": CustomMetrics.metric_specificity(answer, contexts),
            "structure": CustomMetrics.metric_structure(answer),
            "relevance": CustomMetrics.metric_relevance_to_context(answer, contexts)
        }
        
        # Compute weighted overall score
        weights = {
            "completeness": 0.2,
            "actionability": 0.25,
            "specificity": 0.2,
            "structure": 0.15,
            "relevance": 0.2
        }
        
        overall = sum(scores[metric] * weights[metric] for metric in scores)
        scores["overall_quality"] = round(overall, 4)
        
        logging.info(f"Overall Quality Score: {scores['overall_quality']:.2%}")
        logging.info("-"*60)
        
        return scores