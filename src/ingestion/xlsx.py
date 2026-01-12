import pandas as pd
from src.schema.document import DocumentElement

def extract_xlsx(path: str):
    elements = []
    sheets = pd.read_excel(path, sheet_name=None)

    for sheet_name, df in sheets.items():
        for idx, row in df.iterrows():
            text = " | ".join(str(v) for v in row.values if pd.notna(v))
            if len(text.strip()) > 40:
                elements.append(
                    DocumentElement(
                        text=text.strip(),
                        element_type="table_row",
                        source_ref=f"{path}#sheet={sheet_name},row={idx}",
                        sheet=sheet_name,
                        row=idx
                    )
                )
    return elements

