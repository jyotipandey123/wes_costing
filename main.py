"""
main.py
=======
Entry point for the WES Costing Model.

Usage:
    python main.py                    # Run default config (10 sites)
    python main.py --sites 40         # Run for a specific site count
    python main.py --scale            # Print cost curve across 10–100 sites
    python main.py --sites 20 --usd   # Output in USD

Example:
    python main.py --scale
"""

import argparse
from calculators.aggregator import compute_cost_summary, compute_scale_curve


# ── Formatting helpers ──────────────────────────────────────────────────────

def fmt(value: float, currency: str = "₹") -> str:
    return f"{currency}{value:,.2f}"


def print_divider(char: str = "─", width: int = 60):
    print(char * width)


def print_summary_report(num_sites: int, use_usd: bool = False):
    summary = compute_cost_summary(num_sites=num_sites)
    currency = "$" if use_usd else "₹"
    rate = summary.cost_per_sample_usd if use_usd else summary.cost_per_sample_inr
    denom = summary.cost_per_sample_inr  # always INR for component breakdowns

    print()
    print_divider("═")
    print(f"  WES COSTING MODEL — RESULTS")
    print(f"  Sites: {summary.num_sites}  |  Samples/week: {summary.samples_per_week}")
    print_divider("═")

    # Key outputs
    print("\n  KEY OUTPUTS")
    print_divider()
    print(f"  Cost per sample              {fmt(summary.cost_per_sample_inr)}")
    print(f"  Cost per sample per pathogen {fmt(summary.cost_per_sample_per_pathogen_inr)}")
    print(f"  Cost per month               {fmt(summary.cost_per_month_inr)}")
    print(f"  Cost per year                {fmt(summary.cost_per_year_inr)}")
    print(f"  Cost per sample (USD)        ${summary.cost_per_sample_usd:,.2f}")
    print(f"  Lab startup CAPEX            {fmt(summary.lab_startup_cost_inr)}")

    # Step-wise breakdown
    print("\n  STEP-WISE COST PER SAMPLE")
    print_divider()
    for step_name, cost in summary.step_breakdown().items():
        pct = (cost / summary.cost_per_sample_inr) * 100
        print(f"  {step_name:<42} {fmt(cost):>12}  ({pct:.1f}%)")

    # Component breakdown
    print("\n  COMPONENT-WISE COST PER SAMPLE")
    print_divider()
    for component, cost in summary.component_breakdown().items():
        pct = (cost / summary.cost_per_sample_inr) * 100
        print(f"  {component:<42} {fmt(cost):>12}  ({pct:.1f}%)")

    # Overhead detail
    print("\n  OVERHEAD DETAIL (per sample)")
    print_divider()
    print(f"  Utility & Infrastructure     {fmt(summary.overhead.utility_per_sample)}")
    print(f"  Lab Management               {fmt(summary.overhead.lab_management_per_sample)}")
    print(f"  Equipment Maintenance        {fmt(summary.overhead.maintenance_per_sample)}")
    print(f"  HR Training / Cloud          {fmt(summary.overhead.hr_training_per_sample)}")
    print()


def print_scale_curve():
    curve = compute_scale_curve()

    print()
    print_divider("═")
    print("  WES COST SCALE CURVE")
    print_divider("═")
    print(f"  {'Sites':>6}  {'Samples/wk':>12}  {'Cost/Sample (₹)':>18}  {'Cost/Month (₹)':>18}")
    print_divider()
    for row in curve:
        print(
            f"  {row['sites']:>6}  "
            f"{row['samples_per_week']:>12}  "
            f"{row['cost_per_sample_inr']:>18,.2f}  "
            f"{row['cost_per_month_inr']:>18,.2f}"
        )
    print()


# ── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="WES Costing Model")
    parser.add_argument("--sites", type=int, default=10, help="Number of surveillance sites")
    parser.add_argument("--scale", action="store_true", help="Print cost curve across site counts")
    parser.add_argument("--usd", action="store_true", help="Show costs in USD")
    args = parser.parse_args()

    if args.scale:
        print_scale_curve()
    else:
        print_summary_report(num_sites=args.sites, use_usd=args.usd)


if __name__ == "__main__":
    main()
