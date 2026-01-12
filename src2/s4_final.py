"""
Step 4: Compare Regulatory Rules against Bank Policy and System Rules
Fully generalized, scalable comparison - works with ANY input.
Uses semantic matching for parameter comparison.
"""

import json
import csv
import re
from pathlib import Path
from typing import Optional
from difflib import SequenceMatcher
from concurrent.futures import ThreadPoolExecutor
from langchain_ollama import OllamaLLM

# =====================================================
# CONFIG
# =====================================================
MODEL_NAME = "qwen2.5:3b-instruct"
USE_LLM_FOR_MATCHING = True  # Set to False for pure string matching (faster but less accurate)


# =====================================================
# GENERALIZED PARAMETER MATCHING
# =====================================================
def normalize_text(text: str) -> str:
    """Normalize text for comparison - lowercase, remove special chars."""
    if not text:
        return ""
    return re.sub(r'[^a-z0-9]', '', text.lower())


def get_words(param: str) -> set:
    """Extract meaningful words from a parameter name."""
    if not param:
        return set()
    # Split on underscores, camelCase, numbers
    words = re.split(r'[_\s]+', param.lower())
    # Also split camelCase
    expanded = []
    for word in words:
        expanded.extend(re.findall(r'[a-z]+', word))
    # Filter out very short words and common suffixes
    meaningful = {w for w in expanded if len(w) > 2 and w not in {'max', 'min', 'count', 'ratio', 'value'}}
    return meaningful


def string_similarity(s1: str, s2: str) -> float:
    """Calculate string similarity using multiple methods."""
    if not s1 or not s2:
        return 0.0
    
    n1 = normalize_text(s1)
    n2 = normalize_text(s2)
    
    if not n1 or not n2:
        return 0.0
    
    # Exact match
    if n1 == n2:
        return 1.0
    
    # One contains the other
    if n1 in n2 or n2 in n1:
        return 0.85
    
    # Word overlap (most important for parameter matching)
    words1 = get_words(s1)
    words2 = get_words(s2)
    
    if words1 and words2:
        overlap = words1 & words2
        if overlap:
            jaccard = len(overlap) / len(words1 | words2)
            return max(0.7, jaccard)  # At least 0.7 if any word matches
    
    # Sequence matching as fallback
    return SequenceMatcher(None, n1, n2).ratio()


def parameters_match(param1: str, param2: str, threshold: float = 0.4) -> bool:
    """
    Determine if two parameter names refer to the same concept.
    Uses word-based matching - no hardcoded mappings.
    """
    similarity = string_similarity(param1, param2)
    return similarity >= threshold


def operators_compatible(op1: str, op2: str) -> bool:
    """Check if two operators are of the same type (both max or both min)."""
    if not op1 or not op2:
        return True
    
    op1 = op1.upper()
    op2 = op2.upper()
    
    max_ops = {"LTE", "LT", "<=", "<"}
    min_ops = {"GTE", "GT", ">=", ">"}
    eq_ops = {"EQUALS", "EQ", "=", "=="}
    
    if op1 in max_ops and op2 in max_ops:
        return True
    if op1 in min_ops and op2 in min_ops:
        return True
    if op1 in eq_ops and op2 in eq_ops:
        return True
    
    return False


def normalize_operator(op: str) -> str:
    """Normalize operator to standard form."""
    if not op:
        return ""
    
    op_map = {
        "lte": "<=", "gte": ">=", "lt": "<", "gt": ">",
        "equals": "==", "eq": "==",
        "<=": "<=", ">=": ">=", "<": "<", ">": ">",
        "=": "==", "==": "==",
    }
    return op_map.get(op.lower().strip(), op)


# =====================================================
# THRESHOLD COMPARISON (GENERALIZED)
# =====================================================
def compare_thresholds(
    reg_threshold: dict,
    cmp_threshold: dict
) -> tuple[bool, str]:
    """
    Compare two thresholds. Determines if cmp_threshold is at least as strict.
    Fully generalized - no hardcoded parameter knowledge.
    """
    reg_op = normalize_operator(reg_threshold.get("operator", ""))
    cmp_op = normalize_operator(cmp_threshold.get("operator", ""))
    
    reg_val = reg_threshold.get("value_numeric")
    cmp_val = cmp_threshold.get("value_numeric")
    
    reg_param = reg_threshold.get("parameter", "unknown")
    cmp_param = cmp_threshold.get("parameter", "unknown")
    
    # Handle boolean values
    if isinstance(reg_val, bool) or isinstance(cmp_val, bool):
        if reg_val == cmp_val:
            return True, f"Match: both {reg_val}"
        return False, f"Mismatch: reg={reg_val}, found={cmp_val}"
    
    # Handle None/missing values
    if reg_val is None or cmp_val is None:
        return True, "Cannot compare (missing value)"
    
    # Convert to float
    try:
        reg_val = float(reg_val)
        cmp_val = float(cmp_val)
    except (TypeError, ValueError):
        return True, "Cannot compare (non-numeric)"
    
    # Comparison based on operator type
    if reg_op in ["<=", "<"]:
        # MAX limit - stricter means LOWER value
        if cmp_op in ["<=", "<"]:
            if cmp_val <= reg_val:
                return True, f"OK: {cmp_val} ≤ {reg_val}"
            else:
                return False, f"FAIL: allows {cmp_val}, reg caps at {reg_val}"
    
    elif reg_op in [">=", ">"]:
        # MIN requirement - stricter means HIGHER value
        if cmp_op in [">=", ">"]:
            if cmp_val >= reg_val:
                return True, f"OK: {cmp_val} ≥ {reg_val}"
            else:
                return False, f"FAIL: requires {cmp_val}, reg min is {reg_val}"
    
    elif reg_op == "==":
        if cmp_val == reg_val:
            return True, f"OK: exact match {cmp_val}"
        return False, f"FAIL: {cmp_val} ≠ {reg_val}"
    
    return True, "Review needed (operator mismatch)"


# =====================================================
# LLM-BASED SEMANTIC MATCHING (OPTIONAL, FAST)
# =====================================================
llm = None

def get_llm():
    global llm
    if llm is None:
        llm = OllamaLLM(model=MODEL_NAME, temperature=0)
    return llm


def llm_parameters_match(param1: str, param2: str) -> tuple[bool, float, str]:
    """
    Use LLM to determine if two parameters are semantically related.
    Returns (is_match, confidence, explanation).
    Strict matching - only returns True if absolutely certain.
    """
    prompt = f"""Are these two parameter names referring to EXACTLY the same financial metric or requirement?

Parameter 1: {param1}
Parameter 2: {param2}

Rules:
- Only say "yes" if they are EXACTLY the same concept
- Say "no" if they are different, related but not identical, or if unsure

Respond in this exact format:
ANSWER: yes or no
REASON: one brief sentence explaining why"""
    
    try:
        response = get_llm().invoke(prompt).strip()
        lines = response.split('\n')
        
        answer = "no"
        reason = "Could not determine"
        
        for line in lines:
            if line.upper().startswith("ANSWER:"):
                answer = line.split(":", 1)[1].strip().lower()
            elif line.upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()
        
        is_match = answer.startswith("yes")
        return is_match, 0.9 if is_match else 0.1, reason
    except Exception as e:
        return False, 0.0, f"LLM error: {str(e)}"


# =====================================================
# FIND BEST MATCHING THRESHOLD
# =====================================================
def find_best_match(
    reg_threshold: dict,
    candidate_thresholds: list[dict],
    use_llm: bool = USE_LLM_FOR_MATCHING
) -> Optional[tuple[dict, float]]:
    """
    Find the best matching threshold from candidates.
    Returns (best_match, confidence) or None.
    """
    reg_param = reg_threshold.get("parameter", "")
    reg_op = reg_threshold.get("operator", "")
    
    if not reg_param:
        return None
    
    best_match = None
    best_score = 0.0
    
    for cmp_t in candidate_thresholds:
        cmp_param = cmp_t.get("parameter", "")
        cmp_op = cmp_t.get("operator", "")
        
        if not cmp_param:
            continue
        
        # String similarity score
        str_score = string_similarity(reg_param, cmp_param)
        
        # Operator compatibility bonus
        op_bonus = 0.1 if operators_compatible(reg_op, cmp_op) else 0
        
        total_score = str_score + op_bonus
        
        # If high string similarity, use it directly
        if str_score >= 0.7:
            if total_score > best_score:
                best_match = cmp_t
                best_score = total_score
        
        # If moderate similarity and LLM enabled, verify with LLM
        elif str_score >= 0.3 and use_llm:
            is_match, llm_conf, llm_reason = llm_parameters_match(reg_param, cmp_param)
            if is_match:
                adjusted_score = (str_score + llm_conf) / 2 + op_bonus
                if adjusted_score > best_score:
                    best_match = cmp_t
                    best_match["_llm_reason"] = llm_reason
                    best_score = adjusted_score
    
    if best_match and best_score >= 0.4:
        return best_match, best_score
    
    return None


# =====================================================
# RULE COMPARISON
# =====================================================
def compare_rule(
    reg_rule: dict,
    source_rules: list[dict],
    source_type: str
) -> tuple[str, str]:
    """Compare a regulatory rule against source rules."""
    reg_thresholds = reg_rule.get("thresholds", [])
    
    if not reg_thresholds:
        return "N/A", "No thresholds to compare"
    
    # Collect all thresholds from source rules
    all_source_thresholds = []
    for rule in source_rules:
        for t in rule.get("thresholds", []):
            t_copy = t.copy()
            t_copy["_source_id"] = rule.get("rule_id", rule.get("clause_id", ""))
            all_source_thresholds.append(t_copy)
    
    if not all_source_thresholds:
        return "No", f"No {source_type} rules with thresholds"
    
    # Compare each regulatory threshold
    all_compliant = True
    explanations = []
    
    for reg_t in reg_thresholds:
        param = reg_t.get("parameter", "unknown")
        
        # Find best matching threshold
        match_result = find_best_match(reg_t, all_source_thresholds)
        
        if match_result is None:
            # STRICT: No match = Non-compliant
            all_compliant = False
            explanations.append(f"{param}: ✗ NO MATCHING RULE FOUND - cannot verify compliance")
            continue
        
        matched_t, confidence = match_result
        source_id = matched_t.get("_source_id", "?")
        
        # Compare the thresholds
        is_compliant, explanation = compare_thresholds(reg_t, matched_t)
        
        if is_compliant:
            explanations.append(f"{param} [{source_id}]: ✓ {explanation}")
        else:
            all_compliant = False
            explanations.append(f"{param} [{source_id}]: ✗ {explanation}")
    
    status = "Yes" if all_compliant else "No"
    return status, "; ".join(explanations)


# =====================================================
# MAIN
# =====================================================
def load_json(path: Path) -> list[dict]:
    if not path.exists():
        print(f"⚠️ Not found: {path}")
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "data" / "final_jsons"
    output_dir = project_root / "data" / "final_jsons"
    
    print("=" * 60)
    print("COMPLIANCE COMPARISON ENGINE (GENERALIZED)")
    print("=" * 60)
    
    # Load rules
    print("\n📂 Loading rules...")
    reg_rules = load_json(input_dir / "regulatory_rules.json")
    policy_rules = load_json(input_dir / "bank_policy_rules.json")
    system_rules = load_json(input_dir / "system_rules.json")
    
    print(f"   Regulatory: {len(reg_rules)}")
    print(f"   Policy: {len(policy_rules)}")
    print(f"   System: {len(system_rules)}")
    
    # Compare
    csv_rows = []
    print("\n🔍 Comparing...")
    
    for reg in reg_rules:
        reg_id = reg.get("clause_id", reg.get("rule_id", "?"))
        reg_name = reg.get("regulation_name", reg.get("description", "")[:40])
        
        clause_display = f"{reg_name} ({reg_id})"
        
        policy_status, policy_exp = compare_rule(reg, policy_rules, "policy")
        system_status, system_exp = compare_rule(reg, system_rules, "system")
        
        combined_exp = f"Policy: {policy_exp} | System: {system_exp}"
        
        csv_rows.append({
            "Regulatory Clause": clause_display,
            "Compliant with Bank Policy": policy_status,
            "Compliant with System Rules": system_status,
            "Explanation": combined_exp
        })
        
        p_icon = "✓" if policy_status == "Yes" else ("⚠" if policy_status == "N/A" else "✗")
        s_icon = "✓" if system_status == "Yes" else ("⚠" if system_status == "N/A" else "✗")
        print(f"   [{reg_id}] Policy: {p_icon} | System: {s_icon}")
    
    # Save CSV
    output_csv = output_dir / "compliance_report.csv"
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            "Regulatory Clause",
            "Compliant with Bank Policy", 
            "Compliant with System Rules",
            "Explanation"
        ])
        writer.writeheader()
        writer.writerows(csv_rows)
    
    print(f"\n✅ Saved: {output_csv}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    p_ok = sum(1 for r in csv_rows if r["Compliant with Bank Policy"] == "Yes")
    s_ok = sum(1 for r in csv_rows if r["Compliant with System Rules"] == "Yes")
    total = len(csv_rows)
    
    print(f"\n   Policy: {p_ok}/{total} compliant")
    print(f"   System: {s_ok}/{total} compliant")
    
    # Non-compliant
    p_fail = [r for r in csv_rows if r["Compliant with Bank Policy"] == "No"]
    s_fail = [r for r in csv_rows if r["Compliant with System Rules"] == "No"]
    
    if p_fail:
        print(f"\n⚠️ Policy non-compliant:")
        for r in p_fail:
            print(f"   - {r['Regulatory Clause']}")
    
    if s_fail:
        print(f"\n⚠️ System non-compliant:")
        for r in s_fail:
            print(f"   - {r['Regulatory Clause']}")


if __name__ == "__main__":
    main()
