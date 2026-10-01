"""
Oracle AWR RAG - LLM-as-a-Judge Evaluation Harness with Tier Selection
Evaluates Faithfulness, Context Relevance, and Ground Truth Accuracy
Supports: baseline, tier1, tier2
"""

import os
import sys
import json
import time
import argparse
from typing import List, Dict, Any, Tuple
from datetime import datetime
from pydantic import BaseModel, Field

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from core.vector_store import VectorStoreManager
from core.retriever import DocumentRetriever
from core.tier2_retriever import Tier2Retriever
from ingestor.processor import DocumentProcessor
from llm.factory import get_llm
from config.prompts import get_system_prompt
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.logger import logging
import glob

# =====================================================================
# EVALUATION SCHEMA
# =====================================================================
class AwrEvaluationMetrics(BaseModel):
    faithfulness_score: float = Field(
        ..., ge=0.0, le=1.0, 
        description="1.0 if all claims are directly supported by context; lower if hallucinated."
    )
    faithfulness_reasoning: str = Field(
        ..., description="Brief explanation citing what was supported or unsupported."
    )
    context_relevance_score: float = Field(
        ..., ge=0.0, le=1.0, 
        description="1.0 if context contains the exact required table/metric; 0.0 if irrelevant."
    )
    context_relevance_reasoning: str = Field(
        ..., description="Brief explanation of whether the context had the target metric."
    )
    answer_correctness_score: float = Field(
        ..., ge=0.0, le=1.0, 
        description="1.0 if answer matches ground truth numbers and IDs; 0.0 if wrong."
    )
    answer_correctness_reasoning: str = Field(
        ..., description="Brief explanation of correctness relative to ground truth."
    )

# =====================================================================
# ACCURATE GOLDEN DATASET (MATCHED TO EBSCDB AWR REPORT)
# =====================================================================
GOLDEN_SCENARIOS = [
    {
        "question": "What are the Database Name, Instance Name, and Elapsed Time for this AWR report?",
        "ground_truth": "Database Name: EBSCDB, Instance Name: ebscdb, Elapsed Time: 121.57 minutes"
    },
    {
        "question": "What was the total DB Time?",
        "ground_truth": "The total DB Time is 1,942.31 minutes (or ~116,538 seconds)."
    },
    {
        "question": "What is the Redo size generated per second and per transaction?",
        "ground_truth": "Redo size per second: 6,004,534.38 bytes, per transaction: 25,131.51 bytes"
    },
    {
        "question": "How many Logical Reads and Physical Reads occurred per second?",
        "ground_truth": "Logical Reads: 587,289.3 per second, Physical Reads: 8.6 per second"
    },
    {
        "question": "What were the Buffer Cache Hit Ratio and Library Cache Hit Ratio?",
        "ground_truth": "Buffer Cache Hit Ratio: 100.00%, Library Cache Hit Ratio: 100.07%"
    },
    {
        "question": "How many CPUs and Cores does the host system have?",
        "ground_truth": "32 CPUs, 16 cores, 1 socket"
    },
    {
        "question": "What were the top 3 foreground wait events by total wait time (excluding DB CPU)?",
        "ground_truth": "buffer busy waits (13.4K sec), enq: TX - row lock contention (2196 sec), enq: TX - index contention (1819.7 sec)"
    },
    {
        "question": "What percentage of total DB time was spent on 'DB CPU'?",
        "ground_truth": "77.3% of total DB time was spent on DB CPU"
    },
    {
        "question": "Which Wait Class contributed the most to total wait time after DB CPU, and what was its percentage of DB time?",
        "ground_truth": "Concurrency wait class with 14.04% of DB time"
    },
    {
        "question": "Which SQL_ID had the highest Elapsed Time, and what was its total elapsed time?",
        "ground_truth": "SQL_ID 4y08a52989vfk with 30,870.82 seconds elapsed time"
    },
    {
        "question": "Identify the top SQL_ID by Buffer Gets. How many gets did it perform?",
        "ground_truth": "SQL_ID 4y08a52989vfk with 978,437,245 buffer gets"
    },
    {
        "question": "How many executions were there for SQL_ID 0z318y6g3uagc, and what module did it belong to?",
        "ground_truth": "200 executions, module: e:ONT:cp:inv/INCTCW"
    }
]

# =====================================================================
# LLM JUDGE PROMPT
# =====================================================================
JUDGE_PROMPT = """You are an expert Oracle DBA evaluating the quality of an AWR report analysis system.

QUESTION: {question}

GROUND TRUTH (reference answer): {ground_truth}

RETRIEVED CONTEXT (what the system had available): {context}

SYSTEM ANSWER (what the system generated): {answer}

Evaluate this answer on three dimensions:

1. FAITHFULNESS (0-1): Are all claims in the answer directly supported by the retrieved context? 
   - 1.0 = All claims are directly backed by context, no hallucinations
   - 0.5 = Some claims supported, some unsupported
   - 0.0 = Claims contradict context or are completely unsupported

2. CONTEXT RELEVANCE (0-1): Does the retrieved context contain the information needed to answer the question?
   - 1.0 = Context has the exact metric/value needed
   - 0.5 = Context has partial information
   - 0.0 = Context is irrelevant to the question

3. ANSWER CORRECTNESS (0-1): Does the answer match the ground truth?
   - 1.0 = Answer matches ground truth numbers and names accurately
   - 0.5 = Answer is partially correct
   - 0.0 = Answer is wrong or contradicts ground truth

Provide structured evaluation with scores and brief reasoning for each dimension."""

# =====================================================================
# SETUP PIPELINE
# =====================================================================
def setup_pipeline(tier: str = "tier2") -> Tuple[Any, Any, Any]:
    logging.info(f"Setting up pipeline for tier: {tier}")
    
    data_files = glob.glob(os.path.join(PROJECT_ROOT, "data", "*.html"))
    if not data_files:
        raise FileNotFoundError("No AWR html reports found in data/")
    
    file_path = data_files[0]
    doc_id = "ebscdb_baseline_report"
    
    processor = DocumentProcessor()
    chunks = processor.load_and_split_document(file_path, doc_id, os.path.basename(file_path))
    
    vs_manager = VectorStoreManager()
    vs_manager.index_documents(chunks)
    
    base_retriever = DocumentRetriever(vs_manager)
    tier2_retriever = Tier2Retriever(base_retriever)
    
    llm = get_llm("openai", os.getenv("OPENAI_API_KEY"), "gpt-3.5-turbo-0125")
    return tier2_retriever, base_retriever, llm

# =====================================================================
# RETRIEVAL BY TIER
# =====================================================================
def retrieve_by_tier(question: str, tier: str, tier2_retriever: Tier2Retriever, base_retriever: DocumentRetriever) -> List:
    if tier == "tier2":
        docs, _ = tier2_retriever.retrieve_and_rerank(question, [], use_classification=True)
        return docs
    elif tier == "tier1":
        return base_retriever.retrieve_hybrid(question, [], k=6)
    else:  # baseline
        return base_retriever.retrieve_documents(question, [], k=6)

# =====================================================================
# LLM JUDGE EVALUATION
# =====================================================================
def run_llm_judge(question: str, ground_truth: str, context: str, answer: str) -> AwrEvaluationMetrics:
    judge_llm = ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="gpt-4o",
        temperature=0.0
    )
    structured_judge = judge_llm.with_structured_output(AwrEvaluationMetrics)
    prompt = JUDGE_PROMPT.format(
        question=question,
        ground_truth=ground_truth,
        context=context,
        answer=answer
    )
    return structured_judge.invoke(prompt)

# =====================================================================
# BENCHMARK RUNNER
# =====================================================================
def run_benchmark(tier: str = "tier2"):
    print(f"\n{'='*80}")
    print(f"  TIER {tier.upper()} - LLM-AS-A-JUDGE EVALUATION ({len(GOLDEN_SCENARIOS)} Questions)")
    print(f"{'='*80}\n")
    
    tier2_retriever, base_retriever, llm = setup_pipeline(tier)
    base_prompt = get_system_prompt(["all"], "Standard")
    
    results = []
    
    for idx, scenario in enumerate(GOLDEN_SCENARIOS, 1):
        question = scenario["question"]
        ground_truth = scenario["ground_truth"]
        
        try:
            t_start = time.time()
            
            # 1. Retrieve Context
            docs = retrieve_by_tier(question, tier, tier2_retriever, base_retriever)
            context_list = [doc.page_content for doc in docs]
            context_str = "\n---\n".join(context_list)
            
            # 2. Generate Real LLM Answer
            if tier == "tier2":
                system_prompt = tier2_retriever.get_system_prompt_for_query(question, base_prompt)
            else:
                system_prompt = base_prompt
                
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt + "\n\nRetrieved Context:\n{context}"),
                ("user", "{question}")
            ])
            chain = prompt | llm | StrOutputParser()
            answer = chain.invoke({"context": context_str, "question": question})
            
            # 3. Judge Response
            eval_result = run_llm_judge(question, ground_truth, context_str, answer)
            t_elapsed = time.time() - t_start
            
            result_dict = {
                "question_num": idx,
                "question": question,
                "ground_truth": ground_truth,
                "generated_answer": answer,
                "faithfulness_score": eval_result.faithfulness_score,
                "faithfulness_reasoning": eval_result.faithfulness_reasoning,
                "context_relevance_score": eval_result.context_relevance_score,
                "context_relevance_reasoning": eval_result.context_relevance_reasoning,
                "answer_correctness_score": eval_result.answer_correctness_score,
                "answer_correctness_reasoning": eval_result.answer_correctness_reasoning,
                "retrieval_time_sec": round(t_elapsed, 2)
            }
            results.append(result_dict)
            
            print(f"Q{idx}: {question[:60]}...")
            print(f"  Faithfulness: {eval_result.faithfulness_score:.2f} | "
                  f"Relevance: {eval_result.context_relevance_score:.2f} | "
                  f"Correctness: {eval_result.answer_correctness_score:.2f}")
            print(f"  Answer: {answer[:90].replace(chr(10), ' ')}...\n")
        
        except Exception as e:
            logging.error(f"Error evaluating Q{idx}: {e}")
            print(f"Q{idx}: ERROR - {e}\n")
    
    if results:
        avg_faithfulness = sum(r["faithfulness_score"] for r in results) / len(results)
        avg_relevance = sum(r["context_relevance_score"] for r in results) / len(results)
        avg_correctness = sum(r["answer_correctness_score"] for r in results) / len(results)
        
        summary = {
            "tier": tier,
            "timestamp": datetime.now().isoformat(),
            "total_questions": len(results),
            "metrics": {
                "avg_faithfulness": round(avg_faithfulness, 4),
                "avg_context_relevance": round(avg_relevance, 4),
                "avg_answer_correctness": round(avg_correctness, 4),
                "overall_score": round((avg_faithfulness + avg_relevance + avg_correctness) / 3, 4)
            },
            "detailed_results": results
        }
    else:
        summary = {"error": "No results generated", "tier": tier}
    
    output_file = f"llm_judge_evaluation_{tier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n{'='*80}")
    print(f"  TIER {tier.upper()} - BENCHMARK SUMMARY")
    print(f"{'='*80}")
    if "metrics" in summary:
        print(f"Avg Faithfulness:       {summary['metrics']['avg_faithfulness']:.4f}")
        print(f"Avg Context Relevance:  {summary['metrics']['avg_context_relevance']:.4f}")
        print(f"Avg Answer Correctness: {summary['metrics']['avg_answer_correctness']:.4f}")
        print(f"Overall Score:          {summary['metrics']['overall_score']:.4f}")
    print(f"{'='*80}\n")
    
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate AWR RAG with specified tier")
    parser.add_argument(
        "tier",
        nargs="?",
        default="tier2",
        choices=["baseline", "tier1", "tier2"],
        help="Which tier to evaluate (default: tier2)"
    )
    args = parser.parse_args()
    run_benchmark(args.tier)