"""Tests for the report generation module."""

from report import _build_html, _esc, generate_report


class TestEsc:
    def test_escapes_html(self) -> None:
        assert _esc("<script>") == "&lt;script&gt;"

    def test_passes_plain_text(self) -> None:
        assert _esc("Hello") == "Hello"

    def test_escapes_ampersand(self) -> None:
        assert _esc("A & B") == "A &amp; B"


class TestBuildHtml:
    def _make_receipt(self) -> list[dict]:
        return [
            {
                "file": "test.pdf",
                "date": "2026-03-01",
                "time": "12:00",
                "total": 5.0,
                "total_discount": 0.5,
                "items": [
                    {
                        "name_dutch": "PAPRIKA",
                        "quantity": "1",
                        "unit_price": None,
                        "total_price": 2.0,
                        "final_price": 2.0,
                        "bonus_amount": 0.0,
                        "original_bonus_amount": 0.0,
                        "has_bonus": False,
                        "statiegeld": 0,
                    },
                    {
                        "name_dutch": "KOMKOMMER",
                        "quantity": "1",
                        "unit_price": None,
                        "total_price": 3.0,
                        "final_price": 3.0,
                        "bonus_amount": 0.0,
                        "original_bonus_amount": 0.0,
                        "has_bonus": False,
                        "statiegeld": 0,
                    },
                ],
            }
        ]

    def test_contains_date(self) -> None:
        html = _build_html(self._make_receipt(), {}, {})
        assert "2026-03-01" in html

    def test_contains_items(self) -> None:
        html = _build_html(self._make_receipt(), {}, {"PAPRIKA": "Paprika"})
        assert "Paprika" in html

    def test_english_mode_shows_dutch_subtitle(self) -> None:
        translations = {"PAPRIKA": "Bell pepper"}
        html = _build_html(self._make_receipt(), {}, translations, language="en")
        assert "Bell pepper" in html
        assert "PAPRIKA" in html

    def test_dutch_mode(self) -> None:
        html = _build_html(self._make_receipt(), {}, {}, language="nl")
        assert "Kassabon Verdeling Rapport" in html

    def test_english_mode(self) -> None:
        html = _build_html(self._make_receipt(), {}, {}, language="en")
        assert "Grocery Split Report" in html

    def test_roommate_name_in_output(self) -> None:
        html = _build_html(self._make_receipt(), {}, {}, roommate_name="Kevin")
        assert "Kevin" in html

    def test_owes_calculation(self) -> None:
        """With all items shared (default), roommate owes half."""
        receipts = self._make_receipt()
        html = _build_html(receipts, {}, {})
        # All items shared = 5.0, half = 2.50
        assert "&euro;2.50" in html

    def test_assignment_mine(self) -> None:
        """Items assigned as mine (1) should show MINE badge."""
        receipts = self._make_receipt()
        assignments = {"test.pdf": {0: 1, 1: 1}}
        html = _build_html(receipts, assignments, {}, language="en")
        assert "MINE" in html

    def test_assignment_roommate(self) -> None:
        receipts = self._make_receipt()
        assignments = {"test.pdf": {0: 2, 1: 2}}
        html = _build_html(receipts, assignments, {}, roommate_name="Kevin", language="en")
        assert "KEVIN" in html


class TestGenerateReport:
    def test_returns_pdf_bytes(self) -> None:
        receipts = [
            {
                "file": "test.pdf",
                "date": "2026-03-01",
                "time": "12:00",
                "total": 2.0,
                "total_discount": 0.0,
                "items": [
                    {
                        "name_dutch": "PAPRIKA",
                        "quantity": "1",
                        "unit_price": None,
                        "total_price": 2.0,
                        "final_price": 2.0,
                        "bonus_amount": 0.0,
                        "original_bonus_amount": 0.0,
                        "has_bonus": False,
                        "statiegeld": 0,
                    }
                ],
            }
        ]
        pdf_bytes = generate_report(receipts, {}, {})
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"

    def test_empty_receipts(self) -> None:
        pdf_bytes = generate_report([], {}, {})
        assert isinstance(pdf_bytes, bytes)
        assert pdf_bytes[:5] == b"%PDF-"
