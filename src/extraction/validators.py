def validate_extracted_rule(rule):
    """
    Ensures extracted rule is well-formed.
    """

    if rule.rule_type == "LIMIT":
        if rule.metric is None or rule.value is None:
            return False

    if rule.rule_type == "REQUIREMENT":
        if rule.metric is None or rule.operator is None:
            return False

    return True
