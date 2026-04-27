# WES Costing Model

A modular Python implementation of the Wastewater-based Environmental Surveillance (WES) cost estimation model. Calculates cost per sample for SARS-CoV-2, Influenza A, and RSV surveillance across configurable network sizes in India.

---

## Background

This model replicates the logic of the WES Costing Tool Excel workbook. It estimates total cost per sample by summing four cost components — HR, Equipment (CAPEX), Consumables, and Overhead — across four process steps:

1. **Sample Collection & Transportation**
2. **Sample Processing** (concentration via PEG/NaCl, RNA extraction)
3. **Pathogen Detection** (RT-PCR)
4. **Reporting & Waste Disposal**

The shared-resource model means only the proportion of HR time and equipment usage *attributable to WES* is costed — not the full annual cost of any resource.

---

## Project Structure

```
wes_costing/
│
├── config/
│   ├── __init__.py
│   └── inputs.py           ← All user-editable inputs (orange cells in Excel)
│
├── models/
│   ├── __init__.py
│   └── cost_result.py      ← StepCost, OverheadCost, CostSummary dataclasses
│
├── utils/
│   ├── __init__.py
│   └── finance.py          ← Pure math helpers (annualization, availability, etc.)
│
├── calculators/
│   ├── __init__.py
│   ├── hr_calculator.py          ← HR cost per sample (shared-resource model)
│   ├── equipment_calculator.py   ← CAPEX + maintenance cost per sample
│   ├── consumable_calculator.py  ← Consumable cost per sample
│   ├── overhead_calculator.py    ← Utility + lab management cost per sample
│   └── aggregator.py             ← Orchestrates all calculators → CostSummary
│
├── tests/
│   ├── __init__.py
│   └── test_calculators.py ← 42 unit tests
│
└── main.py                 ← CLI entry point
```

---

## Quickstart

No external dependencies are required. Pure Python 3.8+.

```bash
# Single site count (default: 10 sites)
python main.py

# Specific site count
python main.py --sites 40

# Cost scale curve across 10–100 sites
python main.py --scale

# Output in USD
python main.py --sites 20 --usd
```

### Run tests

```bash
python -m unittest discover -s tests -v
```

---

## How to Change Inputs

All inputs live in **`config/inputs.py`**. Never edit the calculator files to change values — only edit `inputs.py`.

| What to change | Where in inputs.py |
|---|---|
| Number of surveillance sites | `SURVEILLANCE["num_sites"]` |
| Sampling frequency per site | `SURVEILLANCE["samples_per_site_per_week"]` |
| Number of pathogens detected | `SURVEILLANCE["num_pathogens_detected"]` |
| HR salaries | `HR[step]["annual_salary_inr"]` |
| Equipment unit costs | `EQUIPMENT[item]["unit_cost_inr"]` |
| Consumable unit prices | `CONSUMABLES[item]["unit_cost_inr"]` |
| Monthly overhead (rent, electricity) | `OVERHEAD` dict |
| Discount rate / equipment life | `ANNUALIZATION` dict |

---

## Cost Calculation Logic

### HR Cost per Sample

```
cost_per_hour = annual_salary / (weeks_per_year × working_hours_per_week)
wes_fraction  = weekly_wes_minutes / total_available_minutes
weekly_cost   = (annual_salary / weeks_per_year) × wes_fraction
cost_per_sample = weekly_cost / samples_per_week
```

### Equipment CAPEX per Sample (time-based)

```
annualization_factor = [D × (1+D)^N] / [(1+D)^N - 1]    (D=discount rate, N=life)
annual_equiv_cost    = unit_cost × annualization_factor
weekly_aec           = annual_equiv_cost / weeks_per_year
wes_availability     = time_used_per_week / total_available_time
weekly_cost          = weekly_aec × wes_availability
cost_per_sample      = weekly_cost / samples_per_week
```

### Equipment CAPEX per Sample (volume-based, for refrigerators/freezers)

```
wes_availability = (samples_per_week × sample_volume_litres) / equipment_volume_litres
cost_per_sample  = (annual_equiv_cost / weeks_per_year × availability) / samples_per_week
```

### Consumable Cost per Sample

```
# Direct per-sample consumable
cost_per_sample = unit_cost × qty_per_sample

# Batch consumable (e.g. 96-well PCR plate)
cost_per_sample = unit_cost / batch_size

# Fuel (derived from distance and mileage)
weekly_fuel_cost = (total_distance_km / mileage) × fuel_price_per_litre
cost_per_sample  = weekly_fuel_cost / samples_per_week
```

### Overhead Cost per Sample

```
samples_per_month = samples_per_week × (weeks_per_year / 12)
utility_per_sample     = monthly_utility_costs / samples_per_month
lab_mgmt_per_sample    = lab_management_monthly / samples_per_month
maintenance_per_sample = Σ(annual_equiv_cost × maintenance_rate × availability)
                         / (samples_per_week × weeks_per_year)
```

### Final Assembly

```
cost_per_sample = Σ step_costs (HR + Equipment + Consumable)
                + overhead_per_sample

cost_per_month  = cost_per_sample × samples_per_week × (weeks_per_year / 12)
cost_per_year   = cost_per_sample × samples_per_week × weeks_per_year
```

---

## Extending the Model

### Add a new consumable

In `config/inputs.py`, add to `CONSUMABLES`:

```python
"my_new_reagent": {
    "step": "sample_processing",
    "unit_cost_inr": 50.0,
    "qty_per_sample": 2,
    "unit": "each",
},
```

No changes needed in any calculator.

### Add a new equipment item

In `config/inputs.py`, add to `EQUIPMENT` with the appropriate `capacity_type`:
- `"time"` — for batch-processed equipment (centrifuge, PCR machine)
- `"volume"` — for storage equipment (refrigerator, freezer)
- `"misc_capex"` — for small items depreciated straight-line (pipettes, beakers)

### Model a different number of sites

```python
from calculators.aggregator import compute_cost_summary
summary = compute_cost_summary(num_sites=50)
print(summary.cost_per_sample_inr)
```

### Run a custom scale curve

```python
from calculators.aggregator import compute_scale_curve
curve = compute_scale_curve(site_range=[5, 10, 25, 50, 75, 100])
for row in curve:
    print(row["sites"], row["cost_per_sample_inr"])
```

---

## Sample Output (10 sites)

```
════════════════════════════════════════════════════════════
  WES COSTING MODEL — RESULTS
  Sites: 10  |  Samples/week: 10
════════════════════════════════════════════════════════════

  KEY OUTPUTS
────────────────────────────────────────────────────────────
  Cost per sample              ₹6,943.66
  Cost per sample per pathogen ₹2,314.55
  Cost per month               ₹3,01,718.93
  Cost per year                ₹36,20,627.20
  Cost per sample (USD)        $80.03
  Lab startup CAPEX            ₹58,37,700.00

  STEP-WISE COST PER SAMPLE
────────────────────────────────────────────────────────────
  Sample Collection & Transportation       ₹456.41   (6.6%)
  Sample Processing                      ₹1,219.93  (17.6%)
  Pathogen Detection                       ₹564.63   (8.1%)
  Reporting & Waste Disposal               ₹301.53   (4.3%)

  COMPONENT-WISE COST PER SAMPLE
────────────────────────────────────────────────────────────
  HR                                       ₹335.22   (4.8%)
  Equipment (CAPEX)                         ₹93.85   (1.4%)
  Consumables                            ₹2,113.43  (30.4%)
  Overhead                               ₹4,401.17  (63.4%)
```

---

## Key Assumptions

- Shared-resource model: resources are costed proportionally to WES usage
- Batch processes use fixed batch sizes (bead bath = 28 samples, PCR = 96 wells)
- Equipment annualized using capital recovery factor at 3% discount rate
- Equipment maintenance = 10% of annual equivalent cost × WES availability
- Storage equipment availability is volume-fraction based (not time-based)
- Overhead (utility + lab management) is treated as fixed monthly cost and divided across all samples processed in that month
- Default: 6 working days/week, 8 hours/day → 48 available hours/week per resource

---

## Test Coverage

42 unit tests covering:
- Annualization factor math
- WES availability fraction logic
- Time-based and volume-based equipment cost computation
- HR cost proportionality
- Consumable direct / batch / derived quantity patterns
- Overhead scaling with sample volume
- Full aggregator: step totals, component totals, USD conversion, scale curve
