from src.compliance.findings import FindingType

def evaluate_trace(trace: dict) -> dict:
    """
    Evaluate compliance for one regulation trace.
    """

    reg = trace["regulation"]
    pol = trace["policy"]["rule"] if trace["policy"] else None
    sys = trace["system"]["rule"] if trace["system"] else None

    findings = []

    # --- Missing enforcement ---
    if not pol:
        findings.append(FindingType.MISSING_POLICY)

    if not sys:
        findings.append(FindingType.MISSING_SYSTEM)

    # --- Numeric limit checks ---
    if reg.rule_type == "LIMIT":
        if not sys:
            findings.append(FindingType.MISSING_SYSTEM)

        elif sys.rule_type != "LIMIT":
            # System uses override instead of numeric enforcement
            findings.append(FindingType.SYSTEM_TOO_LENIENT)

        elif reg.value and sys.value:
            reg_val = int(reg.value.replace("%", ""))
            sys_val = int(sys.value.replace("%", ""))

            if sys_val > reg_val:
                findings.append(FindingType.SYSTEM_TOO_LENIENT)


    # --- Control strength checks ---
    if reg.rule_type == "REQUIREMENT":
        if sys and reg.operator == "REQUIRED":
            if sys.operator == "OPTIONAL":
                findings.append(FindingType.CONTROL_WEAKENED)

    # --- Final classification ---
    if not findings:
        findings.append(FindingType.COMPLIANT)

    return {
        "regulation_text": reg.raw_text,
        "findings": [f.value for f in findings],
        "evidence": {
            "policy": pol.raw_text if pol else None,
            "system": sys.raw_text if sys else None
        }
    }
