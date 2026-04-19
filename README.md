# 薬の一般向け説明チャットボット（最小完成版）

## できること
- `drug_dataset.json` の公的情報サンプルを読み込み、一般向けに説明します。
- `paper_chunks.json` の論文要約があれば、公的情報に補足して表示します。
- 危険な症状が質問に含まれる場合は、安全案内を優先します。
- `OPENAI_API_KEY` があれば生成AIで要約説明を整えます。
- APIキーがなくてもテンプレートモードで動きます。

## フォルダ構成
- `app.py` : Streamlit アプリ本体
- `fetch_pubmed.py` : PubMed から論文情報を取得
- `build_paper_rag.py` : 論文抄録からRAG用要約JSONを作成
- `retrieve.py` : 簡易検索
- `safety.py` : 安全分岐
- `formatter.py` : 用語のやさしい言い換え
- `prompts.py` : 生成時プロンプト
- `data/drug_dataset.json` : 薬剤5種の公的情報サンプル
- `data/paper_chunks.json` : 論文要約サンプル

## 起動方法
### 1. ライブラリを入れる
```bash
python -m pip install -r requirements.txt
```

### 2. アプリを起動する
```bash
python -m streamlit run app.py
```

## OpenAI API を使う場合
`.env` を作成して、次を入れてください。
```env
OPENAI_API_KEY=your_openai_api_key
```

## PubMed取得を使う場合
NCBI の推奨に沿ってメールアドレスを指定してください。必要なら API key も使えます。
`.env` の例:
```env
NCBI_EMAIL=your_email@example.com
NCBI_API_KEY=your_ncbi_api_key
```

### 取得手順
```bash
python fetch_pubmed.py
python build_paper_rag.py
```

## 質問例
- `アムロジピンの効能は？`
- `ロキソプロフェンの副作用は？`
- `アセトアミノフェンはどう働く？`
- `息苦しい`

## 注意
- 収録データは試作用サンプルです。実運用時は PMDA の患者向医薬品ガイド、添付文書、安全性情報などに差し替えてください。
- このアプリは診断や個別の服薬判断を行いません。
