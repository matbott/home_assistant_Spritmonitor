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
SCAN_INTERVAL = timedelta(hours=6)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Spritmonitor from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    vehicle_id = entry.data["vehicle_id"]
    bearer_token = entry.data["bearer_token"]

    headers = {
        "Application-Id": "095369dede84c55797c22d4854ca6efe",
        "Authorization": bearer_token
    }

    # Usar la sesión de Home Assistant en lugar de crear una nueva
    session = async_get_clientsession(hass)

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            # Obtener información del vehículo
            async with session.get(
                "https://api.spritmonitor.de/v1/vehicles.json", 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                vehicles = await response.json()
                vehicle_info = next((v for v in vehicles if v["id"] == vehicle_id), None)
                
                if not vehicle_info:
                    raise UpdateFailed(f"Vehículo con ID {vehicle_id} no encontrado")

            # Obtener últimos 5 repostajes
            async with session.get(
                f"https://api.spritmonitor.de/v1/vehicle/{vehicle_id}/fuelings.json?limit=5", 
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                response.raise_for_status()
                refuelings = await response.json()
                last_refueling = refuelings[0] if refuelings else None
                previous_refueling = refuelings[1] if len(refuelings) > 1 else None

            # Obtener recordatorios/mantenimientos
            reminders = None
            try:
                async with session.get(
                    "https://api.spritmonitor.de/v1/reminders.json", 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        all_reminders = await response.json()
                        # Filtrar solo los recordatorios de este vehículo
                        reminders = [r for r in all_reminders if r.get('vehicle') == vehicle_id]
            except Exception as e:
                _LOGGER.debug("No se pudieron obtener recordatorios: %s", e)

            return {
                "vehicle": vehicle_info,
                "last_refueling": last_refueling,
                "previous_refueling": previous_refueling,
                "refuelings": refuelings,  # Lista completa de repostajes
                "reminders": reminders,
            }
        except aiohttp.ClientError as e:
            raise UpdateFailed(f"Error de conexión con Spritmonitor: {e}")
        except Exception as e:
            raise UpdateFailed(f"Error al obtener datos de Spritmonitor: {e}")

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="spritmonitor_coordinator",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Cargar la plataforma sensor
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
