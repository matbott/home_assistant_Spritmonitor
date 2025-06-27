# Spritmonitor for Home Assistant

Integrate your vehicle's fuel consumption, costs, and maintenance data from [Spritmonitor.de](https://www.spritmonitor.de) directly into Home Assistant.

## Main Features

This integration exposes a wealth of data as entities in Home Assistant, including:

-   **Vehicle Info:** Brand, model, license plate, and tank capacity.
-   **Refueling Data:** Details from the last refueling like date, quantity, cost, consumption, and odometer.
-   **Maintenance:** Alerts for the next service by mileage and date.
-   **Stats & Estimates:** Average consumption, ranking, fuel level, and estimated range.

### Advanced Insights

Get deeper insights into your driving with unique sensors:
-   🔄 **Consumption Trend:** Find out if your efficiency is `Improving`, `Worsening`, or `Stable`.
-   📊 **Consumption Consistency:** Measures the variability of your consumption between refuelings.
-   ⛽ **Average per Refueling:** Know your typical refueling volume.
-   📅 **Average Days Between Refuels:** Discover your refueling frequency.
-   💰 **Price Variability:** The difference between the highest and lowest price per unit you've paid.
-   🌱 **Eco-Driving Index:** A 1-10 score on your driving efficiency.

## Installation (HACS)

1.  In HACS, go to **Integrations**.
2.  Click the three dots (menu) and select **"Custom repositories"**.
3.  Paste the repository URL:
    ```
    [https://github.com/matbott/home_assistant_Spritmonitor](https://github.com/matbott/home_assistant_Spritmonitor)
    ```
4.  Select the category **"Integration"** and click **"Add"**.
5.  Search for **"Spritmonitor"** in HACS, click **"Install"**, and follow the steps.
6.  **Restart Home Assistant** after installation.

## Configuration

1.  Go to **Settings > Devices & Services**.
2.  Click **"Add Integration"** and search for **"Spritmonitor"**.
3.  Enter your ID vehicule.
4.  Enter your Spritmonitor API credentials.
5.  Click **"Submit"**.

NOTE: Application ID = `095369dede84c55797c22d4854ca6efe`

NOTE: Token format = `Bearer xxxxxxxxxxxxxxxxxx`

![image](https://github.com/user-attachments/assets/3cb3da84-cb36-4d55-9708-b61d5829ae14)

![image](https://github.com/user-attachments/assets/516ed019-76b8-44c3-86b4-9cd3a6d14fae)

## Entities

All sensors will be grouped under a device named after your vehicle (e.g., `Ford Focus`).

Entity IDs are now short and clean, for example: `sensor.estimated_range` or `sensor.last_refuel_cost`.

## Troubleshooting

-   **Integration not found:** Check the logs under **Settings > System > Logs** for errors.
-   **Sensors unavailable:** Ensure your API credentials are correct and that Home Assistant has an active internet connection.

## Contributions

Contributions are welcome! Feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
