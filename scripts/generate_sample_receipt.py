#!/usr/bin/env python3
"""Generate a synthetic Albert Heijn receipt PDF for testing.

The output matches the text format that pdfplumber extracts and
receipt_parser.py expects. Run this script to regenerate the fixture:

    python scripts/generate_sample_receipt.py
"""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas

FIXTURE_PATH = Path(__file__).parent.parent / "fixtures" / "sample_receipt.pdf"

# Synthetic receipt lines — must match receipt_parser.py regex patterns
RECEIPT_LINES = [
    "1420",
    "",
    "Albert Heijn",
    "Sample Store",
    "",
    "1 AH PASTA PENNE             1,29 B",
    "1 CHAMPIGNONS                1,49",
    "2 AH BANANEN      0,99       1,98 B",
    "+STATIEGELD 0,25",
    "1 KOMKOMMER                  0,89",
    "1 PAPRIKA                    1,29 B",
    "",
    "SUBTOTAAL                    7,19",
    "",
    "BONUS AHPASTAPENN           -0,30",
    "BONUS AHBANANEN             -0,49",
    "",
    "UW VOORDEEL                  0,79",
    "",
    "TOTAAL                       6,40",
]


def main() -> None:
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)

    c = Canvas(str(FIXTURE_PATH), pagesize=A4)
    width, height = A4

    # Use a monospaced font for consistent spacing
    c.setFont("Courier", 9)

    x = 20 * mm
    y = height - 20 * mm

    for line in RECEIPT_LINES:
        c.drawString(x, y, line)
        y -= 4 * mm

    c.save()
    print(f"Generated: {FIXTURE_PATH}")

    # Verify it parses correctly
    import sys

    sys.path.insert(0, str(FIXTURE_PATH.parent.parent))
    from receipt_parser import parse_receipt

    result = parse_receipt(FIXTURE_PATH)
    print(f"  Items: {len(result['items'])}")
    print(f"  Bonuses: {len(result['bonuses'])}")
    print(f"  Total: {result['total']}")
    for item in result["items"]:
        print(
            f"    {item['name_dutch']:20s}  €{item['total_price']:.2f}  bonus={item['has_bonus']}"
        )
    if result["warnings"]:
        print(f"  Warnings: {result['warnings']}")


if __name__ == "__main__":
    main()
