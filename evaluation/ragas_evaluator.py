"""
RAGAS evaluation framework integration
Evaluates RAG response quality with multiple metrics
"""

import sys
from datetime import datetime
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from datasets import Dataset
from config.settings import RAGAS_METRICS
from utils.logger import logging
from utils.ragas_logger import ragas_logger
from utils.exception import CustomException


class RAGASEvaluator:
    """
    Handles RAGAS evaluation of RAG responses
    Evaluates faithfulness, answer relevancy, context precision and recall
    """
    
    def __init__(self):
        """Initialize RAGAS evaluator"""
        self.evaluation_results = []
        logging.info("RAGASEvaluator initialized")
    
    def evaluate_response(self, question: str, answer: str, contexts: list,
                         ground_truth: str = None, llm=None) -> dict:
        """
        Evaluate a RAG response using RAGAS metrics
        
        Args:
            question: User's question
            answer: Generated answer
            contexts: List of retrieved context chunks
            ground_truth: Optional ground truth answer for additional metrics
            llm: LangChain LLM instance for evaluation
        
        Returns:
            dict: RAGAS evaluation scores
        """
        logging.info("="*70)
        logging.info("STARTING RAGAS EVALUATION")
        logging.info(f"Question: {question[:100]}...")
        logging.info(f"Answer length: {len(answer)} characters")
        logging.info(f"Contexts retrieved: {len(contexts)}")
        
        try:
            if not question or not answer or not contexts:
                logging.error("Missing required evaluation data")
                return {"error": "Missing question, answer, or contexts"}
            
            # Prepare data for RAGAS
            logging.info("Preparing data for RAGAS evaluation...")
            data = {
                "question": [question],
                "answer": [answer],
                "contexts": [contexts]
            }
            
            if ground_truth:
                data["ground_truth"] = [ground_truth]
                logging.info("Ground truth provided - will include precision/recall metrics")
            
            dataset = Dataset.from_dict(data)
            dataset = dataset.flatten()
            
            # Select metrics based on available data
            metrics = [
                faithfulness,
                answer_relevancy
            ]
            
            if ground_truth:
                metrics.extend([context_precision, context_recall])
                logging.info("Using 4 metrics: faithfulness, answer_relevancy, context_precision, context_recall")
            else:
                logging.info("Using 2 metrics: faithfulness, answer_relevancy")
            
            # Check LLM
            if not llm:
                logging.error("No LLM provided for RAGAS evaluation")
                return {"error": "LLM instance required for RAGAS evaluation"}
            
            # Run RAGAS evaluation
            logging.info("Running RAGAS evaluation...")
            from ragas.llms import LangchainLLMWrapper
            
            result = evaluate(
                dataset,
                metrics=metrics,
                llm=LangchainLLMWrapper(llm),
            )
            
            # Convert to dict and round scores
            logging.info("Converting results...")
            scores = result.to_pandas().iloc[0].to_dict()
            scores_out = {k: round(v, 4) for k, v in scores.items() if isinstance(v, (int, float))}
            
            logging.info("="*70)
            logging.info("RAGAS EVALUATION COMPLETED")
            logging.info(f"Scores: {scores_out}")
            logging.info("="*70)
            
            # Log to RAGAS-specific logger
            self._log_results(question, answer, contexts, scores_out, ground_truth)
            
            # Store in memory
            self.evaluation_results.append({
                "timestamp": datetime.now().isoformat(),
                "question": question,
                "answer_length": len(answer),
                "context_count": len(contexts),
                "scores": scores_out
            })
            
            return scores_out
            
        except Exception as e:
            logging.error(f"RAGAS evaluation failed: {e}", exc_info=True)
            logging.info("="*70)
            ragas_logger.error(f"Evaluation failed: {e}")
            raise CustomException(e, sys)
    
    def _log_results(self, question: str, answer: str, contexts: list, 
                     scores: dict, ground_truth: str = None):
        """Log evaluation results to RAGAS logger"""
        try:
            ragas_logger.info("="*70)
            ragas_logger.info(f"Question: {question[:150]}...")
            ragas_logger.info(f"Answer length: {len(answer)} characters")
            ragas_logger.info(f"Contexts retrieved: {len(contexts)}")
            ragas_logger.info(f"Ground truth: {bool(ground_truth)}")
            ragas_logger.info("")
            ragas_logger.info("SCORES:")
            for metric, score in scores.items():
                ragas_logger.info(f"  {metric}: {score}")
            ragas_logger.info(f"Timestamp: {datetime.now().isoformat()}")
            ragas_logger.info("="*70)
        except Exception as e:
            logging.error(f"Error logging RAGAS results: {e}")
    
    def get_evaluation_summary(self) -> dict:
        """
        Get summary of all evaluation results
        
        Returns:
            dict: Summary statistics and all evaluation results
        """
        if not self.evaluation_results:
            return {"message": "No evaluations run yet"}
        
        # Calculate average scores
        all_scores = {}
        for result in self.evaluation_results:
            if not isinstance(result, dict):
                continue
            
            scores = result.get("scores", {})
            if not isinstance(scores, dict):
                continue
            
            for metric, score in scores.items():
                if metric != "error" and isinstance(score, (int, float)):
                    if metric not in all_scores:
                        all_scores[metric] = []
                    all_scores[metric].append(score)
        
        avg_scores = {
            metric: round(sum(scores) / len(scores), 4)
            for metric, scores in all_scores.items()
            if len(scores) > 0
        }
        
        return {
            "total_evaluations": len(self.evaluation_results),
            "average_scores": avg_scores,
            "all_results": self.evaluation_results
        }
    
    def get_metric_statistics(self, metric_name: str) -> dict:
        """
        Get detailed statistics for a specific metric
        
        Args:
            metric_name: Name of the metric (e.g., 'faithfulness')
        
        Returns:
            dict: Statistics including min, max, mean, count
        """
        if not self.evaluation_results:
            return {}
        
        scores = []
        for result in self.evaluation_results:
            if isinstance(result.get("scores"), dict):
                score = result["scores"].get(metric_name)
                if isinstance(score, (int, float)):
                    scores.append(score)
        
        if not scores:
            return {}
        
        return {
            "metric": metric_name,
            "count": len(scores),
            "min": round(min(scores), 4),
            "max": round(max(scores), 4),
            "mean": round(sum(scores) / len(scores), 4),
            "all_scores": scores
        }
    
    def clear_results(self):
        """Clear all stored evaluation results"""
        logging.info("Clearing evaluation results")
        self.evaluation_results = []