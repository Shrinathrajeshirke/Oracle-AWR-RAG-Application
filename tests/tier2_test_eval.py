"""
Tier 2 Evaluation Script
Measures performance with advanced RAG techniques
Compare with baseline_evaluation_summary.md and evaluation_summary_tier1.md
"""

import sys
import os
import glob
import pandas as pd
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()

from core.vector_store import VectorStoreManager
from core.retriever import DocumentRetriever
from core.tier2_retriever import Tier2Retriever
from ingestor.processor import DocumentProcessor
from llm.factory import get_llm
from config.prompts import get_system_prompt
from evaluation.metrics import CustomMetrics
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.logger import logging


GOLDEN_DATA = {
    "question": [
        "What are the Database Name, Instance Name, and Elapsed Time for this AWR report?",
        "What was the total DB Time?",
        "What is the Redo size generated per second and per transaction?",
        "How many Logical Reads and Physical Reads occurred per second?",
        "What were the Buffer Cache Hit Ratio and Library Cache Hit Ratio?",
        "How many CPUs and Cores does the host system have?",
        "What were the top 3 foreground wait events by total wait time (excluding DB CPU)?",
        "What percentage of total DB time was spent on 'DB CPU'?",
        "Which Wait Class contributed the most to total wait time after DB CPU, and what was its percentage of DB time?",
        "Which SQL_ID had the highest Elapsed Time, and what was its total elapsed time?",
        "Identify the top SQL_ID by Buffer Gets. How many gets did it perform?",
        "How many executions were there for SQL_ID 0z318y6g3uagc, and what module did it belong to?"
    ],
    "ground_truth": [
        "Database Name: EBSCDB, Instance Name: ebscdb, Elapsed Time: 121.57 minutes",
        "The total DB Time is 1,942.31 mins.",
        "Redo size per second: 6004534.38 bytes, per transaction: 25131.51 bytes",
        "Logical Reads: 587,289.3 per second, Physical Reads: 8.6 per second",
        "Buffer Cache Hit Ratio: 100.00%, Library Cache Hit Ratio: 100.07%",
        "32 CPUs, 16 cores, 1 socket",
        "Buffer busy waits (13.4K sec), enq: TX - row lock contention (2196 sec), enq: TX - index contention (1819.7 sec)",
        "77.3% of total DB time was spent on DB CPU",
        "Concurrency wait class with 14.0% of DB time",
        "SQL_ID 4y08a52989vfk with 30,870.82 seconds elapsed time",
        "SQL_ID 4y08a52989vfk with 978,437,245 buffer gets",
        "200 executions, module: e:ONT:cp:inv/INCTCW"
    ]
}


def prepare_populated_vector_store() -> VectorStoreManager:
    """Ingests baseline AWR report into the in-memory Qdrant store."""
    data_dir = os.path.join(PROJECT_ROOT, "data")
    candidate_files = (
        glob.glob(os.path.join(data_dir, "*.html")) 
        + glob.glob(os.path.join(data_dir, "*.htm")) 
        + glob.glob(os.path.join(data_dir, "*.txt"))
    )
    if not candidate_files:
        raise FileNotFoundError(f"No AWR files found inside '{data_dir}/'")

    file_path = candidate_files[0]
    filename = os.path.basename(file_path)

    print(f"\n[Setup] Ingesting {filename} into VectorStoreManager...")
    processor = DocumentProcessor()
    chunks = processor.load_and_split_document(
        file_path=file_path, 
        doc_id="ebscdb_baseline_report", 
        filename=filename
    )

    vs_manager = VectorStoreManager()
    vs_manager.index_documents(chunks)
    print(f"[Setup] Ingestion complete. Indexed {len(chunks)} chunks into Qdrant.\n")
    return vs_manager


def get_tier2_responses(questions: list, vs_manager: VectorStoreManager) -> tuple:
    """Gets LLM answers using Tier 2 classification and cross-encoder re-ranking."""
    base_retriever = DocumentRetriever(vs_manager)
    tier2_retriever = Tier2Retriever(base_retriever)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing. Check your .env file.")

    llm = get_llm("openai", api_key, "gpt-3.5-turbo-0125")
    base_system_prompt = get_system_prompt(["all"], "Standard")

    answers = []
    contexts = []
    
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Tier 2 Processing: {q[:65]}...")
        
        # Step 1: Retrieve and Re-rank using Tier 2 Pipeline
        docs, retrieval_info = tier2_retriever.retrieve_and_rerank(
            q, 
            [], 
            use_classification=True
        )
        
        context_list = [doc.page_content for doc in docs]
        contexts.append(context_list)
        
        # Step 2: Dynamically customize system prompt per intent
        custom_system_prompt = tier2_retriever.get_system_prompt_for_query(q, base_system_prompt)
        prompt = ChatPromptTemplate.from_messages([
            ("system", custom_system_prompt + "\n\nContext:\n{context}"),
            ("user", "{question}")
        ])
        
        chain = prompt | llm | StrOutputParser()
        context_text = "\n---\n".join(context_list)
        answer = chain.invoke({"context": context_text, "question": q})
        answers.append(answer)
    
    return answers, contexts


def run_tier2_evaluation(export_reports=True) -> dict:
    logging.info("="*70)
    logging.info("TIER 2 EVALUATION STARTING")
    logging.info("="*70)
    
    vs_manager = prepare_populated_vector_store()
    answers, contexts = get_tier2_responses(GOLDEN_DATA["question"], vs_manager)
    
    logging.info("\nCalculating evaluation metrics...")
    results = []
    for idx, (question, answer, context_list, gt) in enumerate(
        zip(GOLDEN_DATA["question"], answers, contexts, GOLDEN_DATA["ground_truth"]), 
        1
    ):
        custom_scores = CustomMetrics.compute_overall_quality_score(answer, context_list)
        
        result = {
            "question_number": idx,
            "question": question,
            "ground_truth": gt,
            "answer": answer.replace("\r", " ").replace("\n", " ").strip(),
            "completeness": custom_scores.get("completeness", 0),
            "actionability": custom_scores.get("actionability", 0),
            "specificity": custom_scores.get("specificity", 0),
            "structure": custom_scores.get("structure", 0),
            "relevance": custom_scores.get("relevance", 0),
            "overall_quality": custom_scores.get("overall_quality", 0)
        }
        results.append(result)
    
    metrics_columns = ["completeness", "actionability", "specificity", "structure", "relevance", "overall_quality"]
    aggregate = {}
    for metric in metrics_columns:
        values = [r[metric] for r in results if isinstance(r[metric], (int, float))]
        aggregate[metric] = sum(values) / len(values) if values else 0.0
    
    if export_reports:
        df = pd.DataFrame(results)
        
        for m in metrics_columns:
            df[m] = df[m].round(4)
            
        csv_path = os.path.join(PROJECT_ROOT, "tier2_evaluation_results.csv")
        df.to_csv(csv_path, index=False)
        logging.info(f"Evaluation results saved to: {csv_path}")
        
        # Save Markdown Summary
        md_path = os.path.join(PROJECT_ROOT, "tier2_evaluation_summary.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Tier 2 Advanced RAG Evaluation Report\n\n")
            f.write("## Aggregate Summary\n\n")
            for m in metrics_columns:
                f.write(f"- **{m.replace('_', ' ').title()}:** `{aggregate.get(m, 0.0):.4f}`\n")
            f.write("\n## Per-Query Results\n\n")
            f.write("| # | Question | Quality | Completeness | Specificity | Answer Preview |\n")
            f.write("| :---: | :--- | :---: | :---: | :---: | :--- |\n")
            for _, row in df.iterrows():
                preview = row['answer'][:80] + "..." if len(row['answer']) > 80 else row['answer']
                f.write(f"| {row['question_number']} | {row['question']} | {row['overall_quality']:.4f} | {row['completeness']:.4f} | {row['specificity']:.4f} | {preview} |\n")
        
        logging.info(f"Summary markdown saved to: {md_path}")
    
    return aggregate


def print_evaluation_summary(scores: dict):
    print("\n" + "="*70)
    print("TIER 2 EVALUATION SUMMARY")
    print("="*70)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print("\nAggregate Metrics:")
    for metric, score in scores.items():
        print(f"  {metric.replace('_', ' ').title()}: {score:.4f}")
    print("\nBenchmark Comparison:")
    print("  - Baseline (Dense Only):   0.0802 Overall Quality")
    print("  - Tier 1 (Hybrid Search):  0.1025 Overall Quality")
    print("="*70)

if __name__ == "__main__":
    scores = run_tier2_evaluation(export_reports=True)
    print_evaluation_summary(scores)