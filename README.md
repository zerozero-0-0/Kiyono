# LLMO Content Generator (Intern Coding Challenge)

LLMO（Large Language Model Optimization）向けに、**生成AIに引用・参照されやすい記事**を作るためのプロトタイプです。  
ユーザーが入力したキーワード・概要から、以下を行います。

1. タイトル案（5〜10件）の生成  
2. 選択タイトルに基づく記事本文（Markdown）の生成  
3. LLMO要件のバリデーション結果の表示  
4. （任意）Schema.org JSON-LDの出力  

---

## 1. Project Goals

### 背景
従来のSEO中心のコンテンツ制作から、ChatGPT / Claude / Gemini などの生成AIに引用されることを前提とした設計へシフトする必要があります。

### 目的
- 記事企画〜生成の試行錯誤を高速化する
- LLMO向けの構造化ルールを生成時に強制する
- 面接で説明可能な「設計意図・工夫・判断」を残す

### 非目的
- 本番デプロイ
- 大規模RAGシステム構築
- 完全自動の品質保証

---

## 2. Core Features (MVP)

- 入力フォーム
  - キーワード（例: プロジェクト管理、営業DX）
  - 記事概要（想定読者・課題・伝えたい価値）
- タイトル生成
  - 5〜10件を提案
- 本文生成
  - Summary先行
  - 明確な定義（「Xとは、〜である」）
  - 箇条書き・表の活用
  - FAQを末尾に配置
- バリデーション
  - LLMO要件を満たしているかを機械判定して可視化

---

## 3. Repository Structure (Planned)

```kiyono/README.md#L1-40
kiyono/
  app/
    main.py
    config.py
    schemas.py
    services/
      llm_client.py
      title_generator.py
      article_generator.py
      llmo_validator.py
      jsonld_generator.py
  frontend/
    app.py
  prompts/
    title_system.txt
    title_user.txt
    article_system.txt
    article_user.txt
  docs/
    plan.md
    decisions.md
    experiments.md
    references.md
  tests/
    test_api_smoke.py
    test_validator.py
  .env.example
  pyproject.toml
  CLAUDE.md
  README.md
```

---

## 4. Tech Stack

- Backend: `FastAPI`
- Frontend: `Streamlit`
- LLM: `Gemini API`（将来的に他プロバイダ差し替えを想定）
- Package Manager: `uv`
- Validation: `Pydantic`
- Lint/Format: `Ruff`

---

## 5. Setup

## 前提
- Python 3.11+ 推奨
- `uv` インストール済み

## 初期化（予定コマンド）
```kiyono/README.md#L1-20
uv venv
source .venv/bin/activate
uv pip install -e .
```

## 環境変数
`.env` を作成（`.env.example` をコピー）

```kiyono/README.md#L1-10
GEMINI_API_KEY=your_api_key_here
APP_ENV=local
LOG_LEVEL=INFO
```

---

## 6. Run (Planned)

## Backend
```kiyono/README.md#L1-10
uv run uvicorn app.main:app --reload --port 8000
```

## Frontend
```kiyono/README.md#L1-10
uv run streamlit run frontend/app.py
```

アクセス:
- API Docs: `http://localhost:8000/docs`
- UI: `http://localhost:8501`

---

## 7. API Design (Baseline)

### `GET /health`
- ヘルスチェック

### `POST /generate/titles`
Input:
- `keyword: str`
- `brief: str`
- `n_titles: int` (default: 8)

Output:
- `titles: list[str]`

### `POST /generate/article`
Input:
- `selected_title: str`
- `keyword: str`
- `brief: str`
- `audience: str | null`
- `tone: str | null`

Output:
- `markdown_article: str`
- `validation_report: dict`
- `json_ld: dict | null`

---

## 8. LLMO Rules (Must Have)

1. 結論先行（Summaryで開始）
2. 厳密な定義（「Xとは、〜である」）
3. 構造化（箇条書き + 表）
4. FAQ（記事末尾）

---

## 9. Development Policy

- 小さな単位で実装
- 変更理由を `docs/decisions.md` に記録
- 最短動線（入力→生成→表示）を先に完成
- その後に品質改善（validator・実験・UI改善）

---

## 10. Minimal-Diff Commit Strategy

実装時は**最小差分コミット**を徹底します。

例:
- `docs: add initial README and planning docs`
- `chore: bootstrap project with uv and pyproject`
- `feat: add FastAPI app with health endpoint`
- `feat: implement title generation endpoint`
- `feat: implement article generation endpoint`
- `feat: add llmo validator and report`
- `feat: connect streamlit ui to backend api`
- `test: add smoke tests for core endpoints`
- `docs: add experiment notes and interview talking points`

---

## 11. Milestones (2 Weeks)

- Day 1-2: 要件整理・ドキュメント整備・骨組み作成
- Day 3-5: タイトル生成API + UI接続
- Day 6-9: 本文生成 + LLMO制約反映
- Day 10-11: バリデータ実装 + 比較実験
- Day 12-14: 仕上げ・デモ準備・想定問答整理

---

## 12. Interview Readiness Checklist

- [ ] なぜ2段階生成にしたか説明できる
- [ ] LLMO要件をどう担保したか説明できる
- [ ] 参考記事の採用/不採用理由を説明できる
- [ ] 制約下での優先順位と妥協点を説明できる
- [ ] 実装デモを迷わず再現できる

---

## 13. Notes

このリポジトリは、**完成度だけでなく思考過程を示す**ことを重視します。  
「動く実装」と「説明できる判断」をセットで残す方針で進めます。