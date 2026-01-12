from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DocumentElement:
    text: str
    element_type: str      # paragraph, table_row
    source_ref: str        # file + location
    page: Optional[int] = None
    sheet: Optional[str] = None
    row: Optional[int] = None

@dataclass
class NormalizedDocument:
    doc_type: str          # REGULATION / POLICY / SYSTEM
    elements: List[DocumentElement]
