# RFP Extractor

A Python tool to extract structured RFP (Request for Proposal) data from PDF and HTML documents using rule-based logic and Gemini LLM.

---

## Features
- Extracts RFP fields such as bid number, title, due date, contact info, product details, and more.
- Supports **PDF (with optional OCR)** and **HTML** files.
- Combines rule-based extraction with **Gemini LLM** for enhanced accuracy.
- Outputs structured **JSON files** per document.

---

## Requirements
- Python 3.9+
- Packages:
  - `pdfplumber`
  - `pdf2image`
  - `pytesseract`
  - `beautifulsoup4`
  - `lxml`
  - `tqdm`
  - `python-dotenv`
  - `google-genai`
- **Tesseract OCR** installed (for PDF OCR support)

---

## Installation & Usage

1. **Clone the repository**  
```bash
git clone https://github.com/Divyanm5670/RFP-Extractor.git
cd RFP-Extractor
```

 2. **Create a virtual environment**
```bash
python -m venv venv
```

 3. **Activate the virtual environment**

 Windows (PowerShell)
```bash
.\venv\Scripts\Activate.ps1
```

 Linux / MacOS
```bash
source venv/bin/activate
```

 4. **Install dependencies**
```bash
pip install -r requirements.txt
```

 5. **Run the extractor**
```bash
python extract.py
```
