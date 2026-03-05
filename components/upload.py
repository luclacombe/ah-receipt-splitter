"""Step 1: Upload and parse receipt PDFs."""

import streamlit as st

from config import RECEIPTS_DIR
from i18n import UI_STRINGS
from receipt_parser import parse_receipt
from translator import apply_bonuses, translate_items


def render_upload() -> None:
    """Display the file upload form and process receipts on submit."""
    lang = st.session_state.language
    s = UI_STRINGS[lang]

    st.header(s["step_upload_header"])
    st.markdown(s["description"])
    st.divider()

    # Dutch override for Streamlit's hardcoded file uploader UI text
    if lang == "nl":
        st.markdown(
            """<style>
            [data-testid="stFileUploaderDropzoneInstructions"] > div > span:nth-of-type(1) {
                font-size: 0 !important; line-height: 0 !important;
            }
            [data-testid="stFileUploaderDropzoneInstructions"] > div > span:nth-of-type(1)::after {
                font-size: 14px; line-height: 1.5;
                content: "Sleep bestanden hierheen";
            }
            [data-testid="stFileUploaderDropzoneInstructions"] > div > span:nth-of-type(2) {
                font-size: 0 !important;
            }
            [data-testid="stFileUploaderDropzoneInstructions"] > div > span:nth-of-type(2)::after {
                font-size: 12px;
                content: "Maximaal 200MB per bestand \u2022 PDF";
            }
            </style>""",
            unsafe_allow_html=True,
        )

    upload_col, _ = st.columns([1, 3])
    with upload_col:
        uploaded = st.file_uploader(
            s["file_uploader_label"],
            type=["pdf"],
            accept_multiple_files=True,
        )

    name_col, _ = st.columns([1, 3])
    with name_col:
        if lang == "nl":
            st.text_input(
                "Naam huisgenoot",
                placeholder="Bijv. Kevin, Stuart, Bob",
                key="roommate_name_custom",
            )
        else:
            st.text_input(
                "Roommate's name",
                placeholder="Eg. Kevin, Stuart, Bob",
                key="roommate_name_custom",
            )

    if st.button(s["process_button"], type="primary"):
        if not uploaded:
            st.warning(s["warning_no_upload"])
            return

        with st.spinner(s["spinner_parsing"]):
            receipts: list[dict] = []
            all_dutch_names: list[str] = []
            seen_files: set[str] = set()

            for f in uploaded:
                if f.name in seen_files:
                    st.warning(s["duplicate_warning"].format(name=f.name))
                    continue
                seen_files.add(f.name)

                path = RECEIPTS_DIR / f.name
                path.write_bytes(f.getvalue())

                receipt = parse_receipt(path)
                receipt["_path"] = str(path)

                if not receipt["items"] and receipt["total"] == 0.0:
                    st.error(s["invalid_receipt_error"].format(name=f.name))
                    path.unlink(missing_ok=True)
                    continue

                receipts.append(receipt)
                all_dutch_names.extend(i["name_dutch"] for i in receipt["items"])

        if not receipts:
            st.error(s["error_no_valid"])
            return

        if lang == "en":
            with st.spinner(s["spinner_translating"]):
                try:
                    translations = translate_items(list(set(all_dutch_names)))
                except RuntimeError as e:
                    st.error(str(e))
                    return
            st.session_state.translations = translations
        else:
            st.session_state.translations = {}

        for receipt in receipts:
            apply_bonuses(receipt)

        receipts.sort(key=lambda r: (r["date"], r["time"]))

        st.session_state.receipts = receipts
        st.session_state.current_idx = 0
        st.session_state.assignments = {}
        st.session_state.roommate_name_saved = st.session_state.get(
            "roommate_name_custom", ""
        ).strip()
        st.session_state.step = "review"
        st.rerun()
