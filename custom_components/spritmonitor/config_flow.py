from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol
import aiohttp
import logging

DOMAIN = "spritmonitor"
_LOGGER = logging.getLogger(__name__)

# Valor predeterminado para el token de la aplicación
DEFAULT_APP_TOKEN = "095369dede84c55797c22d4854ca6efe"

class SpritmonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Spritmonitor."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                # Obtenemos la información del vehículo para validarla y obtener el nombre
                vehicle_info = await self._get_vehicle_info(
                    user_input["vehicle_id"],
                    user_input["app_token"],
                    user_input["bearer_token"]
                )

                if vehicle_info:
                    # MODIFICADO: Creamos un título descriptivo con la marca y el modelo
                    make = vehicle_info.get("make", "")
                    model = vehicle_info.get("model", "")
                    title = f"{make} {model}".strip() if make and model else f"Spritmonitor Vehicle {user_input['vehicle_id']}"
                    
                    # Guardamos el ID único para evitar duplicados
                    await self.async_set_unique_id(f"spritmonitor_{user_input['vehicle_id']}")
                    self._abort_if_unique_id_configured()

                    # Creamos la entrada de configuración con los datos y el nuevo título
                    return self.async_create_entry(title=title, data=user_input)
                else:
                    errors["base"] = "invalid_auth"
            except Exception as e:
                _LOGGER.error("Error during configuration: %s", e)
                errors["base"] = "cannot_connect"

        # MODIFICADO: Mostramos el formulario con los nuevos valores predeterminados y el campo de intervalo
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("vehicle_id"): int,
                # MODIFICADO: Token con valor predeterminado
                vol.Required("app_token", default=DEFAULT_APP_TOKEN): str,
                vol.Required("bearer_token"): str,
                # AÑADIDO: Campo para el intervalo de actualización en horas
                vol.Required("update_interval", default=6): vol.All(vol.Coerce(int), vol.Range(min=1, max=24))
            }),
            errors=errors,
            description_placeholders={
                "vehicle_id": "Spritmonitor Vehicle ID",
                "app_token": "Spritmonitor Application Token",
                "bearer_token": "Authorization Bearer Token",
                "update_interval": "Update interval in hours"
            }
        )

    async def _get_vehicle_info(self, vehicle_id: int, app_token: str, bearer_token: str) -> dict | None:
        """
        MODIFICADO: Test credentials and get vehicle info.
        Devuelve el diccionario del vehículo si es exitoso, sino None.
        """
        try:
            session = async_get_clientsession(self.hass)
            headers = {
                "Application-Id": app_token,
                "Authorization": bearer_token
            }

            async with session.get(
                "https://api.spritmonitor.de/v1/vehicles.json",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    vehicles = await response.json()
                    # Buscamos el vehículo y lo devolvemos si existe
                    vehicle = next((v for v in vehicles if v["id"] == vehicle_id), None)
                    return vehicle
                else:
                    return None
        except Exception as e:
            _LOGGER.error("Error testing credentials: %s", e)
            return None
