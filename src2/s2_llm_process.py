"""
Step 2: Process regulation text to extract structured clauses
Uses LLM-first approach for generalized extraction from ANY regulatory PDF.
Guarantees consistent JSON output schema regardless of input format.
"""

import json
import re
from pathlib import Path
from langchain_ollama import OllamaLLM
from datetime import datetime
from typing import Optional

# =====================================================
# CONFIG
# =====================================================
MODEL_NAME = "qwen2.5:3b-instruct"

# =====================================================
# GUARANTEED OUTPUT SCHEMA
# =====================================================
# This is the exact schema that EVERY clause will have, regardless of input format.
# Missing fields will be null, never omitted.

CLAUSE_SCHEMA = {
    "clause_id": None,           # str: Unique identifier (from doc or generated)
    "clause_code": None,         # str: Official code if exists (e.g., "REG-001")
    "clause_title": None,        # str: Title/name of the clause
    "regulation_name": None,     # str: Parent regulation/act name
    "section": None,             # str: Section/article reference
    "effective_date": None,      # str: YYYY-MM-DD format
    "category": None,            # str: Category (MORTGAGE, KYC, LENDING, etc.)
    "description": None,         # str: Full text of the clause
    "applies_to": None,          # str: Who/what this applies to
    "conditions": None,          # str: Triggering conditions
    "thresholds": [],            # list: Quantitative limits for comparison
    "compliance_check": None,    # str: How to verify compliance
    "risk_level": "MEDIUM",      # str: HIGH/MEDIUM/LOW
    "source_text": None,         # str: Original raw text
    "extracted_at": None,        # str: ISO timestamp
}

THRESHOLD_SCHEMA = {
    "parameter": None,           # str: Parameter name (e.g., "LTV", "DTI")
    "value": None,               # str: The limit value
    "value_numeric": None,       # float|bool|null: Typed value for comparison
    "operator": None,            # str: LTE, GTE, EQUALS, LT, GT
    "unit": None,                # str: %, days, count, etc.
    "human_readable": None,      # str: Plain English summary
}

# =====================================================
# INIT LLM
# =====================================================
llm = OllamaLLM(model=MODEL_NAME, temperature=0)

# =====================================================
# LLM PROMPTS - DESIGNED FOR ANY FORMAT
# =====================================================

CHUNK_IDENTIFICATION_PROMPT = """
You are analyzing regulatory document text. Your job is to identify and split distinct regulatory clauses or rules.

A regulatory clause typically may contain:
- A clause code/identifier (e.g., REG-MORT-001, Article 5, §12.3)
- A regulation/act name
- A section reference
- An effective date
- The actual rule/requirement text
- Parameters or thresholds

CRITICAL: When splitting, PRESERVE ALL METADATA for each clause. Include:
- Any clause codes (REG-XXX-NNN, etc.)
- Any section/article references
- Any effective dates
- The parent regulation/act name
- The full requirement text
- Any parameters or values

Return a JSON array where each item is the COMPLETE text of one clause INCLUDING all its metadata.
If the text appears to be one clause, return an array with just that one item.
Do NOT strip out headers, codes, dates, or any other information.

Return ONLY a JSON array of strings, nothing else.

TEXT:
{text}
"""

CLAUSE_EXTRACTION_PROMPT = """
You are a regulatory compliance expert. Extract ALL available structured information from this regulatory clause.

CRITICAL INSTRUCTIONS:
1. Look for ANY identifying codes (e.g., REG-MORT-001, Article 5.2, §12.3, Clause 4.1.a)
2. Look for ANY act/law names (e.g., "Mortgage Lending Standards Act", "AML Directive")
3. Look for ANY dates in any format and convert to YYYY-MM-DD
4. Look for ALL numeric requirements - percentages, counts, durations, amounts
5. For boolean requirements (mandatory, required, must have), create a threshold with operator EQUALS and value "true"

You must return a valid JSON object with EXACTLY these fields (use null for missing values):

{{
    "clause_code": "string or null - ANY code/reference number found (REG-XXX-NNN, Art. N, §N.N, Section N.N)",
    "clause_title": "string or null - title of this specific rule if stated",
    "regulation_name": "string or null - the parent act/law/regulation name (e.g., 'Retail Mortgage Lending Standards Act')",
    "section": "string or null - section/article/paragraph reference (e.g., '4.1.a', '12.3')",
    "effective_date": "string or null - any date found, converted to YYYY-MM-DD",
    "category": "string - one of: MORTGAGE, KYC_AML, LENDING, ENVIRONMENTAL, CONSUMER_PROTECTION, DATA_PRIVACY, CAPITAL, LIQUIDITY, INSURANCE, REPORTING, OTHER",
    "description": "string - the full requirement text",
    "applies_to": "string or null - who/what this rule applies to",
    "conditions": "string or null - triggering conditions (e.g., 'Credit Score < 600')",
    "thresholds": [
        {{
            "parameter": "string - metric name in snake_case (e.g., ltv_ratio, min_id_count, flood_insurance_required)",
            "value": "string - the limit value (use 'true'/'false' for boolean requirements)",
            "operator": "string - LTE (max/not exceed), GTE (min/at least), EQUALS (must be/required), LT (<), GT (>)",
            "unit": "string or null - %, count, years, days, currency, boolean, etc.",
            "human_readable": "string - clear summary (e.g., 'Max LTV 80%', 'Min 2 IDs required', 'Flood insurance mandatory')"
        }}
    ],
    "compliance_check": "string - how to verify compliance",
    "risk_level": "string - HIGH (financial/legal risk), MEDIUM (operational risk), LOW (documentation only)"
}}

THRESHOLD EXTRACTION RULES:
- "shall not exceed 80%" → operator: LTE, value: "80"
- "at least two" → operator: GTE, value: "2"  
- "must not exceed 43%" → operator: LTE, value: "43"
- "mandatory/required" → operator: EQUALS, value: "true"
- "capped at 75%" → operator: LTE, value: "75"

CLAUSE TEXT:
{clause_text}

Return ONLY valid JSON, no explanations:
"""

# =====================================================
# JSON UTILITIES
# =====================================================
def recover_json(text: str):
    """Robustly extract JSON from LLM response."""
    if not text or not text.strip():
        return None

    text = text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except:
        pass

    # Try to find JSON array
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    # Try to find JSON object
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    return None


def ensure_schema(data: dict, schema: dict) -> dict:
    """
    Ensure output matches schema exactly.
    Missing fields are set to schema defaults, extra fields are removed.
    """
    result = {}
    for key, default in schema.items():
        if key in data and data[key] is not None:
            result[key] = data[key]
        else:
            # Use a copy of default to avoid mutation issues with lists
            result[key] = [] if isinstance(default, list) else default
    return result


def ensure_threshold_schema(data: dict) -> dict:
    """Ensure threshold matches schema exactly."""
    return ensure_schema(data, THRESHOLD_SCHEMA)


def parse_numeric_value(value: str):
    """Try to parse a string value to numeric type for comparison."""
    if value is None:
        return None
    
    value_str = str(value).strip().lower()
    
    # Boolean
    if value_str in ["true", "yes", "required", "mandatory"]:
        return True
    if value_str in ["false", "no", "optional"]:
        return False
    
    # Numeric - remove common suffixes
    cleaned = re.sub(r"[%$€₹,\s]", "", value_str)
    try:
        return float(cleaned)
    except:
        return None


# =====================================================
# TEXT CHUNKING (FORMAT-AGNOSTIC)
# =====================================================
def smart_chunk_text(text: str, max_chunk_size: int = 2000) -> list[str]:
    """
    Split text into manageable chunks for LLM processing.
    Tries to split at natural boundaries (paragraphs, sections).
    """
    # First, try to split by common section markers
    section_patterns = [
        r'\n(?=(?:Article|Section|§|\d+\.\d+|[A-Z]+-[A-Z]+-\d+))',  # Section headers
        r'\n\n+',  # Double newlines (paragraphs)
        r'\n(?=[A-Z])',  # Lines starting with capital letters
    ]
    
    chunks = [text]
    
    for pattern in section_patterns:
        new_chunks = []
        for chunk in chunks:
            if len(chunk) > max_chunk_size:
                parts = re.split(pattern, chunk)
                new_chunks.extend([p.strip() for p in parts if p.strip()])
            else:
                new_chunks.append(chunk)
        chunks = new_chunks
    
    # If still too large, just split by size
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_size:
            # Split by sentences
            sentences = re.split(r'(?<=[.!?])\s+', chunk)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) > max_chunk_size:
                    if current:
                        final_chunks.append(current.strip())
                    current = sent
                else:
                    current += " " + sent
            if current:
                final_chunks.append(current.strip())
        else:
            final_chunks.append(chunk)
    
    return [c for c in final_chunks if len(c) > 20]  # Filter tiny fragments


def identify_clauses_with_llm(text: str) -> list[str]:
    """Use LLM to identify and split individual clauses from text."""
    prompt = CHUNK_IDENTIFICATION_PROMPT.format(text=text)
    response = llm.invoke(prompt)
    
    clauses = recover_json(response)
    
    if isinstance(clauses, list):
        return [str(c).strip() for c in clauses if c and len(str(c).strip()) > 20]
    
    # Fallback: return original text as single clause
    return [text] if text.strip() else []


# =====================================================
# MAIN EXTRACTION LOGIC
# =====================================================
def extract_clause_with_llm(clause_text: str, clause_index: int) -> dict:
    """
    Extract structured data from a single clause using LLM.
    Returns a dict matching CLAUSE_SCHEMA exactly.
    """
    prompt = CLAUSE_EXTRACTION_PROMPT.format(clause_text=clause_text)
    response = llm.invoke(prompt)
    
    extracted = recover_json(response)
    
    # Start with empty schema
    result = ensure_schema({}, CLAUSE_SCHEMA)
    result["source_text"] = clause_text
    result["extracted_at"] = datetime.now().isoformat()
    result["clause_id"] = f"CLAUSE-{clause_index:03d}"
    
    if isinstance(extracted, dict):
        # Map extracted fields to schema
        for key in CLAUSE_SCHEMA.keys():
            if key in extracted and extracted[key] is not None:
                result[key] = extracted[key]
        
        # Ensure clause_id uses extracted code if available
        if extracted.get("clause_code"):
            result["clause_id"] = extracted["clause_code"]
        
        # Process thresholds to ensure consistent schema
        if "thresholds" in extracted and isinstance(extracted["thresholds"], list):
            result["thresholds"] = []
            for t in extracted["thresholds"]:
                if isinstance(t, dict):
                    threshold = ensure_threshold_schema(t)
                    # Add typed numeric value for comparison
                    threshold["value_numeric"] = parse_numeric_value(threshold.get("value"))
                    result["thresholds"].append(threshold)
    
    return result


def process_regulation_text(text: str) -> list[dict]:
    """
    Main processing pipeline for regulation text.
    Returns list of clauses, each matching CLAUSE_SCHEMA exactly.
    """
    all_clauses = []
    clause_index = 1
    
    # Step 1: Smart chunk the text
    print("   Chunking text...")
    chunks = smart_chunk_text(text)
    print(f"   Created {len(chunks)} chunks")
    
    # Step 2: For each chunk, identify individual clauses
    print("   Identifying clauses...")
    for chunk in chunks:
        clause_texts = identify_clauses_with_llm(chunk)
        
        # Step 3: Extract structured data from each clause
        for clause_text in clause_texts:
            if len(clause_text.strip()) < 30:
                continue
                
            clause_data = extract_clause_with_llm(clause_text, clause_index)
            all_clauses.append(clause_data)
            clause_index += 1
    
    return all_clauses


# =====================================================
# VALIDATION & DEDUPLICATION
# =====================================================
def validate_and_dedupe(clauses: list[dict]) -> list[dict]:
    """
    Validate extracted clauses and remove duplicates.
    """
    seen_texts = set()
    valid_clauses = []
    
    for clause in clauses:
        # Skip if no meaningful content
        if not clause.get("description") and not clause.get("source_text"):
            continue
        
        # Simple deduplication by source text
        text_key = (clause.get("source_text") or "")[:100]
        if text_key in seen_texts:
            continue
        seen_texts.add(text_key)
        
        valid_clauses.append(clause)
    
    return valid_clauses


# =====================================================
# MAIN PIPELINE
# =====================================================
def main():
    project_root = Path(__file__).parent.parent
    input_file = project_root / "data" / "processed" / "regulation_extracted.txt"
    output_dir = project_root / "data" / "processed"
    intermediate_dir = project_root / "intermediate"
    
    intermediate_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)
    
    # Check input exists
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}\nRun s1_extract.py first.")
    
    print("=" * 60)
    print("REGULATORY CLAUSE EXTRACTION PIPELINE (GENERALIZED)")
    print("=" * 60)
    
    # Read extracted text
    text = input_file.read_text(encoding="utf-8")
    print(f"\n📄 Loaded: {input_file.name}")
    print(f"   Characters: {len(text)}")
    
    # ========== PROCESS ==========
    print("\n🤖 Processing with LLM (format-agnostic)...")
    clauses = process_regulation_text(text)
    print(f"   Extracted {len(clauses)} raw clauses")
    
    # ========== VALIDATE & DEDUPE ==========
    print("\n🔍 Validating and deduplicating...")
    clauses = validate_and_dedupe(clauses)
    print(f"   Final count: {len(clauses)} valid clauses")
    
    # ========== SAVE OUTPUTS ==========
    
    # 1. Full extracted clauses (intermediate)
    clauses_output = intermediate_dir / "clauses_extracted.json"
    with open(clauses_output, 'w', encoding='utf-8') as f:
        json.dump(clauses, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved: {clauses_output}")
    
    # 2. Compliance rules (final, same schema as clauses for consistency)
    rules_output = output_dir / "regulatory_rules.json"
    with open(rules_output, 'w', encoding='utf-8') as f:
        json.dump(clauses, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {rules_output}")
    
    # 3. Summary
    summary = {
        "extraction_timestamp": datetime.now().isoformat(),
        "source_file": str(input_file),
        "total_clauses": len(clauses),
        "schema_version": "1.0",
        "by_category": {},
        "by_risk_level": {},
        "all_thresholds": []
    }
    
    for clause in clauses:
        cat = clause.get("category") or "UNKNOWN"
        summary["by_category"][cat] = summary["by_category"].get(cat, 0) + 1
        
        risk = clause.get("risk_level") or "UNKNOWN"
        summary["by_risk_level"][risk] = summary["by_risk_level"].get(risk, 0) + 1
        
        for t in clause.get("thresholds", []):
            summary["all_thresholds"].append({
                "clause_id": clause["clause_id"],
                "parameter": t.get("parameter"),
                "human_readable": t.get("human_readable"),
                "value_numeric": t.get("value_numeric")
            })
    
    summary_output = output_dir / "extraction_summary.json"
    with open(summary_output, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {summary_output}")
    
    # ========== PRINT SUMMARY ==========
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   Total Clauses: {len(clauses)}")
    print(f"\n   By Category:")
    for cat, count in summary["by_category"].items():
        print(f"      - {cat}: {count}")
    print(f"\n   By Risk Level:")
    for risk, count in summary["by_risk_level"].items():
        print(f"      - {risk}: {count}")
    
    if summary["all_thresholds"]:
        print(f"\n   Key Thresholds (for policy comparison):")
        for t in summary["all_thresholds"]:
            print(f"      - [{t['clause_id']}] {t['human_readable']}")
    
    return clauses


if __name__ == "__main__":
    main()
