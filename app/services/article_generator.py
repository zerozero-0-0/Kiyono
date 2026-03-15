"""LLMO構造化Markdown出力のための記事生成サービス。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.constants import (
    ARTICLE_SYSTEM_PROMPT,
    ARTICLE_USER_PROMPT_TEMPLATE,
    DEFAULT_AUDIENCE,
    DEFAULT_TONE,
)


class LLMClientProtocol(Protocol):
    """ジェネレーターで使用されるLLMクライアント実装のためのプロトコル。"""

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """システム/ユーザープロンプトのペアからテキストを生成します。

        引数:
            system_prompt: モデルへの振る舞いの指示。
            user_prompt: タスク固有の入力コンテンツ。

        戻り値:
            生成されたテキスト。
        """
        ...


@dataclass(frozen=True)
class ArticleGenerationInput:
    """記事生成のための入力ペイロード。

    属性:
        selected_title: ユーザーが選択したタイトル。
        keyword: 記事のメインキーワード。
        brief: 記事の概要またはコンテキスト。
        audience: オプションのターゲット読者層。
        tone: オプションの文体。
    """

    selected_title: str
    keyword: str
    brief: str
    audience: str | None = None
    tone: str | None = None


@dataclass(frozen=True)
class ArticleGenerationResult:
    """記事生成のための出力ペイロード。

    属性:
        markdown_article: LLMO構造化Markdown記事。
        model_used: オプションのモデル識別子。
    """

    markdown_article: str
    model_used: str | None = None


class ArticleGenerator:
    """LLMOに最適化されたMarkdown記事を生成します。

    このサービスは以下の方法でLLMO構造を強制します:
    1) 直接的な要約（Summary）から始める。
    2) 辞書形式の明示的な定義を含める。
    3) 構造化されたリストと少なくとも1つのMarkdown表を使用する。
    4) 簡潔なFAQセクションで終わる。
    """

    def __init__(
        self,
        llm_client: LLMClientProtocol | None = None,
        *,
        model_name: str | None = None,
    ) -> None:
        """記事ジェネレーターを初期化します。

        引数:
            llm_client: LLMクライアント実装。
                省略した場合はフォールバックのテンプレートモードが使用されます。
            model_name: メタデータ用のオプションのモデル名。
        """
        self._llm_client: LLMClientProtocol | None = llm_client
        self._model_name: str | None = model_name

    def generate(self, payload: ArticleGenerationInput) -> ArticleGenerationResult:
        """入力ペイロードからMarkdown記事を生成します。

        LLMクライアントが利用可能な場合、このメソッドは厳格な出力制約を用いてモデルにプロンプトを出します。
        そうでない場合は、コアのLLMO構造を満たす決定論的なテンプレートベースの記事を返します。

        引数:
            payload: ユーザーが選択したタイトルとコンテキスト。

        戻り値:
            Markdown出力を含むArticleGenerationResult。
        """
        self._validate_payload(payload)

        if self._llm_client is None:
            markdown = self._build_template_article(payload)
            return ArticleGenerationResult(
                markdown_article=markdown,
                model_used=self._model_name,
            )

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(payload)

        generated = self._llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )
        cleaned = self._postprocess(generated)

        # モデルの出力が空または不正な場合の安全なフォールバック。
        if not cleaned.strip():
            cleaned = self._build_template_article(payload)

        return ArticleGenerationResult(
            markdown_article=cleaned,
            model_used=self._model_name,
        )

    def _validate_payload(self, payload: ArticleGenerationInput) -> None:
        """必須の生成入力を検証します。

        引数:
            payload: 検証する入力ペイロード。

        例外:
            ValueError: 必須フィールドが空の場合。
        """
        if not payload.selected_title.strip():
            raise ValueError("selected_title must not be empty.")
        if not payload.keyword.strip():
            raise ValueError("keyword must not be empty.")
        if not payload.brief.strip():
            raise ValueError("brief must not be empty.")

    def _build_system_prompt(self) -> str:
        """LLMO出力ルールを強制する厳格なシステムプロンプトを構築します。"""
        return ARTICLE_SYSTEM_PROMPT

    def _build_user_prompt(self, payload: ArticleGenerationInput) -> str:
        """入力ペイロードからユーザープロンプトを構築します。

        引数:
            payload: 生成入力。

        戻り値:
            記事生成のためのプロンプト文字列。
        """
        audience = payload.audience or DEFAULT_AUDIENCE
        tone = payload.tone or DEFAULT_TONE

        return ARTICLE_USER_PROMPT_TEMPLATE.format(
            selected_title=payload.selected_title,
            keyword=payload.keyword,
            brief=payload.brief,
            audience=audience,
            tone=tone,
        )

    def _build_template_article(self, payload: ArticleGenerationInput) -> str:
        """LLMO構造を持つ決定論的なフォールバック記事を構築します。

        引数:
            payload: 生成入力。

        戻り値:
            Markdown記事の文字列。
        """
        audience = payload.audience or "想定読者未指定"
        tone = payload.tone or "実務的で簡潔"

        return (
            f"# {payload.selected_title}\n\n"
            "## Summary\n"
            f"{payload.keyword}に取り組むうえで重要なのは、目的を明確化し、"
            "実行手順を分解し、効果測定を継続することである。"
            "本記事では、概要に基づいて実務で再現しやすい進め方を示す。\n\n"
            "## Definitions\n"
            f"- {payload.keyword}とは、意思決定と実行を構造化するアプローチである。\n"
            "- LLMOとは、生成AIに最適化された高情報密度コンテンツの設計思想である。\n"
            "- 構造化記事とは、見出しや表を用いて検索に強い形式で記述された記事である。\n\n"
            "## 実践ポイント\n"
            "- 目的と評価指標を最初に固定する\n"
            "- 想定読者の課題を3つに分解して見出しへ落とし込む\n"
            "- 比較表で選定基準を明文化し、主観を減らす\n"
            "- FAQで検索クエリに近い疑問へ短く回答する\n\n"
            "## 比較表\n"
            "| 観点 | 低成熟な進め方 | 推奨アプローチ |\n"
            "|---|---|---|\n"
            "| 記事導入 | 背景説明が長い | 結論先行（Summary） |\n"
            "| 定義 | 用語の意味が曖昧 | 「Xとは、〜である」で明確化 |\n"
            "| 構成 | 文章中心で冗長 | 箇条書き＋表で情報圧縮 |\n"
            "| 検索適合 | FAQがない | FAQで疑問を網羅 |\n\n"
            "## まとめ\n"
            f"{payload.keyword}の実装・運用では、"
            "構造化された情報提示が意思決定速度と再現性を高める。"
            f"本記事の読者（{audience}）は、まず小さな単位で導入し、"
            f"継続的に改善する運用を選ぶとよい。文体方針は「{tone}」を維持する。\n\n"
            "## FAQ\n"
            "Q: まず何から始めるべきですか？\n"
            "A: 目的・対象読者・評価指標の3点を最初に固定することが最優先です。これらを明確にすることで方向性がブレず、関係者間の認識ズレを防止できます。初期段階でこのプロセスを省略すると後戻りリスクが高まるため、一次情報に基づく判断基準をチーム全体で揃えておくことが実務において非常に重要です。\n\n"
            "Q: 表は必ず必要ですか？\n"
            "A: 比較や選定がある場合、表を使うと要点が圧縮されAIに参照されやすくなります。情報を表で整理すれば読者は短時間で比較でき、意思決定の速度が向上します。構造化データは機械可読性が高くLLMの要約精度に直結するため、実務で積極的に活用すべき一次情報に基づく具体的なアプローチです。\n\n"
            "Q: 長文でも問題ありませんか？\n"
            "A: 見出しや箇条書きで適切に分割していれば、長文でも可読性を維持できます。重要なのは文字数ではなく、結論先行の構造と一次情報に基づく具体性です。読者が知りたい情報へ素早くアクセスできるよう論点を区切り、視覚的な負担を軽減すれば、AIと人間の双方にとって価値の高い実務的な記事になります。\n"
        )

    def _postprocess(self, text: str) -> str:
        """生成されたMarkdownテキストを正規化します。

        引数:
            text: 生成された生のテキスト。

        戻り値:
            クリーンアップされたMarkdown。
        """
        return text.strip()
