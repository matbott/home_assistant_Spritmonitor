from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import UnitOfVolume, UnitOfLength, CURRENCY_EURO
from datetime import datetime
from . import DOMAIN

def calculate_price_per_liter(cost, quantity):
    """Calcular precio por litro."""
    if not cost or not quantity or quantity == 0:
        return None
    # Los costos vienen en centavos, dividir por 100
    return round((float(cost) / 100) / float(quantity), 3)

def calculate_distance_between_refuels(refuelings):
    """Calcular distancia entre últimos dos repostajes."""
    if not refuelings or len(refuelings) < 2:
        return None
    last = refuelings[0]
    previous = refuelings[1]
    return float(last.get('trip', 0))

def format_cost(cost):
    """Formatear costo de centavos a euros."""
    if not cost:
        return None
    return round(float(cost) / 100, 2)

def get_next_service_reminder(reminders):
    """Obtener próximo recordatorio de servicio."""
    if not reminders:
        return None
    
    incomplete_reminders = [r for r in reminders if r.get('completed') == 0]
    if not incomplete_reminders:
        return None
    
    # Buscar el recordatorio con menor kilometraje
    next_reminder = min(incomplete_reminders, key=lambda x: x.get('next_odometer', float('inf')))
    return next_reminder

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Spritmonitor sensors based on a config entry."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    sensors = [
        # === INFORMACIÓN DEL VEHÍCULO ===
        SpritmonitorSensor(
            coordinator, 
            "brand_model", 
            "Marca y modelo", 
            lambda d: f"{d['vehicle'].get('make', '')} {d['vehicle'].get('model', '')}" if d.get('vehicle') else None,
            icon="mdi:car"
        ),
        SpritmonitorSensor(
            coordinator, 
            "license_plate", 
            "Matrícula", 
            lambda d: d['vehicle'].get('sign', 'Desconocida') if d.get('vehicle') else None,
            icon="mdi:card-text"
        ),
        SpritmonitorSensor(
            coordinator, 
            "fuel_capacity", 
            "Capacidad del tanque", 
            lambda d: float(d['vehicle'].get('capacity', 0)) if d.get('vehicle') and d['vehicle'].get('capacity') else None,
            unit=UnitOfVolume.LITERS,
            device_class=SensorDeviceClass.VOLUME,
            icon="mdi:gas-station"
        ),
        SpritmonitorSensor(
            coordinator, 
            "total_distance", 
            "Distancia total", 
            lambda d: float(d['vehicle'].get('tripsum', 0)) if d.get('vehicle') else None,
            unit=UnitOfLength.KILOMETERS,
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.TOTAL,
            icon="mdi:speedometer"
        ),
        SpritmonitorSensor(
            coordinator, 
            "total_fuel", 
            "Combustible total consumido", 
            lambda d: float(d['vehicle'].get('quantitysum', 0)) if d.get('vehicle') else None,
            unit=UnitOfVolume.LITERS,
            device_class=SensorDeviceClass.VOLUME,
            state_class=SensorStateClass.TOTAL,
            icon="mdi:gas-station"
        ),
        SpritmonitorSensor(
            coordinator, 
            "avg_consumption", 
            "Consumo promedio", 
            lambda d: float(d['vehicle'].get('consumption', 0)) if d.get('vehicle') else None,
            unit="km/L",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:chart-line"
        ),
        
        # === ÚLTIMO REPOSTAJE ===
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_date", 
            "Última carga - fecha", 
            lambda d: d['last_refueling'].get('date', '') if d.get('last_refueling') else None,
            icon="mdi:calendar"
        ),
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_quantity", 
            "Última carga - litros", 
            lambda d: float(d['last_refueling'].get('quantity', 0)) if d.get('last_refueling') else None,
            unit=UnitOfVolume.LITERS,
            device_class=SensorDeviceClass.VOLUME,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:gas-station"
        ),
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_cost", 
            "Última carga - precio total", 
            lambda d: format_cost(d['last_refueling'].get('cost', 0)) if d.get('last_refueling') else None,
            unit=CURRENCY_EURO,
            device_class=SensorDeviceClass.MONETARY,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:currency-eur"
        ),
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_price_per_liter", 
            "Última carga - precio por litro", 
            lambda d: calculate_price_per_liter(
                d['last_refueling'].get('cost'), 
                d['last_refueling'].get('quantity')
            ) if d.get('last_refueling') else None,
            unit=f"{CURRENCY_EURO}/L",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:currency-eur"
        ),
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_odometer", 
            "Última carga - kilometraje", 
            lambda d: float(d['last_refueling'].get('odometer', 0)) if d.get('last_refueling') else None,
            unit=UnitOfLength.KILOMETERS,
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.TOTAL,
            icon="mdi:speedometer"
        ),
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_trip", 
            "Última carga - km recorridos", 
            lambda d: float(d['last_refueling'].get('trip', 0)) if d.get('last_refueling') else None,
            unit=UnitOfLength.KILOMETERS,
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:map-marker-distance"
        ),
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_consumption", 
            "Última carga - consumo", 
            lambda d: float(d['last_refueling'].get('consumption', 0)) if d.get('last_refueling') else None,
            unit="km/L",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:car-speed-limiter"
        ),
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_type", 
            "Última carga - tipo", 
            lambda d: d['last_refueling'].get('type', 'Desconocido') if d.get('last_refueling') else None,
            icon="mdi:gas-station"
        ),
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_location", 
            "Última carga - ubicación", 
            lambda d: d['last_refueling'].get('location', 'Desconocida') if d.get('last_refueling') else None,
            icon="mdi:map-marker"
        ),
        SpritmonitorSensor(
            coordinator, 
            "last_refuel_country", 
            "Última carga - país", 
            lambda d: d['last_refueling'].get('country', 'Desconocido') if d.get('last_refueling') else None,
            icon="mdi:flag"
        ),
        
        # === ESTADÍSTICAS DE RANKING ===
        SpritmonitorSensor(
            coordinator, 
            "ranking_position", 
            "Posición en ranking", 
            lambda d: d['vehicle']['rankingInfo'].get('rank', None) if d.get('vehicle') and d['vehicle'].get('rankingInfo') else None,
            icon="mdi:trophy"
        ),
        SpritmonitorSensor(
            coordinator, 
            "ranking_total", 
            "Total vehículos en ranking", 
            lambda d: d['vehicle']['rankingInfo'].get('total', None) if d.get('vehicle') and d['vehicle'].get('rankingInfo') else None,
            icon="mdi:account-group"
        ),
        SpritmonitorSensor(
            coordinator, 
            "ranking_min_consumption", 
            "Mejor consumo del ranking", 
            lambda d: float(d['vehicle']['rankingInfo'].get('min', 0)) if d.get('vehicle') and d['vehicle'].get('rankingInfo') else None,
            unit="km/L",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:trophy-award"
        ),
        SpritmonitorSensor(
            coordinator, 
            "ranking_avg_consumption", 
            "Consumo promedio del ranking", 
            lambda d: float(d['vehicle']['rankingInfo'].get('avg', 0)) if d.get('vehicle') and d['vehicle'].get('rankingInfo') else None,
            unit="km/L",
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:chart-bar"
        ),
        
        # === PRÓXIMO MANTENIMIENTO ===
        SpritmonitorSensor(
            coordinator, 
            "next_service_km", 
            "Próximo servicio - kilometraje", 
            lambda d: get_next_service_reminder(d.get('reminders', [])).get('next_odometer') if get_next_service_reminder(d.get('reminders', [])) else None,
            unit=UnitOfLength.KILOMETERS,
            device_class=SensorDeviceClass.DISTANCE,
            icon="mdi:wrench"
        ),
        SpritmonitorSensor(
            coordinator, 
            "next_service_note", 
            "Próximo servicio - descripción", 
            lambda d: get_next_service_reminder(d.get('reminders', [])).get('note') if get_next_service_reminder(d.get('reminders', [])) else None,
            icon="mdi:note-text"
        ),
        SpritmonitorSensor(
            coordinator, 
            "km_to_next_service", 
            "Kilómetros para próximo servicio", 
            lambda d: calculate_km_to_service(d),
            unit=UnitOfLength.KILOMETERS,
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:car-wrench"
        ),
        
        # === ESTADÍSTICAS CALCULADAS ===
        SpritmonitorSensor(
            coordinator, 
            "fuel_level_estimate", 
            "Nivel estimado de combustible", 
            lambda d: calculate_fuel_level_estimate(d),
            unit=UnitOfVolume.LITERS,
            device_class=SensorDeviceClass.VOLUME,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:gauge"
        ),
        SpritmonitorSensor(
            coordinator, 
            "range_estimate", 
            "Autonomía estimada", 
            lambda d: calculate_range_estimate(d),
            unit=UnitOfLength.KILOMETERS,
            device_class=SensorDeviceClass.DISTANCE,
            state_class=SensorStateClass.MEASUREMENT,
            icon="mdi:gas-station-off"
        ),
    ]

    async_add_entities(sensors)

def calculate_km_to_service(data):
    """Calcular kilómetros restantes para el próximo servicio."""
    if not data.get('last_refueling') or not data.get('reminders'):
        return None
    
    next_service = get_next_service_reminder(data.get('reminders', []))
    if not next_service:
        return None
    
    current_km = float(data['last_refueling'].get('odometer', 0))
    service_km = next_service.get('next_odometer', 0)
    
    return max(0, service_km - current_km)

def calculate_fuel_level_estimate(data):
    """Estimar nivel de combustible basado en consumo y distancia."""
    if not data.get('vehicle') or not data.get('last_refueling'):
        return None
    
    capacity = float(data['vehicle'].get('capacity', 35))  # Valor por defecto
    last_refuel_quantity = float(data['last_refueling'].get('quantity', 0))
    consumption_rate = float(data['vehicle'].get('consumption', 14))  # km/L
    
    # Asumimos que el tanque se llenó en el último repostaje
    # y estimamos cuánto se ha consumido desde entonces
    # Nota: esto es una estimación básica, necesitaríamos más datos para ser preciso
    return min(capacity, last_refuel_quantity)

def calculate_range_estimate(data):
    """Estimar autonomía restante."""
    fuel_level = calculate_fuel_level_estimate(data)
    if not fuel_level or not data.get('vehicle'):
        return None
    
    consumption_rate = float(data['vehicle'].get('consumption', 14))  # km/L
    return round(fuel_level * consumption_rate, 0)

class SpritmonitorSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Spritmonitor sensor."""
    
    def __init__(self, coordinator, sensor_id, name, value_fn, unit=None, device_class=None, state_class=None, icon=None):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._sensor_id = sensor_id
        self._name = name
        self._value_fn = value_fn
        self._attr_native_unit_of_measurement = unit
        self._attr_device_class = device_class
        self._attr_state_class = state_class
        self._attr_icon = icon
        
        # Generar unique_id estable
        vehicle_id = coordinator.data.get('vehicle', {}).get('id', 'unknown') if coordinator.data else 'unknown'
        self._attr_unique_id = f"spritmonitor_{vehicle_id}_{sensor_id}"
        self._attr_name = f"Spritmonitor {name}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this sensor."""
        if not self.coordinator.data or not self.coordinator.data.get('vehicle'):
            return None
            
        vehicle = self.coordinator.data['vehicle']
        return DeviceInfo(
            identifiers={(DOMAIN, str(vehicle.get('id', 'unknown')))},
            name=f"{vehicle.get('make', '')} {vehicle.get('model', '')}".strip() or "Vehículo Spritmonitor",
            manufacturer=vehicle.get('make', 'Unknown'),
            model=vehicle.get('model', 'Unknown'),
            via_device=None,
        )

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        try:
            if not self.coordinator.data:
                return None
            return self._value_fn(self.coordinator.data)
        except (KeyError, TypeError, AttributeError, ValueError):
            return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None