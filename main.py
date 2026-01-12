from src.ingestion.dispatcher import ingest_document


reg = ingest_document("data/raw/regulation.pdf", "REGULATION")
pol = ingest_document("data/raw/policy.docx", "POLICY")
sys = ingest_document("data/raw/system_rules.xlsx", "SYSTEM")


print("Regulation elements:", len(reg.elements))
print("Policy elements:", len(pol.elements))
print("System elements:", len(sys.elements))


print("\nSample regulation clause:")
print(reg.elements[0])


from src.rules.candidates import generate_rule_candidates


reg_candidates = generate_rule_candidates(reg)
pol_candidates = generate_rule_candidates(pol)
sys_candidates = generate_rule_candidates(sys)


print("\n--- RULE CANDIDATES ---")
print("Regulation:")
for c in reg_candidates:
   print(c)


print("\nPolicy:")
for c in pol_candidates:
   print(c)


print("\nSystem:")
for c in sys_candidates:
   print(c)




from src.extraction.extractor import extract_structured_rule


structured_rules = []


for c in reg_candidates + pol_candidates + sys_candidates:
   rule = extract_structured_rule(c)
   if rule:
       structured_rules.append(rule)


print("\n--- STRUCTURED RULES ---")
for r in structured_rules:
   print(r)


from src.linking.linker import TraceabilityLinker


linker = TraceabilityLinker(similarity_threshold=0.6)
trace_links = linker.link(structured_rules)


print("\n--- TRACEABILITY LINKS ---")
for t in trace_links:
   print("\nREGULATION:")
   print(t["regulation"].raw_text)


   print("\nPOLICY MATCH:")
   if t["policy"]:
       print(f"  Text: {t['policy']['rule'].raw_text}")
       print(f"  Similarity: {t['policy']['score']}")
   else:
       print("  ❌ No matching policy rule")


   print("\nSYSTEM MATCH:")
   if t["system"]:
       print(f"  Text: {t['system']['rule'].raw_text}")
       print(f"  Similarity: {t['system']['score']}")
   else:
       print("  ❌ No matching system rule")




from src.compliance.engine import evaluate_trace


print("\n--- COMPLIANCE FINDINGS ---")


for t in trace_links:
   result = evaluate_trace(t)


   print("\nREGULATION:")
   print(result["regulation_text"])


   print("FINDINGS:")
   for f in result["findings"]:
       print(f"  - {f}")


   print("EVIDENCE:")
   if result["evidence"]["policy"]:
       print(f"  Policy: {result['evidence']['policy']}")
   else:
       print("  Policy: ❌ Missing")


   if result["evidence"]["system"]:
       print(f"  System: {result['evidence']['system']}")
   else:
       print("  System: ❌ Missing")




from src.reporting.formatter import format_audit_entry
from src.reporting.exporter import export_json_report, export_text_report


audit_entries = []


for t in trace_links:
   result = evaluate_trace(t)
   audit_entries.append(format_audit_entry(result))


export_json_report(audit_entries)
export_text_report(audit_entries)


print("\nAudit reports generated:")
print(" - audit_report.json")
print(" - audit_report.txt")



