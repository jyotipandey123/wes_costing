"""
tests/test_calculators.py
==========================
Unit tests for each calculator and the aggregator.
Run with:  python -m pytest tests/ -v
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from utils.finance import (
    annualization_factor,
    annual_equivalent_cost,
    wes_availability_fraction,
    time_equipment_cost_per_sample,
    volume_equipment_cost_per_sample,
    misc_capex_cost_per_sample,
)
from calculators.hr_calculator import compute_hr_costs
from calculators.equipment_calculator import compute_equipment_costs, compute_startup_capex
from calculators.consumable_calculator import compute_consumable_costs
from calculators.overhead_calculator import compute_overhead_costs
from calculators.aggregator import compute_cost_summary, compute_scale_curve
from models.cost_result import StepCost, OverheadCost, CostSummary


# ──────────────────────────────────────────────────────────────
# Utils / Finance helpers
# ──────────────────────────────────────────────────────────────

class TestAnnualizationFactor(unittest.TestCase):
    def test_known_value(self):
        """AF for 10-year life, 3% discount ≈ 0.11723."""
        af = annualization_factor(avg_life_years=10, discount_rate=0.03)
        assert abs(af - 0.11723) < 0.0001

    def test_zero_discount_rate_approaches_1_over_n(self):
        """At 0% discount, AF approaches 1/N."""
        # Use near-zero, not exactly 0 (would cause division by zero in formula)
        af = annualization_factor(avg_life_years=10, discount_rate=1e-9)
        assert abs(af - 0.1) < 0.001

    def test_longer_life_lower_factor(self):
        af_10 = annualization_factor(10, 0.05)
        af_20 = annualization_factor(20, 0.05)
        assert af_10 > af_20


class TestWesAvailability(unittest.TestCase):
    def test_full_availability(self):
        """48 hours = 2880 min. If used for 2880 min → fraction = 1.0."""
        fraction = wes_availability_fraction(
            time_used_per_week_min=2880,
            available_hours_per_week=48,
        )
        assert abs(fraction - 1.0) < 1e-9

    def test_half_availability(self):
        fraction = wes_availability_fraction(
            time_used_per_week_min=1440,
            available_hours_per_week=48,
        )
        assert abs(fraction - 0.5) < 1e-9

    def test_proportional(self):
        fraction = wes_availability_fraction(
            time_used_per_week_min=235,
            available_hours_per_week=48,
        )
        expected = 235 / 2880
        assert abs(fraction - expected) < 1e-9


class TestTimeEquipmentCost(unittest.TestCase):
    def test_returns_positive(self):
        cps = time_equipment_cost_per_sample(
            unit_cost=300_000,
            avg_life_years=10,
            discount_rate=0.03,
            batch_size=10,
            time_per_batch_min=235,
            runs_per_week=1,
            samples_per_week=10,
            available_hours_per_week=48,
            weeks_per_year=52.1429,
        )
        assert cps > 0

    def test_more_samples_lower_cost(self):
        """Doubling samples should halve the per-sample cost (linear scaling)."""
        base = time_equipment_cost_per_sample(
            unit_cost=300_000, avg_life_years=10, discount_rate=0.03,
            batch_size=10, time_per_batch_min=235, runs_per_week=1,
            samples_per_week=10, available_hours_per_week=48, weeks_per_year=52.1429,
        )
        double = time_equipment_cost_per_sample(
            unit_cost=300_000, avg_life_years=10, discount_rate=0.03,
            batch_size=10, time_per_batch_min=235, runs_per_week=1,
            samples_per_week=20, available_hours_per_week=48, weeks_per_year=52.1429,
        )
        assert abs(double - base / 2) < 0.01

    def test_zero_samples_returns_zero(self):
        cps = time_equipment_cost_per_sample(
            unit_cost=300_000, avg_life_years=10, discount_rate=0.03,
            batch_size=10, time_per_batch_min=235, runs_per_week=1,
            samples_per_week=0, available_hours_per_week=48, weeks_per_year=52.1429,
        )
        assert cps == 0.0


class TestVolumeEquipmentCost(unittest.TestCase):
    def test_returns_positive(self):
        cps = volume_equipment_cost_per_sample(
            unit_cost=400_000, avg_life_years=10, discount_rate=0.03,
            equipment_volume_litres=600, sample_volume_litres=0.12,
            samples_per_week=10, weeks_per_year=52.1429,
        )
        assert cps > 0

    def test_larger_equipment_lower_cost(self):
        small = volume_equipment_cost_per_sample(
            unit_cost=400_000, avg_life_years=10, discount_rate=0.03,
            equipment_volume_litres=100, sample_volume_litres=0.12,
            samples_per_week=10, weeks_per_year=52.1429,
        )
        large = volume_equipment_cost_per_sample(
            unit_cost=400_000, avg_life_years=10, discount_rate=0.03,
            equipment_volume_litres=600, sample_volume_litres=0.12,
            samples_per_week=10, weeks_per_year=52.1429,
        )
        assert large < small


class TestMiscCapexCost(unittest.TestCase):
    def test_returns_positive(self):
        cps = misc_capex_cost_per_sample(
            unit_cost=10_000, avg_life_years=15,
            num_units=3, samples_per_week=10, weeks_per_year=52.1429,
        )
        assert cps > 0

    def test_proportional_to_num_units(self):
        one = misc_capex_cost_per_sample(10_000, 15, 1, 10, 52.1429)
        three = misc_capex_cost_per_sample(10_000, 15, 3, 10, 52.1429)
        assert abs(three - one * 3) < 0.001


# ──────────────────────────────────────────────────────────────
# HR Calculator
# ──────────────────────────────────────────────────────────────

class TestHRCalculator(unittest.TestCase):
    def test_returns_all_steps(self):
        results = compute_hr_costs(samples_per_week=10)
        assert set(results.keys()) == {
            "sample_collection", "sample_processing",
            "pathogen_detection", "reporting_disposal",
        }

    def test_all_positive(self):
        results = compute_hr_costs(samples_per_week=10)
        for step, cost in results.items():
            assert cost > 0, f"HR cost for {step} should be positive"

    def test_higher_samples_lower_cost(self):
        low = compute_hr_costs(samples_per_week=10)
        high = compute_hr_costs(samples_per_week=100)
        for step in low:
            assert high[step] < low[step]

    def test_reporting_less_than_processing(self):
        """Reporting contributes fewer hours than processing."""
        results = compute_hr_costs(samples_per_week=10)
        assert results["reporting_disposal"] < results["sample_processing"]


# ──────────────────────────────────────────────────────────────
# Equipment Calculator
# ──────────────────────────────────────────────────────────────

class TestEquipmentCalculator(unittest.TestCase):
    def test_result_keys_present(self):
        result = compute_equipment_costs(samples_per_week=10)
        assert "by_item" in result
        assert "by_step" in result
        assert "maintenance_total_per_sample" in result

    def test_all_steps_present(self):
        result = compute_equipment_costs(samples_per_week=10)
        steps = result["by_step"]
        assert "sample_collection" in steps
        assert "sample_processing" in steps
        assert "pathogen_detection" in steps

    def test_maintenance_positive(self):
        result = compute_equipment_costs(samples_per_week=10)
        assert result["maintenance_total_per_sample"] > 0

    def test_rtpcr_machine_in_detection(self):
        result = compute_equipment_costs(samples_per_week=10)
        assert "rtpcr_machine" in result["by_item"]
        assert result["by_item"]["rtpcr_machine"] > 0

    def test_startup_capex_positive(self):
        capex = compute_startup_capex()
        assert capex > 0


# ──────────────────────────────────────────────────────────────
# Consumable Calculator
# ──────────────────────────────────────────────────────────────

class TestConsumableCalculator(unittest.TestCase):
    def test_result_keys_present(self):
        result = compute_consumable_costs(samples_per_week=10)
        assert "by_item" in result
        assert "by_step" in result

    def test_fuel_computed(self):
        result = compute_consumable_costs(samples_per_week=10)
        assert result["by_item"]["fuel"] > 0

    def test_batch_consumable_pcr_plate(self):
        """PCR plate cost per sample = 270 / 96 ≈ 2.8125."""
        result = compute_consumable_costs(samples_per_week=10)
        expected = 270 / 96
        assert abs(result["by_item"]["pcr_96well_plate"] - expected) < 0.001

    def test_detection_kit_cost(self):
        """Detection kit: 157.5 × 3 reactions = 472.5 per sample."""
        result = compute_consumable_costs(samples_per_week=10)
        assert abs(result["by_item"]["pathogen_detection_kit"] - 472.5) < 0.001

    def test_all_steps_covered(self):
        result = compute_consumable_costs(samples_per_week=10)
        steps = result["by_step"]
        assert "sample_collection" in steps
        assert "sample_processing" in steps
        assert "pathogen_detection" in steps
        assert "reporting_disposal" in steps


# ──────────────────────────────────────────────────────────────
# Overhead Calculator
# ──────────────────────────────────────────────────────────────

class TestOverheadCalculator(unittest.TestCase):
    def test_utility_positive(self):
        overhead = compute_overhead_costs(samples_per_week=10, maintenance_per_sample=5.0)
        assert overhead.utility_per_sample > 0

    def test_lab_management_positive(self):
        overhead = compute_overhead_costs(samples_per_week=10, maintenance_per_sample=5.0)
        assert overhead.lab_management_per_sample > 0

    def test_maintenance_passed_through(self):
        overhead = compute_overhead_costs(samples_per_week=10, maintenance_per_sample=99.99)
        assert abs(overhead.maintenance_per_sample - 99.99) < 0.001

    def test_higher_samples_lower_overhead_per_sample(self):
        low = compute_overhead_costs(10, 5.0)
        high = compute_overhead_costs(100, 5.0)
        assert high.utility_per_sample < low.utility_per_sample


# ──────────────────────────────────────────────────────────────
# Aggregator / CostSummary
# ──────────────────────────────────────────────────────────────

class TestAggregator(unittest.TestCase):
    def test_returns_cost_summary(self):
        summary = compute_cost_summary(num_sites=10)
        assert isinstance(summary, CostSummary)

    def test_cost_per_sample_positive(self):
        summary = compute_cost_summary(num_sites=10)
        assert summary.cost_per_sample_inr > 0

    def test_cost_per_pathogen_less_than_total(self):
        summary = compute_cost_summary(num_sites=10)
        assert summary.cost_per_sample_per_pathogen_inr < summary.cost_per_sample_inr

    def test_usd_conversion(self):
        from config.inputs import CONSTANTS
        summary = compute_cost_summary(num_sites=10)
        expected_usd = summary.cost_per_sample_inr / CONSTANTS["dollar_to_inr"]
        assert abs(summary.cost_per_sample_usd - expected_usd) < 0.01

    def test_scale_reduces_cost(self):
        """More sites → lower cost per sample (fixed overhead diluted)."""
        low = compute_cost_summary(num_sites=10)
        high = compute_cost_summary(num_sites=100)
        assert high.cost_per_sample_inr < low.cost_per_sample_inr

    def test_all_steps_present(self):
        summary = compute_cost_summary(num_sites=10)
        assert len(summary.step_costs) == 4

    def test_component_breakdown_sums_to_total(self):
        summary = compute_cost_summary(num_sites=10)
        breakdown_sum = sum(summary.component_breakdown().values())
        assert abs(breakdown_sum - summary.cost_per_sample_inr) < 0.01

    def test_samples_per_week(self):
        summary = compute_cost_summary(num_sites=10)
        assert summary.samples_per_week == 10  # 10 sites × 1 sample/site/week


class TestScaleCurve(unittest.TestCase):
    def test_returns_list(self):
        curve = compute_scale_curve([10, 20])
        assert isinstance(curve, list)
        assert len(curve) == 2

    def test_cost_decreasing(self):
        curve = compute_scale_curve([10, 20, 40, 80, 100])
        costs = [r["cost_per_sample_inr"] for r in curve]
        for i in range(len(costs) - 1):
            assert costs[i] > costs[i + 1], "Cost should decrease as scale increases"

    def test_has_required_keys(self):
        curve = compute_scale_curve([10])
        row = curve[0]
        for key in ["sites", "cost_per_sample_inr", "cost_per_month_inr", "step_breakdown"]:
            assert key in row

if __name__ == '__main__':
    unittest.main()
