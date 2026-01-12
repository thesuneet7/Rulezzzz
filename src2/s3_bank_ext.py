"""
Step 3: Extract structured data from Bank Policy and System Rules
Uses the same LLM-first approach as s2_llm_process.py for consistency.
Processes: policy_extracted.txt and system_rules_extracted.txt
Outputs: bank_policy_rules.json and system_rules.json
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
# Same schema as regulatory rules for easy comparison

RULE_SCHEMA = {
    "rule_id": None,             # str: Unique identifier
    "rule_code": None,           # str: Official code if exists
    "rule_title": None,          # str: Title/name of the rule
    "document_name": None,       # str: Parent document name
    "section": None,             # str: Section reference
    "effective_date": None,      # str: YYYY-MM-DD format
    "category": None,            # str: Category (MORTGAGE, KYC, LENDING, etc.)
    "description": None,         # str: Full text of the rule
    "applies_to": None,          # str: Who/what this applies to
    "conditions": None,          # str: Triggering conditions
    "thresholds": [],            # list: Quantitative limits for comparison
    "source": None,              # str: "POLICY" or "SYSTEM"
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
# LLM PROMPTS
# =====================================================

CHUNK_IDENTIFICATION_PROMPT = """
You are analyzing bank policy or system rules text. Your job is to identify and split distinct policy rules.

A policy rule typically may contain:
- A rule ID/code (e.g., SYS-R-100, Policy 1.1)
- A rule name or title
- A section reference
- An effective date
- The policy requirement text
- Parameters, thresholds, or limits

CRITICAL: When splitting, PRESERVE ALL METADATA for each rule. Include:
- Any rule IDs or codes
- Any section references
- Any dates mentioned
- The parent document/module name
- The full requirement text
- Any parameters, values, or operators

Return a JSON array where each item is the COMPLETE text of one rule INCLUDING all its metadata.
If the text appears to be one rule, return an array with just that one item.
Do NOT strip out headers, codes, dates, or any other information.

Return ONLY a JSON array of strings, nothing else.

TEXT:
{text}
"""

POLICY_EXTRACTION_PROMPT = """
You are a bank compliance expert. Extract ALL available structured information from this bank policy rule.

CRITICAL INSTRUCTIONS:
1. Look for ANY identifying codes (e.g., Policy 1.1, SYS-R-100, Rule ID)
2. Look for ANY policy names or document titles
3. Look for ANY dates in any format and convert to YYYY-MM-DD
4. Look for ALL numeric requirements - percentages, counts, durations, amounts
5. For boolean requirements (required, mandatory), create a threshold with operator EQUALS and value "true"

You must return a valid JSON object with EXACTLY these fields (use null for missing values):

{{
    "rule_code": "string or null - ANY code/reference found (Policy N.N, SYS-R-NNN, Rule ID)",
    "rule_title": "string or null - title of this rule if stated",
    "document_name": "string or null - the parent document name",
    "section": "string or null - section reference (e.g., '1.1', '2.2')",
    "effective_date": "string or null - any date found, converted to YYYY-MM-DD",
    "category": "string - one of: MORTGAGE, KYC_AML, LENDING, AFFORDABILITY, COLLATERAL, INSURANCE, IDENTITY, SYSTEM, OTHER",
    "description": "string - the full policy requirement text",
    "applies_to": "string or null - who/what this rule applies to",
    "conditions": "string or null - triggering conditions",
    "thresholds": [
        {{
            "parameter": "string - metric name in snake_case (e.g., ltv_ratio, dti_ratio, min_id_count)",
            "value": "string - the limit value",
            "operator": "string - LTE (max/cap), GTE (min/at least), EQUALS (must be), LT (<), GT (>)",
            "unit": "string or null - %, count, years, days, etc.",
            "human_readable": "string - clear summary (e.g., 'Max LTV 80%', 'Min 2 IDs required')"
        }}
    ]
}}

THRESHOLD EXTRACTION RULES:
- "capped at 80%" → operator: LTE, value: "80"
- "maximum LTV is 80%" → operator: LTE, value: "80"
- "at least two" or "minimum of 2" → operator: GTE, value: "2"  
- "must not exceed 43%" → operator: LTE, value: "43"
- "required" or "mandatory" → operator: EQUALS, value: "true"

RULE TEXT:
{clause_text}

Return ONLY valid JSON, no explanations:
"""

SYSTEM_RULE_EXTRACTION_PROMPT = """
You are a bank system configuration expert. Extract ALL available structured information from this system rule configuration.

The system rule typically has these fields in a tabular format:
- rule_id: System rule identifier (e.g., SYS-R-100)
- rule_name: Name of the rule
- system_module: Which system module this rule is in
- parameter_name: The parameter being checked
- operator: The comparison operator (LTE, GTE, GT, LT, EQUALS)
- threshold_value: The value to compare against
- data_type: Type of data (Percent, Integer, Currency, etc.)
- last_deployment_date: When this was last deployed
- description: What this rule does

Extract this information and return a JSON object with EXACTLY these fields:

{{
    "rule_code": "string - the rule_id (e.g., SYS-R-100)",
    "rule_title": "string - the rule_name",
    "document_name": "string - the system_module",
    "section": "null",
    "effective_date": "string - last_deployment_date in YYYY-MM-DD format",
    "category": "string - SYSTEM",
    "description": "string - the description",
    "applies_to": "string or null",
    "conditions": "string or null",
    "thresholds": [
        {{
            "parameter": "string - parameter_name",
            "value": "string - threshold_value",
            "operator": "string - operator from the rule",
            "unit": "string - inferred from data_type (Percent→%, Integer→count, Currency→$)",
            "human_readable": "string - summary of the threshold"
        }}
    ]
}}

SYSTEM RULE TEXT:
{clause_text}

Return ONLY valid JSON, no explanations:
"""

# =====================================================
# JSON UTILITIES (same as s2)
# =====================================================
def recover_json(text: str):
    """Robustly extract JSON from LLM response."""
    if not text or not text.strip():
        return None

    text = text.strip()
    
    try:
        return json.loads(text)
    except:
        pass

    match = re.search(r"\[.*\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except:
            pass

    return None


def ensure_schema(data: dict, schema: dict) -> dict:
    """Ensure output matches schema exactly."""
    result = {}
    for key, default in schema.items():
        if key in data and data[key] is not None:
            result[key] = data[key]
        else:
            result[key] = [] if isinstance(default, list) else default
    return result


def ensure_threshold_schema(data: dict) -> dict:
    """Ensure threshold matches schema exactly."""
    return ensure_schema(data, THRESHOLD_SCHEMA)


def parse_numeric_value(value: str):
    """Try to parse a string value to numeric type."""
    if value is None:
        return None
    
    value_str = str(value).strip().lower()
    
    if value_str in ["true", "yes", "required", "mandatory"]:
        return True
    if value_str in ["false", "no", "optional"]:
        return False
    
    cleaned = re.sub(r"[%$€₹,\s]", "", value_str)
    try:
        return float(cleaned)
    except:
        return None


# =====================================================
# TEXT CHUNKING
# =====================================================
def smart_chunk_text(text: str, max_chunk_size: int = 2000) -> list[str]:
    """Split text into manageable chunks."""
    section_patterns = [
        r'\n(?=(?:\d+\.\d+|Policy|SYS-R-))',
        r'\n\n+',
        r'\n(?=[A-Z])',
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
    
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_size:
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
    
    return [c for c in final_chunks if len(c) > 20]


def identify_rules_with_llm(text: str) -> list[str]:
    """Use LLM to identify and split individual rules from text."""
    prompt = CHUNK_IDENTIFICATION_PROMPT.format(text=text)
    response = llm.invoke(prompt)
    
    rules = recover_json(response)
    
    if isinstance(rules, list):
        return [str(r).strip() for r in rules if r and len(str(r).strip()) > 20]
    
    return [text] if text.strip() else []


# =====================================================
# EXTRACTION LOGIC
# =====================================================
def extract_policy_rule(rule_text: str, rule_index: int) -> dict:
    """Extract structured data from a policy rule using LLM."""
    prompt = POLICY_EXTRACTION_PROMPT.format(clause_text=rule_text)
    response = llm.invoke(prompt)
    
    extracted = recover_json(response)
    
    result = ensure_schema({}, RULE_SCHEMA)
    result["source_text"] = rule_text
    result["extracted_at"] = datetime.now().isoformat()
    result["rule_id"] = f"POLICY-{rule_index:03d}"
    result["source"] = "POLICY"
    
    if isinstance(extracted, dict):
        for key in RULE_SCHEMA.keys():
            if key in extracted and extracted[key] is not None:
                result[key] = extracted[key]
        
        if extracted.get("rule_code"):
            result["rule_id"] = extracted["rule_code"]
        
        if "thresholds" in extracted and isinstance(extracted["thresholds"], list):
            result["thresholds"] = []
            for t in extracted["thresholds"]:
                if isinstance(t, dict):
                    threshold = ensure_threshold_schema(t)
                    threshold["value_numeric"] = parse_numeric_value(threshold.get("value"))
                    result["thresholds"].append(threshold)
    
    return result


def extract_system_rule(rule_text: str, rule_index: int) -> dict:
    """Extract structured data from a system rule using LLM."""
    prompt = SYSTEM_RULE_EXTRACTION_PROMPT.format(clause_text=rule_text)
    response = llm.invoke(prompt)
    
    extracted = recover_json(response)
    
    result = ensure_schema({}, RULE_SCHEMA)
    result["source_text"] = rule_text
    result["extracted_at"] = datetime.now().isoformat()
    result["rule_id"] = f"SYSTEM-{rule_index:03d}"
    result["source"] = "SYSTEM"
    
    if isinstance(extracted, dict):
        for key in RULE_SCHEMA.keys():
            if key in extracted and extracted[key] is not None:
                result[key] = extracted[key]
        
        if extracted.get("rule_code"):
            result["rule_id"] = extracted["rule_code"]
        
        if "thresholds" in extracted and isinstance(extracted["thresholds"], list):
            result["thresholds"] = []
            for t in extracted["thresholds"]:
                if isinstance(t, dict):
                    threshold = ensure_threshold_schema(t)
                    threshold["value_numeric"] = parse_numeric_value(threshold.get("value"))
                    result["thresholds"].append(threshold)
    
    return result


def process_text(text: str, extractor_func, source_name: str) -> list[dict]:
    """Process text and extract rules using the specified extractor."""
    all_rules = []
    rule_index = 1
    
    print("   Chunking text...")
    chunks = smart_chunk_text(text)
    print(f"   Created {len(chunks)} chunks")
    
    print("   Identifying rules...")
    for chunk in chunks:
        rule_texts = identify_rules_with_llm(chunk)
        
        for rule_text in rule_texts:
            if len(rule_text.strip()) < 30:
                continue
            
            rule_data = extractor_func(rule_text, rule_index)
            all_rules.append(rule_data)
            rule_index += 1
    
    return all_rules


def validate_and_dedupe(rules: list[dict]) -> list[dict]:
    """Validate and deduplicate extracted rules."""
    seen_texts = set()
    valid_rules = []
    
    for rule in rules:
        if not rule.get("description") and not rule.get("source_text"):
            continue
        
        text_key = (rule.get("source_text") or "")[:100]
        if text_key in seen_texts:
            continue
        seen_texts.add(text_key)
        
        valid_rules.append(rule)
    
    return valid_rules


# =====================================================
# MAIN PIPELINE
# =====================================================
def main():
    project_root = Path(__file__).parent.parent
    processed_dir = project_root / "data" / "processed"
    intermediate_dir = project_root / "intermediate"
    
    intermediate_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("BANK POLICY & SYSTEM RULES EXTRACTION")
    print("=" * 60)
    
    # ========== PROCESS POLICY ==========
    policy_file = processed_dir / "policy_extracted.txt"
    
    if policy_file.exists():
        print(f"\n📋 Processing: policy_extracted.txt")
        policy_text = policy_file.read_text(encoding="utf-8")
        print(f"   Characters: {len(policy_text)}")
        
        print("\n🤖 Extracting policy rules...")
        policy_rules = process_text(policy_text, extract_policy_rule, "POLICY")
        print(f"   Extracted {len(policy_rules)} raw rules")
        
        policy_rules = validate_and_dedupe(policy_rules)
        print(f"   Final count: {len(policy_rules)} valid rules")
        
        # Save policy rules
        policy_output = processed_dir / "bank_policy_rules.json"
        with open(policy_output, 'w', encoding='utf-8') as f:
            json.dump(policy_rules, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved: {policy_output}")
    else:
        print(f"\n⚠️ Policy file not found: {policy_file}")
        policy_rules = []
    
    # ========== PROCESS SYSTEM RULES ==========
    system_file = processed_dir / "system_rules_extracted.txt"
    
    if system_file.exists():
        print(f"\n⚙️ Processing: system_rules_extracted.txt")
        system_text = system_file.read_text(encoding="utf-8")
        print(f"   Characters: {len(system_text)}")
        
        print("\n🤖 Extracting system rules...")
        system_rules = process_text(system_text, extract_system_rule, "SYSTEM")
        print(f"   Extracted {len(system_rules)} raw rules")
        
        system_rules = validate_and_dedupe(system_rules)
        print(f"   Final count: {len(system_rules)} valid rules")
        
        # Save system rules
        system_output = processed_dir / "system_rules.json"
        with open(system_output, 'w', encoding='utf-8') as f:
            json.dump(system_rules, f, indent=2, ensure_ascii=False)
        print(f"   ✓ Saved: {system_output}")
    else:
        print(f"\n⚠️ System rules file not found: {system_file}")
        system_rules = []
    
    # ========== SUMMARY ==========
    print("\n" + "=" * 60)
    print("EXTRACTION COMPLETE")
    print("=" * 60)
    
    print(f"\n📊 Summary:")
    print(f"   Policy Rules: {len(policy_rules)}")
    print(f"   System Rules: {len(system_rules)}")
    
    if policy_rules:
        print(f"\n   Policy Thresholds:")
        for rule in policy_rules:
            for t in rule.get("thresholds", []):
                print(f"      - [{rule['rule_id']}] {t.get('human_readable')}")
    
    if system_rules:
        print(f"\n   System Thresholds:")
        for rule in system_rules:
            for t in rule.get("thresholds", []):
                print(f"      - [{rule['rule_id']}] {t.get('human_readable')}")
    
    print(f"\n✅ Output files:")
    print(f"   - {processed_dir}/bank_policy_rules.json")
    print(f"   - {processed_dir}/system_rules.json")
    
    return policy_rules, system_rules


if __name__ == "__main__":
    main()
