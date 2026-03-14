"""LLMO validation service.

This module provides a lightweight, explainable validator for generated markdown
articles. It checks whether key LLMO structural requirements are present:

1. Summary-first structure
2. Strict definition sentence(s) in the form: "Xとは、〜である"
3. Markdown table usage
4. FAQ section at the end
5. Basic heading hierarchy sanity
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern
from typing import TypedDict


class CheckResult(TypedDict):
    """Serializable validation check entry."""

    name: str
    passed: bool
    detail: str


class StatsResult(TypedDict):
    """Serializable validation stats."""

    definition_count: int
    table_count: int
    has_faq_heading: bool
    h2_count: int
    h3_count: int


class ValidationResult(TypedDict):
    """Serializable validation payload."""

    passed: bool
    checks: list[CheckResult]
    score: int
    max_score: int
    missing_actions: list[str]
    stats: StatsResult


@dataclass(frozen=True)
class ValidationCheck:
    """Represents one validation check result."""

    name: str
    passed: bool
    detail: str


class LLMOValidator:
    """Validate markdown content against LLMO structural requirements."""

    _definition_pattern: Pattern[str] = re.compile(
        r"[^\n。]{1,80}とは、[^。\n]{3,300}である[。.]?",
        flags=re.MULTILINE,
    )
    _h2_pattern: Pattern[str] = re.compile(r"^##\s+.+$", flags=re.MULTILINE)
    _h3_pattern: Pattern[str] = re.compile(r"^###\s+.+$", flags=re.MULTILINE)
    _faq_heading_pattern: Pattern[str] = re.compile(
        r"^##\s*(FAQ|Q&A|よくある質問)\b.*$",
        flags=re.IGNORECASE | re.MULTILINE,
    )
    _table_row_pattern: Pattern[str] = re.compile(r"^\|.+\|$", flags=re.MULTILINE)
    _table_delim_pattern: Pattern[str] = re.compile(
        r"^\|\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$",
        flags=re.MULTILINE,
    )
    _q_pattern: Pattern[str] = re.compile(
        r"^\s*(Q[:：]|質問[:：])",
        flags=re.MULTILINE | re.IGNORECASE,
    )
    _a_pattern: Pattern[str] = re.compile(
        r"^\s*(A[:：]|回答[:：])",
        flags=re.MULTILINE | re.IGNORECASE,
    )

    def validate(self, markdown_article: str) -> ValidationResult:
        """Validate a markdown article and return a structured report."""
        text = markdown_article.strip()

        checks: list[ValidationCheck] = []

        summary_passed, summary_detail = self._check_summary_first(text)
        checks.append(ValidationCheck("summary_first", summary_passed, summary_detail))

        definition_count = self._count_definitions(text)
        definitions_passed = definition_count >= 1
        checks.append(
            ValidationCheck(
                "strict_definitions",
                definitions_passed,
                f"Definition sentences found: {definition_count}",
            )
        )

        table_passed, table_count = self._check_markdown_table(text)
        checks.append(
            ValidationCheck(
                "markdown_table",
                table_passed,
                f"Detected table blocks: {table_count}",
            )
        )

        faq_passed, faq_detail = self._check_faq_section(text)
        checks.append(ValidationCheck("faq_section", faq_passed, faq_detail))

        hierarchy_passed, hierarchy_detail = self._check_heading_hierarchy(text)
        checks.append(ValidationCheck("heading_hierarchy", hierarchy_passed, hierarchy_detail))

        passed_count = sum(1 for check in checks if check.passed)
        max_score = len(checks)
        overall_passed = passed_count == max_score
        missing_actions = self._build_missing_actions(checks)

        check_results: list[CheckResult] = [
            {"name": check.name, "passed": check.passed, "detail": check.detail} for check in checks
        ]

        stats: StatsResult = {
            "definition_count": definition_count,
            "table_count": table_count,
            "has_faq_heading": bool(self._faq_heading_pattern.search(text)),
            "h2_count": len(self._h2_pattern.findall(text)),
            "h3_count": len(self._h3_pattern.findall(text)),
        }

        return {
            "passed": overall_passed,
            "checks": check_results,
            "score": passed_count,
            "max_score": max_score,
            "missing_actions": missing_actions,
            "stats": stats,
        }

    def _check_summary_first(self, text: str) -> tuple[bool, str]:
        """Check whether the article starts with a summary-like section."""
        if not text:
            return False, "Article is empty."

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return False, "Article has no non-empty lines."

        first_line = lines[0]
        greeting_markers = (
            "こんにちは",
            "はじめに",
            "本記事では",
            "この記事では",
            "今日は",
            "まずは",
        )
        if any(marker in first_line for marker in greeting_markers):
            clipped = first_line[:40]
            return False, f"First line looks like an introduction: '{clipped}'"

        summary_markers = ("summary", "要約", "結論", "結論先行")
        first_line_lower = first_line.lower()
        if any(marker in first_line_lower for marker in summary_markers):
            return True, "First non-empty line indicates summary/conclusion."

        top_chunk = "\n".join(lines[:8]).lower()
        has_summary_heading = (
            "## summary" in top_chunk or "## 要約" in top_chunk or "## 結論" in top_chunk
        )
        if has_summary_heading:
            return True, "Top section contains summary/conclusion heading."

        if len(first_line) <= 120 and "。" in first_line:
            return True, "Top line appears concise; treated as summary-first."

        return False, "Summary-first signal not found near top."

    def _count_definitions(self, text: str) -> int:
        """Count strict definition-pattern sentences."""
        return len(self._definition_pattern.findall(text))

    def _check_markdown_table(self, text: str) -> tuple[bool, int]:
        """Check markdown table presence and estimate table block count."""
        rows = self._table_row_pattern.findall(text)
        delims = self._table_delim_pattern.findall(text)

        if not rows or not delims:
            return False, 0

        table_count = len(delims)
        return table_count >= 1, table_count

    def _check_faq_section(self, text: str) -> tuple[bool, str]:
        """Check FAQ section heading and minimal Q/A signal."""
        heading_match = self._faq_heading_pattern.search(text)
        if heading_match is None:
            return False, "FAQ heading not found. Use '## FAQ' or equivalent."

        start_idx = heading_match.start()
        near_end = start_idx >= int(len(text) * 0.6)
        faq_tail = text[start_idx:]

        q_count = len(self._q_pattern.findall(faq_tail))
        a_count = len(self._a_pattern.findall(faq_tail))

        if q_count == 0 or a_count == 0:
            return False, "FAQ heading found, but Q/A pairs are missing."

        if not near_end:
            return True, "FAQ exists with Q/A pairs (not at very end, acceptable)."

        return True, "FAQ heading and Q/A pairs found near article end."

    def _check_heading_hierarchy(self, text: str) -> tuple[bool, str]:
        """Check basic h2/h3 hierarchy sanity."""
        h2_count = len(self._h2_pattern.findall(text))
        h3_count = len(self._h3_pattern.findall(text))

        if h3_count > 0 and h2_count == 0:
            return False, "Found h3 headings without any h2 headings."
        return True, f"h2={h2_count}, h3={h3_count}"

    def _build_missing_actions(self, checks: list[ValidationCheck]) -> list[str]:
        """Generate actionable suggestions for failed checks."""
        actions: list[str] = []

        for check in checks:
            if check.passed:
                continue

            if check.name == "summary_first":
                actions.append("冒頭を挨拶ではなく結論（Summary）から開始してください。")
            elif check.name == "strict_definitions":
                actions.append("「Xとは、〜である」の形式で定義文を最低1つ追加してください。")
            elif check.name == "markdown_table":
                actions.append("Markdown表（| 区切り）を1つ以上追加してください。")
            elif check.name == "faq_section":
                actions.append("記事末尾に「## FAQ」見出しとQ/Aペアを追加してください。")
            elif check.name == "heading_hierarchy":
                actions.append("h3を使う場合は先にh2を配置してください。")
            else:
                actions.append(f"{check.name} を満たすよう本文構造を修正してください。")

        return actions
