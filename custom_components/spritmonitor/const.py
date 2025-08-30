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
API_CURRENCIES_URL = f"{API_BASE_URL}/currencies.json"
API_QUANTITY_UNITS_URL = f"{API_BASE_URL}/quantityunits.json"

# Configuration keys used in config_flow and __init__
CONF_VEHICLE_ID = "vehicle_id"
CONF_APP_TOKEN = "app_token"
CONF_BEARER_TOKEN = "bearer_token"
CONF_UPDATE_INTERVAL = "update_interval"
