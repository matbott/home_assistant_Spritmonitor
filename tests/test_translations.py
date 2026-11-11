"""Checks that every sensor and setup message has text, so users never see raw keys."""
import json
from pathlib import Path

import pytest
from homeassistant.helpers import entity_registry as er

from .conftest import VEHICLE, make_entry, mock_api, setup_entry

COMPONENT = Path(__file__).parent.parent / "custom_components" / "spritmonitor"
TRANSLATION_FILES = [COMPONENT / "strings.json", *sorted((COMPONENT / "translations").glob("*.json"))]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", TRANSLATION_FILES, ids=lambda p: p.name)
def test_setup_messages_present(path):
    config = load(path)["config"]
    assert set(config["error"]) >= {"invalid_auth", "cannot_connect"}
    assert "already_configured" in config["abort"]


def _flat_keys(data, prefix=""):
    keys = set()
    for key, value in data.items():
        if isinstance(value, dict):
            keys |= _flat_keys(value, f"{prefix}{key}.")
        else:
            keys.add(f"{prefix}{key}")
    return keys


@pytest.mark.parametrize(
    "path", [p for p in TRANSLATION_FILES if p.name not in ("strings.json", "en.json")], ids=lambda p: p.name
)
def test_translation_has_every_english_key(path):
    """Every language has a text for everything English has, so nothing falls back to English."""
    english = _flat_keys(load(COMPONENT / "translations" / "en.json"))
    translated = _flat_keys(load(path))
    assert sorted(english - translated) == []
    assert sorted(translated - english) == []


def test_strings_json_matches_english():
    """strings.json is the source of the English texts; the two must not drift apart."""
    assert load(COMPONENT / "strings.json") == load(COMPONENT / "translations" / "en.json")


@pytest.mark.parametrize("vehicle_type", ["combustion", "electric", "phev"])
async def test_every_sensor_has_an_english_name(hass, aioclient_mock, vehicle_type):
    mock_api(aioclient_mock, vehicles=[VEHICLE])
    entry = make_entry(vehicle_type=vehicle_type)
    assert await setup_entry(hass, entry)

    names = load(COMPONENT / "translations" / "en.json")["entity"]["sensor"]
    keys = {e.translation_key for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}
    assert keys, "no sensors were created"
    assert sorted(keys - names.keys()) == []
