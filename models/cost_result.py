"""
models/cost_result.py
=====================
Dataclasses that hold structured cost outputs.
No calculation logic lives here — only data containers.
"""

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class StepCost:
    """Holds the three cost sub-components for a single process step."""
    step_name: str
    hr_cost_per_sample: float = 0.0
    equipment_cost_per_sample: float = 0.0
    consumable_cost_per_sample: float = 0.0

    @property
    def total_per_sample(self) -> float:
        return (
            self.hr_cost_per_sample
            + self.equipment_cost_per_sample
            + self.consumable_cost_per_sample
        )


@dataclass
class OverheadCost:
    """Holds overhead costs computed from monthly fixed costs."""
    utility_per_sample: float = 0.0
    lab_management_per_sample: float = 0.0
    maintenance_per_sample: float = 0.0
    hr_training_per_sample: float = 0.0

    @property
    def total_per_sample(self) -> float:
        return (
            self.utility_per_sample
            + self.lab_management_per_sample
            + self.maintenance_per_sample
            + self.hr_training_per_sample
        )


@dataclass
class CostSummary:
    """Top-level output: aggregated cost across all steps + overhead."""
    num_sites: int
    samples_per_week: int

    step_costs: Dict[str, StepCost] = field(default_factory=dict)
    overhead: OverheadCost = field(default_factory=OverheadCost)

    # Computed totals (populated by aggregator)
    cost_per_sample_inr: float = 0.0
    cost_per_sample_per_pathogen_inr: float = 0.0
    cost_per_month_inr: float = 0.0
    cost_per_year_inr: float = 0.0
    cost_per_sample_usd: float = 0.0

    # Startup cost
    lab_startup_cost_inr: float = 0.0

    def step_total_per_sample(self) -> float:
        return sum(s.total_per_sample for s in self.step_costs.values())

    def component_breakdown(self) -> Dict[str, float]:
        """Returns cost per sample grouped by component type (HR, equip, consumable, overhead)."""
        return {
            "HR": sum(s.hr_cost_per_sample for s in self.step_costs.values()),
            "Equipment (CAPEX)": sum(s.equipment_cost_per_sample for s in self.step_costs.values()),
            "Consumables": sum(s.consumable_cost_per_sample for s in self.step_costs.values()),
            "Overhead": self.overhead.total_per_sample,
        }

    def step_breakdown(self) -> Dict[str, float]:
        """Returns cost per sample grouped by process step."""
        return {name: s.total_per_sample for name, s in self.step_costs.items()}
