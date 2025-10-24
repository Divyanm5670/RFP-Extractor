import os
from rfp_extractor.extractor import batch_extract
from rfp_extractor.llm_client import get_llm_client

def main():
    INPUT_DIR = os.environ.get("RFP_INPUT_DIR", "data")
    OUTPUT_DIR = os.environ.get("RFP_OUTPUT_DIR", "outputs")
    OCR_IF_EMPTY = os.environ.get("ENABLE_OCR", "true").lower() in ("1", "true", "yes")
    
    llm = get_llm_client()
    print(f"[main] Using LLM provider: {os.environ.get('LLM_PROVIDER')}, LLM client: {type(llm).__name__ if llm else 'None'}")
    batch_extract(INPUT_DIR, OUTPUT_DIR, llm_client=llm, ocr_if_empty=OCR_IF_EMPTY)
    print(f"[main] Extraction done. JSON outputs in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()



