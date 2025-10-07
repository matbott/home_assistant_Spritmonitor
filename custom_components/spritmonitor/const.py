# Contenido para: const.py

"""Constants for the Spritmonitor integration."""

# Domain for the integration
DOMAIN = "spritmonitor"
MANUFACTURER = "matbott & 🤖"

# Default values
DEFAULT_APP_TOKEN = "095369dede84c55797c22d4854ca6efe"
DEFAULT_UPDATE_INTERVAL = 6

# API Configuration
API_BASE_URL = "https://api.spritmonitor.de/v1"
API_VEHICLES_URL = f"{API_BASE_URL}/vehicles.json"
API_REMINDERS_URL = f"{API_BASE_URL}/reminders.json"
API_FUELINGS_URL_TPL = f"{API_BASE_URL}/vehicle/{{vehicle_id}}/fuelings.json"

# Configuration keys
CONF_VEHICLE_ID = "vehicle_id"
CONF_APP_TOKEN = "app_token"
CONF_BEARER_TOKEN = "bearer_token"
CONF_UPDATE_INTERVAL = "update_interval"
CONF_VEHICLE_TYPE = "vehicle_type"
CONF_CURRENCY = "currency"

# Vehicle Types
VEHICLE_TYPE_COMBUSTION = "combustion"
VEHICLE_TYPE_ELECTRIC = "electric"
VEHICLE_TYPE_PHEV = "phev" # Nuevo para el futuro