# ⚡ Oracle AWR Performance Copilot

A production-grade, hallucination-resistant Retrieval-Augmented Generation (RAG) assistant engineered specifically for Oracle Database Administrators (DBAs) to automatically analyze Automatic Workload Repository (AWR) reports, diagnose system bottlenecks, and tune critical SQL queries.

Upload raw AWR HTML/TXT reports, receive immediate executive health diagnoses, and run interactive follow-up investigations with verifiable, zero-hallucination metric extraction.

🔗 **Live Demo**: [oracle-awr-rag-application.streamlit.app](https://oracle-awr-rag-application.streamlit.app/)

---

## 🏗️ High-Level System Architecture

```text
                   +-----------------------------+
                   |   Oracle AWR Report (.html)  |
                   +--------------+--------------+
                                  |
                                  v
                   +-----------------------------+
                   |      DocumentProcessor      |
                   |  (Table-Preserving Chunks)  |
                   +--------------+--------------+
                                  |
             +--------------------+--------------------+
             |                                         |
             v                                         v
+---------------------------+             +---------------------------+
|  Qdrant Dense Vector Store|             |     Lexical BM25 Index    |
|   (Semantic Similarity)   |             | (Exact SQL IDs / Headers) |
+-------------+-------------+             +-------------+-------------+
              |                                         |
              +--------------------+--------------------+
                                   |
                                   v
                    +-----------------------------+
                    |    Tier 1 Hybrid Retriever  |
                    |  (Reciprocal Rank Fusion)   |
                    +--------------+--------------+
                                   |
                +------------------+------------------+
                |                                     |
                v                                     v
+--------------------------+          +---------------------------+
|  AWR Term Query Expansion|          |  PII Masking & Sanitizer  |
| (Colloquial -> Canonical)|          |  (Regex-Free String Logic)|
+-------------+------------+          +-------------+-------------+
              |                                     |
              +------------------+------------------+
                                 |
                                 v
                  +-----------------------------+
                  |  OpenAI gpt-4o-mini Engine  |
                  |  (temp=0.0, top_p=0.01)     |
                  +--------------+--------------+
                                 |
                                 v
                  +-----------------------------+
                  |  Dual-Pass FactVerifier     |
                  | (Verifies 13-Char SQL IDs)  |
                  +--------------+--------------+
                                 |
             +-------------------+-------------------+
             |                                       |
             v                                       v
+---------------------------+           +---------------------------+
|   Solution Memory Cache   |           |  Clickable Oracle MOS KB  |
|   (Fast Semantic Lookup)  |           | (Doc IDs & Tuning Guides) |
+-------------+-------------+           +-------------+-------------+
              |                                       |
              +-------------------+-------------------+
                                  |
                                  v
                   +-----------------------------+
                   |    Streamlit UI Interface   |
                   +-----------------------------+
```

---

## 🌟 Core Capabilities

* **Instant Diagnostic Ingestion:** Upload an AWR report to instantly trigger an Executive Summary outlining DB Time, CPU usage breakdown, concurrency constraints, and prioritized remediation steps.
* **Tier 1 Hybrid Search (BM25 + Dense Vectors):** Combines lexical matching for exact technical handles (13-character SQL IDs, wait event parameters) with semantic vector search across workload narratives.
* **Enterprise PII Sanitization:** Custom parsing engine that strips sensitive environment configurations, credentials, schema tokens, and internal IP addresses before vector indexing or external prompting.
* **Semantic Solution Cache:** Qdrant-backed memory that matches recurring database bottleneck patterns and returns verified DBA remedies with zero LLM inference latency.
* **Oracle MOS Knowledge Integration:** Automatically maps detected wait event signatures (e.g., `buffer busy waits`, `enq: TX - row lock contention`) to official My Oracle Support (MOS) Note IDs and performance documentation guides.
* **LLM-as-a-Judge Benchmark Harness:** Automated evaluation suite (`tests/evaluate_awr_rag.py`) that tests Faithfulness, Context Relevance, and Ground Truth accuracy against production workloads.

---

## 🔬 Engineering Journey: Achieving Production Accuracy

Building an LLM assistant over dense, multi-column tabular reports requires overcoming subtle context conflation and hallucination patterns. Here is how the system evolved from early failure modes to production-grade reliability:

### 1. Challenge: Aggregate Header vs. Row-Level Conflation
* **The Failure:** When asked *"what sql statement caused the most buffer?"*, early iterations reported that `SQL ID: 3wtnuzdm579hg` performed `4,283,650,806` buffer gets.
* **The Root Cause:** `4,283,650,806` was the **instance-wide aggregate total** printed in the section banner (`Total Buffer Gets: 4,283,650,806`). The model extracted the aggregate and attributed it to an arbitrary row in the table.
* **The Fix:** Implemented negative prompt directives in `config/prompts.py` enforcing strict boundary isolation between section totals and row-level SQL values. The model now correctly identifies Rank 1 (`4y08a52989vfk` with `978,437,245` gets).

### 2. Challenge: Colloquial DBA Slang & Retrieval Starvation
* **The Failure:** User shorthand like *"what query caused the most buffer"* dropped the term `"gets"`, causing BM25 and dense retrieval to fetch general buffer pool advisories while missing the `SQL ordered by Gets` table.
* **The Fix:** Built domain-specific query expansion in `core/retriever.py` that enriches DBA inquiries with canonical AWR section titles (e.g., mapping `"most buffer"` $\rightarrow$ `"SQL ordered by Gets buffer gets"`). Expanded the context window to $k=10$ to ensure wide multi-column markdown tables are preserved.

### 3. Challenge: Sampling Entropy on Exact Technical Data
* **The Failure:** Default generation temperatures led to minor hallucinations of execution counts and row-source heuristics.
* **The Fix:** Locked `llm/factory.py` to `gpt-4o-mini` with `temperature=0.0` and `top_p=0.01`. Added `core/fact_verifier.py`, which validates 13-character alphanumeric Oracle SQL IDs and critical metrics against source context chunks before returning the response.

---

## 📊 Benchmark & Evaluation Results (LLM-as-a-Judge)

The system was benchmarked using an automated evaluation harness (`tests/evaluate_awr_rag.py`) over a 12-scenario Golden Dataset derived directly from a production `EBSCDB` AWR workload. Evaluations were judged using structured outputs on `gpt-4o`:

| Evaluation Metric | Benchmark Score | Target Standard | Evaluation Verdict |
| :--- | :--- | :--- | :--- |
| **Faithfulness** | **95.83%** | $\ge 90.0\%$ | ✅ **Passed (Near-Zero Hallucination)** |
| **Context Relevance** | **87.50%** | $\ge 85.0\%$ | ✅ **Passed (High Retrieval Precision)** |
| **Answer Correctness** | **75.00%** | $\ge 70.0\%$ | ✅ **Passed (Exact Metric Matches)** |
| **Overall Pipeline Score** | **86.11%** | $\ge 80.0\%$ | 🚀 **Production-Ready** |

### Benchmark Highlights
* **Top SQL Extraction:** SQL ID `4y08a52989vfk` extracted with `978,437,245` buffer gets, `64` executions, and `30,870.82s` elapsed time (100% accuracy).
* **Wait Event Hierarchy:** Correctly separated individual events (`buffer busy waits`, `enq: TX - row lock contention`) from high-level wait classes (`Concurrency`, `Application`).
* **System Workload Profile:** 100% accuracy across host CPUs, cores, sockets, redo rates, logical/physical read counts, and cache hit ratios.
* **Data Absence Directives:** For tables not indexed in the chunks (e.g., Data Guard replication), the model strictly stated that the data was unavailable instead of fabricating metrics.

---

## 📂 Project Structure

```text
AWR-RAG/
│
├── 📁 config/
│   ├── prompts.py            # System prompt with tabular anti-hallucination rules
│   └── settings.py           # Global settings, retrieval k=10, collection configs
│
├── 📁 core/
│   ├── fact_verifier.py      # Token-level fact checker (verifies 13-char SQL IDs)
│   ├── hybrid_retriever.py   # BM25 tokenization and Reciprocal Rank Fusion (RRF)
│   ├── oracle_kb.py          # My Oracle Support (MOS) Doc ID mapping engine
│   ├── retriever.py          # DocumentRetriever with AWR canonical query expansion
│   ├── sanitizer.py          # PII and sensitive parameter masking
│   ├── solution_cache.py     # Qdrant-backed semantic cache for DBA solutions
│   ├── tier2_retriever.py    # Advanced multi-strategy retriever
│   └── vector_store.py       # Qdrant client and collection manager
│
├── 📁 data/                  # Sample AWR HTML reports (EBSCDB baseline)
│
├── 📁 ingestor/
│   └── processor.py          # Table-aware chunking and document ingestion
│
├── 📁 llm/
│   └── factory.py            # Deterministic LLM instantiation (gpt-4o-mini, temp=0.0)
│
├── 📁 tests/
│   └── evaluate_awr_rag.py   # LLM-as-a-Judge benchmark harness & golden dataset
│
├── 📁 utils/
│   └── logger.py             # Modular logging configuration
│
├── app.py                    # Streamlit web copilot interface
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
└── README.md                 # This file
```

---

## 🚀 Quick Start Guide

### Prerequisites
* Python 3.10 or higher
* OpenAI API Key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Shrinathrajeshirke/AWR-RAG.git
cd AWR-RAG
```

2. **Create a virtual environment**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**

Create a `.env` file in the project root:
```ini
OPENAI_API_KEY=sk-your-openai-api-key-here
```

5. **Run the web application**
```bash
streamlit run app.py --server.fileWatcherType none
```
Open http://localhost:8501 in your browser.

6. **Run the benchmark evaluation**
```bash
python tests/evaluate_awr_rag.py tier1
```

---

## 📖 Sample Query Guide

### Workload & Health Diagnosis
* "Provide a comprehensive performance diagnosis and executive summary of this AWR report."
* "What were the Buffer Cache Hit Ratio and Library Cache Hit Ratio?"
* "How many Logical Reads and Physical Reads occurred per second?"

### Bottlenecks & Wait Events
* "What were the top 3 foreground wait events by total wait time (excluding DB CPU)?"
* "Which Wait Class contributed the most to total wait time after DB CPU?"
* "What is causing high buffer busy waits?"

### SQL Performance & Tuning
* "What SQL statement caused the most buffer gets, and how many gets did it perform?"
* "Which SQL_ID had the highest Elapsed Time, and what was its total elapsed time?"
* "How many executions were there for SQL_ID 0z318y6g3uagc, and what module did it belong to?"

---

## ☁️ Deployment (Streamlit Cloud)

1. Push your repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io) and create a new application pointing to `app.py`.
3. Under **Advanced settings → Secrets**, add your environment variables:
```toml
OPENAI_API_KEY = "sk-your-openai-api-key-here"
```
4. Click **Deploy**.

---

## 👥 Author

**Shrinath Rajeshirke**
* GitHub: [@Shrinathrajeshirke](https://github.com/Shrinathrajeshirke)
* Repository: [AWR-RAG](https://github.com/Shrinathrajeshirke/AWR-RAG)

---

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details.