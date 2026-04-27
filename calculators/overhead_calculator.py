"""
calculators/overhead_calculator.py
====================================
Computes overhead cost per sample.

Overhead costs are monthly fixed costs (utility, lab management, maintenance)
that are divided by the number of samples processed per month to get a
per-sample contribution.

samples_per_month = samples_per_week × (weeks_per_year / months_per_year)
"""

from config.inputs import OVERHEAD, CONSTANTS, HR
from models.cost_result import OverheadCost


def compute_overhead_costs(
    samples_per_week: int,
    maintenance_per_sample: float,
    overhead_config: dict = OVERHEAD,
    constants: dict = CONSTANTS,
    hr_config: dict = HR,
) -> OverheadCost:
    """
    Compute overhead cost per sample.

    Args:
        samples_per_week:      WES samples processed per week.
        maintenance_per_sample: Equipment maintenance cost per sample (from
                                equipment_calculator — passed in to avoid
                                re-computing AEC here).
        overhead_config:       Monthly overhead cost inputs.
        constants:             Financial constants.
        hr_config:             HR config (for training cost calculation).

    Returns:
        OverheadCost dataclass.
    """
    weeks_per_year = constants["weeks_per_year"]
    months_per_year = constants["months_per_year"]
    samples_per_month = samples_per_week * (weeks_per_year / months_per_year)

    if samples_per_month == 0:
        return OverheadCost()

    # 1. Utility + infrastructure (electricity, water, internet, lab rent)
    monthly_utility = (
        overhead_config["electricity_per_month_inr"]
        + overhead_config["water_per_month_inr"]
        + overhead_config["internet_per_month_inr"]
        + overhead_config["lab_space_rent_per_month_inr"]
    )
    utility_per_sample = monthly_utility / samples_per_month

    # 2. Lab management cost (fixed monthly overhead)
    lab_mgmt_per_sample = overhead_config["lab_management_per_month_inr"] / samples_per_month

    # 3. HR training (annual, divided across annual samples)
    num_personnel = sum(h["num_personnel"] for h in hr_config.values())
    annual_training = (
        overhead_config["hr_training_per_year_per_person_inr"] * num_personnel
        + overhead_config["cloud_storage_per_year_inr"]
    )
    annual_samples = samples_per_week * weeks_per_year
    hr_training_per_sample = annual_training / annual_samples if annual_samples > 0 else 0.0

    return OverheadCost(
        utility_per_sample=utility_per_sample,
        lab_management_per_sample=lab_mgmt_per_sample,
        maintenance_per_sample=maintenance_per_sample,
        hr_training_per_sample=hr_training_per_sample,
    )
