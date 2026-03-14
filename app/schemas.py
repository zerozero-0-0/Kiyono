"""API request/response schemas for LLMO content generation."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ErrorResponse(BaseModel):
    """Common error response schema."""

    detail: str = Field(..., description="Human-readable error detail.")
    code: str | None = Field(default=None, description="Optional machine-readable error code.")


class GenerateTitlesRequest(BaseModel):
    """Request schema for title generation."""

    keyword: str = Field(..., min_length=1, max_length=200, description="Main topic keyword.")
    brief: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Article overview, audience, and context.",
    )
    n_titles: int = Field(
        default=8,
        ge=1,
        le=10,
        description="Number of title candidates to generate.",
    )

    @field_validator("keyword", "brief")
    @classmethod
    def _must_not_be_blank(cls, value: str) -> str:
        """Ensure text fields are not blank after trimming."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field must not be blank.")
        return stripped


class GenerateTitlesResponse(BaseModel):
    """Response schema for title generation."""

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
        """Validate and normalize generated titles."""
        normalized = [v.strip() for v in values if v.strip()]
        if not normalized:
            raise ValueError("At least one non-empty title is required.")
        if len(normalized) > 10:
            raise ValueError("A maximum of 10 titles is allowed.")
        return normalized

    @field_validator("rationale")
    @classmethod
    def _validate_rationale(cls, values: list[str] | None) -> list[str] | None:
        """Normalize rationale entries if provided."""
        if values is None:
            return None
        normalized = [v.strip() for v in values if v.strip()]
        return normalized or None


class GenerateArticleRequest(BaseModel):
    """Request schema for article generation."""

    selected_title: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Selected title for article generation.",
    )
    keyword: str = Field(..., min_length=1, max_length=200, description="Main topic keyword.")
    brief: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Article overview, audience, and context.",
    )
    audience: str | None = Field(
        default=None,
        max_length=300,
        description="Target audience (optional).",
    )
    tone: str | None = Field(
        default=None,
        max_length=100,
        description="Desired writing tone (optional).",
    )

    @field_validator("selected_title", "keyword", "brief", mode="before")
    @classmethod
    def _strip_required_fields(cls, value: object) -> object:
        """Trim whitespace for required string fields."""
        if isinstance(value, str):
            value = value.strip()
        return value

    @field_validator("selected_title", "keyword", "brief")
    @classmethod
    def _required_fields_not_blank(cls, value: str) -> str:
        """Ensure required text fields are not blank."""
        if not value:
            raise ValueError("Field must not be blank.")
        return value

    @field_validator("audience", "tone", mode="before")
    @classmethod
    def _normalize_optional_fields(cls, value: object) -> object:
        """Normalize optional text fields: blank -> None, otherwise strip."""
        if value is None:
            return None
        if isinstance(value, str):
            stripped = value.strip()
            return stripped if stripped else None
        return value


class ValidationCheck(BaseModel):
    """Single validation check result for LLMO requirements."""

    name: str = Field(..., description="Check name.")
    passed: bool = Field(..., description="Whether the check passed.")
    detail: str = Field(..., description="Explanation of the check result.")


class ValidationReport(BaseModel):
    """Validation report for generated article quality and structure."""

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
    """Response schema for article generation."""

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
        """Ensure generated article is not blank after trimming."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Generated article must not be blank.")
        return stripped
