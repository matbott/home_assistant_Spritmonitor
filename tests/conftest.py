"""Shared fixtures for the Spritmonitor tests.

The Spritmonitor API is never called for real: every test registers the responses it needs with
Home Assistant's aioclient_mock. The sample data follows the schemas in the Spritmonitor OpenAPI
description (https://api.spritmonitor.de/doc).
"""
import copy

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.spritmonitor.const import (
    API_FUELINGS_URL_TPL,
    API_REMINDERS_URL,
    API_VEHICLES_URL,
    CONF_APP_TOKEN,
    CONF_BEARER_TOKEN,
    CONF_CURRENCY,
    CONF_UPDATE_INTERVAL,
    CONF_VEHICLE_ID,
    CONF_VEHICLE_TYPE,
    DOMAIN,
    VEHICLE_TYPE_COMBUSTION,
)

pytest_plugins = "pytest_homeassistant_custom_component"

VEHICLE_ID = 100001

VEHICLE = {
    "id": VEHICLE_ID,
    "make": "VW",
    "model": "Golf",
    "consumption": 5.8,
    "consumptionunit": "l/100km",
    "tripsum": 23003.3,
    "tripunit": "km",
    "quantitysum": 5083.9,
    "maintank": 1,
    "maintanktype": 2,
    "sign": "PA SM000",
    "capacity": 50,
}

# Newest first is not guaranteed by the coordinator's input - it sorts by date itself.
FUELINGS = [
    {"id": 3, "type": "full", "date": "10.03.2026", "odometer": 1300, "trip": 400, "quantity": 30,
     "cost": 60.0, "cost_converted": 60.0, "consumption": 7.5, "tankid": 1},
    {"id": 1, "type": "full", "date": "10.01.2026", "odometer": 500, "trip": 500, "quantity": 35,
     "cost": 70.0, "cost_converted": 70.0, "consumption": 7.0, "tankid": 1},
    {"id": 2, "type": "full", "date": "10.02.2026", "odometer": 900, "trip": 400, "quantity": 28,
     "cost": 50.0, "cost_converted": 50.0, "consumption": 7.0, "tankid": 1},
]

REMINDERS = [
    {"id": 1, "vehicle": VEHICLE_ID, "completed": 0, "next_odometer": 15000, "nextdate": "01.06.2026", "note": "Oil change"},
    {"id": 2, "vehicle": 999, "completed": 0, "next_odometer": 100, "note": "Other vehicle"},
]

ENTRY_DATA = {
    CONF_VEHICLE_ID: VEHICLE_ID,
    CONF_APP_TOKEN: "app-token",
    CONF_BEARER_TOKEN: "Bearer secret",
    CONF_VEHICLE_TYPE: VEHICLE_TYPE_COMBUSTION,
    CONF_CURRENCY: "EUR",
    CONF_UPDATE_INTERVAL: 6,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Let Home Assistant load the integration from custom_components."""
    yield


def mock_api(aioclient_mock, vehicles=None, fuelings=None, reminders=None, extra=None):
    """Register Spritmonitor API responses. `extra` maps further URLs to their JSON response."""
    aioclient_mock.get(API_VEHICLES_URL, json=copy.deepcopy(vehicles if vehicles is not None else [VEHICLE]))
    aioclient_mock.get(
        API_FUELINGS_URL_TPL.format(vehicle_id=VEHICLE_ID),
        json=copy.deepcopy(fuelings if fuelings is not None else FUELINGS),
    )
    aioclient_mock.get(API_REMINDERS_URL, json=copy.deepcopy(reminders if reminders is not None else REMINDERS))
    for url, payload in (extra or {}).items():
        aioclient_mock.get(url, json=copy.deepcopy(payload))


def make_entry(**overrides):
    """A config entry for the sample vehicle."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="VW Golf",
        unique_id=f"spritmonitor_{VEHICLE_ID}",
        data={**ENTRY_DATA, **overrides},
    )


async def setup_entry(hass, entry):
    """Add the entry and set it up, returning whether setup succeeded."""
    entry.add_to_hass(hass)
    result = await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return result


def sensor_state(hass, sensor_id):
    """State of one of the integration's sensors, looked up by its unique id."""
    from homeassistant.helpers import entity_registry as er

    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"spritmonitor_{VEHICLE_ID}_{sensor_id}"
    )
    assert entity_id, f"sensor {sensor_id} was not created"
    return hass.states.get(entity_id)
