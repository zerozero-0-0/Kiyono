# Project Overview
このプロジェクトは、データサイエンスインターン課題「課題2：LLMO用コンテンツ生成システム」の実装を目的とする。  
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

## Evaluation Mindset (Interview-Oriented)
この課題は「完璧なプロダクト」より、以下が重視される：

- 何を優先したか（優先順位設計）
- なぜその方式にしたか（意思決定理由）
- 制約下でどう実装を成立させたか（実行力）
- 参考情報をどう取捨選択したか（適応力）

**したがって、実装と同じくらい `docs/` の意思決定ログが重要。**

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
- **AI Integration:** Gemini API（将来 OpenAI/Anthropic へ差し替え可能な抽象化）
- **Package Management:** uv
- **Validation:** Pydantic
- **Lint/Format:** Ruff（必要に応じて型検査を追加）

---

## Directory Blueprint (Recommended)
```kiyono/CLAUDE.md#L1-80
kiyono/
  app/
    main.py
    schemas.py
    config.py
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
   - 冒頭は挨拶や前置き禁止
   - タイトルへの直接回答（Summary）で開始

2. **厳密な定義**
   - 主要キーワードに対し「Xとは、〜である」の形式を最低1つ以上含める

3. **構造化データ**
   - 箇条書きはMECEを意識
   - 比較・選定軸・数値はMarkdown表を利用

4. **FAQセクション**
   - 記事末尾に想定質問と簡潔回答を配置

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

- 冒頭Summary有無（先頭セクション判定）
- 「とは、〜である」形式の定義文数
- Markdown表の存在（`|` 区切り）
- FAQ見出しとQ/Aペアの存在
- 見出し階層の基本整合（h2/h3）

`validation_report` は以下を含む：
- `passed: bool`
- `checks: list[{name, passed, detail}]`
- `score: int`（任意）
- `missing_actions: list[str]`

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

## Autonomous Coding-Agent Operating Rules
コーディングエージェントは以下に従って自走すること。

1. **Plan First**
   - 実装前に `docs/plan.md` を更新し、目的・範囲・優先順位を明示する。

2. **Thin Vertical Slice**
   - まず「入力→タイトル→記事→表示」の最短動線を完成させる。
   - その後に品質改善を重ねる。

3. **Small, Explainable Commits**
   - 変更は小さく分割し、各コミットで理由を説明可能にする。

4. **Decision Logging**
   - 重要な判断は `docs/decisions.md` に以下で記録：
     - Context
     - Options
     - Decision
     - Consequence

5. **No Silent Assumptions**
   - 不明点は TODO と仮説を明記し、影響範囲を限定する。

6. **Validation Before Expansion**
   - 新機能追加前に既存フローの検査・テストを通す。

7. **Interview Readiness**
   - 実装と同時に「なぜこの設計か」を説明できる材料を残す。

---

## Documentation Requirements
最低限、以下を整備すること：

- `README.md`
  - 起動手順
  - API一覧
  - デモ手順
- `docs/plan.md`
  - 要件分解
  - マイルストーン
- `docs/decisions.md`
  - 設計判断ログ
- `docs/experiments.md`
  - 比較実験（例：ルール有無での出力差）
- `docs/references.md`
  - 参考URL（Zenn/Qiita/公式Docs）と採用・不採用理由

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

---

## Milestone Plan (2 Weeks)
- **Day 1-2:** 要件整理・設計・骨組み作成
- **Day 3-5:** タイトル生成API + UI接続
- **Day 6-9:** 本文生成 + LLMO制約適用
- **Day 10-11:** バリデータ実装 + 比較実験
- **Day 12-14:** README整備・デモ準備・想定問答整理

---

## Definition of Done
以下を満たしたら課題提出可能：

- ローカルで一連フローが再現できる
- LLMO必須要件を機械検査で可視化できる
- READMEで第三者が起動できる
- 設計判断・工夫・比較実験を説明できる資料がある

---

## Commit Message Convention
- `feat:`
- `fix:`
- `docs:`
- `refactor:`
- `test:`
- `chore:`

例：
- `feat: implement two-step generation pipeline`
- `fix: enforce FAQ and definition section in article prompt`
- `docs: add decision log for model abstraction choice`

---

## Final Principle
**「動くもの」だけでなく、「なぜそう作ったか」を残す。**  
この課題の本質は、実装力と同時に、思考と説明責任を示すことにある。