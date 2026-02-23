import os
import requests
from typing import Any, Dict, Optional

KB_RAG_API = os.getenv("KB_RAG_API", "http://127.0.0.1:8000")

def kb_search(query: str, top_k: int = 5, level: Optional[str] = "beginner", include_related: bool = True) -> Dict[str, Any]:
    url = f"{KB_RAG_API}/kb/search"
    resp = requests.post(url, json={
        "query": query,
        "top_k": top_k,
        "level": level,
        "include_related": include_related,
    }, timeout=15)
    resp.raise_for_status()
    return resp.json()