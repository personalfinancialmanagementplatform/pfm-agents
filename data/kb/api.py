import os, re
import numpy as np
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer

DB_URL = os.getenv("DB_URL")
engine = create_engine(DB_URL, pool_pre_ping=True)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

app = FastAPI(title="KB RAG API")

class SearchReq(BaseModel):
    query: str
    top_k: int = 5
    level: Optional[str] = "beginner"
    include_related: bool = True

def embed_query(q: str) -> List[float]:
    v = model.encode([q], normalize_embeddings=True)[0]
    return v.astype(np.float32).tolist()

def extract_codes(q: str) -> List[str]:
    return re.findall(r"\b0\d{3}\b", q)

@app.post("/kb/search")
def kb_search(req: SearchReq) -> Dict[str, Any]:
    qvec = embed_query(req.query)
    codes = extract_codes(req.query)

    sql = text("""
    SELECT id, title, level, tags, related, payload, (embedding <=> :qvec) AS distance
    FROM kb_entries
    WHERE (:level IS NULL OR level = :level)
    ORDER BY embedding <=> :qvec
    LIMIT :k
    """)

    with engine.begin() as conn:
        rows = conn.execute(sql, {"qvec": qvec, "level": req.level, "k": req.top_k}).mappings().all()
        if not rows:
            rows = conn.execute(text("""
              SELECT id, title, level, tags, related, payload, (embedding <=> :qvec) AS distance
              FROM kb_entries
              ORDER BY embedding <=> :qvec
              LIMIT :k
            """), {"qvec": qvec, "k": req.top_k}).mappings().all()

        results = [dict(r) for r in rows]

        # 簡單 tags boost：有代碼（0050/0056）就優先
        if codes:
            def score(it):
                tags = it.get("tags") or []
                hit = len(set(tags) & set(codes))
                return (-float(it["distance"])) + 0.2 * hit
            results.sort(key=score, reverse=True)

        related_items = []
        if req.include_related and results:
            rel_ids = results[0].get("related") or []
            if rel_ids:
                rel_rows = conn.execute(
                    text("SELECT id, title, payload FROM kb_entries WHERE id = ANY(:ids)"),
                    {"ids": rel_ids}
                ).mappings().all()
                related_items = [dict(r) for r in rel_rows]

    return {
        "query": req.query,
        "top": results[0] if results else None,
        "candidates": [{"id": r["id"], "title": r["title"], "distance": float(r["distance"])} for r in results],
        "related": related_items
    }
