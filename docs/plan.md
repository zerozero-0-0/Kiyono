# Implementation Plan

## 1. 目的
このドキュメントは、インターン課題「LLMO用コンテンツ生成システム」を**2週間で実装可能な形**に分解し、  
最小差分コミットで安全に進めるための実行計画を定義する。

---

## 2. ゴール定義

### 2.1 プロダクトゴール
- ユーザー入力（キーワード + 記事概要）からタイトル案を5〜10件生成する
- 選択タイトルに基づいて、LLMO最適化されたMarkdown記事を生成する
- 生成記事に対して、LLMO要件の検査結果を返す
- （任意）Schema.org JSON-LDを出力する

### 2.2 面接ゴール
- 「なぜこの構成にしたか」を説明できる
- 実装中のトレードオフと意思決定を説明できる
- 比較実験の結果を根拠に改善を語れる

---

## 3. スコープ

### 3.1 In Scope（MVP）
- FastAPIバックエンド
- Streamlitフロントエンド
- 2段階生成フロー（タイトル生成 → 本文生成）
- LLMOバリデータ（形式要件チェック）
- ローカル実行可能なデモ

### 3.2 Out of Scope（今回やらない）
- 本番デプロイ
- ユーザー認証
- 大規模RAG
- 高度な監視・課金・権限管理

---

## 4. 成果物（提出時）

- GitHubリポジトリ
- 動作デモ（localhost）
- README（セットアップ・実行手順）
- docs群（plan / decisions / experiments / references）

---

## 5. 実装戦略（最短価値提供）

### 方針
1. まず「入力→生成→表示」の縦スライスを作る
2. 次にLLMO制約の担保を強化する
3. 最後に実験・改善・説明資料を整える

### 採用アーキテクチャ（最小）
- `app/main.py`：APIエンドポイント
- `app/schemas.py`：入出力モデル
- `app/services/llm_client.py`：LLM接続
- `app/services/title_generator.py`：タイトル生成
- `app/services/article_generator.py`：本文生成
- `app/services/llmo_validator.py`：形式検査
- `frontend/app.py`：UI

---

## 6. マイルストーン（2週間）

## M1: ドキュメントと土台（Day 1-2）
**目的**: 迷わず実装に入れる状態を作る  
**完了条件**:
- README初版
- docs初版（plan / decisions / experiments / references）
- `pyproject.toml` と `.env.example` を配置

## M2: 環境構築と起動確認（Day 2-3）
**目的**: 実装速度を落とさない開発基盤を確立  
**完了条件**:
- 仮想環境と依存導入完了
- FastAPI最小起動（`/health`）
- Streamlit最小起動（ダミー画面）

## M3: タイトル生成機能（Day 3-5）
**目的**: 1つ目の価値（企画支援）を提供  
**完了条件**:
- `POST /generate/titles` 実装
- UIからタイトル生成可能
- 5〜10件を安定返却

## M4: 本文生成機能（Day 6-8）
**目的**: 2つ目の価値（記事生成）を提供  
**完了条件**:
- `POST /generate/article` 実装
- 選択タイトルを引き継いで本文生成
- Markdownとして表示可能

## M5: LLMOバリデータ（Day 8-10）
**目的**: 形式品質を可視化  
**完了条件**:
- Summary / 定義 / 表 / FAQ / 見出し整合チェック
- `validation_report` をレスポンスに含める
- 不足項目をユーザーへ表示

## M6: 実験・改善・仕上げ（Day 10-14）
**目的**: 面接説明力を強化  
**完了条件**:
- 最低2本の比較実験記録
- 主要意思決定を docs に明記
- デモ手順の最終化

---

## 7. 最小差分コミット実行計画

## 7.1 ルール
- 1コミット1意図（混ぜない）
- 影響範囲が狭い変更単位で分割
- 仕様変更とリファクタを同時にしない
- コミットメッセージはプレフィックス必須

## 7.2 推奨コミット順（例）
1. `docs: add initial planning and documentation set`
2. `chore: bootstrap project configuration with uv and env template`
3. `feat: add FastAPI app skeleton with health endpoint`
4. `feat: add Streamlit skeleton and basic input form`
5. `feat: implement title generation endpoint and service`
6. `feat: connect title generation from streamlit ui`
7. `feat: implement article generation endpoint and service`
8. `feat: add llmo validator and validation report schema`
9. `feat: render article and validation results in ui`
10. `test: add smoke tests for health and generation endpoints`
11. `docs: add experiment results and architecture decisions`

---

## 8. API実装計画

## 8.1 `GET /health`
- 目的: 起動確認
- 出力: `{"status":"ok"}`

## 8.2 `POST /generate/titles`
- 入力:
  - `keyword: str`
  - `brief: str`
  - `n_titles: int = 8`
- 出力:
  - `titles: list[str]`
- 異常系:
  - 入力不足時は400系

## 8.3 `POST /generate/article`
- 入力:
  - `selected_title: str`
  - `keyword: str`
  - `brief: str`
  - `audience: str | null`
  - `tone: str | null`
- 出力:
  - `markdown_article: str`
  - `validation_report: dict`
  - `json_ld: dict | null`

---

## 9. LLMO品質チェック計画

### チェック項目（最低）
- Summary先頭
- 定義文（「Xとは、〜である」）
- Markdown表の存在
- FAQセクション
- 見出し階層の整合

### レポート形式（案）
- `passed: bool`
- `checks: [{name, passed, detail}]`
- `missing_actions: [str]`

---

## 10. リスクと対策

### リスク1: APIキーや外部依存で詰まる
- 対策: ダミー実装モードを用意してUI〜APIの導線を先に完成

### リスク2: 出力がLLMO要件を満たさない
- 対策: プロンプト制約 + バリデータで二重担保

### リスク3: 期間不足
- 対策: JSON-LDや高度機能は後回し。MVP機能を優先

### リスク4: 面接で設計理由を説明しづらい
- 対策: decisions.md を都度更新し、判断根拠を記録

---

## 11. Definition of Done

以下をすべて満たしたら提出可能:
- ローカルでE2E動作（入力→タイトル→本文→検査表示）
- 主要APIが正常系で動作
- READMEに起動手順がある
- docsに意思決定・実験記録がある
- 最小差分コミット履歴で開発過程を追える

---

## 12. 次アクション（直近）

1. `pyproject.toml` と `.env.example` を作成
2. FastAPI/Streamlitのスケルトン作成
3. `/health` を実装して起動確認
4. タイトル生成APIから順に機能追加
5. 変更ごとに最小差分コミット