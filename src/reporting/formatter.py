def format_audit_entry(result: dict) -> dict:
    """
    Convert compliance evaluation into audit-friendly structure.
    """

    severity = "LOW"

    if "SYSTEM_TOO_LENIENT" in result["findings"]:
        severity = "HIGH"
    elif "CONTROL_WEAKENED" in result["findings"]:
        severity = "MEDIUM"
    elif "MISSING_SYSTEM" in result["findings"]:
        severity = "HIGH"

    return {
        "regulation": result["regulation_text"],
        "findings": result["findings"],
        "severity": severity,
        "evidence": result["evidence"]
    }
