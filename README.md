Spritmonitor Custom Component for Home Assistant
This is a custom component for Home Assistant that integrates data from Spritmonitor.de, allowing you to track your vehicle's fuel consumption, costs, and service reminders directly within Home Assistant.

Componente Personalizado Spritmonitor para Home Assistant
Este es un componente personalizado para Home Assistant que integra datos de Spritmonitor.de, permitiéndote rastrear el consumo de combustible, los costos y los recordatorios de servicio de tu vehículo directamente en Home Assistant.

Características
Información del Vehículo: Marca, modelo, matrícula, capacidad del tanque, distancia total recorrida y combustible total consumido.
Consumo Promedio: Muestra el consumo promedio general del vehículo.
Último Repostaje: Detalles del último repostaje, incluyendo fecha, litros, costo total (en Pesos Uruguayos), precio por litro, kilometraje, km recorridos desde la última carga, consumo de esa carga, tipo de combustible, ubicación y país.
Estadísticas de Ranking: Posición del vehículo en el ranking de Spritmonitor, total de vehículos en el ranking, mejor y promedio consumo del ranking.
Próximo Mantenimiento: Kilometraje y fecha del próximo servicio, y la descripción de la nota de servicio.
Estimaciones: Nivel estimado de combustible en el tanque y autonomía estimada (basadas en datos de Spritmonitor).
Instalación
Instalación Recomendada (HACS)
La forma más sencilla de instalar este componente es a través de HACS (Home Assistant Community Store).

Abre HACS en tu instancia de Home Assistant.
Ve a "Integraciones".
Haz clic en el botón de "..." (tres puntos) en la esquina superior derecha y selecciona "Repositorios personalizados".
En el campo "URL del repositorio", pega: https://github.com/matbott/home_assistant_Spritmonitor
En "Categoría", selecciona "Integración".
Haz clic en "Añadir".
Ahora, busca "Spritmonitor" en la sección de integraciones de HACS.
Haz clic en "Instalar" y sigue las instrucciones.
Reinicia Home Assistant por completo.
Instalación Manual
Copia la carpeta spritmonitor (que contiene __init__.py, sensor.py, config_flow.py, manifest.json) desde este repositorio.
Pega esta carpeta dentro de la carpeta custom_components de tu instalación de Home Assistant. Si la carpeta custom_components no existe, créala. La ruta final debería ser algo como: <config_path>/custom_components/spritmonitor/ (donde <config_path> es la ruta de tu configuración de Home Assistant, usualmente /config).
Reinicia Home Assistant por completo.
Configuración
Después de la instalación (HACS o manual) y el reinicio de Home Assistant:

Ve a "Configuración" > "Dispositivos y servicios".
Haz clic en el botón "Añadir integración".
Busca "Spritmonitor" en la lista.
Se te pedirá que ingreses la siguiente información:
ID del Vehículo: El ID de tu vehículo en Spritmonitor. Puedes encontrarlo en la URL de tu vehículo (ej. https://www.spritmonitor.de/en/detail/[VEHICLE_ID].html).
Application-ID: Tu "Application-ID" de la API de Spritmonitor.
Bearer Token: Tu "Bearer Token" de la API de Spritmonitor.
(Si no tienes tus tokens de API, deberás solicitarlos a Spritmonitor).
Haz clic en "Enviar". La integración intentará validar tus credenciales.
Si la configuración es exitosa, los sensores de Spritmonitor aparecerán automáticamente en tu instancia de Home Assistant.
Sensores Disponibles
Todos los sensores serán entidades de un dispositivo llamado Spritmonitor - [Marca] [Modelo] en Home Assistant.

Los sensores se nombrarán siguiendo el patrón sensor.spritmonitor_vehiculo_[NOMBRE_SENSOR].

Ejemplos de sensores que se crearán:

sensor.spritmonitor_brand_model
sensor.spritmonitor_license_plate
sensor.spritmonitor_fuel_capacity
sensor.spritmonitor_total_distance
sensor.spritmonitor_total_fuel
sensor.spritmonitor_avg_consumption
sensor.spritmonitor_last_refuel_date
sensor.spritmonitor_last_refuel_quantity
sensor.spritmonitor_last_refuel_cost (en UYU)
sensor.spritmonitor_last_refuel_price_per_liter (en UYU/L)
sensor.spritmonitor_last_refuel_odometer
sensor.spritmonitor_last_refuel_trip
sensor.spritmonitor_last_refuel_consumption
sensor.spritmonitor_last_refuel_type
sensor.spritmonitor_last_refuel_location
sensor.spritmonitor_last_refuel_country
sensor.spritmonitor_ranking_position
sensor.spritmonitor_ranking_total
sensor.spritmonitor_ranking_min_consumption
sensor.spritmonitor_ranking_avg_consumption
sensor.spritmonitor_next_service_km
sensor.spritmonitor_next_service_note
sensor.spritmonitor_next_service_date
sensor.spritmonitor_km_to_next_service
sensor.spritmonitor_fuel_level_estimate
sensor.spritmonitor_range_estimate
Solución de Problemas
La integración no aparece después de reiniciar:
Verifica los logs de Home Assistant en "Configuración" > "Registros" en busca de errores relacionados con spritmonitor o custom_components.
Asegúrate de que la estructura de carpetas sea correcta: custom_components/spritmonitor/ y que todos los archivos .py y manifest.json estén dentro.
Asegúrate de que no haya errores de sintaxis en manifest.json.
Los sensores muestran "Desconocido" o "No disponible":
Verifica tus credenciales (ID de Vehículo, Application-ID, Bearer Token) en la configuración de la integración. Es el error más común.
Asegúrate de que tu instancia de Home Assistant tenga acceso a Internet para comunicarse con la API de Spritmonitor.
Revisa los logs para ver si hay errores de conexión o de la API de Spritmonitor.
Contribuciones
¡Las contribuciones son bienvenidas! Si encuentras un error o tienes una mejora, no dudes en abrir un issue o enviar un pull request en el repositorio de GitHub.

Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo LICENCE para más detalles.

English Version (for the same README.md file)
Spritmonitor Custom Component for Home Assistant
This is a custom component for Home Assistant that integrates data from Spritmonitor.de, allowing you to track your vehicle's fuel consumption, costs, and service reminders directly within Home Assistant.

Features
Vehicle Information: Make, model, license plate, tank capacity, total distance driven, and total fuel consumed.
Average Consumption: Displays the overall average consumption of the vehicle.
Last Refueling: Details of the last refueling, including date, liters, total cost (in Uruguayan Pesos), price per liter, odometer reading, distance driven since last fill-up, consumption of that fill-up, fuel type, location, and country.
Ranking Statistics: Vehicle's position in the Spritmonitor ranking, total vehicles in ranking, best and average consumption in ranking.
Next Maintenance: Odometer and date for the next service, and the service note description.
Estimates: Estimated fuel level in the tank and estimated range (based on Spritmonitor data).
Installation
Recommended Installation (HACS)
The easiest way to install this component is through HACS (Home Assistant Community Store).

Open HACS in your Home Assistant instance.
Go to "Integrations".
Click the "..." (three dots) button in the upper right corner and select "Custom repositories".
In the "Repository URL" field, paste: https://github.com/matbott/home_assistant_Spritmonitor
In "Category", select "Integration".
Click "Add".
Now, search for "Spritmonitor" in the HACS integrations section.
Click "Install" and follow the instructions.
Restart Home Assistant completely.
Manual Installation
Copy the spritmonitor folder (containing __init__.py, sensor.py, config_flow.py, manifest.json) from this repository.
Paste this folder into the custom_components folder of your Home Assistant installation. If the custom_components folder does not exist, create it. The final path should look something like: <config_path>/custom_components/spritmonitor/ (where <config_path> is your Home Assistant configuration path, usually /config).
Restart Home Assistant completely.
Configuration
After installation (HACS or manual) and restarting Home Assistant:

Go to "Settings" > "Devices & Services".
Click the "Add Integration" button.
Search for "Spritmonitor" in the list.
You will be prompted to enter the following information:
Vehicle ID: Your vehicle's ID on Spritmonitor. You can find it in your vehicle's URL (e.g., https://www.spritmonitor.de/en/detail/[VEHICLE_ID].html).
Application-ID: Your Spritmonitor API "Application-ID".
Bearer Token: Your Spritmonitor API "Bearer Token".
(If you don't have your API tokens, you will need to request them from Spritmonitor.)
Click "Submit". The integration will attempt to validate your credentials.
If the configuration is successful, the Spritmonitor sensors will automatically appear in your Home Assistant instance.
Available Sensors
All sensors will be entities of a device named Spritmonitor - [Make] [Model] in Home Assistant.

Sensors will be named following the pattern sensor.spritmonitor_vehicle_[SENSOR_NAME].

Examples of sensors that will be created:

sensor.spritmonitor_brand_model
sensor.spritmonitor_license_plate
sensor.spritmonitor_fuel_capacity
sensor.spritmonitor_total_distance
sensor.spritmonitor_total_fuel
sensor.spritmonitor_avg_consumption
sensor.spritmonitor_last_refuel_date
sensor.spritmonitor_last_refuel_quantity
sensor.spritmonitor_last_refuel_cost (in UYU)
sensor.spritmonitor_last_refuel_price_per_liter (in UYU/L)
sensor.spritmonitor_last_refuel_odometer
sensor.spritmonitor_last_refuel_trip
sensor.spritmonitor_last_refuel_consumption
sensor.spritmonitor_last_refuel_type
sensor.spritmonitor_last_refuel_location
sensor.spritmonitor_last_refuel_country
sensor.spritmonitor_ranking_position
sensor.spritmonitor_ranking_total
sensor.spritmonitor_ranking_min_consumption
sensor.spritmonitor_ranking_avg_consumption
sensor.spritmonitor_next_service_km
sensor.spritmonitor_next_service_note
sensor.spritmonitor_next_service_date
sensor.spritmonitor_km_to_next_service
sensor.spritmonitor_fuel_level_estimate
sensor.spritmonitor_range_estimate
Troubleshooting
Integration does not appear after restarting:
Check your Home Assistant logs in "Settings" > "Logs" for errors related to spritmonitor or custom_components.
Ensure the folder structure is correct: custom_components/spritmonitor/ and that all .py files and manifest.json are inside.
Make sure there are no syntax errors in manifest.json.
Sensors show "Unknown" or "Unavailable":
Verify your credentials (Vehicle ID, Application-ID, Bearer Token) in the integration's configuration. This is the most common error.
Ensure your Home Assistant instance has internet access to communicate with the Spritmonitor API.
Check the logs for any connection or Spritmonitor API errors.
Contributions
Contributions are welcome! If you find a bug or have an improvement, feel free to open an issue or submit a pull request on the GitHub repository.

License
This project is licensed under the MIT License. See the LICENCE file for more details.
