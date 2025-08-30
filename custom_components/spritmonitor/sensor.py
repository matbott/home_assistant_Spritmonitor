from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfVolume, UnitOfLength
from datetime import datetime, date
from .const import DOMAIN, MANUFACTURER

# --- FUNCIONES HELPER (SIN CAMBIOS) ---
def get_refueling_currency_id(refueling):
    """Get currency ID from refueling object, trying different possible field names."""
    if not refueling:
        return None
    
    # Try different possible field names for currency
    return (refueling.get('currency') or 
            refueling.get('currency_id') or 
            refueling.get('currencyid') or 
            refueling.get('currency_code'))

def get_quantity_unit_name(data, quantity_unit_id):
    """Get quantity unit name from quantity_units data."""
    if not data.get('quantity_units') or quantity_unit_id is None:
        return "L"  # Default fallback to liters
    
    unit = data['quantity_units'].get(quantity_unit_id)
    if unit:
        # API returns 'name' field with unit like 'l', 'gal', etc.
        return unit.get('name', 'L').upper()  # Convert to uppercase for consistency
    return "L"

def get_refueling_quantity_unit_id(refueling):
    """Get quantity unit ID from refueling object."""
    if not refueling:
        return None
    
    return refueling.get('quantityunitid')

def get_currency_symbol(data, refueling_currency_id):
    """Get currency symbol from currencies data."""
    if not data.get('currencies'):
        return "UYU"  # Default fallback if no currencies available
    
    # Try to get currency_id from refueling
    if refueling_currency_id is not None:
        currency = data['currencies'].get(refueling_currency_id)
        if currency:
            # API returns 'name' field with currency code like 'EUR', 'USD', etc.
            return currency.get('name', 'UYU')
    
    # Fallback: try to get currency from vehicle level
    vehicle = data.get('vehicle', {})
    vehicle_currency_id = vehicle.get('currency') or vehicle.get('currency_id')
    if vehicle_currency_id is not None:
        currency = data['currencies'].get(vehicle_currency_id)
        if currency:
            return currency.get('name', 'UYU')
    
    # Final fallback: try first available currency or default
    if data['currencies']:
        first_currency = next(iter(data['currencies'].values()))
        return first_currency.get('name', 'UYU')
    
    return "UYU"

def calculate_price_per_liter(cost, quantity):
    """Calculate price per liter."""
    if not cost or not quantity or quantity == 0:
        return None
    return round(float(cost) / float(quantity), 3)

def calculate_distance_between_refuels(refuelings):
    """Calculate distance between last two refuelings."""
    if not refuelings or len(refuelings) < 2:
        return None
    last = refuelings[0]
    return float(last.get('trip', 0))

def format_cost_in_pesos(cost):
    """Format cost directly."""
    if cost is None:
        return None
    return round(float(cost), 2)

def get_next_service_reminder(reminders):
    """Get next service reminder by mileage."""
    if not reminders:
        return None
    incomplete_reminders = [r for r in reminders if r.get('completed') == 0]
    if not incomplete_reminders:
        return None
    next_reminder = min(incomplete_reminders, key=lambda x: x.get('next_odometer', float('inf')))
    return next_reminder

def get_next_service_date_reminder(reminders):
    """Get closest service reminder by date."""
    if not reminders:
        return None
    incomplete_reminders = [r for r in reminders if r.get('completed') == 0 and r.get('nextdate')]
    if not incomplete_reminders:
        return None
    reminders_with_dates = []
    for r in incomplete_reminders:
        try:
            date_str = r.get('nextdate')
            if date_str:
                parsed_date = datetime.strptime(date_str, '%d.%m.%Y').date()
                r['parsed_date'] = parsed_date
                reminders_with_dates.append(r)
        except (ValueError, TypeError):
            pass
    if not reminders_with_dates:
        return None
    next_reminder = min(reminders_with_dates, key=lambda x: x['parsed_date'])
    return next_reminder.get('parsed_date')

def calculate_consumption_trend(refuelings):
    """Calculate consumption trend in recent refuelings."""
    if not refuelings or len(refuelings) < 3:
        return None
    consumptions = [float(r['consumption']) for r in refuelings[:5] if r.get('consumption') and float(r.get('consumption')) > 0]
    if len(consumptions) < 3:
        return None
    recent_avg = sum(consumptions[:2]) / 2
    older_avg = sum(consumptions[2:4]) / 2 if len(consumptions) >= 4 else consumptions[2]
    difference = recent_avg - older_avg
    if difference > 0.5: return "improving"
    elif difference < -0.5: return "worsening"
    else: return "stable"

def calculate_consumption_consistency(refuelings):
    """Calculate consumption consistency (standard deviation)."""
    if not refuelings or len(refuelings) < 3:
        return None
    consumptions = [float(r['consumption']) for r in refuelings[:5] if r.get('consumption') and float(r.get('consumption')) > 0]
    if len(consumptions) < 3:
        return None
    mean = sum(consumptions) / len(consumptions)
    variance = sum((x - mean) ** 2 for x in consumptions) / len(consumptions)
    std_dev = variance ** 0.5
    return round(std_dev, 2)

def calculate_avg_refuel_quantity(refuelings):
    """Calculate average liters per refueling."""
    if not refuelings: return None
    quantities = [float(r['quantity']) for r in refuelings[:5] if r.get('quantity') and float(r.get('quantity')) > 0]
    if not quantities: return None
    return round(sum(quantities) / len(quantities), 1)

def calculate_avg_days_between_refuels(refuelings):
    """Calculate average days between refuelings."""
    if not refuelings or len(refuelings) < 2: return None
    dates = []
    for refueling in refuelings[:5]:
        date_str = refueling.get('date')
        if date_str:
            try:
                dates.append(datetime.strptime(date_str, '%d.%m.%Y'))
            except ValueError:
                continue
    if len(dates) < 2: return None
    days_differences = [(dates[i] - dates[i + 1]).days for i in range(len(dates) - 1) if (dates[i] - dates[i + 1]).days > 0]
    if not days_differences: return None
    return round(sum(days_differences) / len(days_differences), 1)

def calculate_price_variability(refuelings):
    """Calculate price per liter variability."""
    if not refuelings: return None
    prices_per_liter = [float(r['cost']) / float(r['quantity']) for r in refuelings[:5] if r.get('cost') and r.get('quantity') and float(r.get('quantity')) > 0]
    if len(prices_per_liter) < 2: return None
    return round(max(prices_per_liter) - min(prices_per_liter), 2)

def calculate_eco_driving_index(refuelings, vehicle_avg_consumption):
    """Calculate eco driving index (1-10)."""
    if not refuelings or not vehicle_avg_consumption: return None
    recent_consumptions = [float(r['consumption']) for r in refuelings[:3] if r.get('consumption') and float(r.get('consumption')) > 0]
    if not recent_consumptions: return None
    recent_avg = sum(recent_consumptions) / len(recent_consumptions)
    vehicle_avg = float(vehicle_avg_consumption)
    consistency = calculate_consumption_consistency(refuelings) or 0
    consistency_score = max(0, 10 - consistency * 2)
    if recent_avg > vehicle_avg * 1.1: performance_score = 10
    elif recent_avg > vehicle_avg: performance_score = 8
    elif recent_avg > vehicle_avg * 0.9: performance_score = 6
    else: performance_score = 3
    eco_index = (performance_score * 0.6 + consistency_score * 0.4)
    return round(eco_index, 1)

def calculate_km_to_service(data):
    """Calculate kilometers remaining to next service."""
    next_service = get_next_service_reminder(data.get('reminders', []))
    if not next_service or not data.get('last_refueling'): return None
    current_km = float(data['last_refueling'].get('odometer', 0))
    service_km = next_service.get('next_odometer', 0)
    return max(0, service_km - current_km)

def calculate_fuel_level_estimate(data):
    """Estimate fuel level based on consumption and distance."""
    if not data.get('vehicle') or not data.get('last_refueling'): return None
    capacity = float(data['vehicle'].get('capacity', 35))
    last_refuel_quantity = float(data['last_refueling'].get('quantity', 0))
    return min(capacity, last_refuel_quantity)

def calculate_range_estimate(data):
    """Estimate remaining range."""
    fuel_level = calculate_fuel_level_estimate(data)
    if not fuel_level or not data.get('vehicle'): return None
    consumption_rate = float(data['vehicle'].get('consumption', 14))
    return round(fuel_level * consumption_rate, 0)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Spritmonitor sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    sensors = [
        # === VEHICLE INFORMATION ===
        SpritmonitorSensor(coordinator, "brand_model", lambda d: f"{d['vehicle'].get('make', '')} {d['vehicle'].get('model', '')}" if d.get('vehicle') else None, icon="mdi:car"),
        SpritmonitorSensor(coordinator, "license_plate", lambda d: d['vehicle'].get('sign', 'Unknown') if d.get('vehicle') else None, icon="mdi:card-text"),
        SpritmonitorSensor(coordinator, "fuel_capacity", lambda d: float(d['vehicle'].get('capacity', 0)) if d.get('vehicle') and d['vehicle'].get('capacity') else None, unit=UnitOfVolume.LITERS, device_class=SensorDeviceClass.VOLUME, icon="mdi:gas-station"),
        SpritmonitorSensor(coordinator, "total_distance", lambda d: float(d['vehicle'].get('tripsum', 0)) if d.get('vehicle') else None, unit=UnitOfLength.KILOMETERS, device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.TOTAL, icon="mdi:speedometer"),
        SpritmonitorSensor(coordinator, "total_fuel", lambda d: float(d['vehicle'].get('quantitysum', 0)) if d.get('vehicle') else None, unit=UnitOfVolume.LITERS, device_class=SensorDeviceClass.VOLUME, state_class=SensorStateClass.TOTAL, icon="mdi:gas-station"),
        SpritmonitorSensor(coordinator, "avg_consumption", lambda d: float(d['vehicle'].get('consumption', 0)) if d.get('vehicle') else None, unit="km/L", state_class=SensorStateClass.MEASUREMENT, icon="mdi:chart-line"),

        # === LAST REFUELING ===
        SpritmonitorSensor(coordinator, "last_refuel_date", lambda d: d['last_refueling'].get('date', '') if d.get('last_refueling') else None, icon="mdi:calendar"),
        SpritmonitorVolumeSensor(coordinator, "last_refuel_quantity", lambda d: float(d['last_refueling'].get('quantity', 0)) if d.get('last_refueling') else None, lambda d: get_quantity_unit_name(d, get_refueling_quantity_unit_id(d.get('last_refueling'))), device_class=SensorDeviceClass.VOLUME, state_class=SensorStateClass.MEASUREMENT, icon="mdi:gas-station"),
        SpritmonitorCostSensor(coordinator, "last_refuel_cost", lambda d: format_cost_in_pesos(d['last_refueling'].get('cost', 0)) if d.get('last_refueling') else None, lambda d: get_currency_symbol(d, get_refueling_currency_id(d.get('last_refueling'))), device_class=None, state_class=SensorStateClass.MEASUREMENT, icon="mdi:currency-usd"),
        SpritmonitorCostSensor(coordinator, "last_refuel_price_per_liter", lambda d: calculate_price_per_liter(d['last_refueling'].get('cost'), d['last_refueling'].get('quantity')) if d.get('last_refueling') else None, lambda d: f"{get_currency_symbol(d, get_refueling_currency_id(d.get('last_refueling')))}/L", state_class=SensorStateClass.MEASUREMENT, icon="mdi:currency-usd"),
        SpritmonitorSensor(coordinator, "last_refuel_odometer", lambda d: float(d['last_refueling'].get('odometer', 0)) if d.get('last_refueling') else None, unit=UnitOfLength.KILOMETERS, device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.TOTAL, icon="mdi:speedometer"),
        SpritmonitorSensor(coordinator, "last_refuel_trip", lambda d: float(d['last_refueling'].get('trip', 0)) if d.get('last_refueling') else None, unit=UnitOfLength.KILOMETERS, device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:map-marker-distance"),
        SpritmonitorSensor(coordinator, "last_refuel_consumption", lambda d: float(d['last_refueling'].get('consumption', 0)) if d.get('last_refueling') else None, unit="km/L", state_class=SensorStateClass.MEASUREMENT, icon="mdi:car-speed-limiter"),
        SpritmonitorSensor(coordinator, "last_refuel_type", lambda d: d['last_refueling'].get('type', 'Unknown') if d.get('last_refueling') else None, icon="mdi:gas-station"),
        SpritmonitorSensor(coordinator, "last_refuel_location", lambda d: d['last_refueling'].get('location', 'Unknown') if d.get('last_refueling') else None, icon="mdi:map-marker"),
        SpritmonitorSensor(coordinator, "last_refuel_country", lambda d: d['last_refueling'].get('country', 'Unknown') if d.get('last_refueling') else None, icon="mdi:flag"),
        SpritmonitorSensor(coordinator, "last_refuel_currency", lambda d: get_currency_symbol(d, get_refueling_currency_id(d.get('last_refueling'))), icon="mdi:currency-usd"),
        SpritmonitorCostSensor(coordinator, "last_refuel_cost_converted", lambda d: format_cost_in_pesos(d['last_refueling'].get('cost_converted', 0)) if d.get('last_refueling') else None, lambda d: get_currency_symbol(d, get_refueling_currency_id(d.get('last_refueling'))), device_class=None, state_class=SensorStateClass.MEASUREMENT, icon="mdi:currency-usd"),
        SpritmonitorSensor(coordinator, "last_refuel_fuel_sort_id", lambda d: d['last_refueling'].get('fuelsortid', 'Unknown') if d.get('last_refueling') else None, icon="mdi:gas-station"),
        SpritmonitorSensor(coordinator, "last_refuel_quantity_unit_id", lambda d: get_refueling_quantity_unit_id(d.get('last_refueling')), icon="mdi:beaker"),

        # === RANKING STATISTICS ===
        SpritmonitorSensor(coordinator, "ranking_position", lambda d: d['vehicle']['rankingInfo'].get('rank', None) if d.get('vehicle') and d['vehicle'].get('rankingInfo') else None, icon="mdi:trophy"),
        SpritmonitorSensor(coordinator, "ranking_total", lambda d: d['vehicle']['rankingInfo'].get('total', None) if d.get('vehicle') and d['vehicle'].get('rankingInfo') else None, icon="mdi:account-group"),
        SpritmonitorSensor(coordinator, "ranking_min_consumption", lambda d: float(d['vehicle']['rankingInfo'].get('min', 0)) if d.get('vehicle') and d['vehicle'].get('rankingInfo') else None, unit="km/L", state_class=SensorStateClass.MEASUREMENT, icon="mdi:trophy-award"),
        SpritmonitorSensor(coordinator, "ranking_avg_consumption", lambda d: float(d['vehicle']['rankingInfo'].get('avg', 0)) if d.get('vehicle') and d['vehicle'].get('rankingInfo') else None, unit="km/L", state_class=SensorStateClass.MEASUREMENT, icon="mdi:chart-bar"),

        # === NEXT MAINTENANCE ===
        SpritmonitorSensor(coordinator, "next_service_km", lambda d: get_next_service_reminder(d.get('reminders', [])).get('next_odometer') if get_next_service_reminder(d.get('reminders', [])) else None, unit=UnitOfLength.KILOMETERS, device_class=SensorDeviceClass.DISTANCE, icon="mdi:wrench"),
        SpritmonitorSensor(coordinator, "next_service_note", lambda d: get_next_service_reminder(d.get('reminders', [])).get('note') if get_next_service_reminder(d.get('reminders', [])) else None, icon="mdi:note-text"),
        SpritmonitorSensor(coordinator, "next_service_date", lambda d: get_next_service_date_reminder(d.get('reminders', [])), device_class=SensorDeviceClass.DATE, icon="mdi:calendar-clock"),
        SpritmonitorSensor(coordinator, "km_to_next_service", lambda d: calculate_km_to_service(d), unit=UnitOfLength.KILOMETERS, device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:car-wrench"),

        # === CALCULATED STATISTICS ===
        SpritmonitorSensor(coordinator, "fuel_level_estimate", lambda d: calculate_fuel_level_estimate(d), unit=UnitOfVolume.LITERS, device_class=None, state_class=SensorStateClass.MEASUREMENT, icon="mdi:gauge"),
        SpritmonitorSensor(coordinator, "range_estimate", lambda d: calculate_range_estimate(d), unit=UnitOfLength.KILOMETERS, device_class=SensorDeviceClass.DISTANCE, state_class=SensorStateClass.MEASUREMENT, icon="mdi:gas-station-off"),

        # === TREND ANALYSIS (based on last 5 refuelings) ===
        SpritmonitorSensor(coordinator, "consumption_trend", lambda d: calculate_consumption_trend(d.get('refuelings', [])), icon="mdi:trending-up"),
        SpritmonitorSensor(coordinator, "consumption_consistency", lambda d: calculate_consumption_consistency(d.get('refuelings', [])), unit="km/L", state_class=SensorStateClass.MEASUREMENT, icon="mdi:chart-bell-curve"),
        SpritmonitorSensor(coordinator, "avg_refuel_quantity", lambda d: calculate_avg_refuel_quantity(d.get('refuelings', [])), unit=UnitOfVolume.LITERS, device_class=None, state_class=SensorStateClass.MEASUREMENT, icon="mdi:gas-station-outline"),
        SpritmonitorSensor(coordinator, "avg_days_between_refuels", lambda d: calculate_avg_days_between_refuels(d.get('refuelings', [])), unit="days", state_class=SensorStateClass.MEASUREMENT, icon="mdi:calendar-range"),
        SpritmonitorCostSensor(coordinator, "price_variability", lambda d: calculate_price_variability(d.get('refuelings', [])), lambda d: f"{get_currency_symbol(d, get_refueling_currency_id(d.get('last_refueling')))}/L", state_class=SensorStateClass.MEASUREMENT, icon="mdi:chart-line-variant"),
        SpritmonitorSensor(coordinator, "eco_driving_index", lambda d: calculate_eco_driving_index(d.get('refuelings', []), d.get('vehicle', {}).get('consumption')), unit="/10", state_class=SensorStateClass.MEASUREMENT, icon="mdi:leaf"),
    ]
    async_add_entities(sensors)


class SpritmonitorSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Spritmonitor sensor."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_id, value_fn, unit=None, device_class=None, state_class=None, icon=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._value_fn = value_fn
        
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        
        vehicle_id = coordinator.data.get('vehicle', {}).get('id', 'unknown') if coordinator.data else 'unknown'
        self._attr_unique_id = f"spritmonitor_{vehicle_id}_{sensor_id}"
        
        self._attr_translation_key = sensor_id

        # --- ¡AQUÍ ESTÁ EL CAMBIO! ---
        # Si el sensor que estamos creando es el de "brand_model",
        # usamos tu descubrimiento para construir la URL de la imagen.
        if sensor_id == "brand_model":
            self._attr_entity_picture = f"https://www.spritmonitor.de/pics/vehicle/{vehicle_id}.jpg"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this sensor."""
        if not self.coordinator.data or not self.coordinator.data.get('vehicle'):
            return None
        vehicle = self.coordinator.data['vehicle']
        
        vehicle_full_name = f"{vehicle.get('make', '')} {vehicle.get('model', '')}".strip() or "Spritmonitor Vehicle"
        
        return DeviceInfo(
            identifiers={(DOMAIN, str(vehicle.get('id', 'unknown')))},
            name=vehicle_full_name,
            manufacturer=MANUFACTURER,
            model=vehicle_full_name,
        )

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        try:
            if not self.coordinator.data:
                return None
            return self._value_fn(self.coordinator.data)
        except (KeyError, TypeError, AttributeError, ValueError, IndexError):
            return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None


class SpritmonitorCostSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Spritmonitor cost sensor with dynamic currency unit."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_id, value_fn, unit_fn, device_class=None, state_class=None, icon=None):
        """Initialize the cost sensor."""
        super().__init__(coordinator)
        self._value_fn = value_fn
        self._unit_fn = unit_fn
        
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        
        vehicle_id = coordinator.data.get('vehicle', {}).get('id', 'unknown') if coordinator.data else 'unknown'
        self._attr_unique_id = f"spritmonitor_{vehicle_id}_{sensor_id}"
        
        self._attr_translation_key = sensor_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this sensor."""
        if not self.coordinator.data or not self.coordinator.data.get('vehicle'):
            return None
        vehicle = self.coordinator.data['vehicle']
        
        vehicle_full_name = f"{vehicle.get('make', '')} {vehicle.get('model', '')}".strip() or "Spritmonitor Vehicle"
        
        return DeviceInfo(
            identifiers={(DOMAIN, str(vehicle.get('id', 'unknown')))},
            name=vehicle_full_name,
            manufacturer=MANUFACTURER,
            model=vehicle_full_name,
        )

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        try:
            if not self.coordinator.data:
                return None
            return self._value_fn(self.coordinator.data)
        except (KeyError, TypeError, AttributeError, ValueError, IndexError):
            return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement for this sensor."""
        try:
            if not self.coordinator.data:
                return "UYU"  # Default fallback
            return self._unit_fn(self.coordinator.data)
        except (KeyError, TypeError, AttributeError, ValueError, IndexError):
            return "UYU"  # Default fallback

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None

class SpritmonitorVolumeSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Spritmonitor volume sensor with dynamic quantity unit."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, sensor_id, value_fn, unit_fn, device_class=None, state_class=None, icon=None):
        """Initialize the volume sensor."""
        super().__init__(coordinator)
        self._value_fn = value_fn
        self._unit_fn = unit_fn
        
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        
        vehicle_id = coordinator.data.get('vehicle', {}).get('id', 'unknown') if coordinator.data else 'unknown'
        self._attr_unique_id = f"spritmonitor_{vehicle_id}_{sensor_id}"
        
        self._attr_translation_key = sensor_id

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this sensor."""
        if not self.coordinator.data or not self.coordinator.data.get('vehicle'):
            return None
        vehicle = self.coordinator.data['vehicle']
        
        vehicle_full_name = f"{vehicle.get('make', '')} {vehicle.get('model', '')}".strip() or "Spritmonitor Vehicle"
        
        return DeviceInfo(
            identifiers={(DOMAIN, str(vehicle.get('id', 'unknown')))},
            name=vehicle_full_name,
            manufacturer=MANUFACTURER,
            model=vehicle_full_name,
        )

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        try:
            if not self.coordinator.data:
                return None
            return self._value_fn(self.coordinator.data)
        except (KeyError, TypeError, AttributeError, ValueError, IndexError):
            return None

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement for this sensor."""
        try:
            if not self.coordinator.data:
                return "L"  # Default fallback to liters
            return self._unit_fn(self.coordinator.data)
        except (KeyError, TypeError, AttributeError, ValueError, IndexError):
            return "L"  # Default fallback to liters

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
