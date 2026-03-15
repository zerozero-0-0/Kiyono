"""LLMOコンテンツジェネレータープロジェクトのためのStreamlit UI。"""

from typing import Any

import httpx
import streamlit as st

API_BASE_URL = "http://localhost:8000"


def init_session_state() -> None:
    """セッション状態変数を初期化します。"""
    if "titles" not in st.session_state:
        st.session_state["titles"] = []
    if "selected_title" not in st.session_state:
        st.session_state["selected_title"] = None
    if "article" not in st.session_state:
        st.session_state["article"] = None
    if "validation_report" not in st.session_state:
        st.session_state["validation_report"] = None


def generate_titles(keyword: str, brief: str, n_titles: int) -> None:
    """バックエンドを呼び出してタイトルを生成します。"""
    with st.status("✨ タイトル候補を生成しています...", expanded=True) as status:
        try:
            st.write("タイトルを作成中...")
            response = httpx.post(
                f"{API_BASE_URL}/generate/titles",
                json={"keyword": keyword, "brief": brief, "n_titles": n_titles},
                timeout=30.0,
            )
            _ = response.raise_for_status()
            data: dict[str, Any] = response.json()
            st.session_state["titles"] = data.get("titles", [])
            st.session_state["selected_title"] = None
            st.session_state["article"] = None
            st.session_state["validation_report"] = None
            status.update(label="タイトル生成が完了しました！", state="complete", expanded=False)
        except Exception as e:
            status.update(label="タイトル生成に失敗しました", state="error", expanded=True)
            _ = st.error(f"Error generating titles: {e}")


def generate_article(selected_title: str, keyword: str, brief: str) -> None:
    """バックエンドを呼び出して記事を生成します。"""
    with st.status("📝 記事を生成しています...（最大1分程度かかります）", expanded=True) as status:
        try:
            st.write("記事を作成中...")
            response = httpx.post(
                f"{API_BASE_URL}/generate/article",
                json={
                    "selected_title": selected_title,
                    "keyword": keyword,
                    "brief": brief,
                },
                timeout=60.0,
            )
            st.write("記事の要件を検証中...")
            _ = response.raise_for_status()
            data: dict[str, Any] = response.json()
            st.session_state["article"] = data.get("markdown_article")
            st.session_state["validation_report"] = data.get("validation_report")
            status.update(
                label="記事の生成と検証が完了しました！", state="complete", expanded=False
            )
        except Exception as e:
            status.update(label="記事生成に失敗しました", state="error", expanded=True)
            _ = st.error(f"Error generating article: {e}")


def main() -> None:
    """メインのStreamlitアプリケーションをレンダリングします。"""
    st.set_page_config(
        page_title="LLMO Content Generator",
        page_icon="🧠",
        layout="wide",
    )
    init_session_state()

    _ = st.title("LLMO向けコンテンツ生成")

    _ = st.sidebar.header("記事の要件を入力")

    keyword: str = str(st.sidebar.text_input("メインキーワード", value="LLMO") or "")
    brief: str = str(
        st.sidebar.text_area(
            "記事の概要",
            value="生成AIに引用されやすい記事の書き方をまとめたい",
            height=150,
        )
        or ""
    )
    n_titles: int = int(st.sidebar.slider("タイトル生成数", min_value=5, max_value=10, value=8))

    if st.sidebar.button("タイトル候補を生成", type="primary"):
        if not keyword.strip() or not brief.strip():
            _ = st.sidebar.error("キーワードと概要を入力してください。")
        else:
            generate_titles(keyword, brief, n_titles)

    if st.session_state["titles"]:
        _ = st.header("タイトルを選択")
        selected: str | None = st.radio(
            "記事のタイトルを以下から1つ選んでください:",
            st.session_state["titles"],
            index=0,
        )

        if st.button("記事を生成する", type="primary"):
            st.session_state["selected_title"] = selected
            if selected:
                generate_article(str(selected), keyword, brief)

    if st.session_state["article"]:
        _ = st.divider()
        _ = st.header("生成された記事")

        col1, col2 = st.columns([2, 1])

        with col1:
            _ = st.subheader("プレビュー")
            _ = st.markdown(st.session_state["article"])

            with st.expander("Markdownのソースコードを表示"):
                _ = st.code(st.session_state["article"], language="markdown")

        with col2:
            _ = st.subheader("LLMO 検査レポート")
            report: dict[str, Any] | None = st.session_state["validation_report"]
            if report:
                passed = bool(report.get("passed", False))
                score = int(report.get("score", 0))
                checks: list[dict[str, Any]] = report.get("checks", [])

                # スコアの最大値を実際のチェック項目数から動的に取得
                max_score = len(checks)

                if passed:
                    _ = st.success(f"✅ 合格！ スコア: {score}/{max_score}")
                else:
                    _ = st.warning(f"⚠️ 要改善 スコア: {score}/{max_score}")

                _ = st.write("**詳細な検査結果:**")

                # チェック項目の表示名を日本語にマッピング
                name_map = {
                    "h1_title": "H1見出し（タイトル）",
                    "ul_lists": "箇条書き（UL）の使用",
                    "summary_first": "結論先行の構成",
                    "strict_definitions": "「とは〜である」形式の定義",
                    "markdown_table": "Markdown表の使用",
                    "faq_section": "FAQセクション",
                    "heading_hierarchy": "見出し階層（H2/H3）",
                }

                for check in checks:
                    icon = "✅" if check.get("passed") else "❌"
                    raw_name = check.get("name", "")
                    ja_name = name_map.get(raw_name, raw_name)
                    _ = st.write(f"{icon} **{ja_name}**")
                    _ = st.caption(check.get("detail"))

                missing_actions: list[str] = report.get("missing_actions", [])
                if missing_actions:
                    _ = st.write("**推奨される修正アクション:**")
                    for action in missing_actions:
                        _ = st.info(action)


if __name__ == "__main__":
    main()
