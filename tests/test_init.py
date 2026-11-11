"""Tests for setting up and unloading the integration (the data coordinator)."""
from homeassistant.config_entries import ConfigEntryState

from custom_components.spritmonitor.const import API_FUELINGS_URL_TPL, API_REMINDERS_URL, API_VEHICLES_URL, DOMAIN

from .conftest import VEHICLE, VEHICLE_ID, make_entry, mock_api, sensor_state, setup_entry


async def test_setup_and_unload(hass, aioclient_mock):
    mock_api(aioclient_mock)
    entry = make_entry()
    assert await setup_entry(hass, entry)
    assert entry.state is ConfigEntryState.LOADED

    coordinator = hass.data[DOMAIN][entry.entry_id]
    # Fuelings are sorted newest first, whatever order the API returns them in
    assert [f["id"] for f in coordinator.data["refuelings"]] == [3, 2, 1]
    assert coordinator.data["last_refueling"]["id"] == 3
    # Only the reminders of this vehicle are kept
    assert [r["id"] for r in coordinator.data["reminders"]] == [1]
    assert coordinator.data["units"] == {"trip": "km", "quantity": "L", "consumption": "L/100km"}

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_vehicle_not_found_retries_setup(hass, aioclient_mock):
    mock_api(aioclient_mock, vehicles=[{**VEHICLE, "id": 42}])
    entry = make_entry()
    await setup_entry(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_api_error_retries_setup(hass, aioclient_mock):
    aioclient_mock.get(API_VEHICLES_URL, status=500)
    entry = make_entry()
    await setup_entry(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_failed_fuelings_request_retries_setup(hass, aioclient_mock):
    aioclient_mock.get(API_VEHICLES_URL, json=[VEHICLE])
    aioclient_mock.get(API_FUELINGS_URL_TPL.format(vehicle_id=VEHICLE_ID), status=401)
    entry = make_entry()
    await setup_entry(hass, entry)
    assert entry.state is ConfigEntryState.SETUP_RETRY


async def test_reminders_are_optional(hass, aioclient_mock):
    aioclient_mock.get(API_VEHICLES_URL, json=[VEHICLE])
    aioclient_mock.get(API_FUELINGS_URL_TPL.format(vehicle_id=VEHICLE_ID), json=[])
    aioclient_mock.get(API_REMINDERS_URL, status=500)
    entry = make_entry()
    assert await setup_entry(hass, entry)
    assert entry.state is ConfigEntryState.LOADED
    assert hass.data[DOMAIN][entry.entry_id].data["reminders"] is None
    assert sensor_state(hass, "next_service_note").state == "unknown"


async def test_electric_vehicle_uses_all_fuelings_as_charges(hass, aioclient_mock):
    ev = {**VEHICLE, "consumptionunit": "kWh/100km", "consumption": 16.0, "capacity": 64}
    charges = [
        {"id": 1, "date": "01.01.2026", "trip": 300, "quantity": 50, "cost": 15, "tankid": 1},
        {"id": 2, "date": "01.02.2026", "trip": 320, "quantity": 52, "cost": 16, "tankid": 1},
    ]
    mock_api(aioclient_mock, vehicles=[ev], fuelings=charges)
    entry = make_entry(vehicle_type="electric")
    assert await setup_entry(hass, entry)
    data = hass.data[DOMAIN][entry.entry_id].data
    assert [c["id"] for c in data["electric_charges"]] == [2, 1]
    assert data["refuelings"] is data["electric_charges"]
    assert data["gas_refuelings"] == []
    assert data["units"]["quantity"] == "kWh"


async def test_phev_splits_fuelings_by_tank(hass, aioclient_mock):
    fuelings = [
        {"id": 1, "date": "01.01.2026", "trip": 500, "quantity": 30, "cost": 60, "tankid": 1},
        {"id": 2, "date": "02.01.2026", "trip": 40, "quantity": 10, "cost": 3, "tankid": 2},
    ]
    mock_api(aioclient_mock, fuelings=fuelings)
    entry = make_entry(vehicle_type="phev")
    assert await setup_entry(hass, entry)
    data = hass.data[DOMAIN][entry.entry_id].data
    assert [f["id"] for f in data["gas_refuelings"]] == [1]
    assert [f["id"] for f in data["electric_charges"]] == [2]
    assert data["last_electric_charge"]["id"] == 2
