"""Session state initialization and management."""

import streamlit as st

from config import PROCESSED_DIR, RECEIPTS_DIR


def ensure_dirs() -> None:
    """Create data directories if they don't exist."""
    RECEIPTS_DIR.mkdir(exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)


def init_state() -> None:
    """Initialize session state with defaults."""
    if "step" not in st.session_state:
        st.session_state.step = "language"
    if "language" not in st.session_state:
        st.session_state.language = "en"
    if "receipts" not in st.session_state:
        st.session_state.receipts = []
    if "current_idx" not in st.session_state:
        st.session_state.current_idx = 0
    if "assignments" not in st.session_state:
        st.session_state.assignments = {}
    if "translations" not in st.session_state:
        st.session_state.translations = {}
    if "roommate_name_custom" not in st.session_state:
        st.session_state.roommate_name_custom = ""
    if "roommate_name_saved" not in st.session_state:
        st.session_state.roommate_name_saved = ""

    # Guard against corrupted state (e.g. browser navigation)
    if st.session_state.step not in ("language", "upload") and not st.session_state.receipts:
        st.session_state.step = "language"
        st.session_state.current_idx = 0
