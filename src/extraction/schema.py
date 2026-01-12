from dataclasses import dataclass
from typing import Optional

@dataclass
class ExtractedRule:
    rule_id: str
    doc_type: str                 # REGULATION / POLICY / SYSTEM
    rule_type: str                # LIMIT / REQUIREMENT / EXCEPTION

    metric: Optional[str]         # e.g., LTV, INCOME_VERIFICATION
    operator: Optional[str]       # <=, >=, REQUIRED, OPTIONAL
    value: Optional[str]          # e.g., 75%

    raw_text: str                 # original clause text
    source_ref: str               # provenance
    confidence: float
