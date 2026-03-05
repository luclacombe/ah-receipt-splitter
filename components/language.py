"""Step 0: Language selection screen."""

import streamlit as st


def render_language_select() -> None:
    """Display language selection cards for Dutch and English."""
    st.markdown(
        '<p style="text-align:center; font-size:1.15em; color:#667788; margin:24px 0 32px;">'
        "Kies je taal &nbsp;&middot;&nbsp; Choose your language"
        "</p>",
        unsafe_allow_html=True,
    )

    _, col_nl, gap, col_en, _ = st.columns([2, 3, 0.5, 3, 2])

    with col_nl:
        st.markdown(
            '<div class="lang-card">'
            '<div class="lang-flag">\U0001f1f3\U0001f1f1</div>'
            '<div class="lang-name">Nederlands</div>'
            '<div class="lang-sub">Artikelnamen in het Nederlands</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button("Nederlands", use_container_width=True, type="primary", key="lang_nl"):
            st.session_state.language = "nl"
            st.session_state.step = "upload"
            st.rerun()

    with col_en:
        st.markdown(
            '<div class="lang-card">'
            '<div class="lang-flag">\U0001f1ec\U0001f1e7</div>'
            '<div class="lang-name">English</div>'
            '<div class="lang-sub">Item names translated to English</div>'
            "</div>",
            unsafe_allow_html=True,
        )
        if st.button("English", use_container_width=True, type="primary", key="lang_en"):
            st.session_state.language = "en"
            st.session_state.step = "upload"
            st.rerun()
