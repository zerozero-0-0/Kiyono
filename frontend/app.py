"""Minimal Streamlit app skeleton for the LLMO content generator project."""

import streamlit as st


def main() -> None:
    """Render the initial Streamlit UI skeleton."""
    st.set_page_config(
        page_title="LLMO Content Generator",
        page_icon="🧠",
        layout="wide",
    )

    st.title("LLMO Content Generator")
    st.caption("Intern Coding Challenge Prototype")

    st.markdown(
        """
この画面は最小構成のフロントエンド雛形です。
次のステップで `FastAPI` バックエンドと接続して、タイトル生成と記事生成を実装します。
"""
    )

    with st.expander("Setup hints", expanded=True):
        st.markdown(
            """
### 1) Environment
- `.env` を作成して API キーを設定
- 推奨: Python 3.11+

### 2) Backend 起動
- `uv run uvicorn app.main:app --reload --port 8000`

### 3) Frontend 起動
- `uv run streamlit run frontend/app.py`

### 4) 確認先
- API Docs: `http://localhost:8000/docs`
- UI: `http://localhost:8501`
"""
        )

    st.divider()
    st.subheader("Status")
    st.info("Frontend skeleton is ready. Backend integration comes next.")


if __name__ == "__main__":
    main()
