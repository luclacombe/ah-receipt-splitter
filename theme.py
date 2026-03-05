"""AH brand theme CSS and header rendering for Streamlit."""

import streamlit as st

from config import AH_LOGO_URL
from i18n import UI_STRINGS

AH_THEME_CSS: str = """
<style>
    /* AH brand colors */
    :root {
        --ah-blue: #00A0E2;
        --ah-dark-blue: #003D97;
        --ah-light-bg: #E8F4FA;
    }

    /* Header area */
    header[data-testid="stHeader"] {
        background-color: #00A0E2;
    }

    /* Primary buttons */
    .stButton > button[kind="primary"],
    button[kind="primary"] {
        background-color: #00A0E2 !important;
        border-color: #00A0E2 !important;
        color: white !important;
    }
    .stButton > button[kind="primary"]:hover,
    button[kind="primary"]:hover {
        background-color: #003D97 !important;
        border-color: #003D97 !important;
    }

    /* Secondary buttons */
    .stButton > button {
        border-color: #00A0E2 !important;
        color: #00A0E2 !important;
    }
    .stButton > button:hover {
        border-color: #003D97 !important;
        color: #003D97 !important;
        background-color: #E8F4FA !important;
    }

    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #00A0E2 !important;
    }

    /* Selectbox styling */
    div[data-baseweb="select"] > div {
        border-color: #00A0E2 !important;
    }

    /* Compact item rows */
    .item-row {
        padding: 6px 0 2px 0;
        line-height: 1.3;
    }
    .item-main {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
    }
    .item-name {
        font-weight: 600;
        font-size: 0.9em;
    }
    .item-price {
        font-family: monospace;
        font-size: 0.9em;
        font-weight: 600;
        white-space: nowrap;
        color: #333;
    }
    .item-details {
        font-size: 0.75em;
        color: #888;
        margin-top: 1px;
    }
    .item-details span {
        margin-right: 8px;
    }
    .item-tag-saved {
        color: #2E7D32;
    }
    .item-tag-deposit {
        color: #666;
    }
    .item-tag-weight {
        color: #888;
    }

    /* Tighter spacing for item list */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0;
    }

    /* Reduce gap between compact item columns */
    .compact-items .stColumn {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    /* Logo styling */
    .ah-logo-header {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 16px;
        margin-bottom: 8px;
    }
    .ah-logo-header img {
        height: 52px;
    }
    .ah-logo-header h1 {
        margin: 0;
        color: #00A0E2;
        font-size: 1.8em;
    }

    /* Metric labels */
    [data-testid="stMetricLabel"] {
        color: #003D97 !important;
    }

    /* Review page header */
    .review-header {
        text-align: center;
        padding: 8px 0 4px 0;
    }
    .review-header .receipt-counter {
        font-size: 1.1em;
        font-weight: 700;
        color: #00A0E2;
    }
    .review-header .receipt-meta {
        font-size: 0.85em;
        color: #999;
        margin-top: 2px;
    }
    .review-header .receipt-total {
        font-size: 1.3em;
        font-weight: 700;
        margin-top: 2px;
    }

    /* Column headers for item list */
    .item-col-headers {
        display: flex;
        justify-content: space-between;
        padding: 4px 0;
        border-bottom: 1px solid #333;
        margin-bottom: 4px;
        font-size: 0.75em;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .item-col-headers .col-item { flex: 4; }
    .item-col-headers .col-price { flex: 0 0 70px; text-align: right; }

    /* Subtle small "Edit Names" / "Done Editing" button above Item column */
    div[data-testid="stVerticalBlock"]:has(#col-controls-anchor)
        > div[data-testid="stHorizontalBlock"]:nth-of-type(1)
        .stButton button {
        height: 26px !important;
        min-height: 26px !important;
        max-height: 26px !important;
        padding: 0 8px !important;
        font-size: 0.72em !important;
        line-height: 26px !important;
        border-radius: 4px !important;
        border-color: #555 !important;
        color: #888 !important;
        background: transparent !important;
        overflow: hidden !important;
    }
    div[data-testid="stVerticalBlock"]:has(#col-controls-anchor)
        > div[data-testid="stHorizontalBlock"]:nth-of-type(1)
        .stButton button:hover {
        border-color: #00A0E2 !important;
        color: #00A0E2 !important;
        background: transparent !important;
    }
    div[data-testid="stVerticalBlock"]:has(#col-controls-anchor)
        > div[data-testid="stHorizontalBlock"]:nth-of-type(1)
        .stButton button p {
        font-size: inherit !important;
        line-height: inherit !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Summary rows aligned with price column */
    .summary-label {
        font-size: 0.85em;
        color: #999;
        margin: 1px 0;
    }
    .summary-value {
        font-size: 0.85em;
        color: #999;
        text-align: right;
        margin: 1px 0;
        font-family: monospace;
    }
    .summary-label-total {
        font-size: 0.9em;
        font-weight: 700;
        color: #eee;
        margin: 4px 0 1px 0;
    }
    .summary-value-total {
        font-size: 0.9em;
        font-weight: 700;
        color: #eee;
        text-align: right;
        margin: 4px 0 1px 0;
        font-family: monospace;
    }

    /* Language select cards */
    .lang-card {
        background: #f8fafc;
        border: 2px solid #e0e8f0;
        border-radius: 16px;
        padding: 32px 24px;
        text-align: center;
        margin-bottom: 12px;
    }
    .lang-flag {
        font-size: 3em;
        line-height: 1;
        margin-bottom: 8px;
    }
    .lang-name {
        font-size: 1.1em;
        font-weight: 700;
        color: #003D97;
        margin-bottom: 4px;
    }
    .lang-sub {
        font-size: 0.82em;
        color: #8899aa;
    }

    /* Receipt preview border */
    [data-testid="stImage"] {
        border: 4px solid #00A0E2;
        border-radius: 12px;
        overflow: hidden;
    }
</style>
"""


def inject_theme() -> None:
    """Inject AH branding CSS into the Streamlit page."""
    st.markdown(AH_THEME_CSS, unsafe_allow_html=True)


def render_logo_header() -> None:
    """Render the AH logo and app title header."""
    lang = st.session_state.get("language", "en")
    title = UI_STRINGS[lang]["app_title"]
    st.markdown(
        f'<div class="ah-logo-header">'
        f'<img src="{AH_LOGO_URL}" alt="Albert Heijn">'
        f"<h1>{title}</h1>"
        f"</div>",
        unsafe_allow_html=True,
    )
