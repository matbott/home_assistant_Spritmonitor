# Spritmonitor Integration for Home Assistant 🚗⛽

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=matbott&repository=home_assistant_Spritmonitor&category=integration)

Integrate your vehicle's fuel consumption, costs, and maintenance data from [Spritmonitor.de](https://www.spritmonitor.de) directly into Home Assistant.

This integration brings a wealth of data to your dashboard, from average consumption to trend analysis and costs, allowing you to create automations and get a complete overview of your car's performance and expenses.

## 🌟 Key Features

* 🔌 **Multi-Vehicle Support**: Supports both **combustion** (gasoline, diesel) and **electric** vehicles.
* 🔧 **Flexible Configuration**: Customize units of measurement to your preference:
    * **Currency**: Choose your local currency symbol (e.g., `USD`, `€`, `UYU`).
    * **Distance**: Kilometers (`km`) or Miles (`mi`).
    * **Volume**: Liters (`L`) or Gallons (`gal`).
* 📊 **Over 30 Entities**: Provides a comprehensive set of sensors for detailed analysis.
* 💡 **Calculated Sensors**: Transforms raw data into useful insights, like consumption trends, an eco-driving index, and your real cost per distance.
* 🏆 **Ranking Data**: Compare your vehicle's performance against other similar models on Spritmonitor.

## 📥 Installation (HACS)

1.  In HACS, go to **Integrations**.
2.  Click the three dots (menu) and select **"Custom repositories"**.
3.  Paste the repository URL:
    `https://github.com/matbott/home_assistant_Spritmonitor`
4.  Select the category **"Integration"** and click **"Add"**.
5.  Search for **"Spritmonitor"** in HACS, click **"Install"**, and follow the steps.
6.  **Restart Home Assistant** after installation.

## ⚙️ Configuration

1.  Go to **Settings > Devices & Services**.
2.  Click **"Add Integration"** and search for **"Spritmonitor"**.
3.  Fill out the form with your vehicle and API credentials. This includes:
    * **Vehicle ID**: Your vehicle's ID number from Spritmonitor.
    * **Application Token** and **Bearer Token**.
    * **Vehicle Type**: Select **Combustion** or **Electric**. This step is crucial!
    * **Currency, Distance Unit, and Volume Unit**.
4.  Click **"Submit"**.

**NOTE:** The default Application ID is `095369dede84c55797c22d4854ca6efe`

**NOTE:** The Bearer Token format is `Bearer xxxxxxxxxxxxxxxxxx`

![image](https://github.com/user-attachments/assets/3cb3da84-cb36-4d55-9708-b61d5829ae14)

![image](https://github.com/user-attachments/assets/516ed019-76b8-44c3-86b4-9cd3a6d14fae)

## 📈 Sensors Created

All sensors will be grouped under a device named after your vehicle (e.g., `BYD Dolphin`).

#### ℹ️ Basic Information
* Brand and Model
* License Plate
* Total Distance Traveled

#### ⛽ Last Charge / Refueling
* Last Charge/Refuel Date
* Last Charge/Refuel Odometer
* Last Trip Distance
* Last Charge/Refuel Cost
* Last Charge/Refuel Type (e.g., `notfull`)
* Last Charge/Refuel Location
* Last Charge/Refuel Country

#### 🏆 Ranking
* Ranking Position
* Total in Ranking
* Ranking's Best Consumption
* Ranking's Average Consumption

#### 🛠️ Maintenance
* Next Service (km)
* Next Service Note
* Next Service Date
* Kilometers to Next Service

---

#### 🔥 Specific Sensors (if type is Combustion)
* Fuel Capacity
* Total Fuel Consumed
* Average Consumption (e.g., `km/L`)
* Last Refuel Quantity
* Last Refuel Price/Liter
* Last Refuel Consumption
* Estimated Fuel Level
* Estimated Range

#### ⚡️ Specific Sensors (if type is Electric)
* Battery Capacity (in `kWh`)
* Total Energy Charged
* Average Energy Consumption (e.g., `kWh/100km`)
* Last Charge Energy
* Last Charge Price/kWh
* Last Charge Consumption
* Full Battery Range Estimate

---

#### 🧠 Calculated Sensors (Common to both)
* **Consumption Trend**: Shows if your consumption is `improving`, `worsening`, or `stable`.
* **Consumption Consistency**: The standard deviation of your consumption. A lower value is better.
* **Average Charge/Refuel Quantity**: The average amount of fuel/energy you add per stop.
* **Average Days Between Charges/Refuels**: How frequently you charge or refuel.
* **Price Variability**: How much the price of energy/fuel has fluctuated.
* **Eco Driving Index**: A score from 1 to 10 on your driving efficiency.
* **Cost per Distance**: The real cost for every kilometer or mile driven.

## Troubleshooting

-   **Integration not found:** After installation, make sure you have restarted Home Assistant.
-   **Sensors unavailable:** Ensure your API credentials (Vehicle ID and Bearer Token) are correct and that Home Assistant has an active internet connection. Check the logs under **Settings > System > Logs** for errors.

## 🤝 Contributions

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 🙏 Acknowledgements

* **@matbott** - Original creator and maintainer.
