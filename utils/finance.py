"""
utils/finance.py
================
Pure mathematical helpers used across multiple calculators.
No imports from config or models — fully stateless functions.
"""

import math


def annualization_factor(avg_life_years: float, discount_rate: float) -> float:
    """
    Converts a one-time capital cost into an equivalent annual cost stream.

    Formula (capital recovery factor):
        AF = [D × (1+D)^N] / [(1+D)^N - 1]

    where D = discount rate, N = average life in years.

    Args:
        avg_life_years: Equipment useful life in years.
        discount_rate:  Annual discount rate (e.g. 0.03 for 3%).

    Returns:
        Annualization factor (scalar).
    """
    D = discount_rate
    N = avg_life_years
    factor = (D * (1 + D) ** N) / ((1 + D) ** N - 1)
    return factor


def annual_equivalent_cost(unit_cost: float, avg_life_years: float, discount_rate: float) -> float:
    """
    Annual equivalent cost of a capital asset.

    Args:
        unit_cost:      Purchase cost of the equipment (INR).
        avg_life_years: Equipment useful life in years.
        discount_rate:  Annual discount rate.

    Returns:
        Annual equivalent cost (INR / year).
    """
    af = annualization_factor(avg_life_years, discount_rate)
    return unit_cost * af


def cost_per_hour(annual_cost: float, weeks_per_year: float, working_hours_per_week: float) -> float:
    """
    Converts an annual cost to a per-hour rate.

    Args:
        annual_cost:            Annual cost (INR / year).
        weeks_per_year:         52.1429 by default.
        working_hours_per_week: e.g. 6 days × 8 hours = 48 hrs/week.

    Returns:
        Cost per hour (INR / hour).
    """
    total_annual_hours = weeks_per_year * working_hours_per_week
    return annual_cost / total_annual_hours


def wes_availability_fraction(
    time_used_per_week_min: float,
    available_hours_per_week: float
) -> float:
    """
    Fraction of total available time actually spent on WES.

    Args:
        time_used_per_week_min:  Minutes the resource is used for WES per week.
        available_hours_per_week: Total available hours for the resource per week.

    Returns:
        Availability fraction (0 to 1).
    """
    available_min = available_hours_per_week * 60
    return time_used_per_week_min / available_min


def time_equipment_cost_per_sample(
    unit_cost: float,
    avg_life_years: float,
    discount_rate: float,
    batch_size: int,
    time_per_batch_min: float,
    runs_per_week: float,
    samples_per_week: int,
    available_hours_per_week: float,
    weeks_per_year: float,
    num_units: int = 1,
) -> float:
    """
    Cost per sample for time-based equipment (batch process).

    Logic:
        1. Compute annual equivalent cost.
        2. Derive cost per hour.
        3. Compute total time used per week = time_per_batch × runs_per_week.
        4. WES availability = time_used / available_time.
        5. Weekly cost = annual_equiv_cost / weeks_per_year × availability.
        6. Cost per sample = weekly_cost / samples_per_week.

    Args:
        unit_cost:               Equipment purchase price (INR).
        avg_life_years:          Equipment life.
        discount_rate:           Annual discount rate.
        batch_size:              Number of samples processed per batch.
        time_per_batch_min:      Duration of one batch run (minutes).
        runs_per_week:           How many batch runs happen per week.
        samples_per_week:        Total WES samples processed per week.
        available_hours_per_week: Total working hours available per week (e.g. 48).
        weeks_per_year:          Year-to-week conversion (52.1429).
        num_units:               Number of equipment units deployed.

    Returns:
        Equipment cost per sample (INR).
    """
    aec = annual_equivalent_cost(unit_cost * num_units, avg_life_years, discount_rate)
    weekly_aec = aec / weeks_per_year

    total_time_per_week_min = time_per_batch_min * runs_per_week
    availability = wes_availability_fraction(total_time_per_week_min, available_hours_per_week)

    weekly_cost = weekly_aec * availability
    return weekly_cost / samples_per_week if samples_per_week > 0 else 0.0


def volume_equipment_cost_per_sample(
    unit_cost: float,
    avg_life_years: float,
    discount_rate: float,
    equipment_volume_litres: float,
    sample_volume_litres: float,
    samples_per_week: int,
    weeks_per_year: float,
    num_units: int = 1,
) -> float:
    """
    Cost per sample for volume-based equipment (refrigerators, incubators).

    The WES availability fraction here is the proportion of equipment volume
    occupied by WES samples, rather than time.

    Logic:
        1. Compute annual equivalent cost.
        2. Total WES volume per week = samples_per_week × sample_volume.
        3. availability = total_wes_volume / equipment_volume.
        4. Weekly cost = annual_equiv_cost / weeks_per_year × availability.
        5. Cost per sample = weekly_cost / samples_per_week.

    Args:
        equipment_volume_litres: Total usable volume of the equipment.
        sample_volume_litres:    Volume occupied per WES sample (aliquot).

    Returns:
        Equipment cost per sample (INR).
    """
    aec = annual_equivalent_cost(unit_cost * num_units, avg_life_years, discount_rate)
    weekly_aec = aec / weeks_per_year

    total_wes_volume = samples_per_week * sample_volume_litres
    availability = total_wes_volume / equipment_volume_litres

    weekly_cost = weekly_aec * availability
    return weekly_cost / samples_per_week if samples_per_week > 0 else 0.0


def misc_capex_cost_per_sample(
    unit_cost: float,
    avg_life_years: float,
    num_units: int,
    samples_per_week: int,
    weeks_per_year: float,
) -> float:
    """
    Cost per sample for miscellaneous equipment using straight-line depreciation.
    No availability fraction — these are allocated fully to WES.

    Annual cost = (unit_cost × num_units) / avg_life_years
    Weekly cost = annual_cost / weeks_per_year
    Cost per sample = weekly_cost / samples_per_week

    Returns:
        Equipment cost per sample (INR).
    """
    annual_cost = (unit_cost * num_units) / avg_life_years
    weekly_cost = annual_cost / weeks_per_year
    return weekly_cost / samples_per_week if samples_per_week > 0 else 0.0


def maintenance_cost_per_sample(
    unit_cost: float,
    avg_life_years: float,
    discount_rate: float,
    availability: float,
    maintenance_rate: float,
    samples_per_week: int,
    weeks_per_year: float,
    num_units: int = 1,
) -> float:
    """
    Annual maintenance cost allocated to WES per sample.

    maintenance_per_year = annual_equivalent_cost × maintenance_rate × availability
    cost_per_sample = maintenance_per_year / (samples_per_week × weeks_per_year)

    Args:
        availability:     WES availability fraction for this equipment.
        maintenance_rate: E.g. 0.10 for 10% of AEC per year.

    Returns:
        Maintenance cost per sample (INR).
    """
    aec = annual_equivalent_cost(unit_cost * num_units, avg_life_years, discount_rate)
    annual_maintenance = aec * maintenance_rate * availability
    annual_samples = samples_per_week * weeks_per_year
    return annual_maintenance / annual_samples if annual_samples > 0 else 0.0
