# Spritmonitor Custom Component for Home Assistant

This Home Assistant custom component integrates data from [Spritmonitor.de](https://www.spritmonitor.de), allowing you to monitor your vehicle's fuel consumption, costs, and maintenance directly within Home Assistant.

## Features

- **Vehicle Data**: Brand, model, license plate, tank capacity, total distance, and total fuel.
- **Last Refueling**: Date, liters, total cost (in UYU), price per liter, odometer, trip distance, consumption, type, location, and country.
- **Average Consumption**: Overall average consumption (km/L).
- **Ranking**: Vehicle's position and average consumption within Spritmonitor rankings.
- **Next Service**: Upcoming service mileage, date, and note.
- **Estimates**: Estimated fuel level and remaining range.
- **New Insights**:
  - 🔄 **Consumption Trend**: Improving / Worsening / Stable.
  - 📊 **Consumption Consistency**: How variable your fuel consumption is over time.
  - ⛽ **Average Liters per Refueling**: Your typical refueling amount.
  - 📅 **Average Days Between Refuels**: Refueling frequency.
  - 💰 **Price Variability**: Difference between your highest and lowest price per liter.
  - 🌱 **Eco Driving Index**: Efficiency score from 1 (worst) to 10 (best).

## Installation

### Recommended Installation (HACS)

1. Open HACS in Home Assistant.
2. Go to **"Integrations"**.
3. Click the **"..."** (three dots) button in the top right and select **"Custom repositories"**.
4. Paste the repository URL:  
   `https://github.com/matbott/home_assistant_Spritmonitor`
5. Select **"Integration"** as the **Category**.
6. Click **"Add"**.
7. Search for **"Spritmonitor"** in HACS, click **"Install"**, and follow the prompts.
8. **Restart Home Assistant** after installation.

## Configuration

After installation and restarting Home Assistant:

1. Go to **Settings > Devices & Services**.
2. Click **"Add Integration"**.
3. Search for **"Spritmonitor"**.
4. Enter your **Vehicle ID**, **Application ID**, and **Bearer Token** from Spritmonitor's API.
5. Click **"Submit"**.

NOTE: Application ID = 095369dede84c55797c22d4854ca6efe

## Available Sensors

All sensors will be grouped under a device named:  
`Spritmonitor - [Make] [Model]`  
They follow the naming pattern:  
`sensor.spritmonitor_vehicle_[SENSOR_NAME]`

### Sensor Categories

- **Vehicle Info**: Brand, model, license plate, tank capacity, total distance, total fuel.
- **Last Refueling**: Date, liters, cost (UYU), price per liter, odometer, trip, consumption, type, location, country.
- **Average Consumption**: Overall km/L.
- **Ranking**: Your vehicle's rank and average consumption compared to others.
- **Next Service**: Estimated mileage/date for next service and any notes.
- **Estimates**: Fuel level (%) and estimated remaining range.

### New Advanced Sensors

- 🔄 `Consumption Trend`: Improving / Worsening / Stable.
- 📊 `Consumption Consistency`: Indicates variability in consumption across refuels.
- ⛽ `Average Liters per Refueling`: Average volume of each refuel.
- 📅 `Average Days Between Refuels`: How often you refuel.
- 💰 `Price Variability`: Difference between your highest and lowest price per liter.
- 🌱 `Eco Driving Index`: A 1–10 score representing how eco-friendly your driving style is.

## Troubleshooting

- **Integration not showing**: Check Home Assistant logs under `Settings > System > Logs`. Ensure the `custom_components/spritmonitor/` folder is structured correctly and `manifest.json` is valid.
- **Sensors not updating or unavailable**: Double-check your API credentials. Also confirm that Home Assistant has a working internet connection.

## Contributions

Contributions are very welcome!  
Feel free to fork this project, create pull requests, or open issues.

## License

This project is licensed under the MIT License.  
See the `LICENSE` file for full details.
