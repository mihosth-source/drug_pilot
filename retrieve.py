from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict


def load_json(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def detect_drug_name(user_query: str, all_docs: List[Dict]) -> str:
    candidate_names = sorted(
        {doc.get("drug_name", "") for doc in all_docs if doc.get("drug_name", "")},
        key=len,
        reverse=True,
    )
    uq = (user_query or "").lower()
    for name in candidate_names:
        if name.lower() in uq:
            return name
    return ""


def detect_intent(user_query: str) -> str:
    q = user_query or ""
    if "効能" in q or "何の薬" in q or "目的" in q:
        return "efficacy"
    if "副作用" in q:
        return "side_effect"
    if "飲み忘れ" in q:
        return "missed_dose"
    if "飲み方" in q or "使い方" in q:
        return "usage"
    if "どう働く" in q or "仕組み" in q or "作用" in q:
        return "mechanism"
    return "general"


def retrieve_docs(user_query: str, all_docs: List[Dict], top_k: int = 8) -> List[Dict]:
    drug_name = detect_drug_name(user_query, all_docs)
    intent = detect_intent(user_query)

    filtered = all_docs
    if drug_name:
        filtered = [d for d in filtered if d.get("drug_name", "").lower() == drug_name.lower()]

    scored = []
    query_tokens = [t for t in user_query.lower().replace("?", " ").replace("？", " ").split() if t]

    for doc in filtered:
        score = 0
        haystack = (doc.get("text", "") + " " + doc.get("source_title", "") + " " + doc.get("section", "")).lower()

        if drug_name and doc.get("drug_name", "").lower() == drug_name.lower():
            score += 5
        if intent != "general" and intent in doc.get("section", ""):
            score += 4
        if doc.get("priority", 3) == 1:
            score += 2

        for token in query_tokens:
            if token in haystack:
                score += 1

        scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored[:top_k] if score > 0]


def build_context(docs: List[Dict]) -> str:
    lines = []
    for i, doc in enumerate(docs, start=1):
        lines.append(
            f"[{i}] drug={doc.get('drug_name','')}, section={doc.get('section','')}, "
            f"source={doc.get('source_type','')}, title={doc.get('source_title','')}\n"
            f"{doc.get('text','')}"
        )
    return "\n\n".join(lines)
