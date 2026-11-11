"""Tests for the lifetime cost per distance calculation (issue #29)."""
import pytest

from custom_components.spritmonitor import sensor as s
from custom_components.spritmonitor.const import API_TANKS_URL_TPL, DOMAIN

from .conftest import VEHICLE, VEHICLE_ID, make_entry, mock_api, sensor_state, setup_entry

TANKS_URL = API_TANKS_URL_TPL.format(vehicle_id=VEHICLE_ID)

# The example tank from the Spritmonitor API description: 7362.98 spent over 50274.98 km
PETROL = {"id": 1, "fuelsorttype": 2, "quantityunittype": 1, "costsum": 7362.98, "costsumunit": "EUR",
          "costtripsum": 50274.98, "tripsum": 54027.3}
ELECTRIC = {"id": 2, "fuelsorttype": 5, "quantityunittype": 3, "costsum": 640.10, "costsumunit": "EUR",
            "costtripsum": 9100.0, "tripsum": 9100.0}
ADBLUE = {"id": 3, "fuelsorttype": 6, "quantityunittype": 1, "costsum": 80.0, "costsumunit": "EUR",
          "costtripsum": 50000.0, "tripsum": 50000.0}


async def test_combustion_uses_lifetime_tank_totals(hass, aioclient_mock):
    mock_api(aioclient_mock, extra={TANKS_URL: [PETROL, ADBLUE]})
    assert await setup_entry(hass, make_entry())
    assert sensor_state(hass, "cost_per_100_distance").state == "14.65"
    assert sensor_state(hass, "cost_per_distance").state == "0.1465"
    assert sensor_state(hass, "cost_per_100_distance").attributes["unit_of_measurement"] == "EUR/100km"


async def test_phev_uses_each_tank(hass, aioclient_mock):
    mock_api(aioclient_mock, extra={TANKS_URL: [ADBLUE, ELECTRIC, PETROL]})
    assert await setup_entry(hass, make_entry(vehicle_type="phev"))
    assert sensor_state(hass, "cost_per_100_distance_fuel").state == "14.65"
    assert sensor_state(hass, "cost_per_100_distance_electric").state == "7.03"


async def test_electric_vehicle_uses_its_main_tank(hass, aioclient_mock):
    ev = {**VEHICLE, "maintank": 2, "consumptionunit": "kWh/100km", "consumption": 16.0}
    mock_api(aioclient_mock, vehicles=[ev], extra={TANKS_URL: [ELECTRIC]})
    assert await setup_entry(hass, make_entry(vehicle_type="electric"))
    assert sensor_state(hass, "cost_per_100_distance").state == "7.03"


async def test_falls_back_to_recent_fuelings_without_tanks(hass, aioclient_mock):
    mock_api(aioclient_mock)
    aioclient_mock.get(TANKS_URL, status=500)
    entry = make_entry()
    assert await setup_entry(hass, entry)
    assert hass.data[DOMAIN][entry.entry_id].data["tanks"] is None
    # 180 EUR over the 1300 km of the sample fuelings
    assert sensor_state(hass, "cost_per_100_distance").state == "13.85"


async def test_falls_back_when_tank_has_no_costs(hass, aioclient_mock):
    mock_api(aioclient_mock, extra={TANKS_URL: [{**PETROL, "costsum": 0, "costtripsum": 0}]})
    assert await setup_entry(hass, make_entry())
    assert sensor_state(hass, "cost_per_100_distance").state == "13.85"


def test_get_tank():
    data = {"vehicle": {"maintank": 1}, "tanks": [ADBLUE, ELECTRIC, PETROL]}
    assert s.get_tank(data, "main")["id"] == 1
    assert s.get_tank(data, "fuel")["id"] == 1  # AdBlue is never taken as the fuel tank
    assert s.get_tank(data, "electric")["id"] == 2
    assert s.get_tank({"vehicle": {"maintank": "2"}, "tanks": [PETROL, ELECTRIC]}, "main")["id"] == 2
    assert s.get_tank({"vehicle": {}, "tanks": [PETROL]}, "main") is None
    assert s.get_tank({"tanks": None}, "fuel") is None
    assert s.get_tank({"tanks": [PETROL]}, "electric") is None


@pytest.mark.parametrize(("per_distance", "expected"), [(1, 0.1465), (100, 14.65)])
def test_lifetime_rounding(per_distance, expected):
    assert s.calculate_cost_per_distance([], per_distance, tank=PETROL) == expected


def test_fallback_uses_converted_cost():
    # An entry made abroad: 100 in the local currency, 90 in the user's currency
    fuelings = [{"cost": 100, "cost_converted": 90, "trip": 600}, {"cost": 60, "trip": 400}]
    assert s.calculate_cost_per_distance(fuelings, 100) == 15.0
    assert s.calculate_cost_per_distance(fuelings, 1, tank={"costsum": "bad"}) == 0.15
    assert s.calculate_cost_per_distance(fuelings[:1], 100) is None
    assert s.calculate_cost_per_distance([{"cost": 10, "trip": 0}, {"cost": 10, "trip": 0}]) is None
