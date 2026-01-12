# 🏦 TraceComply: Regulatory Compliance Traceability Engine

> **AI-Powered Compliance Verification with Explainable, Deterministic Decisions**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://python.org)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-green.svg)](https://ollama.com)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-teal.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React-61DAFB.svg)](https://reactjs.org)

---

## 📋 Table of Contents

- [Problem Statement](#-problem-statement)
- [Solution Overview](#-solution-overview)
- [Key Features](#-key-features)
- [Architecture](#-architecture)
- [Pipeline Deep Dive](#-pipeline-deep-dive)
- [Explainability & Determinism](#-explainability--determinism)
- [Technology Stack](#-technology-stack)
- [Installation](#-installation)
- [Usage](#-usage)
- [Frontend Dashboard](#-frontend-dashboard)
- [API Reference](#-api-reference)
- [Sample Output](#-sample-output)
- [Limitations & Future Work](#-limitations--future-work)

---

## 🎯 Problem Statement

**PS-4: Build an AI system that connects the dots between regulatory text, internal policies, and system rules to prove that the bank is compliant — and highlight misalignments that pose regulatory or operational risk.**

### The Challenge

When regulators audit a bank, they ask deceptively simple but critical questions:

| Question | Challenge |
|----------|-----------|
| *Where is this regulatory requirement reflected in your internal policy?* | Policies live in Word docs, regulations in PDFs |
| *Where is it coded in your underwriting systems?* | System rules in Excel, different naming conventions |
| *Are there gaps or weakened controls?* | No single source of truth |
| *Show me the end-to-end trace.* | Manual, error-prone, time-consuming |

### Why This Is Hard

- Documents exist in **different formats** (PDF, DOCX, XLSX)
- Written in **different styles** and terminology
- Belong to **different organizational silos**
- **No explicit connections** between them

---

## 💡 Solution Overview

TraceComply is a **hybrid AI system** that combines:

| Component | Purpose |
|-----------|---------|
| **LLM-Based Semantic Understanding** | Extract structured rules from unstructured documents |
| **Fuzzy String Matching** | Fast, deterministic parameter matching |
| **LLM Fallback Verification** | Semantic validation when fuzzy matching is uncertain |
| **Deterministic Comparison Engine** | Rule-based compliance checks |

### Core Philosophy

> **"AI assists, logic decides"**

We use LLMs for understanding natural language, but **all compliance decisions are deterministic and explainable**. Every decision can be traced back to specific thresholds and rules.

---

## ✨ Key Features

### 🎯 Explainable Decisions
Every compliance finding includes:
- The specific regulatory threshold
- The matching policy/system rule
- The exact comparison performed
- Clear PASS/FAIL reasoning

### 🔒 Deterministic Compliance
No black-box AI decisions:
- Numeric comparisons are deterministic
- Threshold operators (≤, ≥, =) are explicitly handled
- Edge cases are documented, not hidden

### 🤖 Intelligent Matching
Hybrid matching strategy:
- **String similarity ≥ 70%**: Direct match (fast, deterministic)
- **String similarity 30-70%**: LLM verification (accurate, semantic)
- **String similarity < 30%**: No match (prevents false positives)

### 📊 Audit-Ready Reports
Generate compliance reports that auditors can verify:
- Clear pass/fail status
- Detailed explanations
- Source traceability

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        TRACECOMPLY                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    FRONTEND (React + Vite)               │   │
│  │  • File Upload Interface                                 │   │
│  │  • Processing Status                                     │   │
│  │  • Gap Analysis Dashboard                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    BACKEND (FastAPI)                     │   │
│  │  • File Upload Endpoint                                  │   │
│  │  • Pipeline Orchestration                                │   │
│  │  • Results API                                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              COMPLIANCE PIPELINE (4 Steps)               │   │
│  │                                                          │   │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────┐│   │
│  │  │ Extract  │───▶│  LLM     │───▶│  Bank    │───▶│Final││   │
│  │  │ (s1)     │    │ Process  │    │  Extract │    │Check││   │
│  │  │          │    │ (s2)     │    │  (s3)    │    │(s4) ││   │
│  │  └──────────┘    └──────────┘    └──────────┘    └─────┘│   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    LLM (Ollama Local)                    │   │
│  │                    Model: qwen2.5:3b-instruct            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Pipeline Deep Dive

### Step 1: Document Extraction (`s1_extract.py`)

**Purpose**: Extract raw text from different document formats.

| Input Format | Extraction Method | Output |
|--------------|-------------------|--------|
| PDF (Regulatory) | pdfplumber | `regulation_extracted.txt` |
| DOCX (Policy) | python-docx | `policy_extracted.txt` |
| XLSX (System Rules) | openpyxl | `system_rules_extracted.txt` |

```
📄 regulation.pdf      ─────▶  regulation_extracted.txt
📝 policy.docx         ─────▶  policy_extracted.txt
📊 system_rules.xlsx   ─────▶  system_rules_extracted.txt
```

---

### Step 2: Regulatory Rule Extraction (`s2_llm_process.py`)

**Purpose**: Transform unstructured regulatory text into structured, comparable rules.

**LLM Model**: `qwen2.5:3b-instruct` (via Ollama)

**Why We Chose This Model**:
- Fast inference (3B parameters)
- Strong instruction-following
- Deterministic with temperature=0
- Runs locally (no data leaves premises)

**Extraction Pipeline**:
```
Raw Text
    │
    ▼
┌──────────────────┐
│ Smart Chunking   │  Split by sections, paragraphs
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Clause Identify  │  LLM identifies individual clauses
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Schema Extract   │  LLM extracts to guaranteed schema
└──────────────────┘
    │
    ▼
┌──────────────────┐
│ Validate/Dedupe  │  Remove duplicates, ensure quality
└──────────────────┘
    │
    ▼
regulatory_rules.json
```

**Guaranteed Output Schema**:
```json
{
    "clause_id": "REG-MORT-001",
    "regulation_name": "Retail Mortgage Lending Standards Act",
    "category": "MORTGAGE",
    "thresholds": [
        {
            "parameter": "ltv_standard_max",
            "value": "80",
            "value_numeric": 80.0,
            "operator": "LTE",
            "unit": "%",
            "human_readable": "Max LTV 80%"
        }
    ]
}
```

---

### Step 3: Bank Policy & System Extraction (`s3_bank_ext.py`)

**Purpose**: Extract internal policies and system rules using the same approach.

Uses identical LLM pipeline to ensure **schema consistency** across all rule types.

---

### Step 4: Compliance Comparison (`s4_final.py`)

**Purpose**: Compare regulatory rules against bank policies and system rules.

This is where our **hybrid matching approach** shines:

#### The Matching Algorithm

```
For each regulatory threshold:
    │
    ├─── Calculate string similarity with all candidate thresholds
    │
    ├─── If similarity ≥ 70%:
    │        └── Direct match ✓ (fast, deterministic)
    │
    ├─── If similarity 30-70%:
    │        └── LLM verification (semantic check)
    │            └── If LLM confirms: match ✓
    │            └── If LLM denies: no match ✗
    │
    └─── If similarity < 30%:
             └── No match ✗ (prevents false positives)
```

#### Why Fuzzy + LLM Fallback?

| Approach | Pros | Cons |
|----------|------|------|
| Pure string matching | Fast, deterministic | Misses semantic matches |
| Pure LLM | Semantic understanding | Slow, non-deterministic |
| **Fuzzy + LLM Fallback** | Best of both worlds | Optimal speed + accuracy |

**Example**:
- `ltv_ratio` vs `LTV_Max` → 75% similarity → Direct match ✓
- `min_id_count` vs `identity_documents_required` → 45% similarity → LLM verifies ✓
- `interest_rate` vs `flood_insurance` → 10% similarity → No match (correct!)

#### Threshold Comparison Logic

```python
# For MAX limits (LTE, ≤): stricter = LOWER value
if policy_value <= regulatory_limit:
    COMPLIANT ✓
else:
    NON-COMPLIANT ✗

# For MIN requirements (GTE, ≥): stricter = HIGHER value  
if policy_value >= regulatory_minimum:
    COMPLIANT ✓
else:
    NON-COMPLIANT ✗
```

---

## 🔍 Explainability & Determinism

### Every Decision Is Traceable

For each regulatory requirement, the system outputs:

```
Regulatory Clause: Retail Mortgage Lending Standards Act (REG-MORT-002)
Compliant with Bank Policy: No
Compliant with System Rules: No
Explanation: 
  Policy: ltv_highest_risk_max [POLICY-001]: ✗ FAIL: allows 80.0, reg caps at 75.0
  System: ltv_highest_risk_max [SYS-R-100]: ✗ FAIL: allows 80.0, reg caps at 75.0
```

### What Makes This Explainable

1. **Parameter Identification**: We know exactly which parameters were compared
2. **Source Traceability**: We know which policy/system rule was matched
3. **Numeric Comparison**: Clear ✓/✗ with actual values shown
4. **No Hidden Logic**: All thresholds and operators are visible

### Determinism Guarantees

| Component | Determinism Approach |
|-----------|---------------------|
| LLM Calls | `temperature=0` for reproducible outputs |
| String Matching | Standard algorithms (SequenceMatcher, Jaccard) |
| Threshold Comparison | Pure numeric/boolean comparison |
| Decision Logic | Rule-based, no randomness |

---

## 🛠️ Technology Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **Python 3.9+** | Core language |
| **FastAPI** | REST API framework |
| **Ollama** | Local LLM inference |
| **qwen2.5:3b-instruct** | LLM model |
| **pdfplumber** | PDF extraction |
| **python-docx** | DOCX extraction |
| **openpyxl** | XLSX extraction |
| **langchain-ollama** | LLM integration |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 19** | UI framework |
| **Vite 7** | Build tool |
| **TypeScript** | Type safety |
| **axios** | HTTP client |
| **recharts** | Charts & visualizations |
| **lucide-react** | Icons |

---

## 📦 Installation

### Prerequisites
- Python 3.9+
- Node.js 18+
- [Ollama](https://ollama.com) installed

### 1. Clone the repository
```bash
git clone <repo-url>
cd Rulezzzz
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Install and start Ollama
```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama server
ollama serve

# Pull the model (in another terminal)
ollama pull qwen2.5:3b-instruct
```

### 4. Install frontend dependencies
```bash
cd frontend
npm install
```

---

## 🚀 Usage

### Option 1: Using the Web Interface

**Terminal 1 - Start Backend:**
```bash
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Ensure Ollama is running:**
```bash
ollama serve
```

Then open **http://localhost:5173** in your browser.

### Option 2: Using the CLI

```bash
python main.py
```

This runs the full pipeline sequentially:
1. Extract documents
2. Process regulatory rules
3. Extract bank policies & system rules
4. Generate compliance report

---

## 🖥️ Frontend Dashboard

The web interface provides an intuitive way to interact with the compliance engine.

### Upload Page

Upload your three required documents:
- **Regulatory Standards** (PDF)
- **Internal Policies** (DOCX)
- **System Configs** (XLSX)

<!-- SCREENSHOT: Upload page with three dropzones -->
![Upload Page](screenshots/upload_page.png)

### Processing Screen

Real-time status updates as the pipeline runs:
- Uploading files...
- Running compliance analysis...
- Fetching results...

<!-- SCREENSHOT: Processing spinner -->
![Processing](screenshots/processing.png)

### Results Dashboard

Interactive dashboard showing:
- **Summary Cards**: Uploaded file names
- **Gap Analysis Table**: Real compliance data from the pipeline
- **Charts**: Visual breakdown by category and risk level

<!-- SCREENSHOT: Dashboard with results table -->
![Dashboard](screenshots/dashboard.png)

---

## 📡 API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check & API info |
| `GET` | `/health` | Simple health check |
| `POST` | `/upload` | Upload 3 required files |
| `POST` | `/process` | Run the compliance pipeline |
| `GET` | `/results` | Get compliance report (JSON/CSV) |
| `GET` | `/results/regulatory` | Get extracted regulatory rules |
| `GET` | `/results/policy` | Get extracted policy rules |
| `GET` | `/results/system` | Get extracted system rules |

### Example: Upload Files

```bash
curl -X POST http://localhost:8000/upload \
  -F "regulation=@data/raw/regulation.pdf" \
  -F "policy=@data/raw/policy.docx" \
  -F "system_rules=@data/raw/system_rules.xlsx"
```

### Example: Run Pipeline

```bash
curl -X POST http://localhost:8000/process
```

### Example: Get Results

```bash
curl http://localhost:8000/results
```

---

## 📊 Sample Output

### Compliance Report (CSV)

| Regulatory Clause | Compliant with Bank Policy | Compliant with System Rules | Explanation |
|-------------------|----------------------------|-----------------------------| ------------|
| Retail Mortgage Lending Standards Act (REG-MORT-001) | Yes | Yes | Policy: ltv_standard_max: ✓ OK: 80.0 ≤ 80.0 |
| Anti-Money Laundering Directive (CLAUSE-003) | Yes | No | Policy: ✓ OK: 2.0 ≥ 2.0 \| System: ✗ FAIL: requires 1.0, reg min is 2.0 |
| Climate Risk & Flood Protection Act (REG-ENV-099) | No | No | ✗ NO MATCHING RULE FOUND - cannot verify compliance |

---

## 📁 Repository Structure

```
Rulezzzz/
├── api.py                    # FastAPI backend
├── main.py                   # CLI orchestrator
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── src/
│   ├── s1_extract.py         # Document extraction
│   ├── s2_llm_process.py     # Regulatory rule extraction
│   ├── s3_bank_ext.py        # Bank policy & system extraction
│   └── s4_final.py           # Compliance comparison
│
├── frontend/
│   ├── package.json          # Node dependencies
│   ├── vite.config.ts        # Vite config
│   ├── home.tsx              # Main upload page
│   ├── dropzone.tsx          # File upload component
│   ├── index.css             # Styles
│   └── components/
│       └── Dashboard.tsx     # Results dashboard
│
├── data/
│   ├── raw/                  # Input files
│   ├── processed/            # Extracted text
│   └── final_jsons/          # JSON outputs & CSV report
│
└── .agent/
    └── workflows/            # Agent workflows
```

---

## ⚠️ Limitations & Future Work

### Current Limitations

- **Single language**: Primarily designed for English documents
- **Format constraints**: PDF, DOCX, XLSX only
- **Local LLM**: Requires Ollama running locally
- **Synthetic data**: Tested with generated sample data

### Future Extensions

| Feature | Description |
|---------|-------------|
| **Multi-language support** | Translate and compare multilingual regulations |
| **Scanned document OCR** | Handle scanned PDFs with Tesseract |
| **Traceability graph** | Visual graph of regulation → policy → system links |
| **CI/CD integration** | Continuous compliance checking in pipelines |
| **Regulatory change tracking** | Alert when regulations change |
| **Loan-level decision logs** | Verify individual loan decisions against rules |

---

## 🏆 Conclusion

TraceComply demonstrates a production-ready approach to regulatory compliance:

✅ **AI extracts** structured data from unstructured documents  
✅ **Fuzzy matching** handles terminology differences  
✅ **LLM fallback** provides semantic verification  
✅ **Deterministic comparison** ensures auditable decisions  
✅ **Full explainability** for every compliance finding  

The system directly addresses **PS-4** by proving compliance where it exists and highlighting gaps that pose regulatory risk — all with complete transparency and audit-readiness.

---

<p align="center">
  <b>Built for the Regulatory Traceability Hackathon</b><br>
  <i>Making compliance explainable, deterministic, and automated.</i>
</p>
