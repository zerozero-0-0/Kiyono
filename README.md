# LLMO Content Generator

生成AI時代に向けた、LLMO（Large Language Model Optimization）最適化コンテンツの生成・支援システムです。
データサイエンスインターンのコーディング課題（課題2）として作成されたプロトタイプ実装です。

従来の「検索エンジン（SEO）向け」ではなく、「ChatGPT / Claude / Gemini 等の生成AIに引用・参照されやすい（LLMO向け）」記事の企画から執筆、形式検証までを半自動化します。

---

## 🌟 主な機能 (Core Features)

1. **2段階生成アプローチ**
   - **タイトル案生成**: ユーザーが入力した「キーワード」と「記事概要（ターゲット・課題）」から、AIが読者の関心を惹くタイトル案を5〜10件提案します。
   - **記事本文生成**: ユーザーが選択したタイトルをもとに、LLMOに特化した構成でMarkdown記事を自動生成します。
2. **LLMOフォーマットの厳密な適用**
   - 生成プロンプトを工夫し、AIが情報を抽出しやすい「結論先行（Summary）」「厳密な定義（Xとは〜である）」「構造化データ（Markdown表・箇条書き）」「FAQ（Q&A）」の構成を強制します。
3. **ルールベースのLLMOバリデーション**
   - 生成された記事が本当にLLMOの要件を満たしているかを機械的に検査・スコア化し、不足している場合はユーザーに「Markdown表を追加してください」などの改善アクションを提示します。
4. **決定論的モック（Stub Client）の搭載**
   - 外部APIキーがなくても開発・UI動作確認が可能なローカルスタブモードを搭載しています。

---

## 🛠️ 技術スタック (Tech Stack)

- **Backend**: Python 3.11+, FastAPI, Pydantic (厳格な型推論とバリデーション)
- **Frontend**: Streamlit (高速なプロトタイプUI構築)
- **AI Integration**: `google-genai` (Gemini 2.5 Flash 搭載)
- **Tooling**: `uv` (超高速パッケージ管理), `Ruff` (Linter/Formatter), `Pyright` (Type Checker), `Make`

---

## 🚀 セットアップと起動 (Getting Started)

### 1. 前提条件
- Python 3.11 以上
- [uv](https://github.com/astral-sh/uv) がインストールされていること

### 2. インストール
リポジトリをクローン後、以下のコマンドで依存関係をインストールします。

```bash
make install
```

### 3. 環境変数の設定
`.env.example` をコピーして `.env` ファイルを作成します。

```bash
cp .env.example .env
```
`.env` ファイルを開き、Gemini APIキーを設定してください。
（※ APIキーがない場合は `LLM_PROVIDER=stub` とすることで、固定テキストを返すモックモードで動作確認が可能です）

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_api_key_here
```

### 4. アプリケーションの起動
Makefileを使用して、バックエンドとフロントエンドを同時に起動します。

```bash
make dev
```

起動後、ブラウザで以下のURLにアクセスしてください。
- **Streamlit UI**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Docs (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📁 プロジェクト構成 (Project Structure)

```text
kiyono/
├── app/
│   ├── main.py                # FastAPI エントリポイント
│   ├── config.py              # 環境変数・設定管理 (pydantic-settings)
│   ├── schemas.py             # API入出力・バリデーションのスキーマ
│   └── services/
│       ├── article_generator.py # 本文生成・プロンプト構築ロジック
│       ├── llm_client.py        # Gemini API / Stub クライアントの抽象化
│       ├── llmo_validator.py    # LLMO要件のルールベース検査ロジック
│       └── title_generator.py   # タイトル案生成・後処理ロジック
├── frontend/
│   └── app.py                 # Streamlit UI実装
├── docs/                      # 評価用ドキュメント（企画書・意思決定ログ等）
├── tests/                     # pytestテストコード
├── Makefile                   # 開発用コマンド集
├── pyproject.toml             # パッケージ・ツール設定
└── README.md                  # 本ファイル
```

