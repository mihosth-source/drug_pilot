from __future__ import annotations
import os
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv

from formatter import simplify_terms
from prompts import SYSTEM_PROMPT, ANSWER_PROMPT
from retrieve import load_json, retrieve_docs, build_context, detect_drug_name
from safety import detect_risk, emergency_answer

load_dotenv()

DATA_DIR = Path("data")
DRUG_FILE = DATA_DIR / "drug_dataset.json"
PAPER_FILE = DATA_DIR / "paper_chunks.json"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


PAMPHLET_CSS = """
<style>
.main .block-container {max-width: 980px; padding-top: 2rem; padding-bottom: 3rem;}
.pamphlet-wrap {
    background: #ffffff;
    border: 1px solid #d9e2ec;
    border-radius: 18px;
    padding: 28px 28px 18px 28px;
    box-shadow: 0 4px 18px rgba(15, 23, 42, 0.06);
    margin-top: 1rem;
}
.pamphlet-header {
    background: #eef6ff;
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 20px;
    border-left: 6px solid #4f8cc9;
}
.pamphlet-header h2 {margin: 0 0 6px 0; font-size: 1.6rem;}
.pamphlet-header p {margin: 0; color: #4b5563;}
.section-card {
    background: #fafbfd;
    border: 1px solid #e6edf5;
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 14px;
}
.section-card h3 {
    margin: 0 0 10px 0;
    font-size: 1.05rem;
    color: #174f86;
}
.notice-box {
    background: #fff7ed;
    border: 1px solid #fed7aa;
    border-radius: 14px;
    padding: 14px 16px;
    margin-top: 8px;
}
.small-note {font-size: 0.92rem; color: #6b7280;}
</style>
"""


def fallback_sections(user_query: str, docs: list[dict]) -> dict:
    if not docs:
        return {
            "drug_name": "未確認",
            "use": "該当する情報が見つかりませんでした。薬の名前を入れてもう一度お試しください。",
            "mechanism": "",
            "tips": "薬の名前、効能、副作用、飲み方などを入れると見つかりやすくなります。",
            "side_effects": "",
            "consult": "気になる症状があるときは、自己判断せず医師または薬剤師に相談してください。",
            "extra": "",
            "final_note": "この案内は一般的な情報です。実際の使用は、医師・薬剤師の指示を確認してください。",
        }

    public_docs = [d for d in docs if d.get("priority", 3) == 1]
    paper_docs = [d for d in docs if d.get("source_type") == "pubmed_paper"]
    drug_name = detect_drug_name(user_query, docs) or docs[0].get("drug_name", "未確認")

    efficacy = next((d for d in public_docs if "efficacy" in d.get("section", "")), None)
    mechanism = next((d for d in docs if "mechanism" in d.get("section", "")), None)
    usage_docs = [d for d in public_docs if "usage" in d.get("section", "") or "missed_dose" in d.get("section", "")]
    side_effect_docs = [d for d in docs if "side_effect" in d.get("section", "")]
    consult_doc = next((d for d in docs if "consult" in d.get("section", "") or "warning" in d.get("section", "")), None)

    extra_lines = []
    for d in paper_docs[:2]:
        meta_parts = [p for p in [d.get("journal", ""), d.get("year", "")] if p]
        meta = f"（{'、'.join(meta_parts)}）" if meta_parts else ""
        extra_lines.append(f"{simplify_terms(d.get('text', ''))} {meta}".strip())

    return {
        "drug_name": drug_name,
        "use": simplify_terms(efficacy.get("text", "この薬の主な目的に関する公的情報は見つかりませんでした。") if efficacy else "この薬の主な目的に関する公的情報は見つかりませんでした。"),
        "mechanism": simplify_terms(mechanism.get("text", "薬の働き方に関する補足情報は限られています。") if mechanism else "薬の働き方に関する補足情報は限られています。"),
        "tips": "\n".join([f"・{simplify_terms(d.get('text', ''))}" for d in usage_docs[:3]]) or "・飲み方や量は、処方内容や説明書を確認してください。",
        "side_effects": "\n".join([f"・{simplify_terms(d.get('text', ''))}" for d in side_effect_docs[:3]]) or "・副作用が気になるときは、早めに相談してください。",
        "consult": simplify_terms(consult_doc.get("text", "息苦しさ、強い発疹、意識の変化などがあるときは、早めに受診や相談が必要です。") if consult_doc else "息苦しさ、強い発疹、意識の変化などがあるときは、早めに受診や相談が必要です。"),
        "extra": "\n".join([f"・{line}" for line in extra_lines]) or "・読み込まれた論文から追加できる補足情報はありませんでした。",
        "final_note": "この案内は一般的な情報です。実際の使用は、医師・薬剤師の指示を確認してください。",
    }


def llm_answer(user_query: str, docs: list[dict]) -> str:
    if not OPENAI_API_KEY:
        sections = fallback_sections(user_query, docs)
        return build_pamphlet_markdown(sections)

    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    context = build_context(docs)
    prompt = ANSWER_PROMPT.format(user_query=user_query, context=context)

    response = client.responses.create(
        model="gpt-4.1-mini",
        instructions=SYSTEM_PROMPT,
        input=prompt,
    )
    return simplify_terms(response.output_text.strip())


def ensure_sample_files():
    if not DRUG_FILE.exists():
        raise FileNotFoundError("data/drug_dataset.json が見つかりません。")
    if not PAPER_FILE.exists():
        PAPER_FILE.write_text("[]", encoding="utf-8")


def build_pamphlet_markdown(sections: dict) -> str:
    return f"""
# おくすり案内

## この薬の名前
{sections['drug_name']}

## どんなときに使う薬ですか
{sections['use']}

## どのように働きますか
{sections['mechanism']}

## 使うときのポイント
{sections['tips']}

## 気をつけたい副作用
{sections['side_effects']}

## すぐに相談したほうがよい症状
{sections['consult']}

## 参考になる補足情報
{sections['extra']}

## 相談先と最後の案内
{sections['final_note']}
""".strip()


def render_section(title: str, content: str):
    st.markdown(
        f"<div class='section-card'><h3>{title}</h3><div>{content.replace(chr(10), '<br>')}</div></div>",
        unsafe_allow_html=True,
    )


def render_pamphlet(markdown_text: str, query: str):
    lines = [line.rstrip() for line in markdown_text.splitlines()]
    sections = {}
    current = None
    for line in lines:
        if line.startswith("## "):
            current = line.replace("## ", "").strip()
            sections[current] = []
        elif line.startswith("# "):
            continue
        else:
            if current is not None:
                sections[current].append(line)

    normalized = {k: "\n".join(v).strip() for k, v in sections.items()}
    drug_name = normalized.get("この薬の名前", detect_drug_name(query, load_json(DRUG_FILE)) or "おくすり")

    st.markdown("<div class='pamphlet-wrap'>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='pamphlet-header'><h2>{drug_name}</h2><p>一般の方向けに、薬の情報を見やすく整理した案内です。</p></div>",
        unsafe_allow_html=True,
    )
    render_section("どんなときに使う薬ですか", normalized.get("どんなときに使う薬ですか", ""))
    render_section("どのように働きますか", normalized.get("どのように働きますか", ""))
    render_section("使うときのポイント", normalized.get("使うときのポイント", ""))
    render_section("気をつけたい副作用", normalized.get("気をつけたい副作用", ""))
    render_section("すぐに相談したほうがよい症状", normalized.get("すぐに相談したほうがよい症状", ""))
    render_section("参考になる補足情報", normalized.get("参考になる補足情報", ""))
    st.markdown(
        f"<div class='notice-box'><strong>相談先と最後の案内</strong><br>{normalized.get('相談先と最後の案内', '')}</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def main():
    ensure_sample_files()
    st.set_page_config(page_title="薬の一般向けパンフレット作成アプリ", page_icon="💊", layout="wide")
    st.markdown(PAMPHLET_CSS, unsafe_allow_html=True)
    st.title("💊 薬の一般向けパンフレット作成アプリ")
    st.caption("検索した情報を、一般の方向けのパンフレット形式で表示します。")

    with st.sidebar:
        st.subheader("使い方")
        st.write("1. 薬の名前と知りたいことを入力します。")
        st.write("2. 公的情報を優先して、見出し付きの案内として表示します。")
        st.write("3. OPENAI_API_KEY があれば生成整形、なくてもテンプレート形式で動きます。")
        st.divider()
        st.write("入力例")
        st.code("アムロジピンの効能は？")
        st.code("ロキソプロフェンの副作用は？")
        st.code("アセトアミノフェンの飲み方")

    drug_docs = load_json(DRUG_FILE)
    paper_docs = load_json(PAPER_FILE)
    all_docs = drug_docs + paper_docs

    query = st.text_input("薬の名前や知りたいことを入力してください", placeholder="例：アムロジピンの効能は？")
    col1, col2 = st.columns([1, 1])
    run = col1.button("パンフレットを作成", type="primary")
    show_refs = col2.checkbox("参照データを表示", value=False)

    if run and query:
        risk = detect_risk(query)
        if risk == "high":
            st.error(emergency_answer(query))
            return
        elif risk == "medium":
            st.warning("妊娠・授乳・小児・高齢・飲み合わせなどは個別確認が必要なことがあります。以下は一般的な案内です。")

        docs = retrieve_docs(query, all_docs, top_k=8)
        pamphlet_text = llm_answer(query, docs)
        render_pamphlet(pamphlet_text, query)

        st.download_button(
            "パンフレット文面をMarkdownで保存",
            data=pamphlet_text,
            file_name="drug_pamphlet.md",
            mime="text/markdown",
        )

        if show_refs:
            st.subheader("参照したデータ")
            for d in docs:
                with st.container(border=True):
                    st.write({
                        "drug_name": d.get("drug_name", ""),
                        "section": d.get("section", ""),
                        "source_type": d.get("source_type", ""),
                        "source_title": d.get("source_title", ""),
                        "journal": d.get("journal", ""),
                        "year": d.get("year", ""),
                        "url": d.get("url", ""),
                    })
                    st.write(d.get("text", ""))


if __name__ == "__main__":
    main()
