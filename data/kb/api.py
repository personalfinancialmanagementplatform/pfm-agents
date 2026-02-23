# api.py
import os
import re
from typing import Any, Dict, List, Optional

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer

"""
KB RAG API (Postgres + pgvector)

環境變數：
- DB_URL: 例如 postgresql+psycopg2://user:pass@127.0.0.1:5432/pfm_kb

資料表（建議）：
- kb_docs   : 存文件層 metadata（title/tags/source/doc_type/authority...）
- kb_chunks : 存 chunk 層文字與向量（embedding vector(384)）

如果你目前只有 kb_entries 一張表：
請先用我給你的 ingest_kb.py 版本建立 kb_docs/kb_chunks（或自行 migration）。
"""

DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise RuntimeError("請先設定環境變數 DB_URL")

engine = create_engine(DB_URL, pool_pre_ping=True)
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

app = FastAPI(title="KB RAG API", version="1.1.0")


class SearchReq(BaseModel):
    query: str = Field(..., description="使用者問題")
    top_k: int = Field(5, ge=1, le=50, description="回傳最相關 chunk 數")
    candidate_k: int = Field(30, ge=top_k := 5, le=200, description="先抓候選再 rerank（越大越準但越慢）")
    # 不要預設 beginner，避免把資料擋掉；你可以在上游 Orchestrator 自己填
    level: Optional[str] = Field(None, description="beginner / normal / advanced（可空）")
    doc_type: Optional[str] = Field(None, description="knowledge / regulation / news / practice...（可空）")
    include_related: bool = Field(True, description="是否回 related 文件（僅 doc 層）")


def embed_query(q: str) -> List[float]:
    v = model.encode([q], normalize_embeddings=True)[0]
    return v.astype(np.float32).tolist()


def extract_codes(q: str) -> List[str]:
    # 台股 ETF 代碼：0050、0056...
    return re.findall(r"\b0\d{3}\b", q)


@app.get("/")
def root() -> Dict[str, str]:
    return {"status": "ok", "service": "KB RAG API"}


@app.post("/kb/search")
def kb_search(req: SearchReq) -> Dict[str, Any]:
    qvec = embed_query(req.query)
    codes = extract_codes(req.query)

    # 以 chunk 近鄰做檢索，join doc metadata
    # 重要：(:qvec)::vector cast，避免 pgvector 型別問題
    sql = text(
        """
        WITH candidates AS (
          SELECT
            c.chunk_id, c.doc_id, c.chunk_index, c.text AS chunk_text,
            (c.embedding <=> (:qvec)::vector) AS distance
          FROM kb_chunks c
          ORDER BY c.embedding <=> (:qvec)::vector
          LIMIT :ck
        )
        SELECT
          d.doc_id AS id,
          d.title, d.level, d.tags, d.related, d.payload,
          d.doc_type, d.source, d.authority,
          c.chunk_id, c.chunk_index, c.chunk_text, c.distance
        FROM candidates c
        JOIN kb_docs d ON d.doc_id = c.doc_id
        WHERE (:level IS NULL OR d.level = :level)
          AND (:doc_type IS NULL OR d.doc_type = :doc_type)
        ORDER BY c.distance
        LIMIT :k
        """
    )

    with engine.begin() as conn:
        rows = conn.execute(
            sql,
            {
                "qvec": qvec,
                "level": req.level,
                "doc_type": req.doc_type,
                "ck": req.candidate_k,
                "k": req.top_k,
            },
        ).mappings().all()

        results: List[Dict[str, Any]] = [dict(r) for r in rows]

        # rerank：codes / authority 小幅加權（不破壞語意相似主排序）
        if results:
            codes_set = set(codes)

            def rerank_score(it: Dict[str, Any]) -> float:
                # distance 越小越好，所以用 -distance
                base = -float(it["distance"])
                tags = it.get("tags") or []
                hit = len(set(tags) & codes_set) if codes_set else 0
                authority = float(it.get("authority") or 0)
                # 你可以調整權重：codes 命中與權威來源稍微往前
                return base + 0.25 * hit + 0.05 * authority

            results.sort(key=rerank_score, reverse=True)

        top = results[0] if results else None

        related_items = []
        if req.include_related and top:
            rel_ids = top.get("related") or []
            if rel_ids:
                # 注意：cast 成 text[]，避免 ANY 綁參問題
                rel_rows = conn.execute(
                    text(
                        """
                        SELECT doc_id AS id, title, payload, doc_type, source, authority
                        FROM kb_docs
                        WHERE doc_id = ANY((:ids)::text[])
                        """
                    ),
                    {"ids": rel_ids},
                ).mappings().all()
                related_items = [dict(r) for r in rel_rows]

    return {
        "query": req.query,
        "codes": codes,
        "top": (
            {
                "id": top["id"],
                "title": top["title"],
                "level": top.get("level"),
                "doc_type": top.get("doc_type"),
                "source": top.get("source"),
                "authority": top.get("authority"),
                "distance": float(top["distance"]),
                "chunk": {
                    "chunk_id": top.get("chunk_id"),
                    "chunk_index": top.get("chunk_index"),
                    "text": top.get("chunk_text"),
                },
                "payload": top.get("payload"),
            }
            if top
            else None
        ),
        "candidates": [
            {
                "id": r["id"],
                "title": r["title"],
                "distance": float(r["distance"]),
                "chunk_id": r.get("chunk_id"),
                "chunk_index": r.get("chunk_index"),
            }
            for r in results
        ],
        "related": related_items,
    }