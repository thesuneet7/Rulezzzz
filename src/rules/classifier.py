from src.rules.types import RuleType

LIMIT_KEYWORDS = ["must not exceed", "maximum", "limit", "ratio", "percent", "%"]
REQUIREMENT_KEYWORDS = ["must", "mandatory", "required", "shall"]
EXCEPTION_KEYWORDS = ["exception", "override", "approval", "approved by"]

def classify_rule(text: str) -> RuleType:
    text_l = text.lower()

    if any(k in text_l for k in EXCEPTION_KEYWORDS):
        return RuleType.EXCEPTION

    if any(k in text_l for k in LIMIT_KEYWORDS):
        return RuleType.LIMIT

    if any(k in text_l for k in REQUIREMENT_KEYWORDS):
        return RuleType.REQUIREMENT

    return RuleType.OTHER
