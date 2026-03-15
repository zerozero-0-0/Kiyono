"""決定論的なローカルスタブとGemini APIをサポートするLLMクライアントの抽象化。

このモジュールは以下を提供します:
- テキスト生成のためのプロバイダに依存しないクライアントインターフェース。
- Gemini APIの実装。
- 開発/テスト用の決定論的なローカルスタブ実装。
- 実行時設定に基づいて具体的なクライアントを選択するファクトリ関数。
"""

from __future__ import annotations

import hashlib
import re
from typing import Protocol

from google import genai
from google.genai import types


class LLMClient(Protocol):
    """言語モデルクライアントのプロトコル。"""

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        """プロンプトから非同期でテキストを生成します。"""
        ...

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """プロンプトから同期的にテキストを生成します。"""
        ...


class GeminiClient:
    """GoogleのGemini API用クライアント。"""

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash") -> None:
        """Geminiクライアントを初期化します。

        引数:
            api_key: Gemini APIキー。
            model_name: 使用するモデル識別子。
        """
        self._client = genai.Client(api_key=api_key)
        self._model_name = model_name

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        """Gemini経由で非同期でテキストを生成します。"""
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_prompt,
        )
        response = await self._client.aio.models.generate_content(
            model=self._model_name,
            contents=user_prompt,
            config=config,
        )
        return response.text or ""

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Gemini経由で同期的にテキストを生成します。"""
        # 指定がない場合の同期生成のデフォルト設定
        config = types.GenerateContentConfig(
            temperature=0.4,
            max_output_tokens=8000,
            system_instruction=system_prompt,
        )
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=user_prompt,
            config=config,
        )
        return response.text or ""


class LocalDeterministicStubClient:
    """決定論的なローカルスタブクライアント。

    出力は安定したハッシュとテンプレートロジックを使用してプロンプトコンテンツから生成されます。
    外部APIは呼び出しません。
    """

    async def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        """プロンプトから決定論的なテキストを非同期で生成します。"""
        mode = self._detect_mode(system_prompt=system_prompt, user_prompt=user_prompt)
        if mode == "titles":
            return self._generate_titles(user_prompt=user_prompt)
        return self._generate_article(system_prompt=system_prompt, user_prompt=user_prompt)

    def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """プロンプトから決定論的なテキストを同期的に生成します。"""
        mode = self._detect_mode(system_prompt=system_prompt, user_prompt=user_prompt)
        if mode == "titles":
            return self._generate_titles(user_prompt=user_prompt)
        return self._generate_article(system_prompt=system_prompt, user_prompt=user_prompt)

    def _detect_mode(self, *, system_prompt: str, user_prompt: str) -> str:
        text = f"{system_prompt}\n{user_prompt}".lower()
        title_signals = (
            "title",
            "titles",
            "タイトル",
            "見出し案",
            "n_titles",
            "5〜10",
            "5-10",
        )
        return "titles" if any(signal in text for signal in title_signals) else "article"

    def _generate_titles(self, *, user_prompt: str) -> str:
        keyword = self._extract_field(user_prompt, ("keyword", "キーワード")) or "LLMO"
        brief = self._extract_field(user_prompt, ("brief", "概要")) or "実務で使える知見を整理する"
        count = self._extract_int(user_prompt, ("n_titles", "title_count", "件数")) or 8
        count = max(5, min(count, 10))

        seed = self._seed_from_text(user_prompt)
        patterns = [
            "{k}とは何か？実務で失敗しない導入フレーム",
            "{k}を最短で定着させる5つの実践ステップ",
            "{k}の効果を最大化する設計原則【比較表付き】",
            "現場で使える{k}入門：要点を10分で把握",
            "{k}の導入障壁を突破する意思決定ガイド",
            "{k}で成果を出すためのKPI設計と運用法",
            "{k}をMECEで整理する：基本概念と実務活用",
            "{k}の成功事例に学ぶ再現可能な進め方",
            "{k}と従来手法の違いを一気に理解する",
            "{k}のFAQ：現場で頻出する疑問を先回り解説",
        ]

        rotated = self._rotate(patterns, seed % len(patterns))
        selected = rotated[:count]

        # briefのキーワードを軽く反映（完全一致不要）
        brief_token = self._pick_brief_token(brief)
        result_lines: list[str] = []
        for idx, pat in enumerate(selected, start=1):
            title = pat.format(k=keyword)
            if idx % 3 == 0 and brief_token:
                title = f"{title}（{brief_token}）"
            result_lines.append(f"{idx}. {title}")
        return "\n".join(result_lines)

    def _generate_article(self, *, system_prompt: str, user_prompt: str) -> str:
        title = (
            self._extract_field(user_prompt, ("selected_title", "title", "タイトル"))
            or "LLMO最適化記事"
        )
        keyword = self._extract_field(user_prompt, ("keyword", "キーワード")) or "LLMO"
        brief = (
            self._extract_field(user_prompt, ("brief", "概要"))
            or "生成AIに引用されやすい構造を実現する"
        )
        audience = self._extract_field(user_prompt, ("audience", "読者")) or "マーケティング担当者"

        signature = self._short_signature(system_prompt + "\n" + user_prompt)

        return (
            f"# {title}\n\n"
            f"## Summary\n"
            f"- {title}に対する結論は、{keyword}を構造化することが、"
            f"AIに引用されやすい記事を最短で作る方法である。\n\n"
            f"## Definitions\n"
            f"- {keyword}とは、AIに参照されやすい情報構造を設計する手法である。\n"
            f"- LLMOとは、要約・定義・比較可能性を高める実践である。\n\n"
            f"## 実装アプローチ（MECE）\n"
            f"- 企画: 検索意図を1記事1論点で明確化する\n"
            f"- 構成: Summary / Definitions / Comparison / FAQ を固定化する\n"
            f"- 生成: タイトル生成と本文生成を分離し、プロンプトで出力する\n"
            f"- 検証: 形式準拠（定義・表・FAQ）を機械チェックする\n\n"
            f"## 比較表\n"
            f"| 観点 | 従来SEO中心記事 | LLMO最適化記事 |\n"
            f"|---|---|---|\n"
            f"| 冒頭 | 前置きが長い | 結論先行（Summary） |\n"
            f"| 定義 | 暗黙的 | 「Xとは、〜である」を明示 |\n"
            f"| 比較可能性 | 低い | 表形式で高い |\n"
            f"| 引用されやすさ | 不安定 | 構造化により向上 |\n\n"
            f"## 想定読者への適用\n"
            f"- 想定読者: {audience}\n"
            f"- 記事概要の要点: {brief}\n"
            f"- 生成トレースID: `{signature}`\n\n"
            f"## FAQ\n"
            f"Q: なぜ最初にSummaryが必要ですか？\n"
            f"A: AIは冒頭情報を優先的に要約するため結論先行が引用率を高めます。読者の離脱を防ぎ情報の全体像を即座に提示できる点が重要です。一次情報を冒頭に集約することでLLMに価値ある部分を最初に認識させ、結果として実務における意思決定の速度を劇的に向上させることが可能となります。\n\n"
            f"Q: 定義文はどの程度厳密に書くべきですか？\n"
            f"A: 「{keyword}とは、〜である」の形式で1文で断定すると安定します。曖昧な表現を避け、辞書的な正確さと実務的な一次情報を融合させることで生成AIが情報を抽出しやすくなります。読者に対しても解釈ズレを防ぐ効果があり記事全体の信頼性を高める強固な土台として機能します。\n\n"
            f"Q: 表は必須ですか？\n"
            f"A: 比較軸を明示できるため必須です。構造化データは機械可読性が高く、LLMの要約精度に直結します。情報を表で整理すれば読者は短時間で要素を比較でき意思決定の速度が向上します。抽象的な説明を避け、具体的な一次情報や数値を表に落とし込むことで実務で活用可能な記事になります。\n"
        )

    @staticmethod
    def _seed_from_text(text: str) -> int:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return int(digest[:8], 16)

    @staticmethod
    def _short_signature(text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return digest[:10]

    @staticmethod
    def _rotate(items: list[str], offset: int) -> list[str]:
        if not items:
            return items
        offset = offset % len(items)
        return items[offset:] + items[:offset]

    @staticmethod
    def _extract_field(text: str, keys: tuple[str, ...]) -> str | None:
        for key in keys:
            # Supports: key: value / key = value
            pattern = rf"(?:^|\n)\s*{re.escape(key)}\s*[:=]\s*(.+)"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:
                    return value
        return None

    @staticmethod
    def _extract_int(text: str, keys: tuple[str, ...]) -> int | None:
        for key in keys:
            pattern = rf"(?:^|\n)\s*{re.escape(key)}\s*[:=]\s*(\d+)"
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    @staticmethod
    def _pick_brief_token(brief: str) -> str | None:
        # Pick a short informative token from Japanese/ASCII text.
        candidates: list[str] = re.findall(r"[A-Za-z0-9_]{3,}|[ぁ-んァ-ヶ一-龠]{2,}", brief)
        if not candidates:
            return None

        def _sort_key(item: str) -> tuple[int, str]:
            return (-len(item), item)

        # Deterministic pick: longest, then lexicographic.
        candidates.sort(key=_sort_key)
        return candidates[0][:12]


def get_llm_client(provider: str = "stub") -> LLMClient:
    """プロバイダ名でLLMクライアントを返します。

    引数:
        provider: Provider identifier. Currently supports "gemini" and "stub".

    戻り値:
        Instance conforming to `LLMClient`.
    """
    from app.config import get_settings

    settings = get_settings()

    if provider == "gemini":
        api_key = settings.provider_api_key_value
        if api_key:
            return GeminiClient(api_key=api_key, model_name=settings.llm_model)

    return LocalDeterministicStubClient()
