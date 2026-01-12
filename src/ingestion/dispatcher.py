import os

from src.ingestion.pdf import extract_pdf
from src.ingestion.docx import extract_docx
from src.ingestion.xlsx import extract_xlsx
from src.schema.document import NormalizedDocument


def ingest_document(path: str, doc_type: str):
    """
    Ingest a document of ANY supported format and normalize it.
    doc_type: REGULATION / POLICY / SYSTEM
    """

    ext = os.path.splitext(path)[1].lower()

    if ext == ".pdf":
        elements = extract_pdf(path)

    elif ext == ".docx":
        elements = extract_docx(path)

    elif ext in [".xlsx", ".xls"]:
        elements = extract_xlsx(path)

    else:
        raise ValueError(f"Unsupported document format: {ext}")

    return NormalizedDocument(
        doc_type=doc_type,
        elements=elements
    )
