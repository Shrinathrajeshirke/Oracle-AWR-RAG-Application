import os
import sys
import warnings
import glob
import pandas as pd

warnings.filterwarnings("ignore")

from dotenv import load_dotenv
load_dotenv()

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from ingestor.processor import DocumentProcessor
from ingestor.metadata_manager import MetadataManager
from core.vector_store import VectorStoreManager
from core.retriever import DocumentRetriever
from llm.factory import get_llm
from config.prompts import get_system_prompt
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# =====================================================================
# 1. GOLDEN DATASET (Baseline EBSCDB Snapshot 659-667)
# =====================================================================
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
        "The Database Name is EBSCDB, the Instance Name is ebscdb, and the Elapsed Time is 121.57 mins.",
        "The total DB Time is 1,942.31 mins.",
        "The Redo size generated is 6,004,534.4 bytes per second and 25,131.5 bytes per transaction.",
        "There were 587,289.3 logical reads per second and 8.6 physical reads per second.",
        "The Buffer Cache Hit Ratio was 100.00% and the Library Cache Hit Ratio was 100.07%.",
        "The host system (ebsdb1227) has 32 CPUs and 16 Cores.",
        "The top 3 foreground wait events were 1) buffer busy waits (13.4K sec), 2) enq: TX - row lock contention (2196 sec), and 3) enq: TX - index contention (1819.7 sec).",
        "DB CPU accounted for 77.3% of the total DB time.",
        "The Concurrency wait class contributed the most after DB CPU, accounting for 14.0% of the DB time.",
        "SQL_ID 4y08a52989vfk had the highest elapsed time at 30,870.82 seconds.",
        "SQL_ID 4y08a52989vfk performed the most buffer gets, totaling 978,437,245 gets.",
        "SQL_ID 0z318y6g3uagc had 200 executions and belongs to the module e:ONT:cp:inv/INCTCW."
    ]
}


# =====================================================================
# 2. IN-MEMORY SETUP & PIPELINE INVOCATION
# =====================================================================
def prepare_test_vector_store():
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
    doc_id = "ebscdb_baseline_report"

    print(f"\n[Setup] Ingesting {filename} into VectorStoreManager...")
    processor = DocumentProcessor()
    chunks = processor.load_and_split_document(
        file_path=file_path, 
        doc_id=doc_id, 
        filename=filename
    )

    vs_manager = VectorStoreManager()
    vs_manager.index_documents(chunks)

    meta_manager = MetadataManager()
    meta_manager.register_document(
        doc_id=doc_id,
        filename=filename,
        chunk_count=len(chunks),
        file_size=os.path.getsize(file_path)
    )
    print(f"[Setup] Ingestion complete. Indexed {len(chunks)} chunks.")
    return vs_manager


def get_pipeline_responses(questions: list, vs_manager: VectorStoreManager) -> tuple:
    retriever = DocumentRetriever(vs_manager)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is missing. Check your .env file.")

    llm = get_llm("openai", api_key, "gpt-3.5-turbo-0125")

    answers = []
    contexts = []

    system_prompt = get_system_prompt(["all"], "Standard")
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt + "\n\nContext:\n{context}"),
        ("user", "{question}")
    ])

    def format_docs(docs):
        return "\n---\n".join([doc.page_content for doc in docs])

    rag_chain = (
        {"context": retriever.get_unfiltered_retriever() | format_docs, "question": RunnablePassthrough()}
        | prompt 
        | llm
        | StrOutputParser()
    )

    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] Querying: {q[:70]}...")
        docs = retriever.retrieve_documents(q, [])
        contexts.append([doc.page_content for doc in docs])

        ans = rag_chain.invoke(q)
        answers.append(ans)

    return answers, contexts


# =====================================================================
# 3. BASELINE EVALUATION & FORMATTED EXPORT
# =====================================================================
def save_readable_reports(custom_scores_list: list, mean_scores: dict):
    """Saves both a clean CSV and a Markdown summary file."""
    df = pd.DataFrame(custom_scores_list)

    # Reorder columns for readability
    ordered_cols = [
        "question",
        "overall_quality",
        "completeness",
        "specificity",
        "structure",
        "actionability",
        "relevance",
        "answer"
    ]
    df = df[[c for c in ordered_cols if c in df.columns]]

    # 1. Save Clean CSV (replace multi-line breaks so Excel doesn't scramble rows)
    df_clean = df.copy()
    df_clean["answer"] = df_clean["answer"].apply(lambda x: str(x).replace("\r", " ").replace("\n", " ").strip())
    
    # Round numerical metrics to 4 decimals
    numeric_cols = ["overall_quality", "completeness", "specificity", "structure", "actionability", "relevance"]
    for col in numeric_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].round(4)

    csv_path = os.path.join(PROJECT_ROOT, "baseline_evaluation_scores.csv")
    df_clean.to_csv(csv_path, index=False)
    print(f"\n[Saved] Clean CSV report: {csv_path}")

    # 2. Save Markdown Table Report
    md_path = os.path.join(PROJECT_ROOT, "baseline_evaluation_summary.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# AWR RAG Baseline Evaluation Report\n\n")
        f.write("## Aggregate Summary\n\n")
        f.write(f"- **Overall Quality:** `{mean_scores.get('overall_quality', 0.0):.4f}`\n")
        f.write(f"- **Completeness:** `{mean_scores.get('completeness', 0.0):.4f}`\n")
        f.write(f"- **Specificity:** `{mean_scores.get('specificity', 0.0):.4f}`\n")
        f.write(f"- **Structure:** `{mean_scores.get('structure', 0.0):.4f}`\n")
        f.write(f"- **Actionability:** `{mean_scores.get('actionability', 0.0):.4f}`\n")
        f.write(f"- **Relevance:** `{mean_scores.get('relevance', 0.0):.4f}`\n\n")
        
        f.write("## Per-Query Results\n\n")
        f.write("| # | Question | Quality | Completeness | Specificity | Answer Preview |\n")
        f.write("| :---: | :--- | :---: | :---: | :---: | :--- |\n")
        
        for idx, row in df_clean.iterrows():
            preview = row['answer'][:80] + "..." if len(row['answer']) > 80 else row['answer']
            f.write(
                f"| {idx + 1} | {row['question']} | {row['overall_quality']:.4f} | "
                f"{row['completeness']:.4f} | {row['specificity']:.4f} | {preview} |\n"
            )

    print(f"[Saved] Markdown summary: {md_path}")


def run_baseline_evaluation(export_reports=True) -> dict:
    from evaluation.metrics import CustomMetrics

    vs_manager = prepare_test_vector_store()
    print("\nRunning test queries against the pipeline...")
    answers, contexts = get_pipeline_responses(GOLDEN_DATA["question"], vs_manager)

    print("\nCalculating Custom Evaluation metrics...")
    custom_scores_list = []
    for q, ans, context_list in zip(GOLDEN_DATA["question"], answers, contexts):
        scores = CustomMetrics.compute_overall_quality_score(ans, context_list)
        scores["question"] = q
        scores["answer"] = ans
        custom_scores_list.append(scores)

    metrics_names = ["completeness", "actionability", "specificity", "structure", "relevance", "overall_quality"]
    mean_scores = {}

    for metric in metrics_names:
        values = [s.get(metric, 0) for s in custom_scores_list if isinstance(s.get(metric), (int, float))]
        mean_scores[metric] = sum(values) / len(values) if values else 0.0

    if export_reports:
        save_readable_reports(custom_scores_list, mean_scores)

    return mean_scores


# =====================================================================
# 4. PYTEST HOOK & STANDALONE EXECUTION
# =====================================================================
@pytest.mark.evaluation
def test_rag_baseline_metrics():
    scores = run_baseline_evaluation(export_reports=True)
    print("\n--- Baseline Scores ---")
    for metric, score in scores.items():
        print(f"{metric.replace('_', ' ').title()}: {score:.4f}")

    assert scores.get("overall_quality", 0.0) > 0.0, "Evaluation failed"


if __name__ == "__main__":
    scores = run_baseline_evaluation(export_reports=True)
    print("\n--- Final Aggregate Baseline Scores ---")
    for metric, score in scores.items():
        print(f"{metric.replace('_', ' ').title()}: {score:.4f}")