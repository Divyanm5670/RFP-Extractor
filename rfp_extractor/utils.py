import re
import json
from dateutil import parser as date_parser
from typing import Optional, Dict, Any, List

SCHEMA_FIELDS = [
    "bid_number", "title", "due_date", "bid_submission_type", "term_of_bid",
    "pre_bid_meeting", "installation", "bid_bond_requirement", "delivery_date",
    "payment_terms", "additional_documentation_required", "mfg_for_registration",
    "contract_or_cooperative_to_use", "model_no", "part_no", "product",
    "contact_info", "company_name", "bid_summary", "product_specification", "value"
]

def parse_date(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    try:
        dt = date_parser.parse(text, fuzzy=True, dayfirst=False)
        return dt.date().isoformat()
    except Exception:
        return None

def extract_first_regex(regexes: List[str], text: Any) -> Optional[str]:
    if text is None:
        return None
    if isinstance(text, (list, tuple)):
        text = " ".join([t for t in text if isinstance(t, str)])
    if not isinstance(text, str):
        text = str(text)

    for rx in regexes:
        try:
            m = re.search(rx, text, re.IGNORECASE | re.MULTILINE)
        except re.error:
            continue
        if m:
            try:
                groups = [g for g in m.groups() if g]
                return groups[0].strip() if groups else m.group(0).strip()
            except IndexError:
                try:
                    return m.group(0).strip()
                except Exception:
                    return None
            except Exception:
                try:
                    return m.group(0).strip()
                except Exception:
                    return None
    return None

def safe_extract_json(text: Any) -> Optional[dict]:
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return None
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    obj_matches = re.findall(r"\{(?:[^{}]|\{[^{}]*\})*\}", text, re.DOTALL)
    for j in obj_matches:
        try:
            return json.loads(j)
        except Exception:
            continue
    return None

JUNK_WORDS = {
    "of", "here", "above", "proposed", "the", "this", "is", "are", "for", "as",
    "value", "table", "pricing", "pricing table", "input", "tool", "end of addendum",
    "addendum", "page", "confidential", "attachment", "or", "and"
}

HEADING_NOISE_WORDS = [
    "ADDENDUM", "END OF ADDENDUM", "PAGE", "TABLE OF CONTENTS", "CONTENTS",
    "ATTACHMENT", "EXHIBIT", "SCOPE", "SPECIFICATIONS", "CONFIDENTIAL",
    "NOTICE", "DISCLAIMER"
]

def is_noise_heading(line: str) -> bool:
    if not line or not isinstance(line, str):
        return True
    s = re.sub(r"\s+", " ", line).strip()
    if not s:
        return True
    up = s.upper()
    for kw in HEADING_NOISE_WORDS:
        if kw in up:
            return True
    if len(s) <= 12 and s.upper() == s:
        if re.search(r"\b(ISD|DISTRICT|SCHOOL|UNIVERSITY|COLLEGE)\b", up):
            return False
        return True
    return False

def is_junk_token(val: Optional[str]) -> bool:
    if not val or not isinstance(val, str):
        return True
    s = val.strip().lower()
    if s == "" or all(ch in ".,;:-()[]{}" for ch in s):
        return True
    if s in JUNK_WORDS:
        return True
    if len(s) <= 2:
        return True
    if s in {"or", "and", "the", "a", "an", "to", "of", "for"}:
        return True
    return False

def is_junk_phrase(val: Optional[str]) -> bool:
    if not val or not isinstance(val, str):
        return True
    s = val.strip().lower()
    junk_indicators = [
        "proposed make", "to be included", "for the 'value' field",
        "for the value field", "proposed make and model",
        "as pricing is noted", "see pricing table", "as pricing is noted above",
        "does dallas isd", "under the scope", "product(s) offered",
        "i possess the legal authority", "authorized representative"
    ]
    for ind in junk_indicators:
        if ind in s:
            return True
    return False

def looks_like_identifier(val: Optional[str]) -> bool:
    if not val or not isinstance(val, str):
        return False
    s = val.strip()
    if len(s) < 2 or len(s) > 80:
        return False
    low = s.lower()
    if low in JUNK_WORDS:
        return False
    if is_junk_phrase(s):
        return False
    if re.search(r"\d", s):
        return bool(re.match(r"^[A-Za-z0-9\-\._\/\s]{1,80}$", s))
    if re.match(r"^[A-Za-z\-\._]{2,40}$", s):
        return True
    return False

def looks_like_value(val: Optional[str]) -> bool:
    if not val or not isinstance(val, str):
        return False
    s = val.strip()
    if is_junk_token(s) or is_junk_phrase(s):
        return False
    if re.search(r"[\$\£\€]|usd|inr|rs\.|\bUSD\b|\bINR\b", s.lower()):
        return True
    if re.search(r"\b\d{3,}\b", s.replace(",", "")):
        return True
    if re.match(r"^[\d,\. ]{2,20}$", s):
        return True
    return False

def extract_contact_and_company(text: str) -> Dict[str, Optional[str]]:
    contact = {"contact_name": None, "email": None, "phone": None, "company_name": None}
    if not text or not isinstance(text, str):
        return contact

    email_rx = r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})"
    email = extract_first_regex([email_rx], text)
    if email and not is_junk_token(email):
        contact["email"] = email

    phone_rx = r"(?:\+?\d{1,3}[-\s\.])?(?:\(\d{2,4}\)|\d{2,4})[-\s\.]?\d{3,4}[-\s\.]?\d{3,4}"
    phone = extract_first_regex([phone_rx], text)
    if phone and not is_junk_token(phone):
        contact["phone"] = phone

    org_priority_rx = [
        r"\b(Dallas\s+Independent\s+School\s+District|Dallas\s+ISD)\b",
        r"\b([A-Z][A-Za-z0-9&,\.\- ]{2,120}\b(?:Independent School District|ISD|District|Inc|LLC|Ltd|Co\.|Company|Corporation|Corp|University|College|Authority))\b"
    ]
    for rx in org_priority_rx:
        m = re.search(rx, text, re.IGNORECASE)
        if m:
            cand = m.group(0).strip()
            if len(cand.split()) <= 10 and "?" not in cand and not re.search(r"\b(does|do|is|are|will|can)\b", cand.lower()):
                contact["company_name"] = cand
                break

    if not contact["company_name"]:
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        for ln in lines[:40]:
            if len(ln) > 3 and ln.upper() == ln and len(ln.split()) <= 7 and len(ln) < 90:
                if is_noise_heading(ln):
                    continue
                if re.search(r"\b(ISD|DISTRICT|SCHOOL|INC|LLC|UNIVERSITY|COLLEGE|COMPANY|AUTHORITY)\b", ln.upper()):
                    cand_ln = ln.strip()
                    if re.search(r'\b(i am|i possess|i hereby|authorized representative|thereby affirm|submitter|submitter’s)\b', cand_ln.lower()):
                        continue
                    contact["company_name"] = cand_ln
                    break

    if not contact["company_name"]:
        org_rx = r"\b([A-Z][A-Za-z0-9&,\.\- ]{2,100}\b(?:Inc|LLC|Ltd|Co\.|Company|Corporation|Corp|District|ISD|University|College|Authority))\b"
        orgs = re.findall(org_rx, text)
        if orgs:
            for cand in sorted(orgs, key=lambda s: len(s)):
                if len(cand.split()) <= 8 and "?" not in cand and not re.search(r"\b(does|do|is|are|will|can|does)\b", cand.lower()):
                    if re.search(r'\b(i |we |i am|i possess|authorized representative|thereby affirm)\b', cand.lower()):
                        continue
                    contact["company_name"] = cand.strip()
                    break

    if contact["company_name"] and is_junk_phrase(contact["company_name"]):
        contact["company_name"] = None

    return contact

def extract_product_from_text(text: str, title: Optional[str] = None) -> Optional[str]:
    if not text or not isinstance(text, str):
        return None

    m = re.search(
        r"(including|includes)\s+([A-Za-z0-9 \-,\(\)\/&]+?(?:\b(laptops|desktops|tablet|chromebook|monitor|AIO|device|accessor|display)\b)[A-Za-z0-9 \-,\(\)\/&]*)",
        text, re.IGNORECASE | re.DOTALL
    )
    if m:
        cand = m.group(2).strip()
        cand = re.sub(r"\s+", " ", cand)
        cand = re.sub(r"(,?\s*(etc|and so on|and others)\.?)$", "", cand, flags=re.IGNORECASE).strip()
        if is_junk_phrase(cand):
            return None
        if title and title.strip().lower() in cand.strip().lower():
            cand2 = re.sub(re.escape(title), "", cand, flags=re.IGNORECASE).strip(" ,;-:")
            return cand2[:1000] if cand2 else None
        return cand[:1000]

    m2 = re.search(r"\b(display monitors|monitors|accessories)\s*\(([^)]+)\)", text, re.IGNORECASE)
    if m2:
        cand = m2.group(0).strip()
        if is_junk_phrase(cand):
            return None
        if title and title.strip().lower() in cand.strip().lower():
            return None
        return cand

    list_rx = r"(?m)^(?:-|\u2022|\*)\s*(.+(?:laptop|tablet|monitor|desktop|chromebook|windows|AIO|display|device|accessor).+)$"
    matches = re.findall(list_rx, text, re.IGNORECASE)
    if matches:
        joined = "; ".join(m.strip() for m in matches)
        if is_junk_phrase(joined):
            return None
        if title and title.strip().lower() in joined.strip().lower():
            joined2 = re.sub(re.escape(title), "", joined, flags=re.IGNORECASE).strip(" ,;-:")
            return joined2 if joined2 else None
        return joined[:1000]

    m3 = re.search(r"([A-Z][^.\n]{10,250}\b(?:device|devices|laptop|tablet|monitor|chromebook|desktop|accessor|display).{0,200})", text, re.IGNORECASE | re.DOTALL)
    if m3:
        cand = m3.group(1).strip()
        if re.search(r'\b(affidavit|thereby affirm|i possess|mercury|does not contain|do contain)\b', cand.lower()):
            return None
        if title and title.strip().lower() in cand.strip().lower():
            im = re.search(r"(including|includes)\s+(.{5,200})", cand, re.IGNORECASE)
            if im:
                cand2 = im.group(2).strip()
                return cand2.split(".")[0][:1000]
            return None
        return cand[:1000]

    return None

def rule_based_extract(text: str) -> Dict[str, Any]:
    out = {k: None for k in SCHEMA_FIELDS}
    bid_candidate = extract_first_regex([
        r"\b(?:Bid|RFP|Tender|RFQ)\s*(?:No\.?|Number|#)?\s*[:\-]?\s*([A-Za-z0-9\-/]+)",
        r"\bRef\.\s*([A-Za-z0-9\-/]+)",
        r"\bRFP\s*[:\-]?\s*([A-Za-z0-9\-/]+)"
    ], text)
    if bid_candidate and looks_like_identifier(bid_candidate) and re.search(r"\d", bid_candidate):
        out["bid_number"] = bid_candidate
    else:
        out["bid_number"] = None

    out["title"] = extract_first_regex([
        r"Title[:\s\-]{1,}\s*(.+?)\r?\n",
        r"Subject[:\s\-]{1,}\s*(.+?)\r?\n",
        r"RFP\s+[A-Za-z0-9\-/]+\s*[:\-]\s*(.+?)\r?\n"
    ], text)
    if out["title"]:
        t = re.sub(r"\s+", " ", out["title"]).strip()
        if len(t.split()) > 20 and re.search(r'\b(applicable laws|pursuant to|thereof|hereby|affidavit)\b', t.lower()):
            out["title"] = None
        else:
            out["title"] = t

    due = extract_first_regex([
        r"Due Date[:\s\-]{1,}\s*([A-Za-z0-9,\/\-\s:]+)",
        r"Closing Date[:\s\-]{1,}\s*([A-Za-z0-9,\/\-\s:]+)",
        r"Submission Deadline[:\s\-]{1,}\s*([A-Za-z0-9,\/\-\s:]+)",
        r"Deadline[:\s\-]{1,}\s*([A-Za-z0-9,\/\-\s:]+)"
    ], text)
    out["due_date"] = parse_date(due) if due else None

    out["bid_submission_type"] = extract_first_regex([
        r"Submission Type[:\s\-]{1,}\s*(.+)",
        r"Bid Submission Type[:\s\-]{1,}\s*(.+)",
        r"Submission Instructions[:\s\-]{1,}\s*(.+)"
    ], text)

    out["term_of_bid"] = extract_first_regex([
        r"Term of Bid[:\s\-]{1,}\s*(.+)",
        r"Contract Term[:\s\-]{1,}\s*(.+)",
        r"Term[:\s\-]{1,}\s*(.+ years)"
    ], text)

    out["pre_bid_meeting"] = extract_first_regex([
        r"Pre[-\s]?Bid Meeting[:\s\-]{1,}\s*(.+)",
        r"Pre[-\s]?Bid Conference[:\s\-]{1,}\s*(.+)"
    ], text)

    out["installation"] = extract_first_regex([
        r"Installation[:\s\-]{1,}\s*(.+)",
        r"Installation Requirements[:\s\-]{1,}\s*(.+)"
    ], text)

    out["bid_bond_requirement"] = extract_first_regex([
        r"Bid Bond[:\s\-]{1,}\s*(.+)",
        r"Bid Security[:\s\-]{1,}\s*(.+)"
    ], text)

    out["delivery_date"] = extract_first_regex([
        r"Delivery Date[:\s\-]{1,}\s*([A-Za-z0-9,\/\-\s:]+)",
        r"Anticipated requests.*starting in\s+([A-Za-z0-9,\/\-\s]+)"
    ], text)
    if out["delivery_date"]:
        out["delivery_date"] = parse_date(out["delivery_date"]) or out["delivery_date"]

    out["payment_terms"] = extract_first_regex([
        r"Payment Terms[:\s\-]{1,}\s*(.+)",
        r"Payment[:\s\-]{1,}\s*(\d+\s*days|Net \d+)"
    ], text)

    out["value"] = extract_first_regex([
        r"Estimated Value[:\s\-]{1,}\s*([A-Z\$\d,\. ]+)",
        r"Total Value[:\s\-]{1,}\s*([A-Z\$\d,\. ]+)"
    ], text)

    smart_product = extract_product_from_text(text, title=out.get("title"))
    if smart_product:
        if not is_junk_phrase(smart_product) and not is_junk_token(smart_product):
            out["product"] = smart_product
        else:
            out["product"] = None
    else:
        product_candidate = extract_first_regex([
            r"Product[:\s\-]{1,}\s*(.+?)\r?\n",
            r"Items include[:\s\-]{1,}\s*(.+?)\r?\n"
        ], text)
        if product_candidate and not is_junk_phrase(product_candidate) and not is_junk_token(product_candidate):
            if out.get("title") and out["title"].strip().lower() in product_candidate.strip().lower():
                out["product"] = None
            else:
                out["product"] = product_candidate

    out["model_no"] = extract_first_regex([
        r"Model(?:\s*No\.?| number)?[:\s\-]{1,}\s*([A-Za-z0-9\-\._\/]{2,60})",
        r"Make and Model[:\s\-]{1,}\s*([A-Za-z0-9\-\._\/]{2,60})"
    ], text)

    out["part_no"] = extract_first_regex([
        r"Part(?:\s*No\.?| number)?[:\s\-]{1,}\s*([A-Za-z0-9\-\._\/]{2,60})"
    ], text)

    spec = extract_first_regex([
        r"(?:Specifications|Product Specification|Product Specifications)[:\s\-]{1,}\s*(.+?)(?:\r?\n\r?\n|\Z)",
        r"(?:Minimum|Requires|Requirement|Warranty|Autopilot|Chromebooks|Battery life).*"
    ], text)
    if spec:
        out["product_specification"] = spec.strip()

    docs = []
    docs_rx = r"(Form 1295|Warranty information|deployment service options|Supporting documentation|Company profile|Warranty certificate|Additional warranty information|Signed Addendum No\.\s*\d+)"
    for m in re.finditer(docs_rx, text, re.IGNORECASE):
        try:
            docs.append(m.group(0).strip())
        except Exception:
            continue
    out["additional_documentation_required"] = docs if docs else None

    header_lines = "\n".join([ln.strip() for ln in text.splitlines()[:10] if ln.strip()])
    out["bid_summary"] = (header_lines[:800] + "...") if header_lines else None

    c = extract_contact_and_company(text)
    out["contact_info"] = c
    out["company_name"] = c.get("company_name")

    return out

def clean_and_validate(extracted: Dict[str, Any], original_text: str) -> Dict[str, Any]:
    out = {}
    for k, v in extracted.items():
        if isinstance(v, str):
            s = re.sub(r"\s+", " ", v).strip()
            out[k] = s if s else None
        else:
            out[k] = v

    for fld in ("model_no", "part_no"):
        val = out.get(fld)
        if is_junk_token(val) or (isinstance(val, str) and val.strip().lower() in {"of", "here", "above"}):
            out[fld] = None
        elif val and not looks_like_identifier(val):
            out[fld] = None

    if out.get("product") and out.get("title"):
        try:
            prod = out["product"].strip().lower()
            title = out["title"].strip().lower()
            if prod == title or prod.startswith(title):
                out["product"] = None
        except Exception:
            out["product"] = None

    cn = out.get("company_name")
    if cn and isinstance(cn, str):
        if "?" in cn or re.search(r"\b(does|do|is|are|will|can|relating|relate|regarding|does)\b", cn.lower()):
            m = re.search(r"\b(Dallas\s+Independent\s+School\s+District|Dallas\s+ISD|[A-Z][A-Za-z0-9&,\.\- ]{2,80}\b(?:Inc|LLC|Ltd|Co\.|Company|Corporation|Corp|District|ISD|University|College))\b", original_text, re.IGNORECASE)
            if m:
                out["company_name"] = m.group(0).strip()
            else:
                out["company_name"] = None
        if out.get("company_name") and re.search(r'\b(i am|i possess|authorized representative|thereby affirm|submitter|submitter’s|i hereby)\b', out["company_name"].lower()):
            out["company_name"] = None

    ci = out.get("contact_info") or {}
    if isinstance(ci, dict):
        if not ci.get("company_name") and out.get("company_name"):
            ci["company_name"] = out.get("company_name")
        if not ci.get("email"):
            em = extract_first_regex([r"([A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,})"], original_text)
            if em and not is_junk_token(em):
                ci["email"] = em
        if not ci.get("phone"):
            ph = extract_first_regex([r"(?:\+?\d{1,3}[-\s\.])?(?:\(\d{2,4}\)|\d{2,4})[-\s\.]?\d{3,4}[-\s\.]?\d{3,4}"], original_text)
            if ph and not is_junk_token(ph):
                ci["phone"] = ph
        if ci.get("company_name") and re.search(r'\b(i possess|i am|authorized representative|thereby affirm)\b', str(ci["company_name"]).lower()):
            ci["company_name"] = None
        out["contact_info"] = ci

    val_field = out.get("value")
    if val_field and not looks_like_value(val_field):
        out["value"] = None

    ps = out.get("product_specification")
    if isinstance(ps, str):
        ps = re.sub(r"(\b.+?\b)(?:\s+\1){2,}", r"\1", ps)
        if len(ps) > 1500:
            ps = ps[:1500].rsplit(" ", 1)[0] + "..."
        out["product_specification"] = ps

    ordered = {k: out.get(k, None) for k in SCHEMA_FIELDS}
    return ordered








