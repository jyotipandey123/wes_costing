"""
main.py
=======
Entry point for the WES Costing Model.

Usage:
    python main.py                                        # default WES_Inputs.xlsx, 10 sites
    python main.py --sites 40                             # specific site count
    python main.py --scale                                # cost curve across 10-100 sites
    python main.py --sites 20 --usd                       # output in USD
    python main.py --input_sheet ./path/to/WES_Inputs.xlsx
    python main.py --input_sheet "https://docs.google.com/spreadsheets/d/SHEET_ID/..."

Example:
    python main.py --scale
"""

import argparse
import os
import sys
import urllib.error

from calculators.aggregator import compute_cost_summary, compute_scale_curve
from config.loader import load_all_inputs
from utils.sheet_reader import is_url


# ── Formatting helpers ──────────────────────────────────────────────────────

def fmt(value: float, currency: str = "₹") -> str:
    return f"{currency}{value:,.2f}"


def print_divider(char: str = "─", width: int = 60):
    print(char * width)


def _config_kwargs(configs: dict) -> dict:
    return {
        "surveillance": configs["SURVEILLANCE"],
        "constants": configs["CONSTANTS"],
        "hr_config": configs["HR"],
        "equipment_config": configs["EQUIPMENT"],
        "consumable_config": configs["CONSUMABLES"],
        "overhead_config": configs["OVERHEAD"],
        "annualization": configs["ANNUALIZATION"],
    }


def print_summary_report(num_sites: int, use_usd: bool = False, configs: dict = None):
    kwargs = _config_kwargs(configs) if configs else {}
    summary = compute_cost_summary(num_sites=num_sites, **kwargs)
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


def print_scale_curve(configs: dict = None):
    kwargs = _config_kwargs(configs) if configs else {}
    curve = compute_scale_curve(**kwargs)

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
    parser.add_argument("--sites", type=int, default=10,
                        help="Number of surveillance sites")
    parser.add_argument("--scale", action="store_true",
                        help="Print cost curve across site counts")
    parser.add_argument("--usd", action="store_true",
                        help="Show costs in USD")
    parser.add_argument(
        "--input_sheet",
        type=str,
        default="WES_Inputs.xlsx",
        help=(
            "Local file path or Google Sheets URL for input data "
            "(default: WES_Inputs.xlsx in the current directory)"
        ),
    )
    args = parser.parse_args()

    if is_url(args.input_sheet):
        print(f"Loading inputs from: Google Sheets (downloading...)")
    else:
        print(f"Loading inputs from: {args.input_sheet}")

    try:
        configs = load_all_inputs(args.input_sheet)
    except FileNotFoundError:
        print(f"Input file not found: {args.input_sheet} — check the path and try again")
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(
            f"Could not download input sheet from: {args.input_sheet}\n"
            "The sheet must be publicly shared with 'Anyone with the link can view'.\n"
            f"Error: {exc}"
        )
        sys.exit(1)
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)

    try:
        if args.scale:
            print_scale_curve(configs)
        else:
            print_summary_report(num_sites=args.sites, use_usd=args.usd, configs=configs)
    finally:
        if configs.get("_is_temp"):
            try:
                os.unlink(configs["_resolved_path"])
            except OSError:
                pass


if __name__ == "__main__":
    main()
