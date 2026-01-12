"""
Main Pipeline Orchestrator
Runs all 4 steps sequentially: Extract → Regulation Processing → Bank Extraction → Comparison
"""

import subprocess
import sys
from pathlib import Path


def run_step(script_name: str, description: str) -> bool:
    """Run a Python script and return success status."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    script_path = Path(__file__).parent / "src" / script_name
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=Path(__file__).parent
    )
    
    if result.returncode != 0:
        print(f"❌ {script_name} failed with code {result.returncode}")
        return False
    
    return True


def run_pipeline():
    """Run the complete compliance pipeline."""
    print("\n" + "="*60)
    print("🏦 COMPLIANCE ENGINE - FULL PIPELINE")
    print("="*60)
    
    steps = [
        ("s1_extract.py", "Step 1: Extracting documents (PDF, DOCX, XLSX)"),
        ("s2_llm_process.py", "Step 2: Processing regulatory clauses"),
        ("s3_bank_ext.py", "Step 3: Extracting bank policy & system rules"),
        ("s4_final.py", "Step 4: Comparing compliance"),
    ]
    
    for script, description in steps:
        success = run_step(script, description)
        if not success:
            print(f"\n❌ Pipeline failed at: {script}")
            return False
    
    print("\n" + "="*60)
    print("✅ PIPELINE COMPLETE")
    print("="*60)
    print("\n📊 Output files:")
    print("   - data/final_jsons/regulatory_rules.json")
    print("   - data/final_jsons/bank_policy_rules.json")
    print("   - data/final_jsons/system_rules.json")
    print("   - data/final_jsons/compliance_report.csv")
    
    return True


if __name__ == "__main__":
    success = run_pipeline()
    sys.exit(0 if success else 1)
