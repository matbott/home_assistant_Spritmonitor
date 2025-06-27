from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol
import aiohttp
import logging
from .const import (
    DOMAIN,
    DEFAULT_APP_TOKEN,
    DEFAULT_UPDATE_INTERVAL,
    API_VEHICLES_URL,
    CONF_VEHICLE_ID,
    CONF_APP_TOKEN,
    CONF_BEARER_TOKEN,
    CONF_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

class SpritmonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Spritmonitor."""
    
    VERSION = 1
    _attr_translation_domain = DOMAIN

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                # Se utiliza el session de hass para las pruebas
                session = async_get_clientsession(self.hass)
                vehicle_info = await self._get_vehicle_info(
                    session,
                    user_input[CONF_VEHICLE_ID],
                    user_input[CONF_APP_TOKEN],
                    user_input[CONF_BEARER_TOKEN]
                )
                if vehicle_info:
                    make = vehicle_info.get("make", "")
                    model = vehicle_info.get("model", "")
                    title = f"{make} {model}".strip() if make and model else f"Spritmonitor Vehicle {user_input[CONF_VEHICLE_ID]}"
                    
                    await self.async_set_unique_id(f"spritmonitor_{user_input[CONF_VEHICLE_ID]}")
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(title=title, data=user_input)
                else:
                    errors["base"] = "invalid_auth"
            except aiohttp.ClientError:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.error("Error during configuration: %s", e)
                errors["base"] = "cannot_connect"

        # El data_schema ahora es mucho más limpio.
        # Home Assistant usará strings.json para obtener los títulos y descripciones.
        data_schema = vol.Schema({
            vol.Required(CONF_VEHICLE_ID): int,
            vol.Required(CONF_APP_TOKEN, default=DEFAULT_APP_TOKEN): str,
            vol.Required(CONF_BEARER_TOKEN): str,
            vol.Required(CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=24)
            )
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )

    async def _get_vehicle_info(self, session: aiohttp.ClientSession, vehicle_id: int, app_token: str, bearer_token: str) -> dict | None:
        """Test credentials and get vehicle info."""
        # La función ahora recibe la sesión aiohttp
        headers = {
            "Application-Id": app_token,
            "Authorization": bearer_token
        }
        async with session.get(API_VEHICLES_URL, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
            response.raise_for_status() # Lanza una excepción para errores HTTP
            vehicles = await response.json()
            return next((v for v in vehicles if v["id"] == vehicle_id), None)