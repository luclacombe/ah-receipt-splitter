"""Generate a PDF split report from processed receipts."""

import html as html_mod
from datetime import date

from weasyprint import HTML

from i18n import REPORT_STRINGS


def _esc(s: str) -> str:
    """Escape a string for safe HTML interpolation."""
    return html_mod.escape(str(s))


def generate_report(
    receipts: list[dict],
    assignments: dict,
    translations: dict,
    roommate_name: str = "Roommate",
    language: str = "en",
) -> bytes:
    """Build a PDF report summarising the grocery split.

    Returns PDF bytes ready for download.
    """
    html = _build_html(receipts, assignments, translations, roommate_name, language)
    return HTML(string=html).write_pdf()


def _build_html(
    receipts: list[dict],
    assignments: dict,
    translations: dict,
    roommate_name: str = "Roommate",
    language: str = "en",
) -> str:
    """Build self-contained HTML that will be converted to PDF."""
    rs = REPORT_STRINGS[language]
    safe_roommate = _esc(roommate_name)

    # ── Compute totals (index-based: 0=shared, 1=mine, 2=roommate) ──────────
    total_mine = 0.0
    total_roommate = 0.0
    total_shared = 0.0
    receipt_summaries: list[dict] = []

    for receipt in receipts:
        rkey = receipt["file"]
        r_assign = assignments.get(rkey, {})
        r_mine = r_room = r_shared = 0.0
        rows: list[dict] = []

        for i, item in enumerate(receipt["items"]):
            choice_idx = r_assign.get(i, 0)
            price = item["final_price"]

            if choice_idx == 1:
                r_mine += price
            elif choice_idx == 2:
                r_room += price
            else:
                r_shared += price

            dutch = item["name_dutch"]
            display_name = translations.get(dutch, dutch)
            rows.append(
                {
                    "dutch": dutch,
                    "display_name": display_name,
                    "qty": item["quantity"],
                    "unit_price": item["unit_price"],
                    "price": price,
                    "bonus": item["bonus_amount"],
                    "original_bonus": item.get("original_bonus_amount", item["bonus_amount"]),
                    "has_bonus": item["has_bonus"],
                    "statiegeld": item.get("statiegeld", 0),
                    "choice_idx": choice_idx,
                }
            )

        total_mine += r_mine
        total_roommate += r_room
        total_shared += r_shared
        receipt_summaries.append(
            {
                "date": receipt["date"],
                "time": receipt["time"],
                "total": receipt["total"],
                "discount": receipt["total_discount"],
                "mine": r_mine,
                "roommate": r_room,
                "shared": r_shared,
                "rows": rows,
            }
        )

    grand_total = total_mine + total_roommate + total_shared
    shared_half = total_shared / 2
    roommate_owes = total_roommate + shared_half

    def _r(key: str, **kwargs: str) -> str:
        t = rs[key]
        if kwargs:
            return t.format(roommate=safe_roommate, **kwargs)
        return t.format(roommate=safe_roommate) if "{roommate}" in t else t

    # ── Build receipt sections ───────────────────────────────────────────────
    receipt_sections = ""
    for rsum in receipt_summaries:
        table_rows = ""
        for r in rsum["rows"]:
            choice_idx = r["choice_idx"]
            if choice_idx == 1:
                badge_cls = "badge-mine"
                badge_text = rs["badge_mine"]
            elif choice_idx == 2:
                badge_cls = "badge-room"
                badge_text = _esc(roommate_name).upper()
            else:
                badge_cls = "badge-shared"
                badge_text = rs["badge_shared"]

            extras: list[str] = []
            if r["unit_price"] and r["qty"] not in ("1",):
                extras.append(f"{_esc(r['qty'])} &times; &euro;{r['unit_price']:.2f}")
            if r["statiegeld"]:
                extras.append(rs["deposit_label"].format(amount=f"{r['statiegeld']:.2f}"))
            if r["has_bonus"] and r["bonus"] != 0:
                bonus_edited = abs(r["bonus"] - r["original_bonus"]) > 0.001
                if bonus_edited:
                    extras.append(
                        '<span class="bonus-edited">'
                        + rs["bonus_edited_label"].format(
                            bonus=r["bonus"], original=r["original_bonus"]
                        )
                        + "</span>"
                    )
                else:
                    extras.append(rs["bonus_label"].format(amount=r["bonus"]))
            extras_html = f'<div class="extras">{" &middot; ".join(extras)}</div>' if extras else ""

            display = _esc(r["display_name"])
            dutch_sub = (
                _esc(r["dutch"]) if language == "en" and r["display_name"] != r["dutch"] else ""
            )
            dutch_html = f'<span class="item-nl">{dutch_sub}</span>' if dutch_sub else ""

            table_rows += f"""
            <tr>
                <td class="col-item">
                    <span class="item-en">{display}</span>
                    {dutch_html}
                    {extras_html}
                </td>
                <td class="col-price">&euro;{r["price"]:.2f}</td>
                <td class="col-assign"><span class="badge {badge_cls}">{badge_text}</span></td>
            </tr>"""

        discount_line = ""
        if rsum["discount"] > 0:
            saved_text = rs["saved_label"].format(amount=f"{rsum['discount']:.2f}")
            discount_line = f'<span class="receipt-savings">{saved_text}</span>'

        rs_total = rsum["mine"] + rsum["roommate"] + rsum["shared"]
        receipt_sections += f"""
        <div class="receipt-card">
            <div class="receipt-header">
                <div>
                    <span class="receipt-date">{rsum["date"]}</span>
                    <span class="receipt-time">{rsum["time"]}</span>
                </div>
                <span class="receipt-total">&euro;{rsum["total"]:.2f}</span>
            </div>
            {discount_line}
            <table class="items-table">
                <thead>
                    <tr>
                        <th class="col-item">{rs["col_item"]}</th>
                        <th class="col-price">{rs["col_price"]}</th>
                        <th class="col-assign">{rs["col_assigned"]}</th>
                    </tr>
                </thead>
                <tbody>{table_rows}
                </tbody>
                <tbody class="totals-section">
                    <tr>
                        <td>{rs["mine_label"]}</td>
                        <td class="col-price">&euro;{rsum["mine"]:.2f}</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td>{safe_roommate}</td>
                        <td class="col-price">&euro;{rsum["roommate"]:.2f}</td>
                        <td></td>
                    </tr>
                    <tr>
                        <td>{rs["shared_label"]}</td>
                        <td class="col-price">&euro;{rsum["shared"]:.2f}</td>
                        <td></td>
                    </tr>
                    <tr class="total-row">
                        <td>{rs["grand_total_label"]}</td>
                        <td class="col-price">&euro;{rs_total:.2f}</td>
                        <td></td>
                    </tr>
                </tbody>
            </table>
        </div>"""

    # ── Assemble final HTML ──────────────────────────────────────────────────
    today = date.today().strftime("%d %b %Y")
    n_receipts = len(receipts)
    receipts_count = (
        rs["receipts_single"] if n_receipts == 1 else rs["receipts_plural"].format(n=n_receipts)
    )
    items_count = rs["items_total"].format(n=sum(len(r["items"]) for r in receipts))

    owes_line = _r("owes_line")
    your_items = rs["your_items"]
    roommate_items = _r("roommate_items")
    shared_items = rs["shared_items"]
    shared_half_label = rs["shared_half_label"]
    roommate_own_label = _r("roommate_own_label")
    owes_total_label = _r("owes_total_label")
    grand_total_label = rs["grand_total_label"]
    generated_label = rs["generated_label"]
    report_h1 = rs["report_h1"]
    footer_text = rs["footer"]

    html = f"""<!DOCTYPE html>
<html lang="{language}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{rs["page_title"]}</title>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    @page {{
        size: A4;
        margin: 18mm 15mm;
    }}

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
        background: #ffffff;
        color: #1a2a3a;
        line-height: 1.5;
    }}

    .container {{
        max-width: 680px;
        margin: 0 auto;
    }}

    .brand-header {{
        text-align: center;
        margin-bottom: 28px;
    }}
    .brand-header img {{
        height: 44px;
        margin-bottom: 6px;
    }}
    .brand-header h1 {{
        font-size: 1.4em;
        font-weight: 700;
        color: #00A0E2;
        letter-spacing: -0.02em;
    }}
    .brand-header .gen-date {{
        font-size: 0.8em;
        color: #8899aa;
        margin-top: 2px;
    }}

    .summary-card {{
        background: linear-gradient(135deg, #00A0E2, #003D97);
        color: #fff;
        border-radius: 16px;
        padding: 28px 24px;
        margin-bottom: 28px;
    }}
    .owes-line {{
        font-size: 1.8em;
        font-weight: 700;
        text-align: center;
        margin-bottom: 16px;
        letter-spacing: -0.02em;
    }}
    .owes-line .amount {{ font-size: 1.1em; }}
    .summary-grid {{
        display: flex;
        justify-content: center;
        gap: 12px;
        text-align: center;
    }}
    .summary-box {{
        background: rgba(255,255,255,0.15);
        border-radius: 10px;
        padding: 12px 8px;
        flex: 1;
    }}
    .summary-box .label {{
        font-size: 0.7em;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        opacity: 0.85;
    }}
    .summary-box .value {{
        font-size: 1.3em;
        font-weight: 700;
        margin-top: 2px;
    }}

    .breakdown-calc {{
        background: rgba(255,255,255,0.12);
        border-radius: 10px;
        padding: 14px 20px;
        margin-top: 16px;
        font-size: 0.88em;
    }}
    .calc-row {{
        display: flex;
        justify-content: space-between;
        align-items: baseline;
        padding: 3px 0;
    }}
    .calc-label {{ opacity: 0.9; }}
    .calc-value {{
        font-weight: 600;
        font-variant-numeric: tabular-nums;
        text-align: right;
        min-width: 80px;
    }}
    .calc-divider {{
        border-top: 1px solid rgba(255,255,255,0.35);
        margin: 6px 0;
    }}
    .calc-row.calc-total .calc-label,
    .calc-row.calc-total .calc-value {{
        font-weight: 700;
        font-size: 1.1em;
    }}

    .grand-total-card {{
        background: #fff;
        color: #1a2a3a;
        border-radius: 12px;
        padding: 16px 24px;
        margin-bottom: 28px;
        border: 1px solid #e8ecf0;
    }}
    .grand-total-top {{
        display: flex;
        justify-content: space-between;
        align-items: center;
    }}
    .grand-total-top .gt-label {{ font-size: 0.95em; font-weight: 600; }}
    .grand-total-top .gt-value {{ font-size: 1.3em; font-weight: 700; }}
    .grand-total-meta {{
        display: flex;
        justify-content: space-between;
        font-size: 0.82em;
        color: #667788;
        margin-top: 4px;
    }}

    .receipt-card {{
        background: #fff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid #e8ecf0;
        break-inside: avoid;
    }}
    .receipt-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }}
    .receipt-date {{ font-weight: 700; font-size: 1.05em; color: #003D97; }}
    .receipt-time {{ color: #8899aa; font-size: 0.85em; margin-left: 8px; }}
    .receipt-total {{ font-weight: 700; font-size: 1.15em; color: #1a2a3a; }}
    .receipt-savings {{
        display: inline-block;
        font-size: 0.75em;
        color: #e67300;
        margin-bottom: 10px;
    }}

    .items-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88em;
        margin-top: 8px;
    }}
    .items-table thead th {{
        text-align: left;
        font-size: 0.72em;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8899aa;
        padding: 6px 8px;
        border-bottom: 2px solid #e8ecf0;
    }}
    .items-table thead th.col-price,
    .items-table thead th.col-assign {{ text-align: right; }}
    .items-table tbody tr {{ border-bottom: 1px solid #f0f2f5; }}
    .items-table tbody tr:last-child {{ border-bottom: none; }}
    .items-table td {{ padding: 8px; vertical-align: top; }}
    .col-item {{ width: 60%; }}
    .col-price {{
        width: 18%;
        text-align: right;
        font-variant-numeric: tabular-nums;
        font-weight: 500;
        white-space: nowrap;
    }}
    .col-assign {{ width: 22%; text-align: right; }}

    .item-en {{ display: block; font-weight: 600; color: #1a2a3a; }}
    .item-nl {{ display: block; font-size: 0.82em; color: #8899aa; font-style: italic; }}
    .extras {{ font-size: 0.78em; color: #aab4c0; margin-top: 1px; }}

    .badge {{
        display: inline-block;
        font-size: 0.72em;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    .badge-shared {{ background: #e8f4fa; color: #00A0E2; }}
    .badge-mine {{ background: #e8fae8; color: #2d8a2d; }}
    .badge-room {{ background: #faf0e8; color: #c26a00; }}

    .totals-section {{ margin-top: 4px; border-top: 2px solid #e8ecf0; }}
    .totals-section tr td {{
        padding: 4px 8px;
        font-size: 0.82em;
        color: #667788;
        font-weight: 600;
        border-bottom: none;
    }}
    .totals-section tr td:nth-child(2) {{
        text-align: right;
        font-variant-numeric: tabular-nums;
    }}
    .totals-section tr.total-row td {{
        border-top: 1px solid #e8ecf0;
        color: #1a2a3a;
        font-size: 0.9em;
        font-weight: 700;
        padding-top: 6px;
    }}

    .bonus-edited {{ color: #c26a00; font-weight: 600; }}

    .page-footer {{
        text-align: center;
        margin-top: 28px;
        font-size: 0.75em;
        color: #aab4c0;
    }}
</style>
</head>
<body>
<div class="container">

    <div class="brand-header">
        <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/e/eb/Albert_Heijn_Logo.svg/1200px-Albert_Heijn_Logo.svg.png" alt="Albert Heijn">
        <h1>{report_h1}</h1>
        <div class="gen-date">{generated_label} {today}</div>
    </div>

    <div class="summary-card">
        <div class="owes-line">{owes_line} &nbsp;<span class="amount">&euro;{roommate_owes:.2f}</span></div>
        <div class="summary-grid">
            <div class="summary-box">
                <div class="label">{your_items}</div>
                <div class="value">&euro;{total_mine:.2f}</div>
            </div>
            <div class="summary-box">
                <div class="label">{roommate_items}</div>
                <div class="value">&euro;{total_roommate:.2f}</div>
            </div>
            <div class="summary-box">
                <div class="label">{shared_items}</div>
                <div class="value">&euro;{total_shared:.2f}</div>
            </div>
        </div>
        <div class="breakdown-calc">
            <div class="calc-row">
                <span class="calc-label">{shared_half_label}</span>
                <span class="calc-value">&euro;{shared_half:.2f}</span>
            </div>
            <div class="calc-row">
                <span class="calc-label">{roommate_own_label}</span>
                <span class="calc-value">&euro;{total_roommate:.2f}</span>
            </div>
            <div class="calc-divider"></div>
            <div class="calc-row calc-total">
                <span class="calc-label">{owes_total_label}</span>
                <span class="calc-value">&euro;{roommate_owes:.2f}</span>
            </div>
        </div>
    </div>

    <div class="grand-total-card">
        <div class="grand-total-top">
            <span class="gt-label">{grand_total_label}</span>
            <span class="gt-value">&euro;{grand_total:.2f}</span>
        </div>
        <div class="grand-total-meta">
            <span>{receipts_count}</span>
            <span>{items_count}</span>
        </div>
    </div>

    {receipt_sections}

    <div class="page-footer">
        {footer_text} &middot; {generated_label} {today}
    </div>

</div>
</body>
</html>"""

    return html
