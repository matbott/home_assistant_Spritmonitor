"""Unit tests for the calculation helpers in sensor.py."""
from datetime import date, datetime

import pytest
from freezegun import freeze_time

from custom_components.spritmonitor import sensor as s


def fueling(**kwargs):
    return {"date": "01.01.2026", **kwargs}


@pytest.mark.parametrize(
    ("cost", "quantity", "expected"),
    [(60, 30, 2.0), ("50", "28", 1.786), (None, 30, None), (60, 0, None), (60, None, None)],
)
def test_price_per_unit(cost, quantity, expected):
    assert s.calculate_price_per_unit(cost, quantity) == expected


def test_format_cost():
    assert s.format_cost("12.345") == 12.35
    assert s.format_cost(None) is None


def test_next_service_reminder_picks_lowest_open_odometer():
    reminders = [
        {"completed": 0, "next_odometer": 20000},
        {"completed": 1, "next_odometer": 5000},
        {"completed": 0, "next_odometer": 15000},
    ]
    assert s.get_next_service_reminder(reminders)["next_odometer"] == 15000
    assert s.get_next_service_reminder([{"completed": 1}]) is None
    assert s.get_next_service_reminder(None) is None


def test_next_service_date_reminder():
    reminders = [
        {"completed": 0, "nextdate": "01.09.2026"},
        {"completed": 0, "nextdate": "15.06.2026"},
        {"completed": 0, "nextdate": "not a date"},
        {"completed": 1, "nextdate": "01.01.2026"},
    ]
    assert s.get_next_service_date_reminder(reminders) == date(2026, 6, 15)
    assert s.get_next_service_date_reminder([{"completed": 0, "nextdate": "bad"}]) is None
    assert s.get_next_service_date_reminder([]) is None


def test_km_to_service():
    data = {"reminders": [{"completed": 0, "next_odometer": 15000}], "last_refueling": {"odometer": 13700}}
    assert s.calculate_km_to_service(data) == 1300
    # Overdue services never go negative
    data["last_refueling"]["odometer"] = 16000
    assert s.calculate_km_to_service(data) == 0
    assert s.calculate_km_to_service({"reminders": [], "last_refueling": {"odometer": 1}}) is None


def test_fuel_level_and_range_estimate():
    data = {
        "vehicle": {"capacity": 50, "consumption": 5.8},
        "last_gas_refueling": {"quantity": 30},
        "units": {"consumption": "L/100km"},
    }
    assert s.calculate_fuel_level_estimate(data) == 30
    assert s.calculate_range_estimate(data) == 517
    # A fill larger than the tank is capped at the capacity
    data["last_gas_refueling"]["quantity"] = 70
    assert s.calculate_fuel_level_estimate(data) == 50
    # Consumption given as distance per quantity (e.g. km/L)
    data["units"]["consumption"] = "km/L"
    data["vehicle"]["consumption"] = 17
    assert s.calculate_range_estimate(data) == 850
    assert s.calculate_fuel_level_estimate({"vehicle": {"capacity": 0}, "last_gas_refueling": {"quantity": 5}}) is None


def test_consumption_trend():
    def with_consumptions(*values):
        return [fueling(consumption=v) for v in values]

    assert s.calculate_consumption_trend(with_consumptions(6.0, 6.0, 7.0, 7.0)) == "improving"
    assert s.calculate_consumption_trend(with_consumptions(8.0, 8.0, 7.0, 7.0)) == "worsening"
    assert s.calculate_consumption_trend(with_consumptions(7.5, 7.0, 7.0)) == "stable"
    assert s.calculate_consumption_trend(with_consumptions(7.0, 7.0)) is None


def test_consumption_consistency():
    refuelings = [fueling(consumption=v) for v in (7.5, 7.0, 7.0)]
    assert s.calculate_consumption_consistency(refuelings) == 0.24
    assert s.calculate_consumption_consistency(refuelings[:2]) is None


def test_avg_refuel_quantity():
    assert s.calculate_avg_refuel_quantity([fueling(quantity=q) for q in (30, 28, 35, 0)]) == 31.0
    assert s.calculate_avg_refuel_quantity([]) is None


def test_avg_days_between_refuels():
    refuelings = [fueling(date=d) for d in ("10.03.2026", "10.02.2026", "10.01.2026")]
    assert s.calculate_avg_days_between_refuels(refuelings) == 29.5
    assert s.calculate_avg_days_between_refuels(refuelings[:1]) is None


def test_price_variability():
    refuelings = [fueling(cost=60, quantity=30), fueling(cost=50, quantity=28), fueling(cost=70, quantity=35)]
    assert s.calculate_price_variability(refuelings) == 0.21
    assert s.calculate_price_variability(refuelings[:1]) is None


def test_eco_driving_index():
    refuelings = [fueling(consumption=v) for v in (7.5, 7.0, 7.0)]
    assert s.calculate_eco_driving_index(refuelings, 5.8) == 5.4
    # Driving well below the vehicle's average scores best
    assert s.calculate_eco_driving_index(refuelings, 9.0) == 9.6
    assert s.calculate_eco_driving_index(refuelings, 0) is None


def test_full_battery_range():
    assert s.calculate_full_battery_range({"vehicle": {"capacity": 64, "consumption": 16}}) == 400
    assert s.calculate_full_battery_range({"vehicle": {"capacity": 64, "consumption": 0}}) is None


@freeze_time("2026-03-20")
def test_monthly_energy_charged_counts_current_month_only():
    charges = [
        {"date": "05.03.2026", "quantity": 20.5},
        {"date": "15.03.2026", "quantity": "10"},
        {"date": "28.02.2026", "quantity": 50},
        {"date": "05.03.2025", "quantity": 50},
        {"date": "bad", "quantity": 50},
    ]
    assert s.calculate_monthly_energy_charged(charges) == 30.5
    assert s.calculate_monthly_energy_charged([]) is None


def test_efficiency_per_distance():
    assert s.calculate_efficiency_per_distance({"vehicle": {"consumption": 16}}) == 6.25
    assert s.calculate_efficiency_per_distance({"vehicle": {"consumption": 0}}) is None
