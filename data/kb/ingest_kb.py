# ingest_kb.py

import os
import json
import hashlib
from typing import Any, Dict, List

import yaml
import numpy as np
from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer


"""
將 kb.yaml 的 entries 匯入到 Postgres：

- kb_docs：doc 層（metadata）
- kb_chunks：chunk 層（文字 + embedding）

環境變數：
- DB_URL: postgresql+psycopg2://...
- YAML_PATH: 預設 kb.yaml

注意：
- 需要 pgvector extension
- 並確保 kb_chunks.embedding 是 vector(384)
"""

DB_URL = os.getenv("DB_URL")
YAML_PATH = os.getenv("YAML_PATH", "kb.yaml")

if not DB_URL:
    raise RuntimeError("請先 export DB_URL")

# 384 維 embedding
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")


# ===============================
# 將 entry 轉成可檢索文字
# ===============================
def entry_to_doc_text(e: Dict[str, Any]) -> str:
    tags = ", ".join(map(str, (e.get("tags") or [])))
    related = ", ".join(map(str, (e.get("related") or [])))

    key_points = "\n".join(
        [f"- {x}" for x in (e.get("key_points", []) or [])]
    ) or "- （無）"

    pitfalls = "\n".join(
        [f"- {x}" for x in (e.get("pitfalls", []) or [])]
    ) or "- （無）"

    example = e.get("example") or "（無）"
    summary = e.get("summary") or "（無）"

    return (
        f"[ID] {e.get('id')}\n"
        f"[TITLE] {e.get('title')}\n"
        f"[TAGS] {tags}\n"
        f"[LEVEL] {e.get('level')}\n"
        f"[SUMMARY] {summary}\n\n"
        f"[KEY_POINTS]\n{key_points}\n\n"
        f"[EXAMPLE]\n{example}\n\n"
        f"[PITFALLS]\n{pitfalls}\n\n"
        f"[RELATED]\n{related}"
    ).strip()


# ===============================
# 簡易切塊（帶 overlap）
# ===============================
def simple_chunk(
    text: str,
    max_chars: int = 900,
    overlap: int = 120,
) -> List[str]:

    text = (text or "").strip()
    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    start = 0
    n = len(text)

    while start < n:
        end = min(n, start + max_chars)
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == n:
            break

        start = max(0, end - overlap)

    return chunks


# ===============================
# 產生 embedding
# ===============================
def embed(texts: List[str]) -> List[List[float]]:
    vecs = model.encode(texts, normalize_embeddings=True)
    return [v.astype(np.float32).tolist() for v in vecs]


# ===============================
# 產生穩定 chunk_id
# ===============================
def stable_chunk_id(
    doc_id: str,
    idx: int,
    chunk_text: str,
) -> str:
    h = hashlib.sha1(
        f"{doc_id}:{idx}:{chunk_text}".encode("utf-8")
    ).hexdigest()[:16]

    return f"{doc_id}_c{idx}_{h}"


# ===============================
# 建表與索引
# ===============================
def ensure_tables(conn) -> None:

    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS kb_docs (
                doc_id text PRIMARY KEY,
                title text NOT NULL,
                source text,
                url text,
                doc_type text,
                level text,
                tags jsonb DEFAULT '[]'::jsonb,
                related jsonb DEFAULT '[]'::jsonb,
                authority int DEFAULT 0,
                published_at timestamptz,
                payload jsonb DEFAULT '{}'::jsonb,
                created_at timestamptz DEFAULT now(),
                updated_at timestamptz DEFAULT now()
            );
            """
        )
    )

    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS kb_chunks (
                chunk_id text PRIMARY KEY,
                doc_id text REFERENCES kb_docs(doc_id) ON DELETE CASCADE,
                chunk_index int NOT NULL,
                text text NOT NULL,
                embedding vector(384) NOT NULL,
                created_at timestamptz DEFAULT now()
            );
            """
        )
    )

    # 索引
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS kb_docs_doc_type_idx ON kb_docs (doc_type);"
        )
    )

    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS kb_docs_level_idx ON kb_docs (level);"
        )
    )

    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS kb_docs_tags_gin ON kb_docs USING gin (tags);"
        )
    )

    # 向量索引（IVFFLAT）
    conn.execute(
        text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE c.relname = 'kb_chunks_embedding_ivfflat'
                ) THEN
                    CREATE INDEX kb_chunks_embedding_ivfflat
                    ON kb_chunks
                    USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = 100);
                END IF;
            END
            $$;
            """
        )
    )


# ===============================
# 主程式
# ===============================
def main() -> None:

    engine = create_engine(DB_URL, pool_pre_ping=True)

    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "entries" not in data:
        raise RuntimeError("kb.yaml 格式錯誤：最外層需要有 entries:")

    entries: List[Dict[str, Any]] = data["entries"]

    upsert_doc = text(
        """
        INSERT INTO kb_docs
        (doc_id, title, level, tags, related, payload,
         doc_type, source, authority)
        VALUES
        (:doc_id, :title, :level,
         (:tags)::jsonb, (:related)::jsonb, (:payload)::jsonb,
         :doc_type, :source, :authority)
        ON CONFLICT (doc_id) DO UPDATE SET
            title = EXCLUDED.title,
            level = EXCLUDED.level,
            tags = EXCLUDED.tags,
            related = EXCLUDED.related,
            payload = EXCLUDED.payload,
            doc_type = EXCLUDED.doc_type,
            source = EXCLUDED.source,
            authority = EXCLUDED.authority,
            updated_at = now();
        """
    )

    upsert_chunk = text(
        """
        INSERT INTO kb_chunks
        (chunk_id, doc_id, chunk_index, text, embedding)
        VALUES
        (:chunk_id, :doc_id, :chunk_index, :text,
         (:embedding)::vector)
        ON CONFLICT (chunk_id) DO UPDATE SET
            text = EXCLUDED.text,
            embedding = EXCLUDED.embedding;
        """
    )

    with engine.begin() as conn:

        ensure_tables(conn)

        total_chunks = 0

        for e in entries:

            doc_id = e["id"]
            title = e.get("title") or doc_id
            level = e.get("level")
            tags = e.get("tags", []) or []
            related = e.get("related", []) or []

            doc_text = entry_to_doc_text(e)
            chunks = simple_chunk(doc_text)

            if not chunks:
                continue

            # ===== doc upsert =====
            conn.execute(
                upsert_doc,
                {
                    "doc_id": doc_id,
                    "title": title,
                    "level": level,
                    "tags": json.dumps(tags, ensure_ascii=False),
                    "related": json.dumps(related, ensure_ascii=False),
                    "payload": json.dumps(e, ensure_ascii=False),
                    "doc_type": "knowledge",
                    "source": "kb.yaml",
                    "authority": 1,
                },
            )

            # ===== chunk upsert =====
            vecs = embed(chunks)

            for idx, (ch, v) in enumerate(zip(chunks, vecs)):
                conn.execute(
                    upsert_chunk,
                    {
                        "chunk_id": stable_chunk_id(doc_id, idx, ch),
                        "doc_id": doc_id,
                        "chunk_index": idx,
                        "text": ch,
                        "embedding": v,
                    },
                )
                total_chunks += 1

    print(f"OK. upserted {len(entries)} docs, {total_chunks} chunks.")


if __name__ == "__main__":
    main()