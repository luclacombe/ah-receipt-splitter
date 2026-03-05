"""Step 3: Summary and PDF report download."""

import streamlit as st

from i18n import UI_STRINGS
from report import generate_report


def render_summary() -> None:
    """Display the final cost breakdown and report download."""
    lang = st.session_state.language
    s = UI_STRINGS[lang]

    receipts = st.session_state.receipts
    assignments = st.session_state.assignments
    translations = st.session_state.translations
    custom_name = st.session_state.get("roommate_name_saved", "").strip()
    roommate_name = custom_name if custom_name else s["roommate_name"]

    # Compute totals (index-based: 0=shared, 1=mine, 2=roommate)
    total_mine = 0.0
    total_roommate = 0.0
    total_shared = 0.0
    receipt_data: list[tuple] = []

    for receipt in receipts:
        receipt_key = receipt["file"]
        receipt_assignments = assignments.get(receipt_key, {})
        r_mine = r_roommate = r_shared = 0.0
        rows: list[tuple] = []

        for i, item in enumerate(receipt["items"]):
            display_name = (
                item["name_dutch"]
                if lang == "nl"
                else translations.get(item["name_dutch"], item["name_dutch"])
            )
            choice_idx = receipt_assignments.get(i, 0)
            price = item["final_price"]

            if choice_idx == 1:
                r_mine += price
            elif choice_idx == 2:
                r_roommate += price
            else:
                r_shared += price

            rows.append((display_name, price, choice_idx))

        total_mine += r_mine
        total_roommate += r_roommate
        total_shared += r_shared
        receipt_data.append((receipt, r_mine, r_roommate, r_shared, rows))

    grand_total = total_mine + total_roommate + total_shared
    roommate_owes = total_roommate + (total_shared / 2)

    # Resolve string templates
    if lang == "nl":
        owes_label = f"{roommate_name} is je verschuldigd"
    else:
        owes_label = f"{roommate_name} owes you"
    your_items_label = s["your_items_label"]
    roommate_items_label = (
        s["roommate_items_label"].format(roommate=roommate_name)
        if "{roommate}" in s["roommate_items_label"]
        else s["roommate_items_label"]
    )
    shared_items_label = s["shared_items_label"]
    grand_total_label = s["grand_total_label"]
    shared_half_label = s["shared_half_label"]
    roommate_own_label = (
        s["roommate_own_label"].format(roommate=roommate_name)
        if "{roommate}" in s["roommate_own_label"]
        else s["roommate_own_label"]
    )
    owes_total_label = (
        s["owes_total_label"].format(roommate=roommate_name)
        if "{roommate}" in s["owes_total_label"]
        else s["owes_total_label"]
    )

    # Hero summary card
    st.markdown(
        f"""
<div style="
    background: linear-gradient(160deg, #0b1d3a 0%, #0d2b52 100%);
    border: 1px solid #1a3a6a;
    border-radius: 16px;
    padding: 36px 32px 28px;
    margin-bottom: 20px;
">
    <div style="font-size:0.75em; font-weight:600; color:#00A0E2; text-transform:uppercase; letter-spacing:0.12em; margin-bottom:6px;">{owes_label}</div>
    <div style="font-size:3.4em; font-weight:800; color:#ffffff; letter-spacing:-0.03em; line-height:1; margin-bottom:32px;">&euro;{roommate_owes:.2f}</div>
    <div style="display:flex; gap:0; border-top:1px solid #1a3a6a; padding-top:24px; margin-bottom:24px;">
        <div style="flex:1; padding-right:24px; border-right:1px solid #1a3a6a;">
            <div style="font-size:0.68em; color:#4a6a8a; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:5px;">{your_items_label}</div>
            <div style="font-size:1.35em; font-weight:700; color:#c8ddf0;">&euro;{total_mine:.2f}</div>
        </div>
        <div style="flex:1; padding:0 24px; border-right:1px solid #1a3a6a;">
            <div style="font-size:0.68em; color:#4a6a8a; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:5px;">{roommate_items_label}</div>
            <div style="font-size:1.35em; font-weight:700; color:#c8ddf0;">&euro;{total_roommate:.2f}</div>
        </div>
        <div style="flex:1; padding:0 24px; border-right:1px solid #1a3a6a;">
            <div style="font-size:0.68em; color:#4a6a8a; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:5px;">{shared_items_label}</div>
            <div style="font-size:1.35em; font-weight:700; color:#c8ddf0;">&euro;{total_shared:.2f}</div>
        </div>
        <div style="flex:1; padding-left:24px;">
            <div style="font-size:0.68em; color:#4a6a8a; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:5px;">{grand_total_label}</div>
            <div style="font-size:1.35em; font-weight:700; color:#c8ddf0;">&euro;{grand_total:.2f}</div>
        </div>
    </div>
    <div style="border-top:1px solid #1a3a6a; padding-top:16px;">
        <div style="display:flex; justify-content:space-between; padding:5px 0; font-size:0.875em; color:#5a7a9a;">
            <span>{shared_half_label}</span>
            <span style="font-variant-numeric:tabular-nums; color:#8aaac8;">&euro;{total_shared / 2:.2f}</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:5px 0; font-size:0.875em; color:#5a7a9a;">
            <span>{roommate_own_label}</span>
            <span style="font-variant-numeric:tabular-nums; color:#8aaac8;">&euro;{total_roommate:.2f}</span>
        </div>
        <div style="display:flex; justify-content:space-between; padding:10px 0 0; border-top:1px solid #1a3a6a; margin-top:8px; font-size:1em; font-weight:700; color:#ffffff;">
            <span>{owes_total_label}</span>
            <span style="font-variant-numeric:tabular-nums; color:#00A0E2;">&euro;{roommate_owes:.2f}</span>
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Render the download button placeholder immediately so the rest of the
    # page can render before the slow PDF generation (weasyprint) runs.
    download_placeholder = st.empty()

    st.markdown("---")

    st.subheader(s["receipt_details_header"])
    assign_labels = [s["assignment_options"][0], s["assignment_options"][1], roommate_name]

    for receipt, r_mine, r_roommate, r_shared, rows in receipt_data:
        with st.expander(f"{receipt['date']} \u2014 \u20ac{receipt['total']:.2f}"):
            for display_name, price, choice_idx in rows:
                label = assign_labels[choice_idx]
                item_row = st.columns([5, 1, 2])
                with item_row[0]:
                    st.write(display_name)
                with item_row[1]:
                    st.write(f"\u20ac{price:.2f}")
                with item_row[2]:
                    st.write(f"*{label}*")

            st.caption(
                f"{assign_labels[1]}: \u20ac{r_mine:.2f} | "
                f"{roommate_name}: \u20ac{r_roommate:.2f} | "
                f"{assign_labels[0]}: \u20ac{r_shared:.2f}"
            )

    st.markdown("---")

    if st.button(s["start_over_btn"]):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    # Generate PDF after all page content is rendered so the old review page
    # is fully replaced before weasyprint blocks the render thread.
    report_pdf = generate_report(
        receipts,
        assignments,
        translations,
        roommate_name=roommate_name,
        language=lang,
    )
    download_placeholder.download_button(
        label=s["download_report_btn"],
        data=report_pdf,
        file_name=s["report_filename"],
        mime="application/pdf",
        type="primary",
    )
