"""Parse Albert Heijn receipt PDFs into structured data."""

import re
from pathlib import Path

import pdfplumber


def _parse_price(s: str) -> float:
    """Convert Dutch price string '12,70' to float 12.70."""
    return float(s.replace(",", "."))


def _extract_items(text: str) -> list[dict]:
    """Extract line items from receipt text, including +STATIEGELD deposits."""
    items = []
    # Matches: qty  name  [unit_price]  total  [B]
    item_pattern = re.compile(
        r"^([\d.]+(?:KG)?)\s+(.+?)\s+(?:(\d+,\d+)\s+)?(\d+,\d+)\s*(B)?$",
        re.MULTILINE,
    )
    # Matches: +STATIEGELD  amount
    statiegeld_pattern = re.compile(
        r"^\+STATIEGELD\s+(\d+,\d+)$",
        re.MULTILINE,
    )

    # Build a set of statiegeld line positions and their amounts
    statiegeld_positions = {}
    for m in statiegeld_pattern.finditer(text):
        statiegeld_positions[m.start()] = _parse_price(m.group(1))

    for m in item_pattern.finditer(text):
        name = m.group(2).strip()
        if name in ("SUBTOTAAL",):
            continue
        total_price = _parse_price(m.group(4))

        # Check if a +STATIEGELD line follows this item
        statiegeld = 0.0
        rest = text[m.end() :]
        s = re.match(r"\s*\+STATIEGELD\s+(\d+,\d+)", rest)
        if s:
            statiegeld = _parse_price(s.group(1))

        items.append(
            {
                "quantity": m.group(1),
                "name_dutch": name,
                "unit_price": _parse_price(m.group(3)) if m.group(3) else None,
                "total_price": total_price + statiegeld,
                "has_bonus": m.group(5) == "B",
                "bonus_amount": 0.0,
                "final_price": total_price + statiegeld,
                "statiegeld": statiegeld,
            }
        )
    return items


def _extract_bonuses(text: str) -> list[dict]:
    """Extract bonus discount lines."""
    bonuses = []
    pattern = re.compile(r"^BONUS\s+(\S+)\s+(-\d+,\d+)$", re.MULTILINE)
    for m in pattern.finditer(text):
        name = m.group(1)
        if name == "BOX":
            continue
        bonuses.append(
            {
                "bonus_name": name,
                "amount": _parse_price(m.group(2)),
            }
        )
    return bonuses


def _extract_metadata(text: str, filename: str) -> dict:
    """Extract store ID, date, time, totals."""
    meta = {}

    # Store ID: first line of page 1
    first_line = text.split("\n")[0].strip()
    if first_line.isdigit():
        meta["store_id"] = first_line

    # Subtotal
    m = re.search(r"SUBTOTAAL\s+(\d+,\d+)", text)
    if m:
        meta["subtotal"] = _parse_price(m.group(1))

    # Total discount
    m = re.search(r"UW VOORDEEL\s+(\d+,\d+)", text)
    if m:
        meta["total_discount"] = _parse_price(m.group(1))

    # Total
    m = re.search(r"^TOTAAL\s+(\d+,\d+)", text, re.MULTILINE)
    if m:
        meta["total"] = _parse_price(m.group(1))

    # Date/time from filename (format: AH_receipt_YYYY-MM-DD HHMMSS_STOREID.pdf)
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})\s+(\d{2})(\d{2})(\d{2})", filename)
    if m:
        meta["date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        meta["time"] = f"{m.group(4)}:{m.group(5)}"

    return meta


def parse_receipt(pdf_path: str | Path) -> dict:
    """Parse an AH receipt PDF into structured data.

    Returns dict with keys: store_id, date, time, items, bonuses,
    subtotal, total_discount, total.
    """
    pdf_path = Path(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        all_text = "\n".join((page.extract_text() or "") for page in pdf.pages)

    items = _extract_items(all_text)
    bonuses = _extract_bonuses(all_text)
    metadata = _extract_metadata(all_text, pdf_path.name)

    warnings = []
    if not metadata.get("total"):
        warnings.append("Could not parse receipt total (TOTAAL line not found)")
    if not metadata.get("date"):
        warnings.append("Could not parse date from filename")
    if not items:
        warnings.append("No items found on this receipt")

    result = {
        "file": pdf_path.name,
        "store_id": metadata.get("store_id", ""),
        "date": metadata.get("date", ""),
        "time": metadata.get("time", ""),
        "items": items,
        "bonuses": bonuses,
        "subtotal": metadata.get("subtotal", 0.0),
        "total_discount": metadata.get("total_discount", 0.0),
        "total": metadata.get("total", 0.0),
        "warnings": warnings,
    }

    return result
