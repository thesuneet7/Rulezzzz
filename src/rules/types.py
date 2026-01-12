from enum import Enum

class RuleType(Enum):
    LIMIT = "LIMIT"                 # numeric thresholds
    REQUIREMENT = "REQUIREMENT"     # must / mandatory
    EXCEPTION = "EXCEPTION"         # overrides / approvals
    OTHER = "OTHER"
