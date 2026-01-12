"""
FastAPI Backend for Compliance Engine
Upload files and run the compliance pipeline via API
"""

import os
import json
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import sys

# =====================================================
# APP SETUP
# =====================================================
app = FastAPI(
    title="Compliance Engine API",
    description="Upload regulatory, policy, and system files to check compliance",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
PROJECT_ROOT = Path(__file__).parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_FINAL = PROJECT_ROOT / "data" / "final_jsons"

# Session storage (simple in-memory for now)
sessions = {}


# =====================================================
# HELPER FUNCTIONS
# =====================================================
def save_uploaded_file(file: UploadFile, destination: Path) -> Path:
    """Save an uploaded file to disk."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    
    with open(destination, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return destination


def run_pipeline_step(script_name: str) -> tuple[bool, str]:
    """Run a pipeline step and return (success, output)."""
    script_path = PROJECT_ROOT / "src" / script_name
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True
    )
    
    output = result.stdout + result.stderr
    return result.returncode == 0, output


# =====================================================
# ENDPOINTS
# =====================================================
@app.get("/")
async def root():
    """Health check and API info."""
    return {
        "status": "online",
        "name": "Compliance Engine API",
        "version": "1.0.0",
        "endpoints": {
            "POST /upload": "Upload regulation, policy, and system_rules files",
            "POST /process": "Run the full compliance pipeline",
            "GET /results": "Get compliance report (CSV or JSON)",
            "GET /status": "Check pipeline status"
        }
    }


@app.get("/health")
async def health():
    """Simple health check."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/upload")
async def upload_files(
    regulation: UploadFile = File(..., description="Regulation PDF file"),
    policy: UploadFile = File(..., description="Bank policy DOCX file"),
    system_rules: UploadFile = File(..., description="System rules XLSX file")
):
    """
    Upload the 3 required files for compliance checking.
    Accepted formats: PDF for regulation, DOCX for policy, XLSX for system rules.
    """
    try:
        # Validate file types
        if not regulation.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "Regulation file must be a PDF")
        if not policy.filename.lower().endswith((".docx", ".doc")):
            raise HTTPException(400, "Policy file must be a DOCX")
        if not system_rules.filename.lower().endswith((".xlsx", ".xls")):
            raise HTTPException(400, "System rules file must be an XLSX")
        
        # Save files
        reg_path = save_uploaded_file(regulation, DATA_RAW / "regulation.pdf")
        pol_path = save_uploaded_file(policy, DATA_RAW / "policy.docx")
        sys_path = save_uploaded_file(system_rules, DATA_RAW / "system_rules.xlsx")
        
        return {
            "status": "success",
            "message": "Files uploaded successfully",
            "files": {
                "regulation": str(reg_path.name),
                "policy": str(pol_path.name),
                "system_rules": str(sys_path.name)
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")


@app.post("/process")
async def process_files(background_tasks: BackgroundTasks):
    """
    Run the full compliance pipeline on uploaded files.
    This runs all 4 steps: Extract → Regulation → Bank → Compare
    """
    # Check if files exist
    required_files = [
        DATA_RAW / "regulation.pdf",
        DATA_RAW / "policy.docx",
        DATA_RAW / "system_rules.xlsx"
    ]
    
    for f in required_files:
        if not f.exists():
            raise HTTPException(400, f"Missing file: {f.name}. Please upload files first.")
    
    # Run pipeline steps
    steps = [
        ("s1_extract.py", "Extraction"),
        ("s2_llm_process.py", "Regulation Processing"),
        ("s3_bank_ext.py", "Bank Extraction"),
        ("s4_final.py", "Comparison"),
    ]
    
    results = []
    
    for script, name in steps:
        success, output = run_pipeline_step(script)
        results.append({
            "step": name,
            "success": success,
            "output_preview": output[:500] if output else ""
        })
        
        if not success:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "failed",
                    "failed_at": name,
                    "results": results
                }
            )
    
    return {
        "status": "completed",
        "message": "Pipeline completed successfully",
        "results": results,
        "output_file": "data/final_jsons/compliance_report.csv"
    }


@app.get("/results")
async def get_results(format: str = "json"):
    """
    Get the compliance report.
    Query params:
        format: "json" (default) or "csv"
    """
    csv_path = DATA_FINAL / "compliance_report.csv"
    
    if not csv_path.exists():
        raise HTTPException(404, "No results found. Please run /process first.")
    
    if format.lower() == "csv":
        return FileResponse(
            csv_path,
            media_type="text/csv",
            filename="compliance_report.csv"
        )
    
    # Return as JSON
    import csv
    results = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        results = list(reader)
    
    return {
        "status": "success",
        "total_rules": len(results),
        "results": results
    }


@app.get("/results/regulatory")
async def get_regulatory_rules():
    """Get extracted regulatory rules."""
    path = DATA_FINAL / "regulatory_rules.json"
    if not path.exists():
        raise HTTPException(404, "No regulatory rules found")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.get("/results/policy")
async def get_policy_rules():
    """Get extracted bank policy rules."""
    path = DATA_FINAL / "bank_policy_rules.json"
    if not path.exists():
        raise HTTPException(404, "No policy rules found")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.get("/results/system")
async def get_system_rules():
    """Get extracted system rules."""
    path = DATA_FINAL / "system_rules.json"
    if not path.exists():
        raise HTTPException(404, "No system rules found")
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# =====================================================
# RUN SERVER
# =====================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
