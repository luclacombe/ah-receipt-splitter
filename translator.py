"""Translate Dutch AH receipt items to English and match bonuses to items.

Uses Claude Haiku if ANTHROPIC_API_KEY is set, otherwise falls back to
Ollama running locally. Both paths use persistent JSON caches so each
unique item/bonus is only ever sent to the LLM once.
"""

import json
import logging
import os
from pathlib import Path

from config import BONUS_MATCHES_FILE, HAIKU_MODEL, OLLAMA_MODEL, TRANSLATIONS_FILE

logger = logging.getLogger(__name__)


def _load_cache(path: Path) -> dict[str, str]:
    """Load a JSON cache file, returning an empty dict if it doesn't exist."""
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save_cache(path: Path, data: dict[str, str]) -> None:
    """Persist a dict to a JSON cache file."""
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def _call_llm(system: str, user: str) -> str:
    """Call LLM backend: Claude Haiku if ANTHROPIC_API_KEY is set, else Ollama."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        resp = client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text
    else:
        try:
            import ollama

            resp = ollama.chat(
                model=OLLAMA_MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            return resp["message"]["content"]
        except Exception as e:
            raise RuntimeError(
                f"Ollama is not available ({e}). "
                "Either install and run Ollama (https://ollama.com) with "
                f"model '{OLLAMA_MODEL}', or set ANTHROPIC_API_KEY in your .env file."
            ) from e


def _parse_llm_json(raw: str) -> dict:
    """Extract and parse JSON from an LLM response, handling markdown code blocks."""
    json_str = raw.strip()
    if json_str.startswith("```"):
        json_str = json_str.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(json_str)


# ---------------------------------------------------------------------------
# Translation
# ---------------------------------------------------------------------------


def translate_items(dutch_names: list[str]) -> dict[str, str]:
    """Translate a list of Dutch item names to English.

    Uses local cache first, calls LLM only for unknown names.
    Returns {dutch_name: english_name} for all inputs.
    """
    cache = _load_cache(TRANSLATIONS_FILE)

    known: dict[str, str] = {}
    unknown: list[str] = []
    for name in set(dutch_names):
        if name in cache:
            known[name] = cache[name]
        else:
            unknown.append(name)

    logger.info("Translation cache hit: %d, new: %d", len(known), len(unknown))

    if unknown:
        prompt = (
            "Translate these abbreviated Dutch grocery item names from an "
            "Albert Heijn receipt to concise English. Names are often truncated "
            "(e.g. 'AH HOH GEHAK' = 'AH half-om-half gehakt' = Half beef/pork mince). "
            'Return ONLY valid JSON: {"DUTCH_NAME": "English name", ...}\n\n'
            + json.dumps(unknown, ensure_ascii=False)
        )
        raw = _call_llm(
            system="You translate Dutch grocery items to English. Return only JSON.",
            user=prompt,
        )
        try:
            new_translations = _parse_llm_json(raw)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Failed to parse LLM translation response: %s", raw[:200])
            new_translations = {name: name for name in unknown}

        cache.update(new_translations)
        _save_cache(TRANSLATIONS_FILE, cache)
        known.update(new_translations)

    return {name: known.get(name, name) for name in dutch_names}


def save_translation(dutch_name: str, english_name: str) -> None:
    """Save a user-edited translation to the persistent cache."""
    cache = _load_cache(TRANSLATIONS_FILE)
    cache[dutch_name] = english_name
    _save_cache(TRANSLATIONS_FILE, cache)


# ---------------------------------------------------------------------------
# Bonus matching
# ---------------------------------------------------------------------------


def match_bonuses(
    bonuses: list[dict],
    items: list[dict],
) -> dict[str, str]:
    """Match bonus discount lines to their corresponding B-marked items.

    Only handles specific (non-group) bonuses. Group bonuses (ALLE* prefix)
    should be handled separately via proportional distribution.

    Args:
        bonuses: [{"bonus_name": "AHBROCCOLILO", "amount": -0.49}, ...]
        items: parsed items list (only B-marked items are candidates)

    Returns:
        {bonus_name: item_name_dutch} mapping
    """
    cache = _load_cache(BONUS_MATCHES_FILE)

    b_items = [i for i in items if i["has_bonus"]]
    if not bonuses or not b_items:
        return {}

    matched: dict[str, str] = {}
    unmatched_bonuses: list[dict] = []

    for bonus in bonuses:
        bname = bonus["bonus_name"]
        if bname in cache:
            matched[bname] = cache[bname]
        else:
            # Deterministic: if bonus amount == exactly one B-item's unit price
            candidates = [
                i
                for i in b_items
                if i["unit_price"] is not None
                and abs(abs(bonus["amount"]) - i["unit_price"]) < 0.01
                and i["name_dutch"] not in matched.values()
            ]
            if len(candidates) == 1:
                matched[bname] = candidates[0]["name_dutch"]
                cache[bname] = candidates[0]["name_dutch"]
            else:
                # Deterministic: substring match
                for item in b_items:
                    if item["name_dutch"] not in matched.values():
                        name_parts = item["name_dutch"].split()
                        if any(part in bname.upper() for part in name_parts if len(part) >= 4):
                            matched[bname] = item["name_dutch"]
                            cache[bname] = item["name_dutch"]
                            break
                else:
                    unmatched_bonuses.append(bonus)

    logger.info(
        "Matched %d/%d bonuses deterministically, %d need LLM",
        len(matched),
        len(bonuses),
        len(unmatched_bonuses),
    )

    if unmatched_bonuses:
        remaining_items = [
            {"name": i["name_dutch"], "unit_price": i["unit_price"], "total": i["total_price"]}
            for i in b_items
            if i["name_dutch"] not in matched.values()
        ]
        prompt = (
            "Match these Albert Heijn bonus discount codes to their corresponding items. "
            'Return ONLY valid JSON: {"BONUS_CODE": "ITEM_NAME", ...}\n\n'
            "Bonus codes to match:\n"
            + json.dumps(
                [{"code": b["bonus_name"], "discount": b["amount"]} for b in unmatched_bonuses],
                ensure_ascii=False,
            )
            + "\n\nCandidate items (these had a 'B' bonus marker):\n"
            + json.dumps(remaining_items, ensure_ascii=False)
        )
        raw = _call_llm(
            system="You match Dutch grocery bonus codes to item names. Return only JSON.",
            user=prompt,
        )
        try:
            new_matches = _parse_llm_json(raw)
        except (json.JSONDecodeError, IndexError):
            logger.warning("Failed to parse LLM bonus match response: %s", raw[:200])
            new_matches = {}

        matched.update(new_matches)
        cache.update(new_matches)

    _save_cache(BONUS_MATCHES_FILE, cache)
    return matched


def apply_bonuses(receipt: dict) -> dict:
    """Match bonuses to items and compute final prices in-place.

    Handles two categories:
    - Group bonuses (ALLE* prefix): distributed proportionally across ALL B-items
    - Specific bonuses: matched 1:1 to individual items

    Modifies receipt['items'] to set bonus_amount and final_price.
    Returns the receipt.
    """
    bonuses = receipt["bonuses"]
    items = receipt["items"]
    b_items = [i for i in items if i["has_bonus"]]

    if not bonuses or not b_items:
        return receipt

    # Separate group bonuses (ALLE* pattern) from specific bonuses
    group_bonuses = [b for b in bonuses if b["bonus_name"].upper().startswith("ALLE")]
    specific_bonuses = [b for b in bonuses if not b["bonus_name"].upper().startswith("ALLE")]

    # Step 1: Match and apply specific bonuses (1:1)
    if specific_bonuses:
        mapping = match_bonuses(specific_bonuses, items)
        for bonus in specific_bonuses:
            item_name = mapping.get(bonus["bonus_name"])
            if item_name:
                for item in items:
                    if (
                        item["name_dutch"] == item_name
                        and item["has_bonus"]
                        and item["bonus_amount"] == 0.0
                    ):
                        item["bonus_amount"] = bonus["amount"]
                        item["final_price"] = round(item["total_price"] + bonus["amount"], 2)
                        break

    # Step 2: Distribute group bonuses proportionally across all B-items
    for bonus in group_bonuses:
        total_b_price = sum(i["total_price"] for i in b_items if i["total_price"] > 0)
        if total_b_price > 0:
            for item in b_items:
                if item["total_price"] > 0:
                    proportion = item["total_price"] / total_b_price
                    item_discount = round(bonus["amount"] * proportion, 2)
                    item["bonus_amount"] = round(item["bonus_amount"] + item_discount, 2)
                    item["final_price"] = round(item["total_price"] + item["bonus_amount"], 2)

    # Step 3: Verification — distribute any remaining difference proportionally
    computed = round(sum(i["final_price"] for i in items), 2)
    expected = receipt["total"]
    if abs(computed - expected) > 0.02:
        diff = round(expected - computed, 2)
        unmatched_b = [i for i in items if i["has_bonus"] and i["bonus_amount"] == 0.0]
        if unmatched_b:
            total_unmatched = sum(i["total_price"] for i in unmatched_b if i["total_price"] > 0)
            for item in unmatched_b:
                if total_unmatched > 0:
                    proportion = item["total_price"] / total_unmatched
                    item_discount = round(diff * proportion, 2)
                else:
                    item_discount = round(diff / len(unmatched_b), 2)
                item["bonus_amount"] = item_discount
                item["final_price"] = round(item["total_price"] + item_discount, 2)

    # Snapshot the system-assigned bonus so the PDF can highlight user edits
    for item in items:
        item["original_bonus_amount"] = item["bonus_amount"]

    return receipt
