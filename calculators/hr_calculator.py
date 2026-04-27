"""
calculators/hr_calculator.py
=============================
Computes HR cost per sample for each process step using the shared-resource model.

Shared-Resource Logic:
    WES does not occupy 100% of any HR person's time. We charge only the
    proportion of time they actually spend on WES each week.

    Steps:
        1. Annual salary → cost per hour (based on total working hours/year).
        2. WES time fraction = weekly WES minutes / total available weekly minutes.
        3. Weekly HR cost = (annual salary / weeks_per_year) × WES fraction.
        4. Cost per sample = weekly HR cost / samples_per_week.
"""

from config.inputs import HR, CONSTANTS, SURVEILLANCE
from models.cost_result import StepCost


def _available_hours_per_week(surveillance: dict = SURVEILLANCE) -> float:
    """Total working hours available per week for one HR person."""
    return surveillance["working_days_per_week"] * surveillance["working_hours_per_day"]


def _hr_cost_per_sample(
    annual_salary: float,
    weekly_time_min: float,
    samples_per_week: int,
    available_hours_per_week: float,
    weeks_per_year: float,
) -> float:
    """
    Generic HR cost per sample calculation.

    Args:
        annual_salary:           INR per year for the HR role.
        weekly_time_min:         Minutes the HR person spends on WES per week.
        samples_per_week:        Total samples processed per week.
        available_hours_per_week: Total available working hours per week.
        weeks_per_year:          Year-to-week conversion factor.

    Returns:
        HR cost per sample (INR).
    """
    available_min_per_week = available_hours_per_week * 60
    wes_fraction = weekly_time_min / available_min_per_week
    weekly_salary_cost = annual_salary / weeks_per_year
    weekly_hr_wes_cost = weekly_salary_cost * wes_fraction
    return weekly_hr_wes_cost / samples_per_week if samples_per_week > 0 else 0.0


def compute_hr_costs(
    samples_per_week: int,
    hr_config: dict = HR,
    constants: dict = CONSTANTS,
    surveillance: dict = SURVEILLANCE,
) -> dict:
    """
    Compute HR cost per sample for all four process steps.

    Args:
        samples_per_week: Number of WES samples processed per week.
        hr_config:        HR configuration from config/inputs.py.
        constants:        Financial constants (weeks_per_year etc.).
        surveillance:     Surveillance config (working days/hours).

    Returns:
        Dict mapping step_name -> hr_cost_per_sample (float).
    """
    available_hrs = _available_hours_per_week(surveillance)
    weeks_per_year = constants["weeks_per_year"]

    results = {}
    for step_key, hr_data in hr_config.items():
        cost = _hr_cost_per_sample(
            annual_salary=hr_data["annual_salary_inr"] * hr_data["num_personnel"],
            weekly_time_min=hr_data["weekly_time_contribution_min"],
            samples_per_week=samples_per_week,
            available_hours_per_week=available_hrs,
            weeks_per_year=weeks_per_year,
        )
        results[step_key] = cost

    return results
