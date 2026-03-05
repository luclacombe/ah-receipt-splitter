"""AH Receipt Splitter -- Streamlit app for splitting grocery costs with a roommate."""

import streamlit as st
from dotenv import load_dotenv

from components.language import render_language_select
from components.review import render_review
from components.summary import render_summary
from components.upload import render_upload
from i18n import UI_STRINGS
from state import ensure_dirs, init_state
from theme import inject_theme, render_logo_header

load_dotenv()


def main() -> None:
    """Application entry point — configure page and route to the active step."""
    lang = st.session_state.get("language", "en")
    title = UI_STRINGS[lang]["app_title"]
    st.set_page_config(page_title=f"AH {title}", page_icon="\U0001f6d2", layout="wide")
    inject_theme()
    render_logo_header()
    ensure_dirs()
    init_state()

    step = st.session_state.step
    if step == "language":
        render_language_select()
    elif step == "upload":
        render_upload()
    elif step == "review":
        render_review()
    elif step == "summary":
        render_summary()


if __name__ == "__main__":
    main()
