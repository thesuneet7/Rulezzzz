from docx import Document
from src.schema.document import DocumentElement

def extract_docx(path: str):
    doc = Document(path)
    elements = []

    for i, para in enumerate(doc.paragraphs):
        if len(para.text.strip()) > 40:
            elements.append(
                DocumentElement(
                    text=para.text.strip(),
                    element_type="paragraph",
                    source_ref=f"{path}#paragraph={i}"
                )
            )
    return elements
