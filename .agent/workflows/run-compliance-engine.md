---
description: How to run the Regulatory Compliance Engine
---

# Running the Compliance Engine

## Prerequisites

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure **Tesseract OCR** is installed (for scanned PDFs):
```bash
brew install tesseract  # macOS
```

3. Ensure **Poppler** is installed (for PDF to image conversion):
```bash
brew install poppler  # macOS
```

## Running the Engine

// turbo
1. Run the main compliance analysis:
```bash
python main.py
```

This will:
- Ingest `data/raw/regulation.pdf`, `data/raw/policy.docx`, and `data/raw/system_rules.xlsx`
- Extract and classify rules from each document
- Build semantic traceability links between regulations → policies → systems
- Evaluate compliance and generate findings
- Output `audit_report.json` and `audit_report.txt`

## Input Documents

Place your documents in `data/raw/`:
- **regulation.pdf** — External regulatory requirements
- **policy.docx** — Internal bank policies
- **system_rules.xlsx** — System configuration / business rules

## Output Files

- `audit_report.json` — Machine-readable audit report with timestamps
- `audit_report.txt` — Human-readable audit findings

## Understanding the Output

### Finding Types
| Finding | Meaning |
|---------|---------|
| `COMPLIANT` | Regulation fully traced to matching policy & system |
| `SYSTEM_TOO_LENIENT` | System allows more than regulation permits |
| `CONTROL_WEAKENED` | Policy says REQUIRED but system marks OPTIONAL |
| `MISSING_POLICY` | No internal policy matches the regulation |
| `MISSING_SYSTEM` | No system rule enforces the regulation |

### Severity Levels
- **HIGH** — `SYSTEM_TOO_LENIENT`, `MISSING_SYSTEM`
- **MEDIUM** — `CONTROL_WEAKENED`
- **LOW** — `COMPLIANT`

## Customization

### Adjusting Similarity Threshold
In `main.py`, modify the threshold for semantic matching:
```python
linker = TraceabilityLinker(similarity_threshold=0.6)  # Lower = more matches
```

### Adding New Document Types
Add parsers in `src/ingestion/` and update `dispatcher.py`.
