# Project Overview
このプロジェクトは、データサイエンスインターン課題「LLMO用コンテンツ生成システム」の実装を目的とする。  
狙いは、従来のSEO中心記事ではなく、ChatGPT / Claude / Gemini などの生成AIに引用・参照されやすいコンテンツを、再現可能なプロセスで生成・改善できるようにすること。

---

## Why This Project Exists
急成長SaaS企業のマーケティング文脈では、検索行動が「検索エンジン」から「生成AI」へシフトしつつある。  
本課題は、以下を自動化・半自動化するシステム設計力を問う：

- ユーザー意図を受けたトピック設計
- 引用されやすい記事構造への変換
- 生成品質の最低保証（形式要件）
- 思考プロセスを説明できる実装判断

---

## Product Goal
ユーザー入力（キーワード・記事概要）から、以下を提供する：

1. **タイトル候補生成（5〜10件）**
2. **選択タイトルに基づく記事生成（Markdown）**
3. **LLMO要件に対する検査レポート**
4. **（任意）Schema.org JSON-LDの出力**

---

## Scope

### In Scope (MVP)
- ローカル環境で動くプロトタイプ
- タイトル生成 → 本文生成の2段階フロー
- LLMO必須要件の機械検査
- UIでの入力・選択・結果表示

### Out of Scope
- 本番デプロイ
- 大規模RAG基盤
- 完全自動品質保証
- 複雑なユーザー管理や課金機構

---

## Technical Stack (Default)
- **Backend:** Python + FastAPI
- **Frontend:** Streamlit
- **AI Integration:** Gemini API（抽象化によりプロバイダの差し替えが容易な設計）
- **Package Management:** uv
- **Validation:** Pydantic
- **Lint/Format:** Ruff
- **Type Checker:** ty（Astral製の超高速型チェッカーを採用し開発効率を向上）

---

## Directory Blueprint (Recommended)
```kiyono/CLAUDE.md#L1-80
kiyono/
  app/
    main.py
    schemas.py
    config.py
    constants.py  
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
    test_validator.py
    test_api_smoke.py
  README.md
  .env.example
```

---

## LLMO Content Rules (MUST)
記事生成時は以下を必須要件とする。生成指示・検証ロジックの両方で担保すること。

1. **結論先行・高情報密度**
   - 記事の先頭は必ず `h1`（`# タイトル`）から始める
   - 冒頭は挨拶や前置きを禁止し、タイトルへの直接回答（Summary）で開始
   - 抽象的な表現を避け、具体的な一次情報を明記する

2. **厳密な定義**
   - 主要キーワードに対し「Xとは、〜である」の形式を最低1つ以上含める

3. **構造化データ（タグ付けの徹底）**
   - 見出しの内容には箇条書き（`ul`）を積極的に使用して構造を明確化する
   - 比較・選定軸・数値はMarkdown表を利用

4. **FAQセクション**
   - 記事末尾に「一問一答形式」で配置（QとAの間は必ず改行を入れる）
   - AIが要約しやすいよう、各回答（A）は「130〜140文字程度」に制限

---

## Prompt Engineering Policy
- 生成は必ず**2段階**：
  1) タイトル生成  
  2) 本文生成
- システムプロンプトは「禁止事項」「出力形式」「評価観点」を明示
- ユーザープロンプトは入力内容を構造化して渡す
- 出力フォーマットを固定し、後段検査をしやすくする
- 温度や最大トークンは再現性重視で保守的に設定

---

## API Contract (Baseline)

### POST `/generate/titles`
**Input**
- `keyword: str`
- `brief: str`
- `n_titles: int = 8`

**Output**
- `titles: list[str]`
- `rationale: list[str] | None`（任意）

### POST `/generate/article`
**Input**
- `selected_title: str`
- `keyword: str`
- `brief: str`
- `audience: str | None`
- `tone: str | None`

**Output**
- `markdown_article: str`
- `validation_report: dict`
- `json_ld: dict | None`

### GET `/health`
- ヘルスチェック（モデル接続可否を含めても良い）

---

## Validation Policy (Critical)
`llmo_validator` で最低限以下を検査し、機械判定可能にすること：

- H1見出し（`# タイトル`）の存在
- 箇条書き（`ul`）の十分な使用
- 冒頭Summary有無（先頭セクション判定）
- 「とは、〜である」形式の定義文数
- Markdown表の存在（`|` 区切り）
- FAQ見出しとQ/Aペアの存在、および回答の文字数（短すぎず長すぎないか）
- 見出し階層の基本整合（h2/h3）

`validation_report` は以下を含む：
- `passed: bool`
- `checks: list[{name, passed, detail}]`
- `score: int`（任意）
- `missing_actions: list[str]`

---

## Key Architecture & Implementation Decisions (面接アピールポイント)
1. **リソース配分の最適化**
   - コア価値である「バックエンドの生成・検査ロジック」に注力するため、フロントエンド（Streamlit）の実装は生成AI（コーディングエージェント）をフル活用して工数を大幅に削減。
2. **実験の再現性と一元管理**
   - `app/constants.py` を新設し、システムプロンプトや文字数制限などのパラメーターを分離。これにより、プロンプトの微調整や制約のA/Bテストを容易に行える設計とした。
3. **自作バリデーターによる品質保証**
   - LLMの出力を信用しきらず、`app/services/llmo_validator.py` において、正規表現等を駆使した機械的テスト（H1の有無、箇条書きの数、FAQ文字数など）を実装。要件の合否をUI上で可視化し、評価を透明化した。
4. **モダンで高速なツールの採用**
   - パッケージ管理に `uv`、型検査に `ty` を採用し、環境構築と静的解析の待ち時間を極限まで削減。DX（開発体験）の向上を図った。

---

## Coding Standards

### Python
- PEP 8 準拠
- 型ヒント必須
- GoogleスタイルDocstring必須
- Pydanticで入出力検証
- 副作用のある処理はサービス層へ分離

### Error Handling
- 例外は握りつぶさない
- 利用者向けメッセージと開発者向け詳細を分ける
- APIレスポンスの失敗時形式を統一

### Security
- APIキーは `.env` 管理
- シークレットのハードコード禁止
- ログへの機密情報出力禁止

---

## Research & Reference Policy
- Zenn/Qiita/公式ドキュメントを参考にするのは推奨
- ただし**文章の転載・盗用は禁止**
- 参考は構造・視点の抽象化に使う
- 参照元URLと判断理由を必ず記録する

---

## Testing Policy
最低限のテストを用意する：

1. **Validator Unit Test**
   - 要件を満たす記事が pass する
   - 要件欠落記事が fail する

2. **API Smoke Test**
   - `/health`
   - `/generate/titles`
   - `/generate/article`

3. **Prompt Regression (Optional)**
   - 出力形式の崩れを検出する簡易チェック
