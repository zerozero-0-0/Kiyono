"""Title generation service for LLMO-oriented content creation.

This module provides a provider-agnostic title generation service that:
- validates and normalizes title count requests
- builds a deterministic prompt for LLM title generation
- parses model output into clean title candidates
- applies lightweight post-filters to improve practical quality
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol


class LLMClientProtocol(Protocol):
    """Provider-agnostic LLM client contract.

    Any concrete LLM client (Gemini/OpenAI/Anthropic/etc.) can implement this
    interface so the title generation logic stays independent from providers.
    """

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        """Generate text response from the configured LLM provider."""
        ...


@dataclass(frozen=True, slots=True)
class TitleGenerationInput:
    """Input model for title generation.

    Attributes:
        keyword: Main blog topic or keyword.
        brief: Short summary of user intent, audience, and constraints.
        n_titles: Desired number of titles.
    """

    keyword: str
    brief: str
    n_titles: int = 8


@dataclass(frozen=True, slots=True)
class TitleGenerationResult:
    """Output model for title generation.

    Attributes:
        titles: Generated and sanitized title list.
        rationale: Optional simple rationale list per title.
    """

    titles: list[str]
    rationale: list[str] | None = None


class TitleGenerationService:
    """Generate blog title candidates for LLMO use cases."""

    _MIN_TITLES: int = 1
    _MAX_TITLES: int = 10

    def __init__(
        self,
        llm_client: LLMClientProtocol,
        *,
        temperature: float = 0.4,
        max_output_tokens: int = 1200,
    ) -> None:
        """Initialize service.

        Args:
            llm_client: Provider-agnostic LLM client implementation.
            temperature: Sampling temperature for title generation.
            max_output_tokens: Maximum output tokens from LLM.
        """
        self._llm_client: LLMClientProtocol = llm_client
        self._temperature: float = temperature
        self._max_output_tokens: int = max_output_tokens

    async def generate(self, payload: TitleGenerationInput) -> TitleGenerationResult:
        """Generate title candidates.

        Args:
            payload: Title generation input.

        Returns:
            TitleGenerationResult containing sanitized title list.

        Raises:
            ValueError: If input is invalid after normalization.
        """
        keyword = self._sanitize_text(payload.keyword)
        brief = self._sanitize_text(payload.brief)
        n_titles = self._normalize_title_count(payload.n_titles)

        if not keyword:
            raise ValueError("keyword must not be empty.")
        if not brief:
            raise ValueError("brief must not be empty.")

        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(keyword=keyword, brief=brief, n_titles=n_titles)

        raw = await self._llm_client.generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=self._temperature,
            max_output_tokens=self._max_output_tokens,
        )

        parsed_titles = self._parse_titles(raw)
        clean_titles = self._post_process_titles(
            parsed_titles, target_count=n_titles, keyword=keyword
        )

        if not clean_titles:
            raise ValueError("failed to generate valid titles from model output.")

        return TitleGenerationResult(titles=clean_titles[:n_titles], rationale=None)

    @classmethod
    def _normalize_title_count(cls, n_titles: int) -> int:
        """Clamp requested title count into supported bounds."""
        if n_titles < cls._MIN_TITLES:
            return cls._MIN_TITLES
        if n_titles > cls._MAX_TITLES:
            return cls._MAX_TITLES
        return n_titles

    @staticmethod
    def _sanitize_text(value: str) -> str:
        """Normalize whitespace and trim text."""
        compact = re.sub(r"\s+", " ", value or "")
        return compact.strip()

    @staticmethod
    def _build_system_prompt() -> str:
        """Return system instruction for title generation."""
        return (
            "あなたはB2Bマーケティングに強い編集者です。"
            "与えられたキーワードと概要から、生成AIに引用されやすい記事タイトルを作成してください。"
            "冗長な表現を避け、具体性・検索意図・実務有用性を優先します。"
            "出力は必ずタイトルのみを改行区切りで返してください。"
            "番号、箇条書き記号、前置き、解説文は不要です。"
        )

    @staticmethod
    def _build_user_prompt(*, keyword: str, brief: str, n_titles: int) -> str:
        """Build user prompt with explicit constraints."""
        return (
            f"キーワード: {keyword}\n"
            f"記事概要: {brief}\n"
            f"生成件数: {n_titles}\n\n"
            "制約:\n"
            "- 1タイトルは30〜55文字程度を目安\n"
            "- 曖昧語より具体語を優先\n"
            "- 想定読者が得る価値を匂わせる\n"
            "- 互いに重複しない観点を含める\n"
            "- 煽りすぎない自然な日本語にする\n"
        )

    @staticmethod
    def _parse_titles(raw_text: str) -> list[str]:
        """Parse multiline model output into candidate titles."""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        normalized: list[str] = []
        for line in lines:
            # Remove common list markers like "1. ", "- ", "• "
            cleaned = re.sub(r"^\s*(?:[-•*]|\d+[.)])\s*", "", line).strip()
            if cleaned:
                normalized.append(cleaned)
        return normalized

    @staticmethod
    def _post_process_titles(
        titles: list[str],
        *,
        target_count: int,
        keyword: str,
    ) -> list[str]:
        """Deduplicate and lightly filter titles.

        Rules:
        - remove exact duplicates while preserving order
        - remove titles that are too short
        - prioritize titles that include keyword tokens
        """
        seen: set[str] = set()
        unique: list[str] = []
        for title in titles:
            if len(title) < 8:
                continue
            if title in seen:
                continue
            seen.add(title)
            unique.append(title)

        if not unique:
            return []

        keyword_tokens: list[str] = [token for token in re.split(r"[\s、,]+", keyword) if token]
        with_keyword: list[str] = []
        without_keyword: list[str] = []
        for title in unique:
            if any(token in title for token in keyword_tokens):
                with_keyword.append(title)
            else:
                without_keyword.append(title)

        ranked: list[str] = with_keyword + without_keyword

        # If model returns fewer than requested, return what we have.
        return ranked[:target_count] if len(ranked) >= target_count else ranked
