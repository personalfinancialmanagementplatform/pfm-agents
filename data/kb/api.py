import os, re
import numpy as np
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer  

DB_URL = os.getenv("DB_URL")     # 從環境變數讀取資料庫網址
if not DB_URL:
    raise ValueError("DB_URL is not set") 


engine = create_engine(DB_URL, pool_pre_ping=True)  # 建立SQLAlchemy資料庫連線引擎，連線前先Ｐing一下
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2") # 載入embeddibngmodel ，程式啟動時就載入模型並非每次呼叫api才仔入

app = FastAPI(title="KB RAG API")
 
# request schema 
class SearchReq(BaseModel):      
    query: str
    top_k: int = 5
    level: Optional[str] = None
    include_related: bool = True

def embed_query(q: str) -> List[float]:        #embedding函式
    v = model.encode([q], normalize_embeddings=True)[0]
    return v.astype(np.float32).tolist()

#def extract_codes(q: str) -> List[str]:   #代碼抽取
#    return re.findall(r"\b0\d{3}\b", q)   #正規表達式

#	1.	先用 regex 抓疑似代碼
#	2.	再跟 KB tags / symbol 欄位交叉比對
#	3.	只把真的存在於知識庫的代碼當成代碼

def extract_codes(q: str) -> List[str]:
    # 抓 4~6 位純數字，去重但保留順序
    matches = re.findall(r"\b\d{4,6}\b", q)
    seen = set()
    codes = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            codes.append(m)
    return codes

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
