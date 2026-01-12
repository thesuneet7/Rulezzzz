# 🏦 Regulatory Traceability & Compliance Engine (PS-4)

## Overview

When regulators audit a bank, they ask deceptively simple but critical questions:

- Where is this regulatory requirement reflected in your internal policy?
- Where is it coded in your underwriting systems?
- Are there gaps or weakened controls?
- Show me the end-to-end trace.

In practice, answering these questions is difficult because regulatory text, internal policies, and system rules:
- Live in **different formats** (PDF, Word, Excel, scanned documents)
- Belong to **different organizational silos**
- Are written in different styles and sometimes different languages
- Are not explicitly connected

This project builds an **AI-assisted, audit-grade system** that connects the dots between regulatory clauses, internal policies, and system configuration rules to:
- Prove compliance where it exists
- Highlight misalignments that pose regulatory or operational risk

---

## Problem Statement (PS-4)

> **Build an AI system that connects the dots between regulatory text, internal policies, and system rules to prove that the bank is compliant — and highlight misalignments that pose regulatory or operational risk.**

Participants must generate their own synthetic data for:
- Regulatory clauses  
- Internal policies  
- System configuration / business rules  

---

## Solution Summary

We design a **hybrid system** that combines:

- **AI-based semantic understanding**  
- **Deterministic, rule-based logic**

Compliance decisions are fully explainable and auditable.

---

## System Architecture

```
Input Documents (PDF / DOCX / XLSX, scanned or readable)
        ↓
Ingestion & OCR
        ↓
Clause-Level Normalization
        ↓
Rule Candidate Identification
        ↓
Schema-Guided Rule Extraction
        ↓
Semantic Traceability
        ↓
Deterministic Compliance Engine
        ↓
Audit-Grade Reports
```

---

## Repository Structure

```
.
├── main.py
├── requirements.txt
├── data/
│   └── raw/
├── src/
│   ├── ingestion/
│   ├── schema/
│   ├── rules/
│   ├── extraction/
│   ├── linking/
│   ├── compliance/
│   └── reporting/
└── README.md
```

---

## Requirements

- Python 3.9+
- Tesseract OCR
- Poppler

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## How to Run

```bash
python main.py
```

---

## Outputs

### Console Output
- Extracted rules
- Traceability links
- Compliance findings

### Audit Report
- audit_report.json
- audit_report.txt

---

## Limitations and Future Extensions
- Integration of real loan-level decision logs
- Expanded multilingual demonstrations
- Traceability graph visualization
- Continuous compliance (CI/CD integration)
- Versioning and regulatory change tracking

## Conclusion

This project demonstrates a end-to-end approach to regulatory traceability:
- AI is used to connect unstructured documents
- Compliance decisions remain deterministic and explainable
- Outputs are regulator and auditor-ready
The system directly addresses the problem statement and is designed to scale to real-world regulatory environments.
