# RFP Extractor

A Python tool to extract structured RFP (Request for Proposal) data from PDF, HTML, and TXT documents using rule-based logic and Gemini LLM.

---

## Features
- Extracts RFP fields like bid number, title, due date, contact info, product details, etc.
- Supports PDFs (with optional OCR), HTML, and plain text files.
- Combines rule-based extraction with Gemini LLM for enhanced accuracy.
- Outputs structured JSON files per document.

---

## Requirements
- Python 3.9+
- Packages: `pdfplumber`, `pdf2image`, `pytesseract`, `beautifulsoup4`, `lxml`, `tqdm`, `python-dotenv`, `google-genai`
- Tesseract OCR installed (for PDF OCR support)

```bash
pip install -r requirements.txt
