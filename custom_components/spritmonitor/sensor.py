# Contenido para: sensor.py

import logging
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfEnergy
from datetime import datetime

from .const import (
    DOMAIN, MANUFACTURER, CONF_VEHICLE_TYPE, CONF_CURRENCY, 
    CONF_VEHICLE_ID, VEHICLE_TYPE_COMBUSTION, VEHICLE_TYPE_ELECTRIC, VEHICLE_TYPE_PHEV
)

_LOGGER = logging.getLogger(__name__)

# --- (Las funciones de cálculo se mantienen igual) ---
def calculate_price_per_unit(cost, quantity):
    if not cost or not quantity or float(quantity) == 0: return None
    return round(float(cost) / float(quantity), 3)
def format_cost(cost):
    if cost is None: return None
    return round(float(cost), 2)
def get_next_service_reminder(reminders):
    if not reminders: return None
    incomplete_reminders = [r for r in reminders if r.get('completed') == 0]
    if not incomplete_reminders: return None
    return min(incomplete_reminders, key=lambda x: x.get('next_odometer', float('inf')))
def get_next_service_date_reminder(reminders):
    if not reminders: return None
    incomplete_reminders = [r for r in reminders if r.get('completed') == 0 and r.get('nextdate')]
    if not incomplete_reminders: return None
    reminders_with_dates = []
    for r in incomplete_reminders:
        try:
            date_str = r.get('nextdate')
            if date_str:
                parsed_date = datetime.strptime(date_str, '%d.%m.%Y').date()
                r['parsed_date'] = parsed_date
                reminders_with_dates.append(r)
        except (ValueError, TypeError): pass
    if not reminders_with_dates: return None
    return min(reminders_with_dates, key=lambda x: x['parsed_date']).get('parsed_date')
def calculate_km_to_service(data):
    next_service = get_next_service_reminder(data.get('reminders', []))
    if not next_service or not data.get('last_refueling'): return None
    current_km = float(data['last_refueling'].get('odometer', 0))
    service_km = next_service.get('next_odometer', 0)
    return max(0, service_km - current_km)
def calculate_fuel_level_estimate(data):
    if not data.get('vehicle') or not data.get('last_gas_refueling'): return None
    capacity = float(data['vehicle'].get('capacity', 0))
    last_refuel_quantity = float(data['last_gas_refueling'].get('quantity', 0))
    return min(capacity, last_refuel_quantity) if capacity > 0 else None
def calculate_range_estimate(data):
    fuel_level = calculate_fuel_level_estimate(data)
    if not fuel_level or not data.get('vehicle'): return None
    consumption_val = float(data['vehicle'].get('consumption', 0))
    consumption_unit = data.get('units', {}).get('consumption', '')
    if consumption_val <= 0: return None
    if '100' in consumption_unit:
        return round((fuel_level / consumption_val) * 100)
    return round(fuel_level * consumption_val)
def calculate_consumption_trend(refuelings):
    if not refuelings or len(refuelings) < 3: return None
    consumptions = [float(r['consumption']) for r in refuelings[:5] if r.get('consumption') and float(r.get('consumption')) > 0]
    if len(consumptions) < 3: return None
    recent_avg = sum(consumptions[:2]) / 2
    older_avg = sum(consumptions[2:4]) / 2 if len(consumptions) >= 4 else consumptions[2]
    if older_avg == 0: return "stable"
    trend_ratio = recent_avg / older_avg
    if trend_ratio < 0.95: return "improving"
    elif trend_ratio > 1.05: return "worsening"
    else: return "stable"
def calculate_consumption_consistency(refuelings):
    if not refuelings or len(refuelings) < 3: return None
    consumptions = [float(r['consumption']) for r in refuelings[:5] if r.get('consumption') and float(r.get('consumption')) > 0]
    if len(consumptions) < 3: return None
    mean = sum(consumptions) / len(consumptions)
    variance = sum((x - mean) ** 2 for x in consumptions) / len(consumptions)
    return round(variance ** 0.5, 2)
def calculate_avg_refuel_quantity(refuelings):
    if not refuelings: return None
    quantities = [float(r['quantity']) for r in refuelings[:5] if r.get('quantity') and float(r.get('quantity')) > 0]
    if not quantities: return None
    return round(sum(quantities) / len(quantities), 1)
def calculate_avg_days_between_refuels(refuelings):
    if not refuelings or len(refuelings) < 2: return None
    dates = [datetime.strptime(r['date'], '%d.%m.%Y') for r in refuelings[:5] if r.get('date')]
    if len(dates) < 2: return None
    days_diffs = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1) if (dates[i] - dates[i + 1]).days > 0]
    if not days_diffs: return None
    return round(sum(days_diffs) / len(days_diffs), 1)
def calculate_price_variability(refuelings):
    if not refuelings: return None
    prices_per_unit = [float(r['cost']) / float(r['quantity']) for r in refuelings[:5] if r.get('cost') and r.get('quantity') and float(r.get('quantity')) > 0]
    if len(prices_per_unit) < 2: return None
    return round(max(prices_per_unit) - min(prices_per_unit), 2)
def calculate_eco_driving_index(refuelings, vehicle_avg_consumption):
    if not refuelings or not vehicle_avg_consumption or float(vehicle_avg_consumption) == 0: return None
    recent_consumptions = [float(r['consumption']) for r in refuelings[:3] if r.get('consumption') and float(r.get('consumption')) > 0]
    if not recent_consumptions: return None
    recent_avg = sum(recent_consumptions) / len(recent_consumptions)
    vehicle_avg = float(vehicle_avg_consumption)
    performance_ratio = recent_avg / vehicle_avg
    if performance_ratio < 0.9: performance_score = 10
    elif performance_ratio < 1.0: performance_score = 8
    elif performance_ratio < 1.1: performance_score = 6
    else: performance_score = 4
    consistency = calculate_consumption_consistency(refuelings) or 5
    consistency_score = max(0, 10 - consistency * 5)
    eco_index = (performance_score * 0.7 + consistency_score * 0.3)
    return round(eco_index, 1)
def calculate_cost_per_distance(refuelings):
    if not refuelings or len(refuelings) < 2: return None
    total_cost, total_trip = 0.0, 0.0
    for r in refuelings[:10]:
        cost = r.get('cost')
        trip = r.get('trip')
        if cost and trip and float(trip) > 0:
            total_cost += float(cost)
            total_trip += float(trip)
    if total_trip == 0: return None
    return round(total_cost / total_trip, 2)
def calculate_full_battery_range(data):
    if not data.get('vehicle'): return None
    capacity = float(data['vehicle'].get('capacity', 0))
    consumption_per_100km = float(data['vehicle'].get('consumption', 0))
    if capacity <= 0 or consumption_per_100km <= 0: return None
    return round((capacity * 100) / consumption_per_100km)
def calculate_monthly_energy_charged(charges):
    """Calcula el total de kWh cargados en el mes actual."""
    if not charges: return None
    current_month_year = datetime.now().strftime('%m.%Y')
    total_kwh_this_month = 0.0
    for charge in charges:
        try:
            charge_date_str = charge.get('date')
            quantity = charge.get('quantity')
            if not charge_date_str or not quantity:
                continue
            charge_date = datetime.strptime(charge_date_str, '%d.%m.%Y')
            if charge_date.strftime('%m.%Y') == current_month_year:
                total_kwh_this_month += float(quantity)
        except (ValueError, TypeError):
            # Ignora cargas con formato de fecha o cantidad incorrecto
            continue
    return round(total_kwh_this_month, 2)
    
async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    vehicle_type = config_entry.data.get(CONF_VEHICLE_TYPE)
    
    all_sensors = []
    
    # Sensores comunes
    all_sensors.extend([
        SpritmonitorSensor(coordinator, "brand_model", lambda d: f"{d['vehicle'].get('make', '')} {d['vehicle'].get('model', '')}"),
        SpritmonitorSensor(coordinator, "license_plate", lambda d: d['vehicle'].get('sign')),
        SpritmonitorSensor(coordinator, "total_distance", lambda d: float(d['vehicle'].get('tripsum', 0)), device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.TOTAL),
        SpritmonitorSensor(coordinator, "last_refuel_date", lambda d: d.get('last_refueling', {}).get('date')),
        SpritmonitorSensor(coordinator, "last_refuel_odometer", lambda d: float(d.get('last_refueling', {}).get('odometer', 0)), device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.TOTAL),
        SpritmonitorSensor(coordinator, "last_refuel_trip", lambda d: float(d.get('last_refueling', {}).get('trip', 0)), device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT),
        SpritmonitorSensor(coordinator, "last_refuel_cost", lambda d: format_cost(d.get('last_refueling', {}).get('cost', 0)), device_class=SensorDeviceClass.MONETARY, state_class=None),
        SpritmonitorSensor(coordinator, "last_refuel_type", lambda d: d.get('last_refueling', {}).get('type')),
        SpritmonitorSensor(coordinator, "last_refuel_location", lambda d: d.get('last_refueling', {}).get('location')),
        SpritmonitorSensor(coordinator, "last_refuel_country", lambda d: d.get('last_refueling', {}).get('country')),
        SpritmonitorSensor(coordinator, "ranking_position", lambda d: d['vehicle']['rankingInfo'].get('rank'), state_class=SensorStateClass.MEASUREMENT),
        SpritmonitorSensor(coordinator, "ranking_total", lambda d: d['vehicle']['rankingInfo'].get('total')),
        SpritmonitorSensor(coordinator, "ranking_min_consumption", lambda d: float(d['vehicle']['rankingInfo'].get('min', 0)), state_class=SensorStateClass.MEASUREMENT),
        SpritmonitorSensor(coordinator, "ranking_avg_consumption", lambda d: float(d['vehicle']['rankingInfo'].get('avg', 0)), state_class=SensorStateClass.MEASUREMENT),
        SpritmonitorSensor(coordinator, "next_service_km", lambda d: (r.get('next_odometer') if (r := get_next_service_reminder(d.get('reminders', []))) else None)),
        SpritmonitorSensor(coordinator, "next_service_note", lambda d: (r.get('note') if (r := get_next_service_reminder(d.get('reminders', []))) else None)),
        SpritmonitorSensor(coordinator, "next_service_date", lambda d: get_next_service_date_reminder(d.get('reminders', []))),
        SpritmonitorSensor(coordinator, "km_to_next_service", lambda d: calculate_km_to_service(d), device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT),
    ])

    is_combustion = vehicle_type in [VEHICLE_TYPE_COMBUSTION, VEHICLE_TYPE_PHEV]
    is_electric = vehicle_type in [VEHICLE_TYPE_ELECTRIC, VEHICLE_TYPE_PHEV]

    if is_combustion:
        combustion_sensors = [
            SpritmonitorSensor(coordinator, "fuel_capacity", lambda d: float(d['vehicle'].get('capacity', 0)), device_class=SensorDeviceClass.VOLUME),
            SpritmonitorSensor(coordinator, "total_fuel", lambda d: float(d['vehicle'].get('quantitysum', 0)), device_class=SensorDeviceClass.VOLUME, state_class=SensorStateClass.TOTAL_INCREASING),
            SpritmonitorSensor(coordinator, "avg_consumption", lambda d: float(d['vehicle'].get('consumption', 0)), state_class=SensorStateClass.MEASUREMENT),
            SpritmonitorSensor(coordinator, "last_refuel_quantity", lambda d: float(d.get('last_gas_refueling', {}).get('quantity', 0)), state_class=SensorStateClass.MEASUREMENT),
            SpritmonitorSensor(coordinator, "last_refuel_price_per_liter", lambda d: calculate_price_per_unit(d.get('last_gas_refueling', {}).get('cost'), d.get('last_gas_refueling', {}).get('quantity')), state_class=SensorStateClass.MEASUREMENT),
            SpritmonitorSensor(coordinator, "last_refuel_consumption", lambda d: float(d.get('last_gas_refueling', {}).get('consumption', 0)), state_class=SensorStateClass.MEASUREMENT),
            SpritmonitorSensor(coordinator, "fuel_level_estimate", lambda d: calculate_fuel_level_estimate(d), state_class=SensorStateClass.MEASUREMENT),
            SpritmonitorSensor(coordinator, "range_estimate", lambda d: calculate_range_estimate(d), device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT),
        ]
        all_sensors.extend(combustion_sensors)

    if is_electric:
        electric_sensors = [
            SpritmonitorSensor(coordinator, "battery_capacity", lambda d: float(d['vehicle'].get('capacity', 0)), device_class=SensorDeviceClass.ENERGY, state_class=None),
            SpritmonitorSensor(coordinator, "total_energy_charged", lambda d: float(d['vehicle'].get('quantitysum', 0)), device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL_INCREASING),
            SpritmonitorSensor(coordinator, "avg_energy_consumption", lambda d: float(d['vehicle'].get('consumption', 0)), state_class=SensorStateClass.MEASUREMENT),
            SpritmonitorSensor(coordinator, "last_charge_energy", lambda d: float(d.get('last_electric_charge', {}).get('quantity', 0)), device_class=SensorDeviceClass.ENERGY, state_class=None),
            SpritmonitorSensor(coordinator, "last_charge_price_per_kwh", lambda d: calculate_price_per_unit(d.get('last_electric_charge', {}).get('cost'), d.get('last_electric_charge', {}).get('quantity')), state_class=SensorStateClass.MEASUREMENT),
            SpritmonitorSensor(coordinator, "last_charge_consumption", lambda d: float(d.get('last_electric_charge', {}).get('consumption', 0)), state_class=SensorStateClass.MEASUREMENT),
            SpritmonitorSensor(coordinator, "full_battery_range_estimate", lambda d: calculate_full_battery_range(d), device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT),
            SpritmonitorSensor(coordinator, "monthly_energy_charged", lambda d: calculate_monthly_energy_charged(d.get('electric_charges', [])), device_class=SensorDeviceClass.ENERGY, state_class=SensorStateClass.TOTAL),
        ]
        all_sensors.extend(electric_sensors)
    
    if vehicle_type == VEHICLE_TYPE_PHEV:
        phev_calculated_sensors = [
            SpritmonitorSensor(coordinator, "consumption_trend_fuel", lambda d: calculate_consumption_trend(d.get('gas_refuelings', []))),
            SpritmonitorSensor(coordinator, "consumption_consistency_fuel", lambda d: calculate_consumption_consistency(d.get('gas_refuelings', []))),
            SpritmonitorSensor(coordinator, "avg_refuel_quantity_fuel", lambda d: calculate_avg_refuel_quantity(d.get('gas_refuelings', []))),
            SpritmonitorSensor(coordinator, "avg_days_between_refuels_fuel", lambda d: calculate_avg_days_between_refuels(d.get('gas_refuelings', []))),
            SpritmonitorSensor(coordinator, "price_variability_fuel", lambda d: calculate_price_variability(d.get('gas_refuelings', []))),
            SpritmonitorSensor(coordinator, "eco_driving_index_fuel", lambda d: calculate_eco_driving_index(d.get('gas_refuelings', []), d.get('vehicle', {}).get('consumption'))),
            SpritmonitorSensor(coordinator, "cost_per_distance_fuel", lambda d: calculate_cost_per_distance(d.get('gas_refuelings', []))),
            SpritmonitorSensor(coordinator, "consumption_trend_electric", lambda d: calculate_consumption_trend(d.get('electric_charges', []))),
            SpritmonitorSensor(coordinator, "consumption_consistency_electric", lambda d: calculate_consumption_consistency(d.get('electric_charges', []))),
            SpritmonitorSensor(coordinator, "avg_refuel_quantity_electric", lambda d: calculate_avg_refuel_quantity(d.get('electric_charges', []))),
            SpritmonitorSensor(coordinator, "avg_days_between_refuels_electric", lambda d: calculate_avg_days_between_refuels(d.get('electric_charges', []))),
            SpritmonitorSensor(coordinator, "price_variability_electric", lambda d: calculate_price_variability(d.get('electric_charges', []))),
            SpritmonitorSensor(coordinator, "eco_driving_index_electric", lambda d: calculate_eco_driving_index(d.get('electric_charges', []), d.get('vehicle', {}).get('consumption'))),
            SpritmonitorSensor(coordinator, "cost_per_distance_electric", lambda d: calculate_cost_per_distance(d.get('electric_charges', []))),
        ]
        all_sensors.extend(phev_calculated_sensors)
    else:
        calculated_sensors = [
            SpritmonitorSensor(coordinator, "consumption_trend", lambda d: calculate_consumption_trend(d.get('refuelings', []))),
            SpritmonitorSensor(coordinator, "consumption_consistency", lambda d: calculate_consumption_consistency(d.get('refuelings', []))),
            SpritmonitorSensor(coordinator, "avg_refuel_quantity", lambda d: calculate_avg_refuel_quantity(d.get('refuelings', []))),
            SpritmonitorSensor(coordinator, "avg_days_between_refuels", lambda d: calculate_avg_days_between_refuels(d.get('refuelings', []))),
            SpritmonitorSensor(coordinator, "price_variability", lambda d: calculate_price_variability(d.get('refuelings', []))),
            SpritmonitorSensor(coordinator, "eco_driving_index", lambda d: calculate_eco_driving_index(d.get('refuelings', []), d.get('vehicle', {}).get('consumption'))),
            SpritmonitorSensor(coordinator, "cost_per_distance", lambda d: calculate_cost_per_distance(d.get('refuelings', []))),
        ]
        all_sensors.extend(calculated_sensors)
    
    async_add_entities(all_sensors)

class SpritmonitorSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_id, value_fn, **kwargs):
        super().__init__(coordinator)
        self.sensor_id = sensor_id
        self._value_fn = value_fn
        self._vehicle_id = self.coordinator.config_entry.data.get(CONF_VEHICLE_ID)
        self._attr_device_class = kwargs.get("device_class")
        self._attr_state_class = kwargs.get("state_class")
        self._attr_unique_id = f"spritmonitor_{self._vehicle_id}_{self.sensor_id}"
        self._attr_translation_key = self.sensor_id
        if self.sensor_id == "brand_model":
            self._attr_entity_picture = f"https://www.spritmonitor.de/pics/vehicle/{self._vehicle_id}.jpg"
        else:
            self._attr_icon = self.get_icon()

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit of the sensor, determined dynamically and specifically for each type."""
        if not self.coordinator.data or not self.coordinator.data.get("units"): return None
        
        units = self.coordinator.data.get("units", {})
        currency = self.coordinator.config_entry.data.get(CONF_CURRENCY)
        trip_unit = units.get("trip")
        
        # --- LÓGICA DE UNIDADES MEJORADA ---
        
        # Sensores de Combustión
        if self.sensor_id in ["fuel_capacity", "total_fuel", "last_refuel_quantity", "fuel_level_estimate", "avg_refuel_quantity_fuel", "avg_refuel_quantity"]:
            return units.get("quantity")
        if self.sensor_id in ["avg_consumption", "last_refuel_consumption", "consumption_consistency_fuel", "consumption_consistency"]:
            return units.get("consumption")
        if self.sensor_id in ["last_refuel_price_per_liter", "price_variability_fuel", "price_variability"]:
             return f"{currency}/{units.get('quantity')}"

        # Sensores Eléctricos
        if self.sensor_id in ["battery_capacity", "total_energy_charged", "last_charge_energy", "avg_refuel_quantity_electric", "monthly_energy_charged"]:
            return UnitOfEnergy.KILO_WATT_HOUR
        if self.sensor_id in ["avg_energy_consumption", "last_charge_consumption", "consumption_consistency_electric"]:
            # Para PHEVs, el consumo principal puede ser de gasolina, forzamos la unidad correcta para sensores eléctricos
            return f"kWh/100{trip_unit}" if trip_unit else "kWh/100km"
        if self.sensor_id in ["last_charge_price_per_kwh", "price_variability_electric"]:
            return f"{currency}/{UnitOfEnergy.KILO_WATT_HOUR}"

        # Sensores Comunes y Calculados
        if self.sensor_id in ["total_distance", "last_refuel_odometer", "last_refuel_trip", "km_to_next_service", "next_service_km", "range_estimate", "full_battery_range_estimate"]:
            return trip_unit
        if self.sensor_id == "last_refuel_cost":
            return currency
        if "cost_per_distance" in self.sensor_id:
            return f"{currency}/{trip_unit}"

        # Sensores sin unidad
        if "days" in self.sensor_id: return "days"
        if "eco_driving_index" in self.sensor_id: return "/10"
        
        # Fallback para sensores de ranking que usan la unidad de consumo principal
        if self.sensor_id in ["ranking_min_consumption", "ranking_avg_consumption"]:
            return units.get("consumption")

        return None # Devuelve None si no se encuentra ninguna coincidencia

    @property
    def device_info(self) -> DeviceInfo:
        device_name = f"Spritmonitor {self._vehicle_id}"
        model = None
        if self.coordinator.data and self.coordinator.data.get('vehicle'):
            vehicle = self.coordinator.data['vehicle']
            make = vehicle.get('make', '')
            model_name = vehicle.get('model', '')
            if make and model_name:
                device_name = f"{make} {model_name}"
            model = model_name
        return DeviceInfo(
            identifiers={(DOMAIN, str(self._vehicle_id))}, name=device_name,
            manufacturer=MANUFACTURER, model=model,
            configuration_url=f"https://www.spritmonitor.de/en/detail/{self._vehicle_id}.html"
        )

    @property
    def native_value(self):
        try:
            if self.coordinator.data:
                return self._value_fn(self.coordinator.data)
            return None
        except (KeyError, TypeError, AttributeError, ValueError, IndexError):
            return None

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data is not None

    def get_icon(self):
        base_sensor_id = self.sensor_id.replace('_fuel', '').replace('_electric', '')
        icons = {
            "license_plate": "mdi:card-text", "total_distance": "mdi:speedometer", "last_refuel_date": "mdi:calendar", 
            "last_refuel_odometer": "mdi:speedometer", "last_refuel_trip": "mdi:map-marker-distance",
            "last_refuel_cost": "mdi:currency-usd", "last_refuel_type": "mdi:gas-station-outline",
            "last_refuel_location": "mdi:map-marker", "last_refuel_country": "mdi:flag", "ranking_position": "mdi:trophy",
            "ranking_total": "mdi:account-group", "ranking_min_consumption": "mdi:trophy-award", "ranking_avg_consumption": "mdi:chart-bar",
            "next_service_km": "mdi:wrench", "next_service_note": "mdi:note-text", "next_service_date": "mdi:calendar-clock",
            "km_to_next_service": "mdi:car-wrench", "fuel_capacity": "mdi:gas-station", "total_fuel": "mdi:gas-station",
            "avg_consumption": "mdi:chart-line", "last_refuel_price_per_liter": "mdi:currency-usd", "last_refuel_consumption": "mdi:car-speed-limiter",
            "last_refuel_quantity": "mdi:gas-station", "fuel_level_estimate": "mdi:gauge", "range_estimate": "mdi:gas-station-off",
            "battery_capacity": "mdi:battery", "total_energy_charged": "mdi:lightning-bolt", "avg_energy_consumption": "mdi:chart-line", 
            "last_charge_energy": "mdi:ev-station", "last_charge_price_per_kwh": "mdi:currency-usd",
            "last_charge_consumption": "mdi:car-speed-limiter", "full_battery_range_estimate": "mdi:map-marker-radius", 
            "consumption_trend": "mdi:trending-up", "consumption_consistency": "mdi:chart-bell-curve", "avg_refuel_quantity": "mdi:gas-station-outline", 
            "avg_days_between_refuels": "mdi:calendar-range", "price_variability": "mdi:chart-line-variant", 
            "eco_driving_index": "mdi:leaf", "cost_per_distance": "mdi:cash-multiple",
            "monthly_energy_charged": "mdi:calendar-month"
        }
        return icons.get(base_sensor_id)
