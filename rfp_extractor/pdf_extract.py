import pdfplumber
from typing import List
import os
from pdf2image import convert_from_path
import pytesseract

def extract_pdf_text(path: str, ocr_if_empty: bool = True) -> str:
    tc: List[str] = []
    try:
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                pt = p.extract_text() or ""
                tc.append(pt)
    except Exception as e:
        print(f"[pdf_extract] pdfplumber failed for {path}: {e}")

    combined = "\n".join(tc).strip()
    if combined:
        return combined

    if ocr_if_empty:
        print(f"[pdf_extract] No text found in {os.path.basename(path)} — running OCR fallback (this may be slow).")
        images = convert_from_path(path)
        ocr_texts = []
        for i in images:
            ot = pytesseract.image_to_string(i)
            ocr_texts.append(ot)
        return "\n".join(ocr_texts)
    return combined


