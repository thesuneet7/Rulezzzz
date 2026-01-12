import pdfplumber
import pytesseract
from src.schema.document import DocumentElement
from pdfplumber.utils.exceptions import PdfminerException


def extract_pdf(path: str):
    """
    Extract text from PDFs.
    Handles:
    - text-based PDFs
    - scanned/image PDFs via OCR
    - malformed PDFs with OCR fallback
    """

    elements = []

    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text()

                # Treat as scanned if text is missing or too small
                if not text or len(text.strip()) < 50:
                    image = page.to_image(resolution=300).original
                    text = pytesseract.image_to_string(image)

                for para in text.split("\n"):
                    if len(para.strip()) > 40:
                        elements.append(
                            DocumentElement(
                                text=para.strip(),
                                element_type="paragraph",
                                source_ref=f"{path}#page={i+1}",
                                page=i+1
                            )
                        )

    except PdfminerException:
        # Hard fallback: OCR entire document
        try:
            from pdf2image import convert_from_path
            pages = convert_from_path(path, dpi=300)

            for i, img in enumerate(pages):
                text = pytesseract.image_to_string(img)
                for para in text.split("\n"):
                    if len(para.strip()) > 40:
                        elements.append(
                            DocumentElement(
                                text=para.strip(),
                                element_type="paragraph",
                                source_ref=f"{path}#page={i+1}",
                                page=i+1
                            )
                        )
        except Exception as e:
            raise RuntimeError(f"PDF ingestion failed for {path}: {e}")

    return elements

