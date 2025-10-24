import os
from typing import Optional
import json

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())  

LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "").lower()  

class BaseLLM:
    def extract_json(self, prompt: str) -> Optional[str]:
        raise NotImplementedError

class GeminiLLM(BaseLLM):
    def __init__(self):
        try:
            from google import genai
        except Exception as e:
            raise RuntimeError("google-genai package not installed. Run: pip install google-genai") from e
        self.api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GEMINI_API_KEY or GOOGLE_API_KEY not set in environment. Put it in .env or system env vars."
            )
        try:
            self.client = genai.Client(api_key=self.api_key)
        except TypeError:
            self.client = genai.Client()

    def extract_json(self, prompt: str) -> Optional[str]:
        try:
            resp = self.client.models.generate_content(
                model="gemini-2.5-flash", contents=prompt
            )
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}")
        text = getattr(resp, "text", None) or getattr(resp, "response", None) or str(resp)
        return text

def get_llm_client() -> Optional[BaseLLM]:
    if LLM_PROVIDER == "gemini":
        try:
            return GeminiLLM()
        except Exception as e:
            print(f"[llm_client] Gemini init failed: {e}")
            return None
    if LLM_PROVIDER == "groq":
        try:
            from . import groq_client  
            return groq_client.GroqLLM()
        except Exception as e:
            print(f"[llm_client] Groq init failed: {e}")
            return None

    print("[llm_client] No LLM provider selected (set LLM_PROVIDER env var to 'gemini' or 'groq'). Using rule-based fallback only.")
    return None





