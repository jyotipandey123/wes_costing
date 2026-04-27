"""
calculators/consumable_calculator.py
======================================
Computes consumable cost per sample for each process step.

Three consumable quantity patterns:
    1. Direct per-sample   — qty_per_sample is given. Cost = unit_cost × qty.
    2. Batch consumable    — qty_per_sample is None; batch_size given.
                             Cost = unit_cost / batch_size.
    3. Dynamically derived — qty_per_sample is None and no batch_size.
                             These are computed from surveillance config
                             (fuel, ice packs).
"""

from config.inputs import CONSUMABLES, CONSTANTS, SURVEILLANCE


def _fuel_cost_per_sample(consumable: dict, samples_per_week: int) -> float:
    """
    Fuel cost is driven by total distance covered per week, not per-sample quantity.
    Cost per sample = (total_distance / mileage × fuel_price) / samples_per_week
    """
    distance = consumable["total_distance_per_week_km"]
    mileage = consumable["fuel_consumption_km_per_litre"]
    fuel_price = consumable["unit_cost_inr"]
    weekly_fuel_cost = (distance / mileage) * fuel_price
    return weekly_fuel_cost / samples_per_week if samples_per_week > 0 else 0.0


def _ice_pack_cost_per_sample(
    consumable: dict,
    surveillance: dict,
) -> float:
    """
    Ice pack cost depends on how many samples fit in one transport container.

    samples_per_container = container_volume / sample_volume
    ice_pack_qty_per_sample = ice_packs_per_container / samples_per_container
    cost_per_sample = qty_per_sample × unit_cost
    """
    container_vol = surveillance["thermocol_container_volume_litres"]
    sample_vol = surveillance["volume_grab_sample_litres"]
    samples_per_container = container_vol / sample_vol

    ice_packs_per_container = surveillance["num_ice_packs_per_container"]
    qty_per_sample = ice_packs_per_container / samples_per_container

    return qty_per_sample * consumable["unit_cost_inr"]


def compute_consumable_costs(
    samples_per_week: int,
    consumable_config: dict = CONSUMABLES,
    constants: dict = CONSTANTS,
    surveillance: dict = SURVEILLANCE,
) -> dict:
    """
    Compute consumable cost per sample for all items.

    Returns:
        Dict with:
            "by_item" -> {consumable_key: cost_per_sample}
            "by_step" -> {step_name: total_consumable_cost_per_sample}
    """
    by_item = {}
    by_step = {}

    for con_key, con in consumable_config.items():
        step = con["step"]
        unit_cost = con["unit_cost_inr"]
        qty = con.get("qty_per_sample")
        batch_size = con.get("batch_size")

        # Determine cost per sample based on quantity pattern
        if con_key == "fuel":
            cps = _fuel_cost_per_sample(con, samples_per_week)

        elif con_key == "ice_pack":
            cps = _ice_pack_cost_per_sample(con, surveillance)

        elif qty is not None:
            # Simple direct per-sample consumable
            cps = unit_cost * qty

        elif batch_size is not None:
            # Batch consumable: one unit shared across a batch of samples
            # e.g. one 96-well plate per 96-sample batch
            cps = unit_cost / batch_size

        else:
            # Fallback: zero (should not reach here with complete config)
            cps = 0.0

        by_item[con_key] = cps
        by_step[step] = by_step.get(step, 0.0) + cps

    return {
        "by_item": by_item,
        "by_step": by_step,
    }
