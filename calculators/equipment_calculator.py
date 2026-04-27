"""
calculators/equipment_calculator.py
=====================================
Computes equipment (CAPEX) cost per sample for each process step.

Three equipment capacity types are handled:
    1. "time"       — Equipment used in batches for fixed durations (centrifuge,
                      PCR machine, autoclave). Availability = time used / time available.
    2. "volume"     — Equipment stores samples by volume (refrigerators, freezers).
                      Availability = WES volume / equipment total volume.
    3. "misc_capex" — Small equipment allocated 100% to WES via straight-line
                      depreciation (pipettes, beakers, lab coats).

Equipment maintenance cost is also summed here as it follows the same
availability logic as the main CAPEX cost.
"""

from config.inputs import EQUIPMENT, CONSTANTS, SURVEILLANCE, ANNUALIZATION
from utils.finance import (
    time_equipment_cost_per_sample,
    volume_equipment_cost_per_sample,
    misc_capex_cost_per_sample,
    maintenance_cost_per_sample,
    wes_availability_fraction,
    annual_equivalent_cost,
)


def _available_hours_per_week(surveillance: dict = SURVEILLANCE) -> float:
    return surveillance["working_days_per_week"] * surveillance["working_hours_per_day"]


def compute_equipment_costs(
    samples_per_week: int,
    equipment_config: dict = EQUIPMENT,
    constants: dict = CONSTANTS,
    surveillance: dict = SURVEILLANCE,
    annualization: dict = ANNUALIZATION,
) -> dict:
    """
    Compute equipment cost per sample (CAPEX + maintenance) for every item.

    Returns:
        Dict with two keys:
            "by_item"  -> {equipment_key: cost_per_sample}
            "by_step"  -> {step_name: total_equipment_cost_per_sample}
            "maintenance_total" -> total maintenance cost/sample across all equipment
    """
    available_hrs = _available_hours_per_week(surveillance)
    weeks_per_year = constants["weeks_per_year"]
    discount_rate = annualization["discount_rate"]
    maintenance_rate = annualization["maintenance_rate"]

    by_item = {}
    by_step = {}
    total_maintenance = 0.0

    for eq_key, eq in equipment_config.items():
        step = eq["step"]
        unit_cost = eq["unit_cost_inr"]
        life = eq["avg_life_years"]
        num_units = eq.get("num_units", 1)
        cap_type = eq["capacity_type"]

        # --- Compute CAPEX cost per sample ---
        if cap_type == "time":
            capex_cps = time_equipment_cost_per_sample(
                unit_cost=unit_cost,
                avg_life_years=life,
                discount_rate=discount_rate,
                batch_size=eq["batch_size"],
                time_per_batch_min=eq["time_per_batch_min"],
                runs_per_week=eq["runs_per_week"],
                samples_per_week=samples_per_week,
                available_hours_per_week=available_hrs,
                weeks_per_year=weeks_per_year,
                num_units=num_units,
            )
            # Availability for maintenance calculation
            total_time_min = eq["time_per_batch_min"] * eq["runs_per_week"]
            availability = wes_availability_fraction(total_time_min, available_hrs)

        elif cap_type == "volume":
            capex_cps = volume_equipment_cost_per_sample(
                unit_cost=unit_cost,
                avg_life_years=life,
                discount_rate=discount_rate,
                equipment_volume_litres=eq["equipment_volume_litres"],
                sample_volume_litres=eq["sample_volume_litres"],
                samples_per_week=samples_per_week,
                weeks_per_year=weeks_per_year,
                num_units=num_units,
            )
            # Volume fraction as availability proxy
            total_wes_vol = samples_per_week * eq["sample_volume_litres"]
            availability = total_wes_vol / eq["equipment_volume_litres"]

        else:  # misc_capex — no availability fraction, no maintenance
            capex_cps = misc_capex_cost_per_sample(
                unit_cost=unit_cost,
                avg_life_years=life,
                num_units=num_units,
                samples_per_week=samples_per_week,
                weeks_per_year=weeks_per_year,
            )
            by_item[eq_key] = capex_cps
            by_step[step] = by_step.get(step, 0.0) + capex_cps
            continue  # Skip maintenance for misc items

        # --- Compute maintenance cost per sample for major equipment ---
        maint_cps = maintenance_cost_per_sample(
            unit_cost=unit_cost,
            avg_life_years=life,
            discount_rate=discount_rate,
            availability=availability,
            maintenance_rate=maintenance_rate,
            samples_per_week=samples_per_week,
            weeks_per_year=weeks_per_year,
            num_units=num_units,
        )

        total_cps = capex_cps + maint_cps
        total_maintenance += maint_cps

        by_item[eq_key] = total_cps
        by_step[step] = by_step.get(step, 0.0) + total_cps

    return {
        "by_item": by_item,
        "by_step": by_step,
        "maintenance_total_per_sample": total_maintenance,
    }


def compute_startup_capex(
    equipment_config: dict = EQUIPMENT,
) -> float:
    """
    Total one-time capital expenditure required to set up one lab site.

    Returns:
        Sum of (unit_cost × num_units) for all equipment items (INR).
    """
    return sum(
        eq["unit_cost_inr"] * eq.get("num_units", 1)
        for eq in equipment_config.values()
    )
