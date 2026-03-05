"""Tests for the receipt parser module."""

from pathlib import Path

import pytest

from receipt_parser import (
    _extract_bonuses,
    _extract_items,
    _extract_metadata,
    _parse_price,
    parse_receipt,
)


class TestParsePrice:
    def test_simple_price(self) -> None:
        assert _parse_price("12,70") == 12.70

    def test_small_price(self) -> None:
        assert _parse_price("0,99") == 0.99

    def test_negative_price(self) -> None:
        assert _parse_price("-0,49") == -0.49

    def test_zero(self) -> None:
        assert _parse_price("0,00") == 0.0


class TestExtractItems:
    def test_extracts_correct_count(self, sample_receipt_text: str) -> None:
        items = _extract_items(sample_receipt_text)
        assert len(items) == 5

    def test_item_names(self, sample_receipt_text: str) -> None:
        items = _extract_items(sample_receipt_text)
        names = [i["name_dutch"] for i in items]
        assert "AH PASTA PENNE" in names
        assert "CHAMPIGNONS" in names
        assert "AH BANANEN" in names
        assert "KOMKOMMER" in names
        assert "PAPRIKA" in names

    def test_excludes_subtotaal(self, sample_receipt_text: str) -> None:
        items = _extract_items(sample_receipt_text)
        names = [i["name_dutch"] for i in items]
        assert "SUBTOTAAL" not in names

    def test_bonus_flags(self, sample_receipt_text: str) -> None:
        items = _extract_items(sample_receipt_text)
        bonus_items = [i for i in items if i["has_bonus"]]
        assert len(bonus_items) == 3

    def test_statiegeld(self, sample_receipt_text: str) -> None:
        items = _extract_items(sample_receipt_text)
        bananen = next(i for i in items if i["name_dutch"] == "AH BANANEN")
        assert bananen["statiegeld"] == 0.25
        assert bananen["total_price"] == pytest.approx(2.23, abs=0.01)

    def test_unit_price(self, sample_receipt_text: str) -> None:
        items = _extract_items(sample_receipt_text)
        bananen = next(i for i in items if i["name_dutch"] == "AH BANANEN")
        assert bananen["unit_price"] == 0.99
        assert bananen["quantity"] == "2"

    def test_no_items(self) -> None:
        items = _extract_items("some random text with no receipt data")
        assert items == []


class TestExtractBonuses:
    def test_extracts_bonuses(self, sample_receipt_text: str) -> None:
        bonuses = _extract_bonuses(sample_receipt_text)
        assert len(bonuses) == 2

    def test_bonus_names(self, sample_receipt_text: str) -> None:
        bonuses = _extract_bonuses(sample_receipt_text)
        names = [b["bonus_name"] for b in bonuses]
        assert "AHPASTAPENN" in names
        assert "AHBANANEN" in names

    def test_bonus_amounts(self, sample_receipt_text: str) -> None:
        bonuses = _extract_bonuses(sample_receipt_text)
        amounts = {b["bonus_name"]: b["amount"] for b in bonuses}
        assert amounts["AHPASTAPENN"] == -0.30
        assert amounts["AHBANANEN"] == -0.49

    def test_skips_bonus_box(self) -> None:
        text = "BONUS BOX -1,00\nBONUS AHPASTA -0,30"
        bonuses = _extract_bonuses(text)
        assert len(bonuses) == 1
        assert bonuses[0]["bonus_name"] == "AHPASTA"

    def test_no_bonuses(self) -> None:
        bonuses = _extract_bonuses("no bonus lines here")
        assert bonuses == []


class TestExtractMetadata:
    def test_store_id(self, sample_receipt_text: str) -> None:
        meta = _extract_metadata(sample_receipt_text, "AH_receipt_2026-03-01 120000_1420.pdf")
        assert meta["store_id"] == "1420"

    def test_subtotal(self, sample_receipt_text: str) -> None:
        meta = _extract_metadata(sample_receipt_text, "test.pdf")
        assert meta["subtotal"] == 7.19

    def test_total(self, sample_receipt_text: str) -> None:
        meta = _extract_metadata(sample_receipt_text, "test.pdf")
        assert meta["total"] == 6.40

    def test_total_discount(self, sample_receipt_text: str) -> None:
        meta = _extract_metadata(sample_receipt_text, "test.pdf")
        assert meta["total_discount"] == 0.79

    def test_date_from_filename(self) -> None:
        meta = _extract_metadata("", "AH_receipt_2026-03-01 120000_1420.pdf")
        assert meta["date"] == "2026-03-01"
        assert meta["time"] == "12:00"

    def test_missing_date(self) -> None:
        meta = _extract_metadata("", "random_file.pdf")
        assert "date" not in meta


class TestParseReceipt:
    def test_end_to_end(self, sample_receipt_path: Path) -> None:
        result = parse_receipt(sample_receipt_path)
        assert result["file"] == sample_receipt_path.name
        assert len(result["items"]) > 0
        assert result["total"] > 0

    def test_warnings_on_empty(self, tmp_path: Path) -> None:
        """A file with no parseable content should produce warnings."""
        # Create a minimal valid PDF with no receipt content
        from reportlab.pdfgen.canvas import Canvas

        pdf_path = tmp_path / "empty.pdf"
        c = Canvas(str(pdf_path))
        c.drawString(100, 700, "Not a receipt")
        c.save()

        result = parse_receipt(pdf_path)
        assert len(result["warnings"]) > 0
        assert result["items"] == []
