import os
import json
from typing import Dict, Any
from .pdf_extract import extract_pdf_text
from .html_extract import extract_html_text
from .llm_client import get_llm_client
from .utils import rule_based_extract, safe_extract_json, clean_and_validate
from tqdm import tqdm

def build_prompt(doc_text: str) -> str:
    schema_keys = [
        "bid_number", "title", "due_date", "bid_submission_type", "term_of_bid",
        "pre_bid_meeting", "installation", "bid_bond_requirement", "delivery_date",
        "payment_terms", "additional_documentation_required", "mfg_for_registration",
        "contract_or_cooperative_to_use", "model_no", "part_no", "product",
        "contact_info", "company_name", "bid_summary", "product_specification", "value"
    ]
    schema = {k: "string or null (or list for additional_documentation_required or object for contact_info)" for k in schema_keys}
    prompt = (
        "You are a strict data extraction assistant. Given the provided RFP/addendum text, "
        "return only a single JSON object with the following EXACT keys (use null for missing values):\n\n"
    )
    prompt += json.dumps(schema, indent=2)
    prompt += (
        "\n\nConstraints:\n"
        "1) Return ONLY the JSON object, nothing else (no commentary, no backticks).\n"
        "2) model_no and part_no must be short identifiers (e.g., 'XJ-200', 'PN-54321') — do NOT return long sentences. If not present, set null.\n"
        "3) additional_documentation_required must be a list of short strings or null.\n"
        "4) contact_info must be an object with keys: contact_name, email, phone, company_name (use null for missing subfields).\n"
        "5) product_specification: if present, return a concise summary (max ~300 words). Do NOT copy the entire document.\n"
        "6) company_name: prefer organization names (e.g., 'Dallas ISD', 'ACME Corp').\n"
        "7) For dates return ISO format YYYY-MM-DD when possible, else return a short understandable string.\n"
        "8) Do NOT invent values. If uncertain, use null.\n\n"
        "Now extract from the document text between the markers below.\n\n"
        "DOCUMENT BEGIN\n---START---\n"
    )
    
    prompt += doc_text[:50000]
    prompt += "\n---END---\nDOCUMENT END\n\nReturn only the JSON object."
    return prompt

def extract_from_file(path: str, llm_client=None, ocr_if_empty=True) -> Dict[str, Any]:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        text = extract_pdf_text(path, ocr_if_empty=ocr_if_empty)
    elif ext in (".html", ".htm"):
        text = extract_html_text(path)
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    rule_res = rule_based_extract(text)

    llm_res = None
    if llm_client:
        prompt = build_prompt(text)
        try:
            raw = llm_client.extract_json(prompt)
            parsed = safe_extract_json(raw or "")
            if isinstance(parsed, dict):
                llm_res = parsed
            else:
                llm_res = None
        except Exception as e:
            print(f"[extractor] LLM extraction error for {os.path.basename(path)}: {e}")
            llm_res = None

    merged = {}
    for k in rule_res.keys():
        v_rule = rule_res.get(k)
        v_llm = None
        if llm_res:
            v_llm = llm_res.get(k) if isinstance(llm_res, dict) else None
        if v_llm is not None:
            merged[k] = v_llm
        else:
            merged[k] = v_rule

    merged["_source_file"] = os.path.basename(path)
    merged["_rule_extracted"] = rule_res
    merged["_llm_used"] = bool(llm_res)

    cleaned = clean_and_validate(merged, text)
    return cleaned

def batch_extract(input_dir: str, output_dir: str, llm_client=None, ocr_if_empty=True):
    os.makedirs(output_dir, exist_ok=True)
    files = [os.path.join(input_dir, f) for f in os.listdir(input_dir)
             if f.lower().endswith((".pdf", ".html", ".htm", ".txt"))]
    for f in tqdm(files, desc="Processing files"):
        try:
            res = extract_from_file(f, llm_client=llm_client, ocr_if_empty=ocr_if_empty)
            out_path = os.path.join(output_dir, os.path.splitext(os.path.basename(f))[0] + ".json")
            with open(out_path, "w", encoding="utf-8") as fw:
                json.dump(res, fw, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[batch_extract] Failed on {f}: {e}")
 
     




