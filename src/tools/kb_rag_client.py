# src/tools/kb_rag_client.py
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml


KB_RAG_API = os.getenv("KB_RAG_API", "http://127.0.0.1:8000")
# fallback yaml path（相對於專案根目錄）
KB_YAML_PATH = os.getenv("KB_YAML_PATH", "data/kb/kb.yaml")

# 控制項：demo 時建議保持預設 True
ENABLE_KB_FALLBACK = os.getenv("ENABLE_KB_FALLBACK", "true").lower() in ("1", "true", "yes", "y", "on")
# 你也可以強制只走 fallback（完全不打 API），demo 很穩
FORCE_KB_FALLBACK = os.getenv("FORCE_KB_FALLBACK", "false").lower() in ("1", "true", "yes", "y", "on")

# 快取 YAML（避免每次查詢都讀檔）
_KB_CACHE: Optional[List[Dict[str, Any]]] = None


def _load_kb_yaml(path: str) -> List[Dict[str, Any]]:
    """
    讀 data/kb/kb.yaml，回傳 entries list。
    YAML 結構預期：
    entries:
      - id, tags, title, level, summary, key_points, example, pitfalls, related
    """
    global _KB_CACHE
    if _KB_CACHE is not None:
        return _KB_CACHE

    if not os.path.exists(path):
        _KB_CACHE = []
        return _KB_CACHE

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    entries = data.get("entries") or []
    if not isinstance(entries, list):
        entries = []

    # 只保留 dict
    _KB_CACHE = [e for e in entries if isinstance(e, dict)]
    return _KB_CACHE


def _tokenize(text: str) -> List[str]:
    """
    很輕量的 tokenizer：中英數字混用下，抓出：
    - 連續英文/數字
    - 連續中文（以 2~6 字長度滑窗也不做，先簡化）
    """
    t = (text or "").strip().lower()
    if not t:
        return []
    # 英文/數字 token
    en = re.findall(r"[a-z0-9]+", t)
    # 中文 token（直接把連續中文段當 token）
    zh = re.findall(r"[\u4e00-\u9fff]+", t)
    tokens = en + zh
    # 去重但保序
    seen = set()
    out = []
    for x in tokens:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _count_occurrences(text: str, token: str) -> int:
    """count non-overlapping occurrences; token/text assumed lowercased"""
    if not text or not token:
        return 0
    return text.count(token)


def _bm25_like(tf: int, doc_len: int, avg_len: float, idf: float, k1: float = 1.2, b: float = 0.75) -> float:
    """
    BM25-ish scoring component.
    tf: term frequency in doc (integer)
    doc_len: doc length proxy (integer)
    avg_len: average doc length proxy
    idf: inverse document frequency (float)
    """
    if tf <= 0:
        return 0.0
    denom = tf + k1 * (1.0 - b + b * (doc_len / max(avg_len, 1.0)))
    return idf * ((tf * (k1 + 1.0)) / max(denom, 1e-9))


def _score_entry(query_tokens: List[str], entry: Dict[str, Any]) -> float:
    """
    BM25-ish scoring over YAML entry fields (demo/CPU friendly).
    Fields & weights:
      - title: strongest signal
      - tags: strong exact/partial match signal
      - summary: medium
      - key_points: light

    Returns: higher = more relevant
    """
    title = str(entry.get("title") or "").lower()
    summary = str(entry.get("summary") or "").lower()

    tags = entry.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    tags_l = [str(x).lower() for x in tags]

    key_points = entry.get("key_points") or []
    if not isinstance(key_points, list):
        key_points = []
    kp_text = " ".join([str(x) for x in key_points]).lower()

    # Document length proxy (very rough; good enough for ranking)
    doc_len = len(title) + len(summary) + len(kp_text) + 5 * len(tags_l)

    # average length proxy: since we don't have corpus stats here, use a stable constant
    # (keeps scoring shape consistent; ranking still improves a lot vs naive match)
    avg_len = 400.0

    # Base weights
    W_TITLE = 3.0
    W_SUMMARY = 1.5
    W_KP = 1.0

    score = 0.0

    for tok in query_tokens:
        if not tok:
            continue

        # --- tags boost (acts like high-idf exact match) ---
        # exact match is strongest; partial match also helps
        tag_exact = any(tok == tg for tg in tags_l)
        tag_partial = any(tok in tg for tg in tags_l)

        if tag_exact:
            score += 6.0
        elif tag_partial:
            score += 3.0

        # --- BM25-ish field scoring ---
        # TF by occurrence count
        tf_title = _count_occurrences(title, tok)
        tf_summary = _count_occurrences(summary, tok)
        tf_kp = _count_occurrences(kp_text, tok)

        # Lightweight IDF proxy:
        # if token appears in high-signal places (title/tags), treat it as rarer/more important
        # (No corpus => can't compute real DF; this is a practical stand-in.)
        idf = 1.0
        if tag_exact or tf_title > 0:
            idf = 1.6
        elif tag_partial or tf_summary > 0:
            idf = 1.2

        score += W_TITLE * _bm25_like(tf_title, doc_len, avg_len, idf)
        score += W_SUMMARY * _bm25_like(tf_summary, doc_len, avg_len, idf)
        score += W_KP * _bm25_like(tf_kp, doc_len, avg_len, idf)

    # tiny smoothing to avoid 0 when only punctuation etc.
    return float(score)


def _level_ok(entry_level: str, wanted_level: str) -> bool:
    """
    目前 YAML 內 level 主要是 beginner；先做寬鬆匹配：
    - wanted_level == None 就都收
    - wanted_level != entry_level 時，仍允許進候選，但會降權（在 score 之外處理）
    """
    if not wanted_level:
        return True
    if not entry_level:
        return True
    return True  # 先不嚴格 filter，避免 demo 問題太少命中


def _build_payload(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    knowledge_executor.py 期待 top.payload 裡有：
      summary, key_points, pitfalls, example, title
    """
    return {
        "title": entry.get("title") or "",
        "summary": entry.get("summary") or "",
        "key_points": entry.get("key_points") or [],
        "pitfalls": entry.get("pitfalls") or [],
        "example": entry.get("example") or "",
        "tags": entry.get("tags") or [],
        "level": entry.get("level") or "",
        "related": entry.get("related") or [],
    }


def _in_memory_kb_search(
    query: str,
    top_k: int = 5,
    level: Optional[str] = "beginner",
    include_related: bool = True,
    yaml_path: str = KB_YAML_PATH,
) -> Dict[str, Any]:
    """
    不用 DB、不用 KB API 的 lightweight retrieval：
    - 從 kb.yaml 讀 entries
    - 用 token match 做 scoring
    - 回傳與 KB API 相容的結構
    """
    entries = _load_kb_yaml(yaml_path)
    q_tokens = _tokenize(query)

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for e in entries:
        e_level = str(e.get("level") or "")
        if not _level_ok(e_level, level or ""):
            continue
        s = _score_entry(q_tokens, e)

        # level mismatch 稍微降權（避免完全不命中）
        if level and e_level and (e_level != level):
            s *= 0.85

        if s > 0:
            scored.append((s, e))

    scored.sort(key=lambda x: x[0], reverse=True)

    # candidates
    candidates = []
    for s, e in scored[: max(top_k, 1)]:
        # distance：用 1/(score+1) 映射成「越小越像」的形式，符合你 knowledge_executor 的註解
        dist = 1.0 / (s + 1.0)
        candidates.append(
            {
                "id": e.get("id"),
                "title": e.get("title"),
                "distance": dist,
                "payload": _build_payload(e),
            }
        )

    top = candidates[0] if candidates else None

    # related：如果 include_related，試著把 top 的 related id 也帶出來（能讓 demo 更像真的）
    related_items = []
    if include_related and top:
        rel_ids = (top.get("payload") or {}).get("related") or []
        if isinstance(rel_ids, list) and rel_ids:
            id_map = {str(e.get("id")): e for e in entries if e.get("id")}
            for rid in rel_ids[:5]:
                e = id_map.get(str(rid))
                if not e:
                    continue
                related_items.append(
                    {
                        "id": e.get("id"),
                        "title": e.get("title"),
                        "distance": None,
                        "payload": _build_payload(e),
                    }
                )

    result = {
        "query": query,
        "top": top,
        "candidates": candidates[1:] if len(candidates) > 1 else [],
        "related": related_items,
        "engine": "in_memory_yaml",
    }

    # 新增：給上層做 RAG trace 用
    if top:
        payload = top.get("payload") or {}
        result["trace"] = {
            "engine": "in_memory_yaml",
            "top": {
                "id": top.get("id"),
                "title": top.get("title"),
                "distance": top.get("distance"),
                "summary": payload.get("summary"),
                "key_points": (payload.get("key_points") or [])[:3],
            },
            "candidates_preview": [
                {
                    "id": c.get("id"),
                    "title": c.get("title"),
                    "distance": c.get("distance"),
                }
                for c in (result["candidates"] or [])[:3]
            ],
        }
    else:
        result["trace"] = {
            "engine": "in_memory_yaml",
            "top": None,
            "candidates_preview": [],
        }

    return result


def kb_search(
    query: str,
    top_k: int = 5,
    level: Optional[str] = "beginner",
    include_related: bool = True,
) -> Dict[str, Any]:
    """
    對外統一介面（給 knowledge_executor 用）：

    1) 預設先打 KB API（pgvector/DB 版）
    2) 若 FORCE_KB_FALLBACK=true 或 API 失敗且 ENABLE_KB_FALLBACK=true：
       自動改走 in-memory YAML fallback
    """
    if FORCE_KB_FALLBACK:
        return _in_memory_kb_search(query, top_k=top_k, level=level, include_related=include_related)

    url = f"{KB_RAG_API}/kb/search"
    try:
        resp = requests.post(
            url,
            json={
                "query": query,
                "top_k": top_k,
                "level": level,
                "include_related": include_related,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        # 保底：API 回來結構怪，也別讓 executor 爆
        if not isinstance(data, dict):
            raise ValueError("KB API response is not a dict")

        # executor 需要 top 是 dict 或 None
        top = data.get("top")
        if top is not None and not isinstance(top, dict):
            data["top"] = None

        # engine 標記一下方便 debug
        data.setdefault("engine", "kb_api")
        return data

    except Exception as e:
        if not ENABLE_KB_FALLBACK:
            # 不允許 fallback 就直接把錯往上丟，讓你能看見環境問題
            raise

        fb = _in_memory_kb_search(query, top_k=top_k, level=level, include_related=include_related)
        fb["fallback_reason"] = f"{type(e).__name__}: {str(e)}"
        return fb