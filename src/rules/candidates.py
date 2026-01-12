from typing import List
from src.schema.document import NormalizedDocument
from src.rules.classifier import classify_rule
from src.rules.types import RuleType

def generate_rule_candidates(doc: NormalizedDocument) -> List[dict]:
    """
    Generate candidate rules from a normalized document.
    """

    candidates = []

    for el in doc.elements:
        rule_type = classify_rule(el.text)

        # Filter out non-rules
        if rule_type == RuleType.OTHER:
            continue

        confidence = estimate_confidence(el.text, rule_type)

        candidates.append({
            "text": el.text,
            "doc_type": doc.doc_type,
            "rule_type": rule_type.value,
            "confidence": confidence,
            "source_ref": el.source_ref
        })

    return candidates


def estimate_confidence(text: str, rule_type: RuleType) -> float:
    """
    Simple heuristic confidence score.
    """
    score = 0.5

    if rule_type == RuleType.LIMIT:
        if "%" in text or "percent" in text.lower():
            score += 0.3

    if rule_type == RuleType.REQUIREMENT:
        if "must" in text.lower() or "shall" in text.lower():
            score += 0.3

    if rule_type == RuleType.EXCEPTION:
        if "approval" in text.lower():
            score += 0.3

    return min(score, 1.0)
