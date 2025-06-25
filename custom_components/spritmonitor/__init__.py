import logging
import aiohttp
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    API_VEHICLES_URL,
    API_REMINDERS_URL,
    API_FUELINGS_URL_TPL,
    CONF_VEHICLE_ID,
    CONF_APP_TOKEN,
    CONF_BEARER_TOKEN,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spritmonitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    vehicle_id = entry.data[CONF_VEHICLE_ID]
    app_token = entry.data[CONF_APP_TOKEN]
    bearer_token = entry.data[CONF_BEARER_TOKEN]
    
    update_interval_hours = entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

    headers = {
        "Application-Id": app_token,
        "Authorization": bearer_token
    }

    session = async_get_clientsession(hass)

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            async with session.get(API_VEHICLES_URL, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                vehicles = await response.json()
                vehicle_info = next((v for v in vehicles if v["id"] == vehicle_id), None)
                if not vehicle_info:
                    raise UpdateFailed(f"Vehicle with ID {vehicle_id} not found")

            fuelings_url = API_FUELINGS_URL_TPL.format(vehicle_id=vehicle_id)
            async with session.get(f"{fuelings_url}?limit=5", headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                response.raise_for_status()
                refuelings = await response.json()
                last_refueling = refuelings[0] if refuelings else None
                previous_refueling = refuelings[1] if len(refuelings) > 1 else None

            reminders = None
            try:
                async with session.get(API_REMINDERS_URL, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        all_reminders = await response.json()
                        reminders = [r for r in all_reminders if r.get('vehicle') == vehicle_id]
            except Exception as e:
                _LOGGER.debug("Could not fetch reminders: %s", e)

            return {
                "vehicle": vehicle_info,
                "last_refueling": last_refueling,
                "previous_refueling": previous_refueling,
                "refuelings": refuelings,
                "reminders": reminders,
            }
        except aiohttp.ClientError as e:
            raise UpdateFailed(f"Connection error with Spritmonitor: {e}")
        except Exception as e:
            raise UpdateFailed(f"Error fetching data from Spritmonitor: {e}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="spritmonitor_coordinator",
        update_method=async_update_data,
        update_interval=timedelta(hours=update_interval_hours),
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
