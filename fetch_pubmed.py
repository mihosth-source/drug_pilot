from __future__ import annotations
import json
import os
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
TOOL_NAME = "drug_chatbot"
EMAIL = os.getenv("NCBI_EMAIL", "your_email@example.com")
API_KEY = os.getenv("NCBI_API_KEY", "")

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def pubmed_search(query: str, retmax: int = 5) -> list[str]:
    url = f"{BASE_URL}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": retmax,
        "retmode": "json",
        "tool": TOOL_NAME,
        "email": EMAIL,
        "sort": "relevance",
    }
    if API_KEY:
        params["api_key"] = API_KEY
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data.get("esearchresult", {}).get("idlist", [])


def pubmed_fetch_details(pmids: list[str]) -> list[dict]:
    if not pmids:
        return []
    url = f"{BASE_URL}/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "tool": TOOL_NAME,
        "email": EMAIL,
    }
    if API_KEY:
        params["api_key"] = API_KEY
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()

    root = ET.fromstring(r.text)
    articles = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//PMID", default="").strip()
        title = article.findtext(".//ArticleTitle", default="").strip()

        abstract_parts = []
        for elem in article.findall(".//Abstract/AbstractText"):
            label = elem.attrib.get("Label", "").strip()
            text = "".join(elem.itertext()).strip()
            if text:
                abstract_parts.append(f"{label}: {text}" if label else text)
        abstract = "\n".join(abstract_parts).strip()

        journal = article.findtext(".//Journal/Title", default="").strip()
        year = article.findtext(".//PubDate/Year", default="").strip()

        articles.append({
            "pmid": pmid,
            "title": title,
            "abstract": abstract,
            "journal": journal,
            "year": year,
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })
    return articles


def fetch_pubmed_for_drug(drug_name: str, keywords: list[str], retmax: int = 5) -> list[dict]:
    papers, seen = [], set()
    for kw in keywords:
        query = f'(\"{drug_name}\"[Title/Abstract]) AND ({kw})'
        pmids = pubmed_search(query, retmax=retmax)
        time.sleep(0.34)
        details = pubmed_fetch_details(pmids)
        time.sleep(0.34)
        for paper in details:
            if paper["pmid"] not in seen:
                seen.add(paper["pmid"])
                paper["drug_name"] = drug_name
                paper["search_keyword"] = kw
                papers.append(paper)
    return papers


def main():
    targets = {
        "acetaminophen": ["mechanism OR patient education OR health literacy OR adverse effects counseling"],
        "loxoprofen": ["mechanism OR patient education OR health literacy OR adverse effects counseling"],
        "amlodipine": ["mechanism OR patient education OR health literacy OR adherence"],
        "magnesium oxide": ["patient education OR adherence OR adverse effects counseling"],
        "amoxicillin": ["patient education OR adherence OR adverse effects counseling"],
    }

    all_papers = []
    for drug, kws in targets.items():
        print(f"Fetching: {drug}")
        all_papers.extend(fetch_pubmed_for_drug(drug, kws, retmax=5))

    out_path = DATA_DIR / "pubmed_papers.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
