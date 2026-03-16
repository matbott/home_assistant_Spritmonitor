"""Define services for the Spritmonitor integration."""

from datetime import datetime as dt
import logging
import aiohttp

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import async_get as async_get_device_registry

from .const import (
    DOMAIN,
    SERVICE_ADD_FUELING_SCHEMA,
    SERVICE_ADD_FUELING,
    CONF_VEHICLE_ID,
    CONF_APP_TOKEN,
    CONF_BEARER_TOKEN,
    API_BASE_URL,
)

_LOGGER = logging.getLogger(__name__)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register all Spritmonitor services."""

    async def handle_add_fueling(call: ServiceCall) -> None:
        """Handle the add fueling service call."""
        await _async_add_fueling(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_FUELING,
        handle_add_fueling,
        schema=SERVICE_ADD_FUELING_SCHEMA,
    )
    _LOGGER.info("Spritmonitor services registered.")


async def _async_add_fueling(hass: HomeAssistant, call: ServiceCall) -> None:
    """Add a fueling entry to Spritmonitor."""
    data = dict(call.data)  # Make mutable copy
    _LOGGER.debug("Service call data: %s", data)

    # Handle position
    _validate_position(data)

    # Resolve device and config
    entry = _resolve_config_entry(hass, data["vehicle_device"])
    vehicle_id = entry.data[CONF_VEHICLE_ID]
    _LOGGER.info("Adding fueling for vehicle_id=%s", vehicle_id)

    # Parse date
    data["date"] = _parse_date(data.get("date"))

    # Prepare parameters
    params = _prepare_base_params(data)
    params.update(_prepare_optional_params(data))
    _combine_attributes(data, params)
    _combine_charge_info(data, params)

    # Submit fueling
    await _submit_fueling(hass, entry, vehicle_id, data["tank_id"], params)


def _validate_position(data: dict) -> None:
    lat, lon = data.get("latitude"), data.get("longitude")
    if lat is not None and lon is not None:
        data["position"] = f"{lat},{lon}"
        _LOGGER.debug("Position set: %s", data["position"])
    elif lat is not None or lon is not None:
        raise HomeAssistantError("Both latitude and longitude must be provided together.")
    else:
        data.pop("position", None)
        _LOGGER.debug("No position provided, skipping.")


def _resolve_config_entry(hass: HomeAssistant, device_id: str):
    device_registry = async_get_device_registry(hass)
    device_entry = device_registry.devices.get(device_id)
    if not device_entry:
        raise HomeAssistantError(f"Device {device_id} not found in HA registry")

    entry = next(
        (e for e in hass.config_entries.async_entries(DOMAIN)
         if e.entry_id in device_entry.config_entries),
        None
    )
    if not entry:
        raise HomeAssistantError(f"No Spritmonitor config found for device {device_id}")
    return entry


def _parse_date(value) -> dt:
    if isinstance(value, dt):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
            try:
                parsed_date = dt.strptime(value, fmt)
                _LOGGER.debug("Parsed date: %s using format %s", parsed_date, fmt)
                return parsed_date
            except ValueError:
                continue
    raise HomeAssistantError(f"Invalid date format: {value}.")


def _prepare_base_params(data: dict) -> dict:
    return {
        "date": data["date"].strftime("%d.%m.%Y"),
        "trip": data["trip"],
        "quantity": data["quantity"],
        "type": data["type"],
        "fuelsortid": data["fuelsort_id"],
        "quantityunitid": data["quantity_unit_id"],
    }


def _prepare_optional_params(data: dict) -> dict:
    """Prepare optional parameters for the API call."""
    mapping = {
        "odometer": "odometer",
        "price": "price",
        "currency_id": "currencyid",
        "pricetype": "pricetype",
        "note": "note",
        "stationname": "stationname",
        "location": "location",
        "country": "country",
        "bc_consumption": "bc_consumption",
        "bc_quantity": "bc_quantity",
        "bc_speed": "bc_speed",
        "percentage": "percent",
        "charging_power": "charging_power",
        "charging_duration": "charging_duration",
        "streets": "streets",
        "position": "position",
    }

    params = {}
    for key, api_name in mapping.items():
        value = data.get(key)
        if value is None:
            continue

        if key == "streets":
            if isinstance(value, list):
                value = ",".join(value)
            elif not isinstance(value, str):
                value = None

        if value is not None:
            params[api_name] = value
            _LOGGER.debug("Optional param: %s -> %s = %s", key, api_name, value)
    return params


def _combine_attributes(data: dict, params: dict) -> None:
    attributes = []
    if data.get("attributes_tires"):
        attributes.append(data["attributes_tires"])
    if data.get("attributes_driving_style"):
        attributes.append(data["attributes_driving_style"])
    for attr in ("ac", "heating", "trailer"):
        if data.get(f"attributes_{attr}"):
            attributes.append(attr)
    if attributes:
        params["attributes"] = ",".join(attributes)
        _LOGGER.debug("Combined attributes: %s", params["attributes"])


def _combine_charge_info(data: dict, params: dict) -> None:
    info = []
    if data.get("charge_info_ac_dc"):
        info.append(data["charge_info_ac_dc"])
    if data.get("charge_info_source"):
        info.append(data["charge_info_source"])
    if info:
        params["charge_info"] = ",".join(info)
        _LOGGER.debug("Combined charge_info: %s", params["charge_info"])


async def _submit_fueling(hass: HomeAssistant, entry, vehicle_id: str, tank_id: str, params: dict) -> None:
    url = f"{API_BASE_URL}/vehicle/{vehicle_id}/tank/{tank_id}/fueling.json"
    headers = {
        "Accept": "application/json",
        "Application-Id": entry.data[CONF_APP_TOKEN],
        "Authorization": entry.data[CONF_BEARER_TOKEN],
    }
    session = async_get_clientsession(hass)
    _LOGGER.info("Submitting fueling to Spritmonitor: %s", params)

    try:
        async with session.post(url, data=params, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            resp_text = await response.text()
            _LOGGER.debug("Response status: %s, text: %s", response.status, resp_text)
            try:
                resp_json = await response.json()
            except Exception:
                resp_json = {"raw_response": resp_text}

            if response.status != 200:
                error_msg = resp_json.get("errors", resp_json.get("message", resp_text))
                raise HomeAssistantError(f"API Error ({response.status}): {error_msg}")
            if resp_json.get("errors"):
                raise HomeAssistantError(f"API Errors: {resp_json['errors']}")

            _LOGGER.info("Fueling successfully added for vehicle %s (tank %s)", vehicle_id, tank_id)

            coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
            if coordinator:
                _LOGGER.debug("Refreshing data coordinator for vehicle %s", vehicle_id)
                await coordinator.async_request_refresh()

    except aiohttp.ClientError as err:
        raise HomeAssistantError(f"Connection error: {err}") from err
