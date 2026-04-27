"""
calculators/aggregator.py
==========================
Orchestrates all four cost calculators and assembles the final CostSummary.

Call hierarchy:
    compute_cost_summary()
        ├── compute_hr_costs()
        ├── compute_equipment_costs()
        ├── compute_consumable_costs()
        ├── compute_overhead_costs()
        └── assemble → CostSummary

This is the single entry point that downstream scripts and tests should use.
"""

from config.inputs import SURVEILLANCE, CONSTANTS, HR, EQUIPMENT, CONSUMABLES, OVERHEAD, ANNUALIZATION
from models.cost_result import StepCost, CostSummary

from calculators.hr_calculator import compute_hr_costs
from calculators.equipment_calculator import compute_equipment_costs, compute_startup_capex
from calculators.consumable_calculator import compute_consumable_costs
from calculators.overhead_calculator import compute_overhead_costs 


# Canonical step names used to build StepCost objects
STEPS = [
    "sample_collection",
    "sample_processing",
    "pathogen_detection",
    "reporting_disposal",
]

STEP_LABELS = {
    "sample_collection": "Sample Collection & Transportation",
    "sample_processing": "Sample Processing",
    "pathogen_detection": "Pathogen Detection",
    "reporting_disposal": "Reporting & Waste Disposal",
}


def compute_cost_summary(
    num_sites: int = None,
    surveillance: dict = SURVEILLANCE,
    constants: dict = CONSTANTS,
    hr_config: dict = HR,
    equipment_config: dict = EQUIPMENT,
    consumable_config: dict = CONSUMABLES,
    overhead_config: dict = OVERHEAD,
    annualization: dict = ANNUALIZATION,
) -> CostSummary:
    """
    Full cost model: computes cost per sample for a given network configuration.

    Args:
        num_sites: Override the number of surveillance sites (optional).
                   If None, uses the value in surveillance config.
        All other args: configuration dicts from config/inputs.py.

    Returns:
        CostSummary dataclass populated with step costs, overhead, and totals.
    """
    # Allow overriding num_sites without mutating the global config
    if num_sites is not None:
        surveillance = {**surveillance, "num_sites": num_sites}

    samples_per_week = (
        surveillance["num_sites"]
        * surveillance["samples_per_site_per_week"]
    )

    # --- 1. HR costs ---
    hr_by_step = compute_hr_costs(
        samples_per_week=samples_per_week,
        hr_config=hr_config,
        constants=constants,
        surveillance=surveillance,
    )

    # --- 2. Equipment costs ---
    eq_result = compute_equipment_costs(
        samples_per_week=samples_per_week,
        equipment_config=equipment_config,
        constants=constants,
        surveillance=surveillance,
        annualization=annualization,
    )
    eq_by_step = eq_result["by_step"]
    maintenance_total = eq_result["maintenance_total_per_sample"]

    # --- 3. Consumable costs ---
    con_result = compute_consumable_costs(
        samples_per_week=samples_per_week,
        consumable_config=consumable_config,
        constants=constants,
        surveillance=surveillance,
    )
    con_by_step = con_result["by_step"]

    # --- 4. Overhead costs ---
    overhead = compute_overhead_costs(
        samples_per_week=samples_per_week,
        maintenance_per_sample=maintenance_total,
        overhead_config=overhead_config,
        constants=constants,
        hr_config=hr_config,
    )

    # --- 5. Assemble StepCost objects ---
    step_costs = {}
    for step in STEPS:
        step_costs[step] = StepCost(
            step_name=STEP_LABELS[step],
            hr_cost_per_sample=hr_by_step.get(step, 0.0),
            equipment_cost_per_sample=eq_by_step.get(step, 0.0),
            consumable_cost_per_sample=con_by_step.get(step, 0.0),
        )

    # --- 6. Build CostSummary ---
    summary = CostSummary(
        num_sites=surveillance["num_sites"],
        samples_per_week=samples_per_week,
        step_costs=step_costs,
        overhead=overhead,
    )

    # --- 7. Compute aggregate totals ---
    weeks_per_year = constants["weeks_per_year"]
    months_per_year = constants["months_per_year"]
    num_pathogens = surveillance["num_pathogens_detected"]
    dollar_rate = constants["dollar_to_inr"]

    direct_cost_per_sample = summary.step_total_per_sample()
    cost_per_sample = direct_cost_per_sample + overhead.total_per_sample

    summary.cost_per_sample_inr = cost_per_sample
    summary.cost_per_sample_per_pathogen_inr = cost_per_sample / num_pathogens
    summary.cost_per_month_inr = cost_per_sample * samples_per_week * (weeks_per_year / months_per_year)
    summary.cost_per_year_inr = cost_per_sample * samples_per_week * weeks_per_year
    summary.cost_per_sample_usd = cost_per_sample / dollar_rate
    summary.lab_startup_cost_inr = compute_startup_capex(equipment_config)

    return summary


def compute_scale_curve(
    site_range: list = None,
    **kwargs,
) -> list:
    """
    Run the cost model across a range of site counts to produce the scale curve.

    Args:
        site_range: List of site counts to model (e.g. [10, 20, 40, 60, 80, 100]).
        **kwargs:   Forwarded to compute_cost_summary.

    Returns:
        List of dicts: [{"sites": N, "cost_per_sample": X, ...}, ...]
    """
    if site_range is None:
        site_range = [10, 20, 40, 60, 80, 100]

    results = []
    for n_sites in site_range:
        summary = compute_cost_summary(num_sites=n_sites, **kwargs)
        results.append({
            "sites": n_sites,
            "samples_per_week": summary.samples_per_week,
            "cost_per_sample_inr": round(summary.cost_per_sample_inr, 2),
            "cost_per_sample_usd": round(summary.cost_per_sample_usd, 2),
            "cost_per_month_inr": round(summary.cost_per_month_inr, 2),
            "cost_per_year_inr": round(summary.cost_per_year_inr, 2),
            "step_breakdown": {k: round(v, 2) for k, v in summary.step_breakdown().items()},
            "component_breakdown": {k: round(v, 2) for k, v in summary.component_breakdown().items()},
        })
    return results
