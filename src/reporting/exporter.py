import json
from datetime import datetime

def export_json_report(entries, path="audit_report.json"):
    with open(path, "w") as f:
        json.dump({
            "generated_at": datetime.utcnow().isoformat(),
            "results": entries
        }, f, indent=2)


def export_text_report(entries, path="audit_report.txt"):
    with open(path, "w") as f:
        f.write("=== REGULATORY COMPLIANCE AUDIT REPORT ===\n\n")

        for i, e in enumerate(entries, 1):
            f.write(f"Finding {i}\n")
            f.write("-" * 40 + "\n")
            f.write(f"Regulation:\n{e['regulation']}\n\n")
            f.write(f"Severity: {e['severity']}\n")
            f.write("Findings:\n")

            for finding in e["findings"]:
                f.write(f"  - {finding}\n")

            f.write("\nEvidence:\n")
            f.write(f"  Policy: {e['evidence']['policy'] or '❌ Missing'}\n")
            f.write(f"  System: {e['evidence']['system'] or '❌ Missing'}\n")
            f.write("\n\n")
