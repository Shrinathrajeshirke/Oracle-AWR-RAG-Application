# 📊 Oracle AWR RAG Application

A production-grade Retrieval-Augmented Generation (RAG) system designed specifically for Oracle Database Administrators to analyze AWR (Automatic Workload Repository) reports using advanced AI models. Upload multiple AWR reports, ask questions in natural language, and receive intelligent insights with actionable recommendations.

**Live Demo**: [https://oracle-awr-rag-application.streamlit.app/]

---

## 🌟 Key Features

### 🔍 Multi-Document Analysis
- Upload and index multiple AWR reports simultaneously
- Compare performance across different time periods
- Track trends and identify degradation patterns
- Cross-reference metrics from multiple databases

### 🤖 AI-Powered Insights
- **Three Analysis Styles**:
  - **Standard**: Balanced analysis with clear structure
  - **Detailed Step-by-Step**: Deep dive with reasoning at each step
  - **Issue-Focused**: Executive summary with prioritized issues
- Natural language query interface
- Root cause analysis with evidence-based reasoning
- Actionable recommendations with priority and effort estimates

### 🎯 Advanced RAG Capabilities
- Semantic search using vector embeddings (Qdrant)
- Context-aware retrieval with document filtering
- Support for multiple LLM providers:
  - **OpenAI**: GPT-4o, GPT-4-turbo, GPT-3.5-turbo
  - **Groq**: Llama-3.1-8b-instant (ultra-fast inference)
  - **HuggingFace**: Zephyr-7b, Mixtral-8x7B

### 📊 Quality Evaluation
- **RAGAS Metrics**: Faithfulness, Answer Relevancy, Context Precision, Context Recall
- **Custom Metrics**: Completeness, Actionability, Specificity, Structure, Relevance
- Automatic evaluation logging and tracking
- Quality score visualization on UI

### 📧 Report Generation & Distribution
- Export analysis in multiple formats:
  - **PDF**: Professional reports with formatting
  - **HTML**: Interactive web-based reports
  - **Text**: Plain text for easy sharing
- Email delivery with SMTP support
- Customizable report templates

### 🔐 Enterprise-Ready
- Secure API key management
- Environment variable support
- Comprehensive logging and debugging
- Collection statistics and monitoring
- Session state management

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11** or higher
- pip (Python package manager)
- Git

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

# macOS/Linux
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**

Create a `.env` file in the project root:

```env
# LLM API Keys (choose one or more)
OPENAI_API_KEY=sk-xxx-your-openai-key
GROQ_API_KEY=xxx-your-groq-key
HUGGINGFACE_API_KEY=xxx-your-huggingface-token

# RAGAS Evaluation (uses OpenAI)
RAGAS_OPENAI_KEY=sk-xxx-your-openai-key

# SMTP Configuration (for email reports)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# Vector Database (optional - default is in-memory)
QDRANT_LOCATION=:memory:

# Embedding Model (optional - default is all-MiniLM-L6-v2)
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
```

5. **Run the application**
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

---

## 📖 Usage Guide

### Step 1: Upload AWR Reports

1. Navigate to **"1️⃣ Upload & Index Documents"**
2. Click **"Upload AWR Reports"**
3. Select one or more AWR reports (PDF, TXT, DOCX, HTML)
4. Files are automatically indexed with:
   - Document chunking
   - Vector embedding generation
   - Qdrant collection storage
   - Metadata tracking

### Step 2: Configure Query Settings

1. **Select LLM Provider**: 
   - OpenAI (best quality)
   - Groq (fastest)
   - HuggingFace (open-source)

2. **Enter API Key**: Provide your API key for the selected provider
   - OpenAI: https://platform.openai.com/api-keys
   - Groq: https://console.groq.com/keys
   - HuggingFace: https://huggingface.co/settings/tokens

3. **Select Model**: Choose from available models
   - GPT-4o (recommended for complex analysis)
   - Llama-3.1-8b (fastest, good quality)

4. **Select Documents**: Choose which indexed documents to query

5. **Choose Analysis Style**:
   - **Standard**: Best for general queries
   - **Detailed Step-by-Step**: For learning and deep analysis
   - **Issue-Focused**: For executive summaries

### Step 3: Ask Questions

Example queries:

**Performance Analysis:**
```
"Analyze this AWR report and identify performance issues"
"What are the top 3 bottlenecks in this database?"
"Identify all metrics that are outside normal ranges"
```

**Wait Events:**
```
"What are the top wait events and how can we resolve them?"
"Explain the 'db file sequential read' wait event"
"Why is 'latch: shared pool' consuming so much time?"
```

**SQL Tuning:**
```
"Which SQL statements need optimization?"
"Analyze the top SQL by elapsed time"
"Are there any full table scans that should be avoided?"
```

**Comparison:**
```
"Compare the CPU usage between these two reports"
"What improved after the tuning changes?"
"Show me the performance trend over these time periods"
```

### Step 4: Review Results

- View AI-generated analysis with structured insights
- Check retrieved context count (relevant chunks found)
- Review evaluation scores (RAGAS metrics if enabled)
- View custom quality metrics
- Download or email reports in preferred format

---

## 🏗️ Project Structure

```
AWR-RAG/
│
├── 📁 config/
│   ├── __init__.py
│   ├── settings.py           # Configuration constants
│   └── prompts.py            # Analysis prompt templates
│
├── 📁 core/
│   ├── __init__.py
│   ├── embeddings.py         # Embedding model management
│   ├── vector_store.py       # Qdrant vector store wrapper
│   ├── retriever.py          # Document retrieval with filtering
│   └── rag_chain.py          # RAG pipeline orchestration
│
├── 📁 ingestor/
│   ├── __init__.py
│   ├── document_loader.py    # Document loading & chunking
│   ├── processor.py          # Document processing pipeline
│   └── metadata_manager.py   # Document metadata & tracking
│
├── 📁 llm/
│   ├── __init__.py
│   └── factory.py            # LLM provider factory
│
├── 📁 evaluation/
│   ├── __init__.py
│   ├── ragas_evaluator.py    # RAGAS evaluation framework
│   └── metrics.py            # Custom quality metrics
│
├── 📁 reporting/
│   ├── __init__.py
│   ├── generators/
│   │   ├── __init__.py
│   │   ├── text_generator.py
│   │   ├── html_generator.py
│   │   └── pdf_generator.py
│   ├── email_service.py      # Email delivery service
│   └── report_builder.py     # Report orchestration
│
├── 📁 ui/
│   ├── __init__.py
│   ├── session_manager.py    # Streamlit session management
│   └── components/
│       ├── __init__.py
│       ├── document_uploader.py
│       └── query_interface.py
│
├── 📁 utils/
│   ├── __init__.py
│   ├── logger.py             # Logging configuration
│   ├── ragas_logger.py       # RAGAS evaluation logging
│   └── exception.py          # Custom exception handling
│
├── 📁 temp_files/            # Temporary file storage (auto-created)
├── 📁 logs/                  # Application logs (auto-created)
│
├── app.py                    # Main application entry point
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this)
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

---

## ⚙️ Configuration

### Core Settings (`config/settings.py`)

```python
# Text Chunking
CHUNK_SIZE = 1000           # Characters per chunk
CHUNK_OVERLAP = 200         # Overlap between chunks

# Embeddings
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Vector Database
QDRANT_COLLECTION_NAME = "multi_doc_comparison_rag"
QDRANT_LOCATION = ":memory:"  # or file path for persistence

# LLM Models
MODEL_CHOICES = {
    "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo-0125"],
    "groq": ["llama-3.1-8b-instant"],
    "huggingface": ["HuggingFaceH4/zephyr-7b-beta", "mistralai/Mixtral-8x7B-Instruct-v0.1"]
}

# RAGAS Metrics
RAGAS_METRICS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
```

### Analysis Styles (`config/prompts.py`)

Three pre-built prompt templates for different analysis approaches:

1. **Standard** - Balanced analysis with clear structure
2. **Detailed Step-by-Step** - Deep dive with step-by-step reasoning
3. **Issue-Focused** - Executive summary with prioritized issues

---

## 🔧 Architecture Overview

### Data Flow

```
1. Document Upload
   ↓
2. Processing & Chunking (ingestor/processor.py)
   ↓
3. Vector Embedding (core/embeddings.py)
   ↓
4. Storage in Qdrant (core/vector_store.py)
   ↓
5. Metadata Tracking (ingestor/metadata_manager.py)
   ↓
6. User Query
   ↓
7. Semantic Retrieval (core/retriever.py)
   ↓
8. LLM Processing (llm/factory.py + config/prompts.py)
   ↓
9. Quality Evaluation (evaluation/ragas_evaluator.py + metrics.py)
   ↓
10. Report Generation (reporting/report_builder.py)
    ↓
11. Email Delivery (reporting/email_service.py)
```

### Key Components

**Core Infrastructure**
- `core/embeddings.py`: Singleton embedding manager (loads model once)
- `core/vector_store.py`: Qdrant wrapper with collection management
- `core/retriever.py`: Semantic search with document filtering
- `llm/factory.py`: LLM provider abstraction (OpenAI, Groq, HuggingFace)

**Document Processing**
- `ingestor/processor.py`: Document loading, chunking, validation
- `ingestor/metadata_manager.py`: Persistent document tracking (JSON storage)

**Quality & Evaluation**
- `evaluation/ragas_evaluator.py`: RAGAS framework integration
- `evaluation/metrics.py`: Custom quality metrics (5 metrics)

**Report Generation**
- `reporting/generators/`: Separate generators for Text, HTML, PDF
- `reporting/email_service.py`: SMTP email handling
- `reporting/report_builder.py`: Orchestrates all report operations

**UI & Session**
- `ui/session_manager.py`: Centralized Streamlit state management
- `ui/components/document_uploader.py`: Upload and indexing component
- `ui/components/query_interface.py`: Query configuration and execution
- `app.py`: Lightweight main entry point (50 lines)

---

## 📊 Analysis Styles Explained

### 🟢 Standard Analysis
Best for quick reviews and general performance assessment

**What you get:**
- Key metrics analysis (CPU, DB Time, Wait Events)
- Issue identification with severity levels
- Root cause analysis with evidence
- Solutions with priority and effort estimates

### 🔵 Detailed Step-by-Step
Best for learning, training, or detailed investigations

**What you get:**
- Systematic 4-step analysis process
- Metric extraction with explanations
- Threshold comparisons against Oracle best practices
- Reasoning shown at each step
- Educational format explaining the "why"

### 🟣 Issue-Focused
Best for management reports and incident response

**What you get:**
- Executive summary with health score
- Categorized issues (Critical/Warning/Info)
- Metric comparison tables
- Top 3 prioritized action items
- Professional report format

---

## 🔧 Email Setup

### For Gmail Users

1. **Enable 2-Factor Authentication**
   - Go to https://myaccount.google.com/security

2. **Generate App Password**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Other (Custom name)"
   - Copy the 16-character password

3. **Add to `.env` file**
   ```env
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your_email@gmail.com
   SMTP_PASSWORD=abcd efgh ijkl mnop
   ```

### For Other Email Providers

Update SMTP_SERVER and SMTP_PORT accordingly:
- **Outlook**: smtp-mail.outlook.com:587
- **Gmail**: smtp.gmail.com:587
- **Yahoo**: smtp.mail.yahoo.com:587

---

## 🐛 Troubleshooting

### Issue: "reportlab not found" error
**Solution:**
```bash
pip uninstall reportlab
pip install reportlab --no-cache-dir
```

### Issue: Email sending fails
**Possible causes:**
1. SMTP credentials not set in `.env`
2. Using regular password instead of App Password (Gmail)
3. Firewall blocking port 587

**Solution:**
- Verify credentials in `.env` file
- For Gmail: Use App Password (https://myaccount.google.com/apppasswords)
- Test SMTP connection with simple script

### Issue: "No documents retrieved" error
**Possible causes:**
1. Documents not indexed properly
2. Document IDs don't match filter
3. Query not matching any content

**Solution:**
- Re-upload and index documents
- Try a broader query
- Check logs in `logs/` directory

### Issue: LLM API errors
**Common errors:**
- `Invalid API key`: Check your API key is correct
- `Rate limit exceeded`: Wait or upgrade plan
- `Model not found`: Select a different model

### Issue: Out of memory (Qdrant)
**Solution:** Use file-based storage instead of `:memory:`

In `config/settings.py`:
```python
QDRANT_LOCATION = "./qdrant_storage"
```

---

## 📦 Dependencies

Core libraries used:

| Library | Purpose |
|---------|---------|
| `streamlit` | Web UI framework |
| `langchain` | RAG orchestration |
| `langchain_openai` | OpenAI integration |
| `langchain_groq` | Groq integration |
| `langchain_huggingface` | HuggingFace integration |
| `qdrant-client` | Vector database |
| `sentence-transformers` | Embedding generation |
| `ragas` | RAG evaluation |
| `reportlab` | PDF generation |
| `python-dotenv` | Environment variables |
| `markdown` | Markdown to HTML |

Full list: See `requirements.txt`

---

## 🚀 Deployment

### Streamlit Cloud (Easiest - FREE)

**Already deployed at**: https://awr-rag.streamlit.app/

To deploy your own:

1. **Push code to GitHub**
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

2. **Deploy on Streamlit Cloud**
   - Go to https://share.streamlit.io/
   - Click "New app"
   - Select your repository
   - Main file: `app.py`
   - Click "Advanced settings" → "Secrets"
   - Add your secrets:
     ```toml
     OPENAI_API_KEY = "sk-xxx"
     GROQ_API_KEY = "xxx"
     SMTP_USERNAME = "your_email@gmail.com"
     SMTP_PASSWORD = "your_app_password"
     ```
   - Click "Deploy"

3. **Your app will be live at**: `https://your-app-name.streamlit.app/`

---

## 📊 Logging

### Application Logs
- **Location**: `logs/12_14_2025_21_31_40.log` (timestamp varies)
- **Contains**: All application events including errors, initialization, queries
- **Purpose**: Debugging and monitoring

### RAGAS Evaluation Logs
- **Location**: `logs/ragas_eval_20251214.log` (one per day)
- **Contains**: Detailed evaluation metrics and scores
- **Purpose**: Track AI quality metrics over time
- **When**: Only created when RAGAS evaluation is enabled and runs

### Log Levels
- **INFO**: Normal operations
- **WARNING**: Potential issues
- **ERROR**: Application errors
- **DEBUG**: Detailed debugging information

---

## 🤝 Contributing

Contributions are welcome! 

### How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Make your changes
4. Commit (`git commit -m 'Add AmazingFeature'`)
5. Push to branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/your-username/AWR-RAG.git
cd AWR-RAG
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
streamlit run app.py
```

---

## 👥 Authors

- **Shrinath Rajeshirke** - Creator & Maintainer
  - GitHub: [@Shrinathrajeshirke](https://github.com/Shrinathrajeshirke)
  - Repository: [AWR-RAG](https://github.com/Shrinathrajeshirke/AWR-RAG)

---

## 🙏 Acknowledgments

- **Oracle Corporation** - For the AWR reporting framework
- **LangChain** - For RAG orchestration tools
- **Anthropic** - For Claude AI capabilities
- **Streamlit** - For the web UI framework
- **Qdrant** - For the vector database
- **HuggingFace** - For open-source models
- **OpenAI** - For GPT models
- **Groq** - For ultra-fast inference
- Open-source community for various libraries

---

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/Shrinathrajeshirke/AWR-RAG/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Shrinathrajeshirke/AWR-RAG/discussions)
- **Live Demo**: [awr-rag.streamlit.app](https://awr-rag.streamlit.app/)

---

## 📜 License

This project is licensed under the MIT License - see LICENSE file for details.

---

**⭐ Star this repo** if you find it helpful!

**Made with ❤️ for DBAs by DBAs**
