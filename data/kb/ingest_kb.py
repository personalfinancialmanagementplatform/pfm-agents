import os, json
import yaml
import numpy as np
from typing import Any, Dict, List

from sqlalchemy import create_engine, text
from sentence_transformers import SentenceTransformer

DB_URL = os.getenv("DB_URL")
YAML_PATH = os.getenv("YAML_PATH", "kb.yaml")

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")  # 384 dims

def entry_to_doc(e: Dict[str, Any]) -> str:
    tags = ", ".join(map(str, (e.get("tags") or [])))
    related = ", ".join(map(str, (e.get("related") or [])))
    key_points = "\n".join([f"- {x}" for x in (e.get("key_points", []) or [])]) or "- （無）"
    pitfalls = "\n".join([f"- {x}" for x in (e.get("pitfalls", []) or [])]) or "- （無）"

    return f"""[ID] {e.get('id')}
[TITLE] {e.get('title')}
[TAGS] {tags}
[LEVEL] {e.get('level')}
[SUMMARY] {e.get('summary')}

[KEY_POINTS]
{key_points}

[EXAMPLE]
{e.get('example')}

[PITFALLS]
{pitfalls}

[RELATED]
{related}
""".strip()

def embed(texts: List[str]) -> List[List[float]]:
    vecs = model.encode(texts, normalize_embeddings=True)
    return [v.astype(np.float32).tolist() for v in vecs]

def main():
    if not DB_URL:
        raise RuntimeError("請先 export DB_URL")

    engine = create_engine(DB_URL, pool_pre_ping=True)

    with open(YAML_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    entries = data["entries"]
    docs = [entry_to_doc(e) for e in entries]
    vecs = embed(docs)

    upsert = text("""
    INSERT INTO kb_entries (id, title, level, tags, related, payload, doc, embedding)
    VALUES (:id, :title, :level, :tags, :related, :payload, :doc, :embedding)
    ON CONFLICT (id) DO UPDATE SET
    title = EXCLUDED.title,
    level = EXCLUDED.level,
    tags = EXCLUDED.tags,
    related = EXCLUDED.related,
    payload = EXCLUDED.payload,
    doc = EXCLUDED.doc,
    embedding = EXCLUDED.embedding
    """)

    with engine.begin() as conn:
        for e, d, v in zip(entries, docs, vecs):
            conn.execute(upsert, {
                "id": e["id"],
                "title": e["title"],
                "level": e.get("level"),
                "tags": json.dumps(e.get("tags", []), ensure_ascii=False),
                "related": json.dumps(e.get("related", []), ensure_ascii=False),
                "payload": json.dumps(e, ensure_ascii=False),
                "doc": d,
                "embedding": v,
            })

    print(f"OK. upserted {len(entries)} entries.")

if __name__ == "__main__":
    main()
