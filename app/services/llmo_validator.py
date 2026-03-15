"""LLMOバリデーションサービス。

このモジュールは、生成されたMarkdown記事に対する軽量で説明可能なバリデータを提供します。
主要なLLMO構造要件が存在するかどうかを確認します:

1. 結論先行（Summary-first）の構造
2. 「Xとは、〜である」の形式の厳密な定義文
3. Markdown表の使用
4. 末尾のFAQセクション
5. 基本的な見出し階層の健全性
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern
from typing import TypedDict


class CheckResult(TypedDict):
    """シリアライズ可能な検証チェックエントリ。"""

    name: str
    passed: bool
    detail: str


class StatsResult(TypedDict):
    """シリアライズ可能な検証統計情報。"""

    definition_count: int
    table_count: int
    has_faq_heading: bool
    h2_count: int
    h3_count: int


class ValidationResult(TypedDict):
    """シリアライズ可能な検証ペイロード。"""

    passed: bool
    checks: list[CheckResult]
    score: int
    max_score: int
    missing_actions: list[str]
    stats: StatsResult


@dataclass(frozen=True)
class ValidationCheck:
    """1つの検証チェック結果を表します。"""

    name: str
    passed: bool
    detail: str


class LLMOValidator:
    """MarkdownコンテンツがLLMOの構造要件を満たしているか検証します。"""

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
        r"^\s*(?:-\s*)?\**(?:Q|質問)\d*\**[:：.]?",
        flags=re.MULTILINE | re.IGNORECASE,
    )
    _a_pattern: Pattern[str] = re.compile(
        r"^\s*(?:-\s*)?\**(?:A|回答)\d*\**[:：.]?",
        flags=re.MULTILINE | re.IGNORECASE,
    )
    _h1_pattern: Pattern[str] = re.compile(r"^#\s+.+$", flags=re.MULTILINE)
    _ul_pattern: Pattern[str] = re.compile(r"^[ \t]*[-*]\s+.+$", flags=re.MULTILINE)
    _a_block_pattern: Pattern[str] = re.compile(
        r"^\s*(?:-\s*)?\**(?:A|回答)\d*\**[:：.]?\s*(.*?)(?=\n\s*(?:-\s*)?\**(?:Q|質問|A|回答)\d*\**[:：.]?|\n#|$)",
        flags=re.MULTILINE | re.IGNORECASE | re.DOTALL,
    )

    def validate(self, markdown_article: str) -> ValidationResult:
        """Markdown記事を検証し、構造化されたレポートを返します。"""
        text = markdown_article.strip()

        checks: list[ValidationCheck] = []

        h1_passed, h1_detail = self._check_h1_title(text)
        checks.append(ValidationCheck("h1_title", h1_passed, h1_detail))

        ul_passed, ul_detail = self._check_ul_usage(text)
        checks.append(ValidationCheck("ul_lists", ul_passed, ul_detail))

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

    def _check_h1_title(self, text: str) -> tuple[bool, str]:
        """記事にh1タイトルが存在するか確認します。"""
        if self._h1_pattern.search(text):
            return True, "H1 title found."
        return False, "H1 title (#) not found."

    def _check_ul_usage(self, text: str) -> tuple[bool, str]:
        """記事内に箇条書き（ul）が十分に使用されているか確認します。"""
        count = len(self._ul_pattern.findall(text))
        if count >= 3:
            return True, f"Found {count} UL items."
        return False, f"Not enough UL items (found {count}, expected at least 3)."

    def _check_summary_first(self, text: str) -> tuple[bool, str]:
        """記事が要約のようなセクションで始まっているか確認します。"""
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
        """厳密な定義パターンの文をカウントします。"""
        return len(self._definition_pattern.findall(text))

    def _check_markdown_table(self, text: str) -> tuple[bool, int]:
        """Markdown表の存在を確認し、表のブロック数を推定します。"""
        rows = self._table_row_pattern.findall(text)
        delims = self._table_delim_pattern.findall(text)

        if not rows or not delims:
            return False, 0

        table_count = len(delims)
        return table_count >= 1, table_count

    def _check_faq_section(self, text: str) -> tuple[bool, str]:
        """FAQセクションの見出しとQ/Aペア、および回答の長さを確認します。"""
        heading_match = self._faq_heading_pattern.search(text)
        if heading_match is None:
            return False, "FAQ heading not found. Use '## FAQ' or equivalent."

        start_idx = heading_match.start()
        near_end = start_idx >= int(len(text) * 0.6)
        faq_tail = text[start_idx:]

        q_count = len(self._q_pattern.findall(faq_tail))
        answers = [m.group(1).strip() for m in self._a_block_pattern.finditer(faq_tail)]

        if q_count == 0 or len(answers) == 0:
            return False, "FAQ heading found, but Q/A pairs are missing."

        # 回答の文字数（空白除去後）が極端に短すぎないか、長すぎないかをチェック（30〜300文字のゆとりを持たせた範囲）
        lengths = [len(re.sub(r"\s+", "", a)) for a in answers]
        invalid_lengths = [l for l in lengths if not (30 <= l <= 300)]

        detail_msg = f"Q/A found. Answer lengths: {lengths}."
        if invalid_lengths:
            return False, f"FAQ answers length out of bounds (30-300 chars). {detail_msg}"

        if not near_end:
            return True, f"FAQ exists (not at very end). {detail_msg}"

        return True, f"FAQ heading and valid Q/A found near article end. {detail_msg}"

    def _check_heading_hierarchy(self, text: str) -> tuple[bool, str]:
        """基本的なh2/h3階層の健全性を確認します。"""
        h2_count = len(self._h2_pattern.findall(text))
        h3_count = len(self._h3_pattern.findall(text))

        if h3_count > 0 and h2_count == 0:
            return False, "Found h3 headings without any h2 headings."
        return True, f"h2={h2_count}, h3={h3_count}"

    def _build_missing_actions(self, checks: list[ValidationCheck]) -> list[str]:
        """失敗したチェックに対する実行可能な提案を生成します。"""
        actions: list[str] = []

        for check in checks:
            if check.passed:
                continue

            if check.name == "h1_title":
                actions.append("記事の先頭に「# タイトル」の形式でh1見出しを追加してください。")
            elif check.name == "ul_lists":
                actions.append(
                    "見出しの内容に箇条書き（ul: `- `）を適切に使用して構造化してください。"
                )
            elif check.name == "summary_first":
                actions.append("冒頭を挨拶ではなく結論（Summary）から開始してください。")
            elif check.name == "strict_definitions":
                actions.append("「Xとは、〜である」の形式で定義文を最低1つ追加してください。")
            elif check.name == "markdown_table":
                actions.append("Markdown表（| 区切り）を1つ以上追加してください。")
            elif check.name == "faq_section":
                actions.append(
                    "記事末尾に「## FAQ」見出しとQ/Aペアを追加し、各回答を130〜140文字程度にまとめてください。"
                )
            elif check.name == "heading_hierarchy":
                actions.append("h3を使う場合は先にh2を配置してください。")
            else:
                actions.append(f"{check.name} を満たすよう本文構造を修正してください。")

        return actions
