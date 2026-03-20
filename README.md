Hello, thank you for downloading and using this integration. I appreciate the feedback from each of you. I acknowledge that it has some bugs, but unfortunately, I don't have the time to continue improving it.
I hope someone else in the community can continue this project and take it to the level it deserves.

Thank you very much.

# Spritmonitor Integration for Home Assistant 🚗⛽

[![Open in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=matbott&repository=home_assistant_Spritmonitor&category=integration)

Integrate your vehicle's fuel consumption, costs, and maintenance data from [Spritmonitor.de](https://www.spritmonitor.de) directly into Home Assistant.

This integration brings a wealth of data to your dashboard, from average consumption to trend analysis and costs, allowing you to create automations and get a complete overview of your car's performance and expenses.

## 🌟 Key Features

* 🔌 **Complete Vehicle Support**: Supports **Combustion** (gasoline, diesel), pure **Electric** (EV), and **Plug-in Hybrid (PHEV)** vehicles.
* 🧠 **Automatic Unit Detection**: Configuration is simpler than ever! The integration automatically detects and uses the units (`km`/`mi`, `L/100km`/`km/L`, etc.) directly from your Spritmonitor profile.
* 🚗⚡️ **Full Plug-in Hybrid (PHEV) Support**: Get a complete picture of your PHEV's performance. When configured as a PHEV, the integration creates **both** the full set of fuel sensors and the full set of electric sensors.
* 📊 **Over 30 Entities**: Provides a comprehensive set of sensors for a detailed analysis of each fuel type.
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
3.  Fill out the form with your vehicle and API credentials. The configuration is now much simpler:
    * **Vehicle ID**: Your vehicle's ID number from Spritmonitor.
    * **Application Token** and **Bearer Token**.
    * **Vehicle Type**: Select `Combustion`, `Electric`, or `PHEV`. This step is crucial!
    * **Currency**: Enter your desired currency symbol (e.g., `USD`, `€`, `UYU`).
4.  Click **"Submit"**.

**NOTE:** The default Application ID is `095369dede84c55797c22d4854ca6efe`

**NOTE:** The Bearer Token format is `Bearer xxxxxxxxxxxxxxxxxx`

![vehicleID](images/VehicleID.png?raw=true)

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
* Average Consumption
* Last Refuel Quantity
* Last Refuel Price/Liter
* Last Refuel Consumption
* Estimated Fuel Level
* Estimated Range

#### ⚡️ Specific Sensors (if type is Electric)
* Battery Capacity (in `kWh`)
* Total Energy Charged
* Average Energy Consumption
* Average Electric Efficiency (in mi/kWh or km/kWh e.g. 3.4 mi/kWh)
* Last Charge Energy
* Last Charge Price/kWh
* Last Charge Consumption
* Full Battery Range Estimate

---

#### 🚗⚡️ Specific Sensors (if type is PHEV)
When a vehicle is configured as a Plug-in Hybrid, the integration will create **both** of the above groups: the full set of **🔥 Combustion Sensors** and the full set of **⚡️ Electric Sensors**, allowing for a complete overview of the vehicle.

---

#### 🧠 Calculated Sensors
* **For Combustion and Electric vehicles**, these common sensors are created:
    * Consumption Trend
    * Consumption Consistency
    * Average Charge/Refuel Quantity
    * Average Days Between Charges/Refuels
    * Price Variability
    * Eco Driving Index
    * Cost per Distance
* **For PHEV vehicles**, these sensors are created **twice**—once for each fuel type—with clear names to distinguish them (e.g., `Cost per Distance (Fuel)` and `Cost per Distance (Electric)`).

## Sending data back to Spritmonitor
This integration allows you to send data back to Spritmonitor. This is useful for example with PHEV/BEV vehicles. You can setup automations for when charging is complete to update SpritMonitor automatically. 
The following is an example automation that will send daily charge data back to Spritmonitor, including trip since last charge, amount of electricity added etc etc, it will also send a notification to HA Companion App to show charging stats and a persistent notification:

```
alias: "EV Charging: Session Summary (IOG Friendly)"
description: Triggers when Ohme finishes and sends a formatted summary with Total Cost.
triggers:
  - entity_id: sensor.ohme_home_go_status
    to: unavailable
    for:
      minutes: 2
    trigger: state
conditions:
  - condition: numeric_state
    entity_id: sensor.ev_charging_energy_today
    above: 0.1
actions:
  - variables:
      actual_trip: "{{ states('sensor.ev_trip_meter') | float(0) }}"
      total_cost: "{{ states('sensor.ev_charging_cost_today') | float(0) | round(2) }}"
  - action: notify.all_devices_james
    data:
      title: 🚗 Mazda CX-60 Charged
      message: >
        💰 Cost: £{{ "%.2f" | format(total_cost) }}   🔋 Added:
        {{states('sensor.ev_charging_energy_today') }} kWh   🛣️ Trip: {{
        actual_trip}} mi  📈 Final SoC: {{
        states('sensor.mazda_cx_60_charge_level') }}% ⏱️ Time Active: {{
        states('sensor.ev_charging_time_today') }} 🛣️ Odometer: {{
        states('sensor.mazda_cx_60_odometer') | float(0) | round(0) }} {{
        state_attr('sensor.mazda_cx_60_odometer', 'unit_of_measurement') }}
      data:
        notification_icon: mdi:car-connected
        color: "#2ecc71"
        group: car
  - action: notify.persistent_notification
    data:
      title: 🚗 Mazda CX-60 Charged
      message: >
        💰 Cost: £{{ "%.2f" | format(total_cost) }}   🔋 Added:
        {{states('sensor.ev_charging_energy_today') }} kWh   🛣️ Trip: {{
        actual_trip}} mi  📈 Final SoC: {{
        states('sensor.mazda_cx_60_charge_level') }}% ⏱️ Time Active: {{
        states('sensor.ev_charging_time_today') }} 🛣️ Odometer: {{
        states('sensor.mazda_cx_60_odometer') | float(0) | round(0) }} {{
        state_attr('sensor.mazda_cx_60_odometer', 'unit_of_measurement') }}
      data:
        notification_icon: mdi:car-connected
        color: "#2ecc71"
        group: car
  - action: spritmonitor.add_fueling
    data:
      vehicle_device: da208b77aff3c937ebf0bce607dc4174
      tank_id: "2"
      date: "{{ now().strftime('%Y-%m-%d') }}"
      quantity: "{{ states('sensor.ev_charging_energy_today') | float(0) | round(2) }}"
      type: >-
        {{ 'full' if states('sensor.mazda_cx_60_charge_level') | int(0) >= 98
        else 'notfull' }}
      fuelsort_id: "19"
      quantity_unit_id: "5"
      odometer: "{{ states('sensor.mazda_cx_60_odometer') | int(0) }}"
      trip: "{{ actual_trip }}"
      price: "{{ total_cost }}"
      currency_id: "4"
      pricetype: "0"
      percentage: "{{ states('sensor.mazda_cx_60_charge_level') | int(0) }}"
      charge_info_source: source_wallbox
      streets:
        - city
        - land
        - autobahn
      attributes_tires: allyeartires
      attributes_driving_style: normal
      attributes_ac: true
      attributes_heating: true
  - delay: "00:00:05"
  - action: input_number.set_value
    target:
      entity_id: input_number.odometer_at_last_charge
    data:
      value: "{{ states('sensor.mazda_cx_60_odometer') | float(0) }}"
mode: single

```

## Troubleshooting

-   **Integration not found:** After installation, make sure you have restarted Home Assistant.
-   **Sensors unavailable:** Ensure your API credentials (Vehicle ID and Bearer Token) are correct and that Home Assistant has an active internet connection. Check the logs under **Settings > System > Logs** for errors.

## 🤝 Contributions

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 🙏 Acknowledgements

* **@matbott** - Original creator and maintainer.
