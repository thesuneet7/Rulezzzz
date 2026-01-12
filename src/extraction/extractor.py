import re
import uuid
from src.extraction.schema import ExtractedRule
from src.extraction.validators import validate_extracted_rule

def extract_structured_rule(candidate: dict) -> ExtractedRule:
    """
    Convert a rule candidate into a structured ExtractedRule.
    """

    text = candidate["text"]
    rule_type = candidate["rule_type"]

    metric = None
    operator = None
    value = None

    # --- LIMIT rules ---
    if rule_type == "LIMIT":
        if "ltv" in text.lower() or "loan-to-value" in text.lower():
            metric = "LTV"
            operator = "<="
            m = re.search(r'(\d+)\s*(%|percent)', text.lower())
            if m:
                value = m.group(1) + "%"

    # --- REQUIREMENT rules ---
    if rule_type == "REQUIREMENT":
        if "income" in text.lower():
            metric = "INCOME_VERIFICATION"
            operator = "REQUIRED" if "must" in text.lower() else "OPTIONAL"

    # --- EXCEPTION rules ---
    if rule_type == "EXCEPTION":
        operator = "REQUIRES_APPROVAL"
        value = "TRUE"

    rule = ExtractedRule(
        rule_id=str(uuid.uuid4()),
        doc_type=candidate["doc_type"],
        rule_type=rule_type,
        metric=metric,
        operator=operator,
        value=value,
        raw_text=text,
        source_ref=candidate["source_ref"],
        confidence=candidate["confidence"]
    )

    if not validate_extracted_rule(rule):
        return None

    return rule
