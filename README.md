# Spritmonitor Custom Component for Home Assistant

This Home Assistant custom component integrates data from Spritmonitor.de, allowing you to monitor your vehicle's fuel consumption, costs, and maintenance within Home Assistant.

## Features

* **Vehicle Data**: Brand, model, license plate, tank capacity, total distance, and total fuel.
* **Last Refueling**: Date, liters, total cost (in UYU), price per liter, odometer, trip distance, consumption, type, location, and country.
* **Average Consumption**: Overall average consumption (km/L).
* **Ranking**: Vehicle's position and average consumption within Spritmonitor rankings.
* **Next Service**: Upcoming service mileage, date, and note.
* **Estimates**: Estimated fuel level and remaining range.

## Installation

### Recommended Installation (HACS)

1.  Open HACS in Home Assistant.
2.  Go to **"Integrations"**.
3.  Click the "..." (three dots) button in the top right and select **"Custom repositories"**.
4.  Paste `https://github.com/matbott/home_assistant_Spritmonitor` into the **"Repository URL"** field.
5.  Select **"Integration"** as the **"Category"**.
6.  Click **"Add"**.
7.  Search for **"Spritmonitor"** in HACS, then click **"Install"** and follow the prompts.
8.  **Restart Home Assistant**.

### Manual Installation

1.  Copy the `spritmonitor` folder from this repository into your Home Assistant's `custom_components` directory.
    *(e.g., `<config_path>/custom_components/spritmonitor/`)*.
2.  **Restart Home Assistant**.

## Configuration

After installation and Home Assistant restart:

1.  Go to **"Settings" > "Devices & Services"**.
2.  Click **"Add Integration"**.
3.  Search for **"Spritmonitor"**.
4.  Enter your **Vehicle ID**, **Application-ID**, and **Bearer Token** from Spritmonitor's API.
5.  Click **"Submit"**.

## Available Sensors

All sensors will appear under a device named `Spritmonitor - [Make] [Model]` in Home Assistant, following the naming pattern `sensor.spritmonitor_vehicle_[SENSOR_NAME]`.

## Troubleshooting

* **Integration not showing**: Check Home Assistant logs for errors (`Settings > Logs`). Ensure `custom_components/spritmonitor/` structure is correct and `manifest.json` is valid.
* **Sensors unavailable**: Verify your API credentials. Ensure Home Assistant has internet access.

## Contributions

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENCE` file for details.
