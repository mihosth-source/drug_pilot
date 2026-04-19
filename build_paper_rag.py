from __future__ import annotations
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_DIR = Path("data")
INPUT_FILE = DATA_DIR / "pubmed_papers.json"
OUTPUT_FILE = DATA_DIR / "paper_chunks.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def simple_fallback_summary(title: str, abstract: str) -> str:
    text = abstract.strip() if abstract.strip() else title.strip()
    if len(text) > 700:
        text = text[:700] + "..."
    return text


def llm_summary(title: str, abstract: str) -> str:
    if not OPENAI_API_KEY:
        return simple_fallback_summary(title, abstract)

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = f"""
以下の医学論文情報を、日本の一般市民向け薬説明チャットボット用に要約してください。

条件:
- 120〜180字程度
- 効能を断定しすぎない
- 一般向け説明に役立つ範囲に限定する
- 研究条件付きの内容なら、その旨がわかるようにする
- 難しい専門用語はできるだけ避ける

論文タイトル:
{title}

抄録:
{abstract}
"""
    response = client.responses.create(model="gpt-4.1-mini", input=prompt)
    return response.output_text.strip()


def detect_section(text: str) -> str:
    lower = text.lower()
    if "mechanism" in lower:
        return "mechanism"
    if "adverse" in lower or "side effect" in lower:
        return "side_effect_support"
    if "adherence" in lower or "patient education" in lower or "health literacy" in lower:
        return "education_support"
    return "paper_support"


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE} がありません。先に fetch_pubmed.py を実行してください。")

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        papers = json.load(f)

    chunks = []
    for paper in papers:
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        summary = llm_summary(title, abstract)
        chunks.append({
            "drug_name": paper.get("drug_name", ""),
            "section": detect_section((title + " " + abstract)),
            "source_type": "pubmed_paper",
            "source_title": title,
            "text": summary,
            "pmid": paper.get("pmid", ""),
            "journal": paper.get("journal", ""),
            "year": paper.get("year", ""),
            "url": paper.get("url", ""),
            "priority": 2,
        })

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
