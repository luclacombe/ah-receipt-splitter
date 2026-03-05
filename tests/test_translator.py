"""Tests for the translator module."""

import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from translator import (
    _call_llm,
    _parse_llm_json,
    apply_bonuses,
    match_bonuses,
    save_translation,
    translate_items,
)


class TestCallLlm:
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test", "OPENAI_API_KEY": ""})
    def test_anthropic_used_when_key_set(self) -> None:
        mock_anthropic = MagicMock()
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value.content = [MagicMock(text="response")]
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            result = _call_llm("system", "user")
        assert result == "response"
        mock_client.messages.create.assert_called_once()

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": "sk-test"})
    def test_openai_used_when_key_set(self) -> None:
        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_message = MagicMock()
        mock_message.message.content = "response"
        mock_client.chat.completions.create.return_value.choices = [mock_message]
        with patch.dict(sys.modules, {"openai": mock_openai}):
            result = _call_llm("system", "user")
        mock_openai.OpenAI.assert_called_once_with(api_key="sk-test")
        assert result == "response"

    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test", "OPENAI_API_KEY": "sk-test"})
    def test_anthropic_preferred_over_openai(self) -> None:
        """When both keys are set, Anthropic should be used."""
        mock_anthropic = MagicMock()
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value.content = [MagicMock(text="response")]
        with patch.dict(sys.modules, {"anthropic": mock_anthropic}):
            result = _call_llm("system", "user")
        assert result == "response"
        mock_client.messages.create.assert_called_once()


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

    def test_markdown_without_language_tag(self) -> None:
        """Code block without 'json' language tag should still parse."""
        raw = '```\n{"PAPRIKA": "Paprika"}\n```'
        result = _parse_llm_json(raw)
        assert result == {"PAPRIKA": "Paprika"}

    def test_json_with_surrounding_whitespace(self) -> None:
        raw = '  \n  {"PAPRIKA": "Paprika"}  \n  '
        result = _parse_llm_json(raw)
        assert result == {"PAPRIKA": "Paprika"}

    def test_empty_json_object(self) -> None:
        result = _parse_llm_json("{}")
        assert result == {}

    def test_json_with_unicode(self) -> None:
        raw = '{"BRÖTCHEN": "Bread roll"}'
        result = _parse_llm_json(raw)
        assert result["BRÖTCHEN"] == "Bread roll"


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

    @patch("translator._save_cache")
    @patch("translator._load_cache")
    def test_empty_list(self, mock_load: MagicMock, mock_save: MagicMock) -> None:
        """Empty input should return empty dict without LLM call."""
        mock_load.return_value = {}
        result = translate_items([])
        assert result == {}

    @patch("translator._save_cache")
    @patch("translator._call_llm")
    @patch("translator._load_cache")
    def test_duplicate_names_deduplicated(
        self, mock_load: MagicMock, mock_llm: MagicMock, mock_save: MagicMock
    ) -> None:
        """Duplicate Dutch names should only trigger one LLM call per unique name."""
        mock_load.return_value = {}
        mock_llm.return_value = '{"PAPRIKA": "Paprika"}'
        result = translate_items(["PAPRIKA", "PAPRIKA", "PAPRIKA"])
        assert result == {"PAPRIKA": "Paprika"}
        mock_llm.assert_called_once()

    @patch("translator._save_cache")
    @patch("translator._call_llm")
    @patch("translator._load_cache")
    def test_partial_cache_hit(
        self, mock_load: MagicMock, mock_llm: MagicMock, mock_save: MagicMock
    ) -> None:
        """Mix of cached and uncached items: LLM called only for uncached."""
        mock_load.return_value = {"PAPRIKA": "Paprika"}
        mock_llm.return_value = '{"KOMKOMMER": "Cucumber", "WORTEL": "Carrot"}'
        result = translate_items(["PAPRIKA", "KOMKOMMER", "WORTEL"])
        assert result["PAPRIKA"] == "Paprika"
        assert result["KOMKOMMER"] == "Cucumber"
        assert result["WORTEL"] == "Carrot"
        mock_llm.assert_called_once()

    @patch("translator._save_cache")
    @patch("translator._call_llm")
    @patch("translator._load_cache")
    def test_llm_returns_partial_translations(
        self, mock_load: MagicMock, mock_llm: MagicMock, mock_save: MagicMock
    ) -> None:
        """LLM returns translations for only some items; missing ones get identity mapping."""
        mock_load.return_value = {}
        mock_llm.return_value = '{"PAPRIKA": "Paprika"}'
        result = translate_items(["PAPRIKA", "UNKNOWN_ITEM"])
        assert result["PAPRIKA"] == "Paprika"
        assert result["UNKNOWN_ITEM"] == "UNKNOWN_ITEM"


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

    def test_multiple_items_same_price_no_false_match(self) -> None:
        """When two B-items share the same unit_price, price match should not return either (ambiguous)."""
        bonuses = [{"bonus_name": "AHKAAS", "amount": -1.29}]
        items = [
            {"name_dutch": "AH KAAS", "has_bonus": True, "unit_price": 1.29, "total_price": 1.29},
            {"name_dutch": "AH BROOD", "has_bonus": True, "unit_price": 1.29, "total_price": 1.29},
        ]
        with patch("translator._load_cache", return_value={}), patch("translator._save_cache"):
            # Price match has 2 candidates → falls through to substring match
            # "KAAS" (4 chars) should match "AHKAAS"
            result = match_bonuses(bonuses, items)
            assert result.get("AHKAAS") == "AH KAAS"

    def test_llm_fallback_for_unmatched(self) -> None:
        """Bonuses that match neither by price nor substring should trigger LLM."""
        bonuses = [{"bonus_name": "XYZCODE", "amount": -0.50}]
        items = [
            {"name_dutch": "AB CD", "has_bonus": True, "unit_price": 2.00, "total_price": 2.00},
        ]
        with (
            patch("translator._load_cache", return_value={}),
            patch("translator._save_cache"),
            patch("translator._call_llm", return_value='{"XYZCODE": "AB CD"}') as mock_llm,
        ):
            result = match_bonuses(bonuses, items)
            mock_llm.assert_called_once()
            assert result["XYZCODE"] == "AB CD"

    def test_llm_fallback_malformed_returns_empty(self) -> None:
        """Malformed LLM response for bonus matching should not crash."""
        bonuses = [{"bonus_name": "XYZCODE", "amount": -0.50}]
        items = [
            {"name_dutch": "AB CD", "has_bonus": True, "unit_price": 2.00, "total_price": 2.00},
        ]
        with (
            patch("translator._load_cache", return_value={}),
            patch("translator._save_cache"),
            patch("translator._call_llm", return_value="not json"),
        ):
            result = match_bonuses(bonuses, items)
            assert "XYZCODE" not in result

    def test_short_name_parts_skip_substring_match(self) -> None:
        """Name parts shorter than 4 chars should not be used for substring matching."""
        bonuses = [{"bonus_name": "AHEI", "amount": -0.30}]
        items = [
            {"name_dutch": "AH EI", "has_bonus": True, "unit_price": 1.00, "total_price": 1.00},
        ]
        with (
            patch("translator._load_cache", return_value={}),
            patch("translator._save_cache"),
            patch("translator._call_llm", return_value='{"AHEI": "AH EI"}'),
        ):
            # "AH" (2 chars) and "EI" (2 chars) are both < 4, so substring won't match
            # Falls through to LLM
            result = match_bonuses(bonuses, items)
            assert result.get("AHEI") == "AH EI"


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

    def test_group_bonus_distributed_proportionally(self) -> None:
        """ALLE* prefixed bonuses should split proportionally across B-items."""
        receipt = {
            "bonuses": [{"bonus_name": "ALLEGROENTE", "amount": -1.00}],
            "items": [
                {
                    "name_dutch": "PAPRIKA",
                    "has_bonus": True,
                    "unit_price": None,
                    "total_price": 3.00,
                    "bonus_amount": 0.0,
                    "final_price": 3.00,
                },
                {
                    "name_dutch": "KOMKOMMER",
                    "has_bonus": True,
                    "unit_price": None,
                    "total_price": 1.00,
                    "bonus_amount": 0.0,
                    "final_price": 1.00,
                },
            ],
            "total": 3.00,
        }
        result = apply_bonuses(receipt)
        paprika = result["items"][0]
        komkommer = result["items"][1]
        # 3/(3+1) = 75% of -1.00 = -0.75, 1/(3+1) = 25% of -1.00 = -0.25
        assert paprika["bonus_amount"] == pytest.approx(-0.75, abs=0.01)
        assert komkommer["bonus_amount"] == pytest.approx(-0.25, abs=0.01)
        assert paprika["final_price"] == pytest.approx(2.25, abs=0.01)
        assert komkommer["final_price"] == pytest.approx(0.75, abs=0.01)

    def test_verification_redistributes_difference(self) -> None:
        """If computed total != receipt total, difference is redistributed to unmatched B-items."""
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
                },
                {
                    "name_dutch": "PAPRIKA",
                    "has_bonus": True,
                    "unit_price": None,
                    "total_price": 1.00,
                    "bonus_amount": 0.0,
                    "final_price": 1.00,
                },
                {
                    "name_dutch": "KOMKOMMER",
                    "has_bonus": False,
                    "unit_price": None,
                    "total_price": 0.89,
                    "bonus_amount": 0.0,
                    "final_price": 0.89,
                },
            ],
            # Total is lower than sum of items minus known bonus,
            # forcing verification redistribution to PAPRIKA (unmatched B-item)
            "total": 2.38,
        }
        with (
            patch("translator._load_cache", return_value={"AHPASTA": "AH PASTA"}),
            patch("translator._save_cache"),
        ):
            result = apply_bonuses(receipt)
        # AH PASTA gets -0.30 specific bonus → 0.99
        assert result["items"][0]["bonus_amount"] == -0.30
        # Computed without redistribution: 0.99 + 1.00 + 0.89 = 2.88
        # Expected: 2.38, diff = -0.50, assigned to PAPRIKA
        paprika = result["items"][1]
        assert paprika["bonus_amount"] != 0.0
        assert paprika["final_price"] < paprika["total_price"]

    def test_apply_bonuses_sets_original_for_all_items(self) -> None:
        """Every item should get original_bonus_amount snapshot, even non-bonus items."""
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
                },
                {
                    "name_dutch": "KOMKOMMER",
                    "has_bonus": False,
                    "unit_price": None,
                    "total_price": 0.89,
                    "bonus_amount": 0.0,
                    "final_price": 0.89,
                },
            ],
            "total": 1.88,
        }
        with (
            patch("translator._load_cache", return_value={"AHPASTA": "AH PASTA"}),
            patch("translator._save_cache"),
        ):
            apply_bonuses(receipt)
        for item in receipt["items"]:
            assert "original_bonus_amount" in item

    def test_mixed_specific_and_group_bonuses(self) -> None:
        """Both specific and group bonuses in one receipt."""
        receipt = {
            "bonuses": [
                {"bonus_name": "AHPASTA", "amount": -0.30},
                {"bonus_name": "ALLEGROENTE", "amount": -0.50},
            ],
            "items": [
                {
                    "name_dutch": "AH PASTA",
                    "has_bonus": True,
                    "unit_price": None,
                    "total_price": 1.29,
                    "bonus_amount": 0.0,
                    "final_price": 1.29,
                },
                {
                    "name_dutch": "PAPRIKA",
                    "has_bonus": True,
                    "unit_price": None,
                    "total_price": 1.00,
                    "bonus_amount": 0.0,
                    "final_price": 1.00,
                },
            ],
            "total": 1.49,
        }
        with (
            patch("translator._load_cache", return_value={"AHPASTA": "AH PASTA"}),
            patch("translator._save_cache"),
        ):
            result = apply_bonuses(receipt)
        pasta = result["items"][0]
        paprika = result["items"][1]
        # Pasta: specific -0.30 + proportional share of group bonus
        assert pasta["bonus_amount"] < 0
        # Paprika: proportional share of group bonus
        assert paprika["bonus_amount"] < 0
