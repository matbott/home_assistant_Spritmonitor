"""Tests for the spritmonitor.add_fueling action."""
import aiohttp
import pytest
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from custom_components.spritmonitor.const import API_BASE_URL, DOMAIN, SERVICE_ADD_FUELING

from .conftest import VEHICLE_ID, make_entry, mock_api, setup_entry

FUELING_URL = f"{API_BASE_URL}/vehicle/{VEHICLE_ID}/tank/1/fueling.json"


@pytest.fixture
async def device_id(hass, aioclient_mock):
    mock_api(aioclient_mock)
    assert await setup_entry(hass, make_entry())
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, str(VEHICLE_ID))})
    assert device
    return device.id


def service_data(device_id, **extra):
    return {
        "vehicle_device": device_id,
        "tank_id": 1,
        "date": "2026-03-10 08:00:00",
        "trip": 412.5,
        "quantity": 31.2,
        "type": "full",
        "fuelsort_id": 7,
        "quantity_unit_id": 1,
        **extra,
    }


def posted(aioclient_mock):
    calls = [c for c in aioclient_mock.mock_calls if c[0] == "POST"]
    assert len(calls) == 1
    return calls[0][2]


async def test_add_fueling_posts_entry(hass, aioclient_mock, device_id):
    aioclient_mock.post(FUELING_URL, json={"errors": 0})
    await hass.services.async_call(
        DOMAIN,
        SERVICE_ADD_FUELING,
        service_data(
            device_id,
            price=63.4,
            latitude=51.14,
            longitude=0.87,
            streets=["city", "land"],
            attributes_tires="wintertires",
            attributes_ac=True,
            charge_info_ac_dc="ac",
            charge_info_source="source_wallbox",
            note=None,
        ),
        blocking=True,
    )
    params = posted(aioclient_mock)
    assert params["date"] == "10.03.2026"
    assert params["trip"] == 412.5
    assert params["fuelsortid"] == 7
    assert params["quantityunitid"] == 1
    assert params["price"] == 63.4
    assert params["position"] == "51.14,0.87"
    assert params["streets"] == "city,land"
    assert params["attributes"] == "wintertires,ac"
    assert params["charge_info"] == "ac,source_wallbox"
    assert "note" not in params


async def test_add_fueling_without_position(hass, aioclient_mock, device_id):
    aioclient_mock.post(FUELING_URL, json={"errors": 0})
    await hass.services.async_call(DOMAIN, SERVICE_ADD_FUELING, service_data(device_id), blocking=True)
    assert "position" not in posted(aioclient_mock)


async def test_latitude_without_longitude_is_rejected(hass, device_id):
    with pytest.raises(HomeAssistantError, match="latitude and longitude"):
        await hass.services.async_call(
            DOMAIN, SERVICE_ADD_FUELING, service_data(device_id, latitude=51.1), blocking=True
        )


async def test_rejected_entry_raises(hass, aioclient_mock, device_id):
    # Spritmonitor answers 200 even when it rejects an entry - the body carries the errors
    aioclient_mock.post(
        FUELING_URL, json={"errors": 1, "errormessages": {"quantity": {"isEmpty": "Value is required"}}}
    )
    with pytest.raises(HomeAssistantError, match="API Errors"):
        await hass.services.async_call(DOMAIN, SERVICE_ADD_FUELING, service_data(device_id), blocking=True)


async def test_http_error_raises(hass, aioclient_mock, device_id):
    aioclient_mock.post(FUELING_URL, status=500, json={"message": "boom"})
    with pytest.raises(HomeAssistantError, match="500"):
        await hass.services.async_call(DOMAIN, SERVICE_ADD_FUELING, service_data(device_id), blocking=True)


async def test_driving_style_attribute(hass, aioclient_mock, device_id):
    aioclient_mock.post(FUELING_URL, json={"errors": 0})
    await hass.services.async_call(
        DOMAIN, SERVICE_ADD_FUELING,
        service_data(device_id, attributes_driving_style="normal", attributes_heating=True), blocking=True,
    )
    assert posted(aioclient_mock)["attributes"] == "normal,heating"


async def test_non_json_error_response_raises(hass, aioclient_mock, device_id):
    aioclient_mock.post(FUELING_URL, status=502, text="Bad Gateway")
    with pytest.raises(HomeAssistantError, match="502"):
        await hass.services.async_call(DOMAIN, SERVICE_ADD_FUELING, service_data(device_id), blocking=True)


async def test_connection_error_raises(hass, aioclient_mock, device_id):
    aioclient_mock.post(FUELING_URL, exc=aiohttp.ClientError("down"))
    with pytest.raises(HomeAssistantError, match="Connection error"):
        await hass.services.async_call(DOMAIN, SERVICE_ADD_FUELING, service_data(device_id), blocking=True)


async def test_unknown_device_raises(hass, device_id):
    with pytest.raises(HomeAssistantError, match="not found"):
        await hass.services.async_call(DOMAIN, SERVICE_ADD_FUELING, service_data("nope"), blocking=True)
