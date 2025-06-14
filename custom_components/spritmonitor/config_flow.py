from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol
import aiohttp
import logging

DOMAIN = "spritmonitor"
_LOGGER = logging.getLogger(__name__)

class SpritmonitorConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Spritmonitor."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            # Validar las credenciales
            try:
                vehicle_id = user_input["vehicle_id"]
                app_token = user_input["app_token"]
                bearer_token = user_input["bearer_token"]
                
                # Probar la conexión
                is_valid = await self._test_credentials(
                    vehicle_id, app_token, bearer_token
                )
                
                if is_valid:
                    # Crear un título más descriptivo
                    title = f"Spritmonitor - Vehículo {vehicle_id}"
                    
                    # Verificar si ya existe una entrada para este vehículo
                    await self.async_set_unique_id(f"spritmonitor_{vehicle_id}")
                    self._abort_if_unique_id_configured()
                    
                    return self.async_create_entry(title=title, data=user_input)
                else:
                    errors["base"] = "invalid_auth"
            except Exception as e:
                _LOGGER.error("Error durante la configuración: %s", e)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("vehicle_id"): int,
                vol.Required("app_token"): str,
                vol.Required("bearer_token"): str
            }),
            errors=errors,
            description_placeholders={
                "vehicle_id": "ID del vehículo en Spritmonitor",
                "app_token": "Token de aplicación de Spritmonitor",
                "bearer_token": "Token Bearer de autorización"
            }
        )

    async def _test_credentials(self, vehicle_id: int, app_token: str, bearer_token: str) -> bool:
        """Test if the credentials are valid."""
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
                    # Verificar que el vehículo existe
                    vehicle_exists = any(v["id"] == vehicle_id for v in vehicles)
                    return vehicle_exists
                else:
                    return False
        except Exception as e:
            _LOGGER.error("Error testing credentials: %s", e)
            return False
