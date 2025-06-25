import logging
import asyncio
import aiohttp
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

DOMAIN = "spritmonitor"
_LOGGER = logging.getLogger(__name__)
# MODIFICADO: Ya no necesitamos una constante global para el intervalo
# SCAN_INTERVAL = timedelta(hours=6)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spritmonitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    vehicle_id = entry.data["vehicle_id"]
    app_token = entry.data["app_token"]
    bearer_token = entry.data["bearer_token"]
    # AÑADIDO: Obtenemos el intervalo de actualización desde la configuración
    update_interval_hours = entry.data["update_interval"]

    headers = {
        "Application-Id": app_token,
        "Authorization": bearer_token
    }

    session = async_get_clientsession(hass)

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            # (El resto de esta función no necesita cambios)
            async with session.get(
                "https://api.spritmonitor.de/v1/vehicles.json",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                vehicles = await response.json()
                vehicle_info = next((v for v in vehicles if v["id"] == vehicle_id), None)

                if not vehicle_info:
                    raise UpdateFailed(f"Vehicle with ID {vehicle_id} not found")

            async with session.get(
                f"https://api.spritmonitor.de/v1/vehicle/{vehicle_id}/fuelings.json?limit=5",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                refuelings = await response.json()
                last_refueling = refuelings[0] if refuelings else None
                previous_refueling = refuelings[1] if len(refuelings) > 1 else None

            reminders = None
            try:
                async with session.get(
                    "https://api.spritmonitor.de/v1/reminders.json",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
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
        # MODIFICADO: Usamos el intervalo de actualización dinámico
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
