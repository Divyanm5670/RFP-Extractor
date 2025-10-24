from bs4 import BeautifulSoup
from typing import List

def extract_html_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        html = f.read()
    soup = BeautifulSoup(html, "lxml")
    for s in soup(["script", "style", "noscript"]):
        s.extract()
    t = soup.get_text(separator="\n")
    l = [line.strip() for line in t.splitlines() if line.strip()]
    return "\n".join(l)







