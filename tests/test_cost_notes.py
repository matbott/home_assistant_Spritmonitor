"""Tests for the latest cost/note entry sensors (issue #27)."""
import pytest

from custom_components.spritmonitor import sensor as s
from custom_components.spritmonitor.const import (
    API_COSTSDISTRIBUTION_URL_TPL,
    API_COSTSNOTES_URL_TPL,
    COSTSNOTES_FETCH_LIMIT,
    DOMAIN,
)

from .conftest import VEHICLE_ID, make_entry, mock_api, sensor_state, setup_entry

COSTSNOTES_URL = API_COSTSNOTES_URL_TPL.format(vehicle_id=VEHICLE_ID)
DISTRIBUTION_URL = API_COSTSDISTRIBUTION_URL_TPL.format(vehicle_id=VEHICLE_ID)

# Deliberately not in date order - the coordinator sorts them newest first
COSTS_NOTES = [
    {"id": 5, "date": "01.06.2025", "costtype": 1, "cost": 320.0, "cost_converted": 320.0,
     "odometer": 70100, "note": "Big service"},
    {"id": 9, "date": "02.10.2026", "costtype": 7, "cost": 450.0, "cost_converted": 412.5,
     "currencyid": 2, "odometer": 0, "note": "Annual insurance", "repeatinterval": 12},
    {"id": 8, "date": "15.06.2026", "costtype": 1, "cost": 189.99, "cost_converted": 189.99,
     "odometer": 84210, "note": "Oil + filter"},
]
# Names come translated into the user's language
DISTRIBUTION = [
    {"id": 1, "name": "Service", "costsum": 509.99, "curname": "EUR"},
    {"id": 7, "name": "Insurance", "costsum": 412.5, "curname": "EUR"},
]


def calls_to(aioclient_mock, url):
    return [c for c in aioclient_mock.mock_calls if str(c[1]).startswith(url)]


async def test_cost_note_sensors(hass, aioclient_mock):
    mock_api(aioclient_mock, extra={COSTSNOTES_URL: COSTS_NOTES, DISTRIBUTION_URL: DISTRIBUTION})
    assert await setup_entry(hass, make_entry())

    date_state = sensor_state(hass, "last_cost_entry_date")
    assert date_state.state == "2026-10-02"
    assert date_state.attributes["device_class"] == "date"
    # The insurance entry has no odometer (0), so the odometer is unknown rather than 0
    assert sensor_state(hass, "last_cost_entry_odometer").state == "unknown"
    assert sensor_state(hass, "last_cost_entry_odometer").attributes["unit_of_measurement"] == "km"
    assert sensor_state(hass, "last_cost_entry_note").state == "Annual insurance"

    attrs = sensor_state(hass, "last_cost_entry_note").attributes
    assert attrs["cost_type"] == "Insurance"
    assert attrs["cost"] == 412.5  # converted to the user's currency, not the 450 entered
    assert attrs["repeat_interval_months"] == 12
    assert attrs["latest_by_type"] == {
        "Insurance": {"date": "2026-10-02", "odometer": None, "note": "Annual insurance"},
        "Service": {"date": "2026-06-15", "odometer": 84210.0, "note": "Oil + filter"},
    }
    # Fetches enough history to find the latest entry of each type
    assert f"limit={COSTSNOTES_FETCH_LIMIT}" in str(calls_to(aioclient_mock, COSTSNOTES_URL)[0][1])


async def test_cost_notes_are_optional(hass, aioclient_mock):
    mock_api(aioclient_mock)
    aioclient_mock.get(COSTSNOTES_URL, status=500)
    entry = make_entry()
    assert await setup_entry(hass, entry)
    assert hass.data[DOMAIN][entry.entry_id].data["costs_notes"] is None
    assert sensor_state(hass, "last_cost_entry_date").state == "unknown"
    assert sensor_state(hass, "last_cost_entry_note").attributes.get("latest_by_type") is None
    # Nothing to name, so the cost types are not requested at all
    assert not calls_to(aioclient_mock, DISTRIBUTION_URL)


async def test_unknown_cost_type_falls_back_to_id(hass, aioclient_mock):
    mock_api(aioclient_mock, extra={COSTSNOTES_URL: COSTS_NOTES, DISTRIBUTION_URL: []})
    assert await setup_entry(hass, make_entry())
    attrs = sensor_state(hass, "last_cost_entry_note").attributes
    assert attrs["cost_type"] == "7"
    assert set(attrs["latest_by_type"]) == {"1", "7"}


async def test_cost_type_names_are_cached(hass, aioclient_mock):
    mock_api(aioclient_mock, extra={COSTSNOTES_URL: COSTS_NOTES, DISTRIBUTION_URL: DISTRIBUTION})
    entry = make_entry()
    assert await setup_entry(hass, entry)
    coordinator = hass.data[DOMAIN][entry.entry_id]
    assert len(calls_to(aioclient_mock, DISTRIBUTION_URL)) == 1

    # Same cost types again: names come from the cache
    await coordinator.async_refresh()
    assert len(calls_to(aioclient_mock, DISTRIBUTION_URL)) == 1

    # A new cost type appears: the names are fetched again
    aioclient_mock.clear_requests()
    mock_api(
        aioclient_mock,
        extra={
            COSTSNOTES_URL: [*COSTS_NOTES, {"id": 10, "date": "03.10.2026", "costtype": 3, "cost": 40, "note": "Tyres"}],
            DISTRIBUTION_URL: [*DISTRIBUTION, {"id": 3, "name": "Tyres", "costsum": 40, "curname": "EUR"}],
        },
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(calls_to(aioclient_mock, DISTRIBUTION_URL)) == 1
    assert sensor_state(hass, "last_cost_entry_note").attributes["cost_type"] == "Tyres"


@pytest.mark.parametrize(
    ("entry", "expected"),
    [({"odometer": "84210"}, 84210.0), ({"odometer": 0}, None), ({"odometer": None}, None), ({}, None)],
)
def test_cost_note_odometer(entry, expected):
    assert s._cost_note_odometer(entry) == expected


def test_entries_with_bad_dates_are_skipped():
    data = {
        "cost_types": {"1": "Service"},
        "costs_notes": [
            {"date": "garbage", "costtype": 1, "note": "junk"},
            {"date": "01.01.2026", "costtype": 1, "note": "ok", "cost": "5"},
        ],
    }
    assert s.get_last_cost_note(data)["note"] == "ok"
    assert s.cost_notes_by_type(data) == {"Service": {"date": "2026-01-01", "odometer": None, "note": "ok"}}
    # Falls back to the original cost when there is no converted one
    assert s.cost_note_attributes(data)["cost"] == 5.0


def test_no_entries():
    assert s.get_last_cost_note({"costs_notes": None}) is None
    assert s.cost_note_attributes({}) is None
    assert s.cost_notes_by_type({}) == {}
