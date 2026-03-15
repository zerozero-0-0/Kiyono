"""アプリケーション全体で共有する定数やプロンプトテンプレート。

発表用のアピールポイント:
LLM（Gemini等）へ送信するリクエストの文字数制限や、生成精度を上げるための
システムプロンプトの調整結果をこのファイルで一元管理しています。
ここでプロンプトや文字数の実験を繰り返し、最適なパラメータを定義しました。
"""

# ==========================================
# 文字数制限・入力バリデーション用パラメータ
# ==========================================
# LLMのコンテキストウィンドウや処理時間を考慮し、実用的な文字数上限を定義
MAX_KEYWORD_LENGTH = 200
MAX_BRIEF_LENGTH = 5000     # 概要が長すぎるとLLMが発散するため、5000文字を上限とする
MAX_TITLE_LENGTH = 300
MAX_AUDIENCE_LENGTH = 300
MAX_TONE_LENGTH = 100

# ==========================================
# タイトル生成用パラメータ & プロンプト
# ==========================================
TITLE_MIN_GENERATION_COUNT = 1
TITLE_MAX_GENERATION_COUNT = 10
TITLE_MIN_LENGTH_FILTER = 8 # 短すぎるタイトル（ノイズ）を除外する閾値

TITLE_SYSTEM_PROMPT = (
    "あなたはB2Bマーケティングに強い編集者です。"
    "与えられたキーワードと概要から、生成AIに引用されやすい記事タイトルを作成してください。"
    "冗長な表現を避け、具体性・検索意図・実務有用性を優先します。"
    "出力は必ずタイトルのみを改行区切りで返してください。"
    "番号、箇条書き記号、前置き、解説文は不要です。"
)

TITLE_USER_PROMPT_TEMPLATE = (
    "キーワード: {keyword}\n"
    "記事概要: {brief}\n"
    "生成件数: {n_titles}\n\n"
    "制約:\n"
    "- 1タイトルは30〜55文字程度を目安\n"
    "- 曖昧語より具体語を優先\n"
    "- 想定読者が得る価値を匂わせる\n"
    "- 互いに重複しない観点を含める\n"
    "- 煽りすぎない自然な日本語にする\n"
)

# ==========================================
# 記事本文生成用パラメータ & プロンプト
# ==========================================
DEFAULT_AUDIENCE = "指定なし"
DEFAULT_TONE = "実務的で簡潔"

ARTICLE_SYSTEM_PROMPT = (
    "You are an expert technical content writer specializing in LLMO "
    "(Large Language Model Optimization).\n"
    "Generate a highly structured Japanese markdown article optimized "
    "to be cited by AI models.\n\n"
    "CRITICAL INSTRUCTIONS:\n"
    "- Start EXACTLY with `## Summary` or `## 結論`. "
    "Do NOT output `# Title` or any greetings.\n"
    "- Provide EXACTLY the required headings. Do NOT deviate from the outline.\n"
    "- Include a definition section where at least one keyword is defined "
    "using the EXACT phrase: 'とは、〜である。'\n"
    "- Ensure the article contains at least one markdown table "
    "(`|---|---|`) for comparison.\n"
    "- End the article with `## FAQ` and at least two Q&A pairs "
    "formatted as `Q: ...` and `A: ...`.\n"
    "- Keep paragraphs short and use bullet points frequently.\n"
)

ARTICLE_USER_PROMPT_TEMPLATE = (
    "以下の条件で記事を作成してください。\n\n"
    "- タイトル: {selected_title}\n"
    "- メインキーワード: {keyword}\n"
    "- 概要: {brief}\n"
    "- 想定読者: {audience}\n"
    "- 文体: {tone}\n\n"
    "以下の構成（Markdown見出し）に厳密に従って出力してください:\n\n"
    "## Summary\n"
    "（ここにタイトルに対する結論を150文字以内で書く）\n\n"
    "## Definitions\n"
    "（ここに「Xとは、〜である。」という形式の定義を最低2つ書く）\n\n"
    "## 実践ポイント\n"
    "（箇条書きで具体的に解説）\n\n"
    "## 比較表\n"
    "（必ず1つ以上のMarkdown表を含める）\n\n"
    "## まとめ\n"
    "（記事の要約）\n\n"
    "## FAQ\n"
    "（Q: と A: の形式で3つ以上の想定質問と回答を書く）\n"
)
