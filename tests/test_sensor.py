"""Tests for the sensors created for each vehicle type."""
from homeassistant.helpers import entity_registry as er

from custom_components.spritmonitor.const import DOMAIN

from .conftest import VEHICLE, make_entry, mock_api, sensor_state, setup_entry


def created_sensor_ids(hass, entry):
    prefix = "spritmonitor_100001_"
    return {
        e.unique_id.removeprefix(prefix)
        for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    }


async def test_combustion_sensors(hass, aioclient_mock):
    mock_api(aioclient_mock)
    entry = make_entry()
    assert await setup_entry(hass, entry)

    def value(sensor_id):
        return sensor_state(hass, sensor_id).state

    def unit(sensor_id):
        return sensor_state(hass, sensor_id).attributes.get("unit_of_measurement")

    assert value("brand_model") == "VW Golf"
    assert value("license_plate") == "PA SM000"
    assert value("total_distance") == "23003.3" and unit("total_distance") == "km"
    assert value("last_refuel_date") == "10.03.2026"
    assert value("last_refuel_cost") == "60.0" and unit("last_refuel_cost") == "EUR"
    assert value("avg_consumption") == "5.8" and unit("avg_consumption") == "L/100km"
    assert value("last_refuel_price_per_liter") == "2.0" and unit("last_refuel_price_per_liter") == "EUR/L"
    assert value("range_estimate") == "517"
    assert value("next_service_km") == "15000"
    assert value("km_to_next_service") == "13700.0"
    assert value("next_service_note") == "Oil change"
    assert value("next_service_date") == "2026-06-01"
    assert value("avg_days_between_refuels") == "29.5" and unit("avg_days_between_refuels") == "days"
    assert value("eco_driving_index") == "5.4" and unit("eco_driving_index") == "/10"

    # Cost per distance: 180 EUR over 1300 km (PR #30 keeps the original rolling calculation)
    assert unit("cost_per_distance") == "EUR/km"
    assert value("cost_per_100_distance") == "13.85" and unit("cost_per_100_distance") == "EUR/100km"

    assert sensor_state(hass, "brand_model").attributes["entity_picture"].endswith("/100001.jpg")
    # Data the API does not provide leaves the sensor unknown instead of failing
    assert value("ranking_position") == "unknown"

    ids = created_sensor_ids(hass, entry)
    assert {"fuel_capacity", "range_estimate", "cost_per_distance"} <= ids
    assert not ids & {"battery_capacity", "cost_per_distance_fuel", "cost_per_distance_electric"}


async def test_cost_sensors_use_trip_unit(hass, aioclient_mock):
    mock_api(aioclient_mock, vehicles=[{**VEHICLE, "tripunit": "mi"}])
    assert await setup_entry(hass, make_entry(currency="GBP"))
    assert sensor_state(hass, "cost_per_distance").attributes["unit_of_measurement"] == "GBP/mi"
    assert sensor_state(hass, "cost_per_100_distance").attributes["unit_of_measurement"] == "GBP/100mi"


async def test_electric_sensors(hass, aioclient_mock):
    ev = {**VEHICLE, "consumptionunit": "kWh/100km", "consumption": 16.0, "capacity": 64}
    charges = [
        {"id": 1, "date": "01.01.2026", "trip": 300, "quantity": 50, "cost": 15, "consumption": 16.6, "tankid": 1},
        {"id": 2, "date": "01.02.2026", "trip": 320, "quantity": 52, "cost": 16, "consumption": 16.2, "tankid": 1},
    ]
    mock_api(aioclient_mock, vehicles=[ev], fuelings=charges)
    entry = make_entry(vehicle_type="electric")
    assert await setup_entry(hass, entry)

    assert sensor_state(hass, "battery_capacity").state == "64.0"
    assert sensor_state(hass, "full_battery_range_estimate").state == "400"
    assert sensor_state(hass, "efficiency_per_distance").state == "6.25"
    assert sensor_state(hass, "efficiency_per_distance").attributes["unit_of_measurement"] == "km/kWh"
    assert sensor_state(hass, "avg_energy_consumption").attributes["unit_of_measurement"] == "kWh/100km"
    assert sensor_state(hass, "last_charge_price_per_kwh").state == "0.308"
    assert sensor_state(hass, "cost_per_100_distance").state == "5.0"

    ids = created_sensor_ids(hass, entry)
    assert not ids & {"fuel_capacity", "range_estimate"}


async def test_phev_creates_sensors_per_tank(hass, aioclient_mock):
    fuelings = [
        {"id": 1, "date": "01.01.2026", "trip": 500, "quantity": 30, "cost": 60, "tankid": 1},
        {"id": 2, "date": "01.02.2026", "trip": 500, "quantity": 30, "cost": 50, "tankid": 1},
        {"id": 3, "date": "02.01.2026", "trip": 40, "quantity": 10, "cost": 3, "tankid": 2},
        {"id": 4, "date": "02.02.2026", "trip": 60, "quantity": 12, "cost": 4, "tankid": 2},
    ]
    mock_api(aioclient_mock, fuelings=fuelings)
    entry = make_entry(vehicle_type="phev")
    assert await setup_entry(hass, entry)

    ids = created_sensor_ids(hass, entry)
    assert {"fuel_capacity", "battery_capacity", "cost_per_100_distance_fuel", "cost_per_100_distance_electric"} <= ids
    assert "cost_per_distance" not in ids
    assert sensor_state(hass, "cost_per_100_distance_fuel").state == "11.0"
    assert sensor_state(hass, "cost_per_100_distance_electric").state == "7.0"


async def test_sensors_unavailable_after_failed_update(hass, aioclient_mock):
    mock_api(aioclient_mock)
    entry = make_entry()
    assert await setup_entry(hass, entry)
    assert sensor_state(hass, "total_distance").state == "23003.3"

    aioclient_mock.clear_requests()
    aioclient_mock.get("https://api.spritmonitor.de/v1/vehicles.json", status=500)
    await hass.data[DOMAIN][entry.entry_id].async_refresh()
    await hass.async_block_till_done()
    assert sensor_state(hass, "total_distance").state == "unavailable"
