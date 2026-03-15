"""LLMO指向のコンテンツ作成のためのタイトル生成サービス。

このモジュールは、プロバイダに依存しない以下の機能を持つタイトル生成サービスを提供します:
- タイトル数のリクエストを検証および正規化します
- LLMタイトル生成のための決定論的プロンプトを構築します
- モデルの出力をクリーンなタイトル候補に解析します
- 実用的な品質を向上させるための軽量なポストフィルターを適用します
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol

from app.constants import (
    TITLE_MAX_GENERATION_COUNT,
    TITLE_MIN_GENERATION_COUNT,
    TITLE_MIN_LENGTH_FILTER,
    TITLE_SYSTEM_PROMPT,
    TITLE_USER_PROMPT_TEMPLATE,
)


class LLMClientProtocol(Protocol):
    """プロバイダに依存しないLLMクライアントのコントラクト。

    タイトル生成ロジックがプロバイダから独立して維持されるように、
    任意の具体的なLLMクライアント（Gemini/OpenAI/Anthropicなど）がこのインターフェースを実装できます。
    """

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        """設定されたLLMプロバイダからテキストレスポンスを生成します。"""
        ...


@dataclass(frozen=True, slots=True)
class TitleGenerationInput:
    """タイトル生成のための入力モデル。

    属性:
        keyword: メインのブログトピックまたはキーワード。
        brief: ユーザーの意図、読者層、制約の短い要約。
        n_titles: 希望するタイトルの数。
    """

    keyword: str
    brief: str
    n_titles: int = 8


@dataclass(frozen=True, slots=True)
class TitleGenerationResult:
    """タイトル生成のための出力モデル。

    属性:
        titles: 生成およびサニタイズされたタイトルリスト。
        rationale: 各タイトルに対する簡単な理由のリスト（オプション）。
    """

    titles: list[str]
    rationale: list[str] | None = None


class TitleGenerationService:
    """LLMOのユースケースのためのブログタイトル候補を生成します。"""

    _MIN_TITLES: int = TITLE_MIN_GENERATION_COUNT
    _MAX_TITLES: int = TITLE_MAX_GENERATION_COUNT

    def __init__(
        self,
        llm_client: LLMClientProtocol,
        *,
        temperature: float = 0.4,
        max_output_tokens: int = 1200,
    ) -> None:
        """サービスを初期化します。

        引数:
            llm_client: プロバイダに依存しないLLMクライアント実装。
            temperature: タイトル生成のサンプリング温度。
            max_output_tokens: LLMからの最大出力トークン。
        """
        self._llm_client: LLMClientProtocol = llm_client
        self._temperature: float = temperature
        self._max_output_tokens: int = max_output_tokens

    async def generate(self, payload: TitleGenerationInput) -> TitleGenerationResult:
        """タイトル候補を生成します。

        引数:
            payload: タイトル生成の入力。

        戻り値:
            サニタイズされたタイトルリストを含むTitleGenerationResult。

        例外:
            ValueError: 正規化後に入力が無効な場合。
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
        """要求されたタイトル数をサポートされる範囲内に制限します。"""
        if n_titles < cls._MIN_TITLES:
            return cls._MIN_TITLES
        if n_titles > cls._MAX_TITLES:
            return cls._MAX_TITLES
        return n_titles

    @staticmethod
    def _sanitize_text(value: str) -> str:
        """空白を正規化し、テキストをトリミングします。"""
        compact = re.sub(r"\s+", " ", value or "")
        return compact.strip()

    @staticmethod
    def _build_system_prompt() -> str:
        """タイトル生成のためのシステム指示を返します。"""
        return TITLE_SYSTEM_PROMPT

    @staticmethod
    def _build_user_prompt(*, keyword: str, brief: str, n_titles: int) -> str:
        """明示的な制約を持つユーザープロンプトを構築します。"""
        return TITLE_USER_PROMPT_TEMPLATE.format(keyword=keyword, brief=brief, n_titles=n_titles)

    @staticmethod
    def _parse_titles(raw_text: str) -> list[str]:
        """複数行のモデル出力をタイトル候補に解析します。"""
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        normalized: list[str] = []
        for line in lines:
            # "1. ", "- ", "• " のような一般的なリストマーカーを削除します
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
        """タイトルを重複排除し、軽くフィルタリングします。

        ルール:
        - 順序を保持しながら完全な重複を削除する
        - 短すぎるタイトルを削除する
        - キーワードトークンを含むタイトルを優先する
        """
        seen: set[str] = set()
        unique: list[str] = []
        for title in titles:
            if len(title) < TITLE_MIN_LENGTH_FILTER:
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

        # モデルの返却数が要求より少ない場合は、取得できた分だけ返します
        return ranked[:target_count] if len(ranked) >= target_count else ranked
