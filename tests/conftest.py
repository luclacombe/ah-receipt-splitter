"""Shared test fixtures for the receipt splitter test suite."""

from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def sample_receipt_path() -> Path:
    """Path to the sample AH receipt PDF fixture."""
    path = FIXTURES_DIR / "sample_receipt.pdf"
    assert path.exists(), f"Fixture not found: {path}"
    return path


@pytest.fixture
def sample_receipt_text() -> str:
    """Raw text representing a typical AH receipt (as extracted by pdfplumber)."""
    return (
        "1420\n"
        "Albert Heijn\n"
        "Sample Store\n"
        "\n"
        "1 AH PASTA PENNE 1,29 B\n"
        "1 CHAMPIGNONS 1,49\n"
        "2 AH BANANEN 0,99 1,98 B\n"
        "+STATIEGELD 0,25\n"
        "1 KOMKOMMER 0,89\n"
        "1 PAPRIKA 1,29 B\n"
        "SUBTOTAAL 7,19\n"
        "BONUS AHPASTAPENN -0,30\n"
        "BONUS AHBANANEN -0,49\n"
        "UW VOORDEEL 0,79\n"
        "TOTAAL 6,40"
    )


@pytest.fixture
def sample_items() -> list[dict]:
    """Pre-parsed items for testing assignment and report logic."""
    return [
        {
            "quantity": "1",
            "name_dutch": "AH PASTA PENNE",
            "unit_price": None,
            "total_price": 1.29,
            "has_bonus": True,
            "bonus_amount": -0.30,
            "final_price": 0.99,
            "statiegeld": 0,
            "original_bonus_amount": -0.30,
        },
        {
            "quantity": "1",
            "name_dutch": "CHAMPIGNONS",
            "unit_price": None,
            "total_price": 1.49,
            "has_bonus": False,
            "bonus_amount": 0.0,
            "final_price": 1.49,
            "statiegeld": 0,
            "original_bonus_amount": 0.0,
        },
        {
            "quantity": "2",
            "name_dutch": "AH BANANEN",
            "unit_price": 0.99,
            "total_price": 1.98,
            "has_bonus": True,
            "bonus_amount": -0.49,
            "final_price": 1.74,
            "statiegeld": 0.25,
            "original_bonus_amount": -0.49,
        },
        {
            "quantity": "1",
            "name_dutch": "KOMKOMMER",
            "unit_price": None,
            "total_price": 0.89,
            "has_bonus": False,
            "bonus_amount": 0.0,
            "final_price": 0.89,
            "statiegeld": 0,
            "original_bonus_amount": 0.0,
        },
        {
            "quantity": "1",
            "name_dutch": "PAPRIKA",
            "unit_price": None,
            "total_price": 1.29,
            "has_bonus": True,
            "bonus_amount": 0.0,
            "final_price": 1.29,
            "statiegeld": 0,
            "original_bonus_amount": 0.0,
        },
    ]


@pytest.fixture
def sample_receipt_data(sample_items: list[dict]) -> dict:
    """A complete parsed receipt dict for testing."""
    return {
        "file": "AH_receipt_2026-03-01 120000_1420.pdf",
        "store_id": "1420",
        "date": "2026-03-01",
        "time": "12:00",
        "items": sample_items,
        "bonuses": [
            {"bonus_name": "AHPASTAPENN", "amount": -0.30},
            {"bonus_name": "AHBANANEN", "amount": -0.49},
        ],
        "subtotal": 7.19,
        "total_discount": 0.79,
        "total": 6.40,
        "warnings": [],
    }
