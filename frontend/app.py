"""Streamlit UI for the LLMO content generator project."""

import httpx
import streamlit as st

API_BASE_URL = "http://localhost:8000"


def init_session_state() -> None:
    """Initialize session state variables."""
    if "titles" not in st.session_state:
        st.session_state.titles = []
    if "selected_title" not in st.session_state:
        st.session_state.selected_title = None
    if "article" not in st.session_state:
        st.session_state.article = None
    if "validation_report" not in st.session_state:
        st.session_state.validation_report = None


def generate_titles(keyword: str, brief: str, n_titles: int) -> None:
    """Call backend to generate titles."""
    with st.spinner("Generating titles..."):
        try:
            response = httpx.post(
                f"{API_BASE_URL}/generate/titles",
                json={"keyword": keyword, "brief": brief, "n_titles": n_titles},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            st.session_state.titles = data.get("titles", [])
            st.session_state.selected_title = None
            st.session_state.article = None
            st.session_state.validation_report = None
        except Exception as e:
            _ = st.error(f"Error generating titles: {e}")


def generate_article(selected_title: str, keyword: str, brief: str) -> None:
    """Call backend to generate article."""
    with st.spinner("Generating article..."):
        try:
            response = httpx.post(
                f"{API_BASE_URL}/generate/article",
                json={
                    "selected_title": selected_title,
                    "keyword": keyword,
                    "brief": brief,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            st.session_state.article = data.get("markdown_article")
            st.session_state.validation_report = data.get("validation_report")
        except Exception as e:
            _ = st.error(f"Error generating article: {e}")


def main() -> None:
    """Render the main Streamlit application."""
    st.set_page_config(
        page_title="LLMO Content Generator",
        page_icon="🧠",
        layout="wide",
    )
    init_session_state()

    _ = st.title("LLMO Content Generator")
    _ = st.caption("Intern Coding Challenge Prototype")

    _ = st.sidebar.header("Step 1: Input Brief")

    keyword = st.sidebar.text_input("Main Keyword", value="LLMO")
    brief = st.sidebar.text_area(
        "Article Brief",
        value="生成AIに引用されやすい記事の書き方をまとめたい",
        height=150,
    )
    n_titles = st.sidebar.slider("Number of Titles", min_value=5, max_value=10, value=8)

    if st.sidebar.button("Generate Titles", type="primary"):
        if not keyword.strip() or not brief.strip():
            _ = st.sidebar.error("Keyword and Brief are required.")
        else:
            generate_titles(keyword, brief, n_titles)

    if st.session_state.titles:
        _ = st.header("Step 2: Select a Title")
        selected = st.radio(
            "Choose a title for your article:",
            st.session_state.titles,
            index=0,
        )

        if st.button("Generate Article", type="primary"):
            st.session_state.selected_title = selected
            if selected:
                generate_article(str(selected), keyword, brief)

    if st.session_state.article:
        _ = st.divider()
        _ = st.header("Step 3: Review Generated Article")

        col1, col2 = st.columns([2, 1])

        with col1:
            _ = st.subheader("Markdown Article")
            _ = st.markdown(st.session_state.article)

            with st.expander("Show Raw Markdown"):
                _ = st.code(st.session_state.article, language="markdown")

        with col2:
            _ = st.subheader("LLMO Validation Report")
            report = st.session_state.validation_report
            if report:
                passed = report.get("passed", False)
                score = report.get("score", 0)
                max_score = report.get("max_score", 5)

                if passed:
                    _ = st.success(f"Passed! Score: {score}/{max_score}")
                else:
                    _ = st.warning(f"Needs Improvement. Score: {score}/{max_score}")

                _ = st.write("**Detailed Checks:**")
                for check in report.get("checks", []):
                    icon = "✅" if check.get("passed") else "❌"
                    _ = st.write(f"{icon} **{check.get('name')}**")
                    _ = st.caption(check.get("detail"))

                missing_actions = report.get("missing_actions", [])
                if missing_actions:
                    _ = st.write("**Recommended Actions:**")
                    for action in missing_actions:
                        _ = st.info(action)


if __name__ == "__main__":
    main()
