"""Tests for the translator module."""

import json
from unittest.mock import MagicMock, patch

import pytest

from translator import (
    _parse_llm_json,
    apply_bonuses,
    match_bonuses,
    save_translation,
    translate_items,
)


class TestParseLlmJson:
    def test_plain_json(self) -> None:
        result = _parse_llm_json('{"PAPRIKA": "Paprika"}')
        assert result == {"PAPRIKA": "Paprika"}

    def test_markdown_wrapped(self) -> None:
        raw = '```json\n{"PAPRIKA": "Paprika"}\n```'
        result = _parse_llm_json(raw)
        assert result == {"PAPRIKA": "Paprika"}

    def test_invalid_json_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            _parse_llm_json("not json at all")


class TestTranslateItems:
    @patch("translator._save_cache")
    @patch("translator._load_cache")
    def test_all_cached(self, mock_load: MagicMock, mock_save: MagicMock) -> None:
        """When all items are cached, no LLM call is made."""
        mock_load.return_value = {"PAPRIKA": "Paprika", "KOMKOMMER": "Cucumber"}
        result = translate_items(["PAPRIKA", "KOMKOMMER"])
        assert result == {"PAPRIKA": "Paprika", "KOMKOMMER": "Cucumber"}

    @patch("translator._save_cache")
    @patch("translator._call_llm")
    @patch("translator._load_cache")
    def test_unknown_items_call_llm(
        self, mock_load: MagicMock, mock_llm: MagicMock, mock_save: MagicMock
    ) -> None:
        mock_load.return_value = {"PAPRIKA": "Paprika"}
        mock_llm.return_value = '{"KOMKOMMER": "Cucumber"}'
        result = translate_items(["PAPRIKA", "KOMKOMMER"])
        assert result["KOMKOMMER"] == "Cucumber"
        mock_llm.assert_called_once()

    @patch("translator._save_cache")
    @patch("translator._call_llm")
    @patch("translator._load_cache")
    def test_malformed_llm_response_fallback(
        self, mock_load: MagicMock, mock_llm: MagicMock, mock_save: MagicMock
    ) -> None:
        """Malformed LLM response should fall back to identity mapping."""
        mock_load.return_value = {}
        mock_llm.return_value = "This is not JSON"
        result = translate_items(["PAPRIKA"])
        assert result["PAPRIKA"] == "PAPRIKA"


class TestSaveTranslation:
    @patch("translator._save_cache")
    @patch("translator._load_cache")
    def test_saves_to_cache(self, mock_load: MagicMock, mock_save: MagicMock) -> None:
        mock_load.return_value = {"PAPRIKA": "Paprika"}
        save_translation("KOMKOMMER", "Cucumber")
        saved = mock_save.call_args[0][1]
        assert saved["KOMKOMMER"] == "Cucumber"
        assert saved["PAPRIKA"] == "Paprika"


class TestMatchBonuses:
    def test_price_match(self) -> None:
        """Single candidate with matching unit price should match deterministically."""
        bonuses = [{"bonus_name": "AHPASTA", "amount": -1.29}]
        items = [
            {
                "name_dutch": "AH PASTA",
                "has_bonus": True,
                "unit_price": 1.29,
                "total_price": 1.29,
            }
        ]
        with patch("translator._load_cache", return_value={}), patch("translator._save_cache"):
            result = match_bonuses(bonuses, items)
        assert result["AHPASTA"] == "AH PASTA"

    def test_substring_match(self) -> None:
        """Substring matching should work when name parts appear in bonus code."""
        bonuses = [{"bonus_name": "AHBANANEN", "amount": -0.49}]
        items = [
            {
                "name_dutch": "AH BANANEN",
                "has_bonus": True,
                "unit_price": 0.99,
                "total_price": 1.98,
            }
        ]
        with patch("translator._load_cache", return_value={}), patch("translator._save_cache"):
            result = match_bonuses(bonuses, items)
        assert result["AHBANANEN"] == "AH BANANEN"

    def test_cached_match(self) -> None:
        """Cached matches should be returned without any matching logic."""
        bonuses = [{"bonus_name": "AHPASTA", "amount": -0.30}]
        items = [
            {"name_dutch": "AH PASTA", "has_bonus": True, "unit_price": None, "total_price": 1.29}
        ]
        with (
            patch("translator._load_cache", return_value={"AHPASTA": "AH PASTA"}),
            patch("translator._save_cache"),
        ):
            result = match_bonuses(bonuses, items)
        assert result["AHPASTA"] == "AH PASTA"

    def test_empty_bonuses(self) -> None:
        result = match_bonuses([], [{"has_bonus": True}])
        assert result == {}

    def test_no_bonus_items(self) -> None:
        result = match_bonuses([{"bonus_name": "X", "amount": -1}], [{"has_bonus": False}])
        assert result == {}


class TestApplyBonuses:
    def test_specific_bonuses_applied(self) -> None:
        """Specific bonuses should reduce item final_price."""
        receipt = {
            "bonuses": [{"bonus_name": "AHPASTA", "amount": -0.30}],
            "items": [
                {
                    "name_dutch": "AH PASTA",
                    "has_bonus": True,
                    "unit_price": None,
                    "total_price": 1.29,
                    "bonus_amount": 0.0,
                    "final_price": 1.29,
                }
            ],
            "total": 0.99,
        }
        with (
            patch("translator._load_cache", return_value={"AHPASTA": "AH PASTA"}),
            patch("translator._save_cache"),
        ):
            result = apply_bonuses(receipt)
        assert result["items"][0]["final_price"] == 0.99
        assert result["items"][0]["bonus_amount"] == -0.30

    def test_no_bonuses_passthrough(self) -> None:
        receipt = {"bonuses": [], "items": [{"has_bonus": False}], "total": 1.0}
        result = apply_bonuses(receipt)
        assert result is receipt

    def test_original_bonus_snapshot(self) -> None:
        """apply_bonuses should snapshot original_bonus_amount."""
        receipt = {
            "bonuses": [{"bonus_name": "AHPASTA", "amount": -0.30}],
            "items": [
                {
                    "name_dutch": "AH PASTA",
                    "has_bonus": True,
                    "unit_price": None,
                    "total_price": 1.29,
                    "bonus_amount": 0.0,
                    "final_price": 1.29,
                }
            ],
            "total": 0.99,
        }
        with (
            patch("translator._load_cache", return_value={"AHPASTA": "AH PASTA"}),
            patch("translator._save_cache"),
        ):
            apply_bonuses(receipt)
        assert receipt["items"][0]["original_bonus_amount"] == -0.30
