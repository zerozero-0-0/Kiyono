"""Article generation service for LLMO-structured markdown output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LLMClientProtocol(Protocol):
    """Protocol for LLM client implementations used by the generator."""

    def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        """Generate text from a system/user prompt pair.

        Args:
            system_prompt: Behavioral instruction for the model.
            user_prompt: Task-specific input content.

        Returns:
            Generated text.
        """
        ...


@dataclass(frozen=True)
class ArticleGenerationInput:
    """Input payload for article generation.

    Attributes:
        selected_title: Title chosen by user.
        keyword: Main keyword for the article.
        brief: Article brief or context.
        audience: Optional target audience.
        tone: Optional writing tone.
    """

    selected_title: str
    keyword: str
    brief: str
    audience: str | None = None
    tone: str | None = None


@dataclass(frozen=True)
class ArticleGenerationResult:
    """Output payload for article generation.

    Attributes:
        markdown_article: LLMO-structured markdown article.
        model_used: Optional model identifier.
    """

    markdown_article: str
    model_used: str | None = None


class ArticleGenerator:
    """Generate LLMO-optimized markdown articles.

    This service enforces LLMO structure by:
    1) Starting with a direct summary.
    2) Including explicit dictionary-style definitions.
    3) Using structured lists and at least one markdown table.
    4) Ending with a concise FAQ section.
    """

    def __init__(
        self,
        llm_client: LLMClientProtocol | None = None,
        *,
        model_name: str | None = None,
    ) -> None:
        """Initialize article generator.

        Args:
            llm_client: LLM client implementation. If omitted, fallback template mode is used.
            model_name: Optional model name for metadata.
        """
        self._llm_client: LLMClientProtocol | None = llm_client
        self._model_name: str | None = model_name

    def generate(self, payload: ArticleGenerationInput) -> ArticleGenerationResult:
        """Generate a markdown article from input payload.

        If an LLM client is available, this method prompts the model with strict
        output constraints. Otherwise, it returns a deterministic template-based
        article that still satisfies core LLMO structure.

        Args:
            payload: User-selected title and context.

        Returns:
            ArticleGenerationResult containing markdown output.
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

        # Safety fallback when model output is empty or malformed.
        if not cleaned.strip():
            cleaned = self._build_template_article(payload)

        return ArticleGenerationResult(
            markdown_article=cleaned,
            model_used=self._model_name,
        )

    def _validate_payload(self, payload: ArticleGenerationInput) -> None:
        """Validate required generation inputs.

        Args:
            payload: Input payload to validate.

        Raises:
            ValueError: If required fields are blank.
        """
        if not payload.selected_title.strip():
            raise ValueError("selected_title must not be empty.")
        if not payload.keyword.strip():
            raise ValueError("keyword must not be empty.")
        if not payload.brief.strip():
            raise ValueError("brief must not be empty.")

    def _build_system_prompt(self) -> str:
        """Build strict system prompt enforcing LLMO output rules."""
        return (
            "You are an expert technical content writer for LLMO.\n"
            "Generate a Japanese markdown article that is highly citable by LLMs.\n"
            "Follow these hard rules:\n"
            "1) Start immediately with a 'Summary' section answering the title.\n"
            "2) Add a 'Definitions' section with at least 2 dictionary-style definitions "
            "using the pattern 'Xとは、〜である。'.\n"
            "3) Use MECE-oriented bullet lists for key points.\n"
            "4) Include at least one markdown table for comparison or decision criteria.\n"
            "5) End with an 'FAQ' section containing at least 3 Q&A pairs.\n"
            "6) Avoid greetings and long introductions.\n"
            "7) Output markdown only.\n"
        )

    def _build_user_prompt(self, payload: ArticleGenerationInput) -> str:
        """Build user prompt from input payload.

        Args:
            payload: Generation input.

        Returns:
            Prompt string for article generation.
        """
        audience = payload.audience or "指定なし"
        tone = payload.tone or "実務的で簡潔"

        return (
            "以下の条件で記事を作成してください。\n\n"
            f"- タイトル: {payload.selected_title}\n"
            f"- メインキーワード: {payload.keyword}\n"
            f"- 概要: {payload.brief}\n"
            f"- 想定読者: {audience}\n"
            f"- 文体: {tone}\n\n"
            "必須構成:\n"
            "## Summary\n"
            "## Definitions\n"
            "## 実践ポイント\n"
            "## 比較表\n"
            "## まとめ\n"
            "## FAQ\n"
        )

    def _build_template_article(self, payload: ArticleGenerationInput) -> str:
        """Build deterministic fallback article with LLMO structure.

        Args:
            payload: Generation input.

        Returns:
            Markdown article string.
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
            "### Q1. まず何から始めるべきですか？\n"
            "A1. 目的・対象読者・評価指標の3点を最初に固定することが最優先です。\n\n"
            "### Q2. 表は必ず必要ですか？\n"
            "A2. 比較や選定がある場合は、表を使うと要点が圧縮されAIに参照されやすくなります。\n\n"
            "### Q3. 長文でも問題ありませんか？\n"
            "A3. 見出しや箇条書きで情報を適切に分割していれば、長文でも可読性を維持できます。\n"
        )

    def _postprocess(self, text: str) -> str:
        """Normalize generated markdown text.

        Args:
            text: Raw generated text.

        Returns:
            Cleaned markdown.
        """
        return text.strip()
