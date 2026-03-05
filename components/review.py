"""Step 2: Review each receipt and assign items."""

import shutil
from pathlib import Path

import pdfplumber
import streamlit as st

from config import PROCESSED_DIR
from i18n import UI_STRINGS
from translator import save_translation


def _render_receipt_image(pdf_path: str) -> None:
    """Render the first page of a PDF as an image in Streamlit."""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        img = page.to_image(resolution=150)
        st.image(img.original, width="stretch")


def render_review() -> None:
    """Display the item assignment UI for each receipt."""
    lang = st.session_state.language
    s = UI_STRINGS[lang]

    receipts = st.session_state.receipts
    idx = st.session_state.current_idx
    total = len(receipts)
    custom_name = st.session_state.get("roommate_name_saved", "").strip()
    roommate_name = custom_name if custom_name else s["roommate_name"]
    display_options = [s["assignment_options"][0], s["assignment_options"][1], roommate_name]

    if idx >= total:
        st.session_state.step = "summary"
        st.rerun()
        return

    receipt = receipts[idx]
    receipt_key = receipt["file"]

    if receipt_key not in st.session_state.assignments:
        st.session_state.assignments[receipt_key] = {}

    def _move_and_advance() -> None:
        src = Path(receipt["_path"])
        dst = PROCESSED_DIR / src.name
        if src.exists():
            shutil.move(str(src), str(dst))
            receipt["_path"] = str(dst)
        st.session_state.current_idx += 1
        if st.session_state.current_idx >= total:
            st.session_state.step = "summary"
        st.rerun()

    # --- Compact header: nav + receipt info ---
    nav_cols = st.columns([1, 4, 1], vertical_alignment="center")
    with nav_cols[0]:
        if idx > 0:
            if st.button(s["prev_btn"], key="top_prev", use_container_width=True):
                st.session_state.current_idx -= 1
                st.rerun()
    with nav_cols[1]:
        counter = s["receipt_counter"].format(idx=idx + 1, total=total)
        st.markdown(
            f'<div class="review-header">'
            f'<div class="receipt-counter">{counter}</div>'
            f'<div class="receipt-meta">{receipt["date"]} \u00b7 {receipt["time"]}</div>'
            f'<div class="receipt-total">\u20ac{receipt["total"]:.2f}</div>'
            f"</div>",
            unsafe_allow_html=True,
        )
    with nav_cols[2]:
        finish_or_next = s["finish_btn"] if idx == total - 1 else s["next_btn"]
        if st.button(finish_or_next, type="primary", key="top_next", use_container_width=True):
            _move_and_advance()

    st.progress(idx / total)

    # Display parser warnings
    for w in receipt.get("warnings", []):
        st.warning(w)

    # Verify parsed items sum matches receipt total
    items_sum = sum(item["final_price"] for item in receipt["items"])
    diff = abs(items_sum - receipt["total"])
    if diff > 0.01 * len(receipt["items"]):
        st.warning(
            s["items_mismatch_warning"].format(
                items_sum=items_sum, receipt_total=receipt["total"], diff=diff
            ),
            icon="\u26a0\ufe0f",
        )

    # --- Two-column layout: receipt image | item list ---
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.subheader(s["original_receipt"])
        _render_receipt_image(receipt["_path"])

    with right:
        translations = st.session_state.translations
        edit_mode_key = f"edit_mode_{receipt_key}"
        editing_names = st.session_state.get(edit_mode_key, False)

        def _set_all(option_idx: int) -> None:
            for i in range(len(receipt["items"])):
                st.session_state.assignments[receipt_key][i] = option_idx
                st.session_state[f"select_{receipt_key}_{i}"] = display_options[option_idx]

        # --- Controls row ---
        st.markdown('<div id="col-controls-anchor"></div>', unsafe_allow_html=True)
        ctrl = st.columns([4, 1, 2])

        # Edit Names button only shown in English mode
        if lang == "en":
            with ctrl[0]:
                edit_label = s["done_editing_btn"] if editing_names else s["edit_names_btn"]
                if st.button(edit_label, key="tb_edit"):
                    st.session_state[edit_mode_key] = not editing_names
                    st.rerun()

        qa_key = f"quick_assign_{receipt_key}"
        if qa_key not in st.session_state:
            st.session_state[qa_key] = s["assign_all_placeholder"]
        all_roommate_opt = f"Alles {roommate_name}" if lang == "nl" else f"All {roommate_name}"
        qa_opts = [
            s["assign_all_placeholder"],
            s["all_shared"],
            s["all_mine"],
            all_roommate_opt,
        ]
        # Process quick-assign action BEFORE rendering the widget to avoid
        # "cannot modify after widget instantiation" error
        pending_qa = st.session_state[qa_key]
        if pending_qa != s["assign_all_placeholder"]:
            if pending_qa in [s["all_shared"], s["all_mine"], all_roommate_opt]:
                _set_all([s["all_shared"], s["all_mine"], all_roommate_opt].index(pending_qa))
            st.session_state[qa_key] = s["assign_all_placeholder"]

        with ctrl[2]:
            st.selectbox(
                "quick_assign",
                qa_opts,
                key=qa_key,
                label_visibility="collapsed",
            )

        # --- Column headers ---
        hdr = st.columns([4, 1, 2])
        with hdr[0]:
            st.markdown(
                f'<p style="font-size:0.75em; color:#888; text-transform:uppercase; '
                f'letter-spacing:0.05em; margin:0; padding:8px 0 2px 0;">{s["col_item"]}</p>',
                unsafe_allow_html=True,
            )
        with hdr[1]:
            st.markdown(
                f'<p style="font-size:0.75em; color:#888; text-transform:uppercase; '
                f'letter-spacing:0.05em; text-align:right; margin:0; padding:8px 0 2px 0;">'
                f"{s['col_final_price']}</p>",
                unsafe_allow_html=True,
            )
        with hdr[2]:
            st.markdown(
                f'<p style="font-size:0.75em; color:#888; text-transform:uppercase; '
                f'letter-spacing:0.05em; margin:0; padding:8px 0 2px 0;">{s["col_split"]}</p>',
                unsafe_allow_html=True,
            )
        st.markdown(
            '<hr style="margin:0 0 4px 0; border-top: 1px solid #333; border-bottom: none;">',
            unsafe_allow_html=True,
        )

        # --- Item list ---
        for i, item in enumerate(receipt["items"]):
            dutch_name = item["name_dutch"]
            display_name = dutch_name if lang == "nl" else translations.get(dutch_name, dutch_name)

            # Build detail tags
            details: list[str] = []
            if item["unit_price"] and (item["quantity"] not in ("1",)):
                details.append(
                    f'<span class="item-tag-weight">'
                    f"{item['quantity']} \u00d7 \u20ac{item['unit_price']:.2f}"
                    f"</span>"
                )
            if item.get("statiegeld"):
                deposit_text = s["deposit_label"].format(amount=f"{item['statiegeld']:.2f}")
                details.append(f'<span class="item-tag-deposit">{deposit_text}</span>')
            if item["has_bonus"] and item["bonus_amount"] != 0:
                saved = abs(item["bonus_amount"])
                saved_text = s["saved_label"].format(amount=f"{saved:.2f}")
                details.append(f'<span class="item-tag-saved">{saved_text}</span>')
            details_html = f'<div class="item-details">{"".join(details)}</div>' if details else ""

            item_key = f"{receipt_key}_{i}"
            widget_key = f"select_{item_key}"

            if widget_key not in st.session_state:
                default_idx = st.session_state.assignments[receipt_key].get(i, 0)
                st.session_state[widget_key] = display_options[default_idx]

            # Edit mode only available in English
            if lang == "en" and editing_names:
                english = translations.get(dutch_name, dutch_name)
                edit_cols = st.columns([4, 1, 2])
                with edit_cols[0]:
                    new_name = st.text_input(
                        f"Translation for {dutch_name}",
                        value=english,
                        key=f"edit_input_{item_key}",
                        label_visibility="collapsed",
                    )
                    if new_name and new_name != english:
                        st.session_state.translations[dutch_name] = new_name
                        save_translation(dutch_name, new_name)
                with edit_cols[1]:
                    st.markdown(
                        f'<p style="font-family:monospace; font-size:0.9em; font-weight:600; '
                        f'text-align:right; margin:0; padding:8px 0;">'
                        f"\u20ac{item['final_price']:.2f}</p>",
                        unsafe_allow_html=True,
                    )
                with edit_cols[2]:
                    choice = st.selectbox(
                        f"assign_{item_key}",
                        display_options,
                        label_visibility="collapsed",
                        key=widget_key,
                    )
            else:
                row = st.columns([4, 1, 2])
                with row[0]:
                    st.markdown(
                        f'<div class="item-row">'
                        f'<span class="item-name">{display_name}</span>'
                        f"{details_html}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with row[1]:
                    st.markdown(
                        f'<p style="font-family:monospace; font-size:0.9em; font-weight:600; '
                        f'text-align:right; margin:0; padding:4px 0; white-space:nowrap;">'
                        f"\u20ac{item['final_price']:.2f}</p>",
                        unsafe_allow_html=True,
                    )
                with row[2]:
                    choice = st.selectbox(
                        f"assign_{item_key}",
                        display_options,
                        label_visibility="collapsed",
                        key=widget_key,
                    )
            st.session_state.assignments[receipt_key][i] = display_options.index(choice)

        # --- Summary footer ---
        subtotal = sum(item["total_price"] for item in receipt["items"])
        total_bonuses = sum(
            abs(item["bonus_amount"]) for item in receipt["items"] if item["bonus_amount"] != 0
        )

        st.markdown(
            '<hr style="margin:8px 0 4px 0; border-top: 1px solid #333; border-bottom: none;">',
            unsafe_allow_html=True,
        )
        if total_bonuses > 0:
            sub_row = st.columns([4, 1, 2])
            with sub_row[0]:
                st.markdown(
                    f'<p class="summary-label">{s["col_subtotal"]}</p>',
                    unsafe_allow_html=True,
                )
            with sub_row[1]:
                st.markdown(
                    f'<p class="summary-value">\u20ac{subtotal:.2f}</p>',
                    unsafe_allow_html=True,
                )
            bon_row = st.columns([4, 1, 2])
            with bon_row[0]:
                st.markdown(
                    f'<p class="summary-label">{s["col_bonuses"]}</p>',
                    unsafe_allow_html=True,
                )
            with bon_row[1]:
                st.markdown(
                    f'<p class="summary-value">\u2212\u20ac{total_bonuses:.2f}</p>',
                    unsafe_allow_html=True,
                )
        tot_row = st.columns([4, 1, 2])
        with tot_row[0]:
            st.markdown(
                f'<p class="summary-label-total">{s["col_total"]}</p>',
                unsafe_allow_html=True,
            )
        with tot_row[1]:
            st.markdown(
                f'<p class="summary-value-total">\u20ac{receipt["total"]:.2f}</p>',
                unsafe_allow_html=True,
            )

        # --- Edit Bonus Splits ---
        if receipt["bonuses"]:
            b_items_list = [
                (i, item) for i, item in enumerate(receipt["items"]) if item["has_bonus"]
            ]
            if b_items_list:
                with st.expander(s["edit_bonus_title"], expanded=False, icon="\u2139\ufe0f"):
                    st.caption(s["edit_bonus_caption"])
                    for i, item in b_items_list:
                        bonus_key = f"bonus_override_{receipt_key}_{i}"
                        current_bonus = item["bonus_amount"]
                        item_display = (
                            item["name_dutch"]
                            if lang == "nl"
                            else translations.get(item["name_dutch"], item["name_dutch"])
                        )
                        new_val = st.number_input(
                            label=f"{item_display} (was \u20ac{item['total_price']:.2f})",
                            value=float(current_bonus),
                            step=0.01,
                            format="%.2f",
                            key=bonus_key,
                        )
                        if abs(new_val - current_bonus) > 0.001:
                            item["bonus_amount"] = new_val
                            item["final_price"] = round(item["total_price"] + new_val, 2)

    # --- Bottom navigation ---
    st.markdown("---")
    bot_nav = st.columns([1, 4, 1], vertical_alignment="center")
    with bot_nav[0]:
        if idx > 0:
            if st.button(s["prev_btn"], key="bot_prev", use_container_width=True):
                st.session_state.current_idx -= 1
                st.rerun()
    with bot_nav[2]:
        if st.button(finish_or_next, type="primary", key="bot_next", use_container_width=True):
            _move_and_advance()
