# Contenido para: const.py

"""Constants for the Spritmonitor integration."""
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

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

# --- URL DE FUELINGS CORREGIDA (VUELTA A LA ORIGINAL) ---
API_FUELINGS_URL_TPL = f"{API_BASE_URL}/vehicle/{{vehicle_id}}/fuelings.json"

# --- LÍNEA ANTIGUA ELIMINADA ---
# API_FUELINGS_URL = f"{API_BASE_URL}/fuelings.json"

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
VEHICLE_TYPE_PHEV = "phev"

# Service constants
SERVICE_ADD_FUELING = "add_fueling"
SERVICE_ADD_FUELING_SCHEMA = vol.Schema(
    {
        vol.Required("vehicle_device"): cv.string,
        vol.Required("tank_id"): vol.Coerce(int),
        vol.Required("date"): cv.datetime,
        vol.Required("trip"): vol.Coerce(float),
        vol.Required("quantity"): vol.Coerce(float),
        vol.Required("type"): cv.string,
        vol.Required("fuelsort_id"): vol.Coerce(int),
        vol.Required("quantity_unit_id"): vol.Coerce(int),
        vol.Optional("odometer"): vol.Any(vol.Coerce(float), None),
        vol.Optional("price"): vol.Any(vol.Coerce(float), None),
        vol.Optional("currency_id"): vol.Any(vol.Coerce(int), None),
        vol.Optional("pricetype"): vol.Any(vol.Coerce(int), None),
        vol.Optional("note"): vol.Any(cv.string, None),
        vol.Optional("stationname"): vol.Any(cv.string, None),
        vol.Optional("location"): vol.Any(cv.string, None),
        vol.Optional("country"): vol.Any(cv.string, None),
        vol.Optional("bc_consumption"): vol.Any(vol.Coerce(float), None),
        vol.Optional("bc_quantity"): vol.Any(vol.Coerce(float), None),
        vol.Optional("bc_speed"): vol.Any(vol.Coerce(float), None),
        vol.Optional("latitude"): vol.Any(vol.Coerce(float), None),
        vol.Optional("longitude"): vol.Any(vol.Coerce(float), None),
        vol.Optional("percentage"): vol.Any(vol.Coerce(int), None),
        vol.Optional("charging_power"): vol.Any(vol.Coerce(float), None),
        vol.Optional("charging_duration"): vol.Any(vol.Coerce(int), None),
        vol.Optional("charge_info_ac_dc"): vol.Any(cv.string, None),
        vol.Optional("charge_info_source"): vol.Any(cv.string, None),
        vol.Optional("streets"): vol.Any([cv.string], None),
        vol.Optional("attributes_tires"): vol.Any(cv.string, None),
        vol.Optional("attributes_driving_style"): vol.Any(cv.string, None),
        vol.Optional("attributes_ac"): vol.Any(bool, None),
        vol.Optional("attributes_heating"): vol.Any(bool, None),
        vol.Optional("attributes_trailer"): vol.Any(bool, None),
    }
)