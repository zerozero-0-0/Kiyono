"""LLMOコンテンツ生成のためのAPIリクエスト/レスポンススキーマ。"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.constants import (
    MAX_AUDIENCE_LENGTH,
    MAX_BRIEF_LENGTH,
    MAX_KEYWORD_LENGTH,
    MAX_TITLE_LENGTH,
    MAX_TONE_LENGTH,
    TITLE_MAX_GENERATION_COUNT,
    TITLE_MIN_GENERATION_COUNT,
)


class ErrorResponse(BaseModel):
    """共通のエラーレスポンススキーマ。"""

    detail: str = Field(..., description="Human-readable error detail.")
    code: str | None = Field(default=None, description="Optional machine-readable error code.")


class GenerateTitlesRequest(BaseModel):
    """タイトル生成のためのリクエストスキーマ。"""

    keyword: str = Field(
        ..., min_length=1, max_length=MAX_KEYWORD_LENGTH, description="Main topic keyword."
    )
    brief: str = Field(
        ...,
        min_length=1,
        max_length=MAX_BRIEF_LENGTH,
        description="Article overview, audience, and context.",
    )
    n_titles: int = Field(
        default=8,
        ge=TITLE_MIN_GENERATION_COUNT,
        le=TITLE_MAX_GENERATION_COUNT,
        description="Number of title candidates to generate.",
    )

    @field_validator("keyword", "brief")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """トリミング後、テキストフィールドが空でないことを確認します。"""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be blank.")
        return stripped


class GenerateTitlesResponse(BaseModel):
    """タイトル生成のためのレスポンススキーマ。"""

    titles: list[str] = Field(
        ...,
        min_length=1,
        description="Generated title candidates.",
    )
    rationale: list[str] | None = Field(
        default=None,
        description="Optional per-title rationale.",
    )

    @field_validator("titles")
    @classmethod
    def _validate_titles(cls, values: list[str]) -> list[str]:
        """生成されたタイトルを検証して正規化します。"""
        normalized = [v.strip() for v in values if v.strip()]
        if not normalized:
            raise ValueError("At least one non-empty title is required.")
        if len(normalized) > TITLE_MAX_GENERATION_COUNT:
            raise ValueError(f"A maximum of {TITLE_MAX_GENERATION_COUNT} titles is allowed.")
        return normalized

    @field_validator("rationale")
    @classmethod
    def _validate_rationale(cls, values: list[str] | None) -> list[str] | None:
        """提供されている場合、根拠エントリを正規化します。"""
        if values is None:
            return None
        normalized = [v.strip() for v in values if v.strip()]
        return normalized or None


class GenerateArticleRequest(BaseModel):
    """記事生成のためのリクエストスキーマ。"""

    selected_title: str = Field(
        ...,
        min_length=1,
        max_length=MAX_TITLE_LENGTH,
        description="Selected title for article generation.",
    )
    keyword: str = Field(
        ..., min_length=1, max_length=MAX_KEYWORD_LENGTH, description="Main topic keyword."
    )
    brief: str = Field(
        ...,
        min_length=1,
        max_length=MAX_BRIEF_LENGTH,
        description="Article overview, audience, and context.",
    )
    audience: str | None = Field(
        default=None,
        max_length=MAX_AUDIENCE_LENGTH,
        description="Target audience (optional).",
    )
    tone: str | None = Field(
        default=None,
        max_length=MAX_TONE_LENGTH,
        description="Desired writing tone (optional).",
    )

    @field_validator("selected_title", "keyword", "brief", mode="before")
    @classmethod
    def _strip_required_fields(cls, value: object) -> object:
        """必須の文字列フィールドの空白をトリミングします。"""
        if isinstance(value, str):
            value = value.strip()
        return value

    @field_validator("selected_title", "keyword", "brief")
    @classmethod
    def _required_fields_not_blank(cls, value: str) -> str:
        """必須のテキストフィールドが空でないことを確認します。"""
        if not value:
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("audience", "tone", mode="before")
    @classmethod
    def _normalize_optional_fields(cls, value: object) -> object:
        """オプションのテキストフィールドを正規化します。

        空の場合はNone、それ以外はトリミングします。
        """
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        return value


class ValidationCheck(BaseModel):
    """LLMO要件に対する単一の検証チェック結果。"""

    name: str = Field(..., description="Check name.")
    passed: bool = Field(..., description="Whether the check passed.")
    detail: str = Field(..., description="Explanation of the check result.")


class ValidationReport(BaseModel):
    """生成された記事の品質と構造に関する検証レポート。"""

    passed: bool = Field(..., description="Overall validation status.")
    checks: list[ValidationCheck] = Field(
        default_factory=list,
        description="Detailed per-rule validation checks.",
    )
    missing_actions: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations for missing requirements.",
    )
    score: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Optional aggregate score.",
    )


class GenerateArticleResponse(BaseModel):
    """記事生成のためのレスポンススキーマ。"""

    markdown_article: str = Field(
        ...,
        min_length=1,
        description="Generated markdown article body.",
    )
    validation_report: ValidationReport = Field(
        ...,
        description="LLMO structure and quality validation result.",
    )
    json_ld: dict[str, object] | None = Field(
        default=None,
        description="Optional Schema.org JSON-LD payload.",
    )

    @field_validator("markdown_article")
    @classmethod
    def _article_not_blank(cls, value: str) -> str:
        """トリミング後、生成された記事が空でないことを確認します。"""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Generated article must not be blank.")
        return stripped
