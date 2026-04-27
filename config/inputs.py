"""
config/inputs.py
================
Single source of truth for all WES costing model inputs.

Orange cells in the WES Costing Tool Excel map to values here.
Do NOT put any calculation logic in this file.

Sections:
  1. Surveillance & Network Configuration
  2. Financial & Time Conversion Constants
  3. HR Personnel
  4. Equipment (Major + Miscellaneous)
  5. Consumables (Major + Miscellaneous)
  6. Overhead Costs
  7. Equipment & Annualization Assumptions
"""

# ---------------------------------------------------------------------------
# 1. SURVEILLANCE & NETWORK CONFIGURATION
# ---------------------------------------------------------------------------

SURVEILLANCE = {
    "pathogen": "Respiratory Pathogens (SARS-CoV2 + Influenza + RSV)",
    "num_pathogens_detected": 3,
    "sampling_type": "Grab",
    "samples_per_site_per_week": 1,
    "num_sites": 10,                    # Change to model different network sizes
    "working_days_per_week": 6,
    "working_hours_per_day": 8,

    # Transport assumptions
    "grab_sampling_time_window_min": 240,
    "time_to_collect_grab_sample_min": 10,
    "time_at_each_site_min": 24,        # aquaprobe / measurement time
    "one_way_courier_cost_inr": 1000,
    "vehicle_speed_km_per_min": 0.6667,
    "avg_distance_lab_to_site_km": 20,
    "avg_distance_site_to_site_km": 10,
    "is_lab_in_same_city": True,
    "vehicle_ownership": "Owned",       # "Owned" or "Rental"
    "rental_cost_per_week": 0,

    # Sample volume & aliquot assumptions
    "volume_grab_sample_litres": 1,
    "num_aliquots_per_sample": 3,
    "thermocol_container_volume_litres": 5,
    "num_ice_packs_per_container": 4,
    "num_transport_containers": 2,

    # PCR batch assumptions
    "pcr_wells_per_plate": 96,
    "rtpcr_runs_per_week": 1,
}

# ---------------------------------------------------------------------------
# 2. FINANCIAL & TIME CONVERSION CONSTANTS
# ---------------------------------------------------------------------------

CONSTANTS = {
    "weeks_per_year": 52.1429,
    "months_per_year": 12,
    "dollar_to_inr": 86.76,
    "discount_rate": 0.03,              # Used in equipment annualization
    "equipment_maintenance_rate": 0.10, # 10% of annual equivalent cost/year
}

# ---------------------------------------------------------------------------
# 3. HR PERSONNEL
# Per step: annual salary (INR), weekly time contribution (minutes)
# ---------------------------------------------------------------------------

HR = {
    "sample_collection": {
        "role": "Sample Collection Agent (HR-1)",
        "num_personnel": 1,
        "annual_salary_inr": 420_000,
        "weekly_time_contribution_min": 470,   # total minutes on WES per week
    },
    "sample_processing": {
        "role": "Lab Technician (HR-2)",
        "num_personnel": 1,
        "annual_salary_inr": 600_000,
        "weekly_time_contribution_min": 310,
    },
    "pathogen_detection": {
        "role": "Lab Analyst (HR-3)",
        "num_personnel": 1,
        "annual_salary_inr": 600_000,
        "weekly_time_contribution_min": 150,
    },
    "reporting_disposal": {
        "role": "Lab Analyst (HR-3)",
        "num_personnel": 1,
        "annual_salary_inr": 600_000,
        "weekly_time_contribution_min": 50,
    },
}

# ---------------------------------------------------------------------------
# 4. EQUIPMENT
# Each entry: unit_cost, avg_life_years, num_units,
#             time_per_batch_min, batch_size (samples or volume fraction),
#             capacity_type: "time" | "volume"
# ---------------------------------------------------------------------------

EQUIPMENT = {
    # --- Sample Collection & Transportation ---
    "vehicle": {
        "step": "sample_collection",
        "unit_cost_inr": 300_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 10,
        "time_per_batch_min": 235,
        "runs_per_week": 1,
        "shared_across_pathogens": False,
    },
    "thermocol_container": {
        "step": "sample_collection",
        "unit_cost_inr": 1_500,
        "avg_life_years": 15,
        "num_units": 1,
        "capacity_type": "misc_capex",
        "shared_across_pathogens": False,
    },
    "lab_container": {
        "step": "sample_collection",
        "unit_cost_inr": 1_500,
        "avg_life_years": 15,
        "num_units": 1,
        "capacity_type": "misc_capex",
        "shared_across_pathogens": False,
    },

    # --- Sample Processing ---
    "bead_bath": {
        "step": "sample_processing",
        "unit_cost_inr": 100_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 28,
        "time_per_batch_min": 90,
        "runs_per_week": 1,
        "shared_across_pathogens": True,
    },
    "centrifuge_1": {
        "step": "sample_processing",
        "unit_cost_inr": 600_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 2,               # 6 slots / 3 aliquots per sample
        "time_per_batch_min": 30,
        "runs_per_week": 5,
        "shared_across_pathogens": True,
    },
    "weighing_balance": {
        "step": "sample_processing",
        "unit_cost_inr": 90_000,
        "avg_life_years": 20,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 1,
        "time_per_batch_min": 45,
        "runs_per_week": 10,
        "shared_across_pathogens": True,
    },
    "bsl_cabinet": {
        "step": "sample_processing",
        "unit_cost_inr": 300_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 1,
        "time_per_batch_min": 67,
        "runs_per_week": 10,
        "shared_across_pathogens": True,
    },
    "fridge_2_8c": {
        "step": "sample_processing",
        "unit_cost_inr": 400_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "volume",
        "equipment_volume_litres": 600,
        "sample_volume_litres": 0.12,
        "shared_across_pathogens": True,
    },
    "vortex_mixer": {
        "step": "sample_processing",
        "unit_cost_inr": 60_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 1,
        "time_per_batch_min": 15,
        "runs_per_week": 4.8,
        "shared_across_pathogens": True,
    },
    "refrigerator_minus20": {
        "step": "sample_processing",
        "unit_cost_inr": 96_500,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "volume",
        "equipment_volume_litres": 600,
        "sample_volume_litres": 0.25,
        "shared_across_pathogens": True,
    },
    # Miscellaneous processing equipment (straight-line depreciation)
    "test_tube_stand_1": {
        "step": "sample_processing",
        "unit_cost_inr": 5_000,
        "avg_life_years": 15,
        "num_units": 10,
        "capacity_type": "misc_capex",
    },
    "test_tube_stand_2": {
        "step": "sample_processing",
        "unit_cost_inr": 2_000,
        "avg_life_years": 15,
        "num_units": 19,
        "capacity_type": "misc_capex",
    },
    "micropipette_100ml": {
        "step": "sample_processing",
        "unit_cost_inr": 50_000,
        "avg_life_years": 15,
        "num_units": 1,
        "capacity_type": "misc_capex",
    },
    "pipette_set": {
        "step": "sample_processing",
        "unit_cost_inr": 10_000,
        "avg_life_years": 15,
        "num_units": 3,
        "capacity_type": "misc_capex",
    },
    "beaker_set": {
        "step": "sample_processing",
        "unit_cost_inr": 500,
        "avg_life_years": 15,
        "num_units": 5,
        "capacity_type": "misc_capex",
    },
    "head_band": {
        "step": "sample_processing",
        "unit_cost_inr": 50,
        "avg_life_years": 15,
        "num_units": 1,
        "capacity_type": "misc_capex",
    },
    "micro_tube_vortex": {
        "step": "sample_processing",
        "unit_cost_inr": 36_500,
        "avg_life_years": 15,
        "num_units": 1,
        "capacity_type": "misc_capex",
    },
    "dustbin_processing": {
        "step": "sample_processing",
        "unit_cost_inr": 150,
        "avg_life_years": 15,
        "num_units": 2,
        "capacity_type": "misc_capex",
    },
    "lab_coat": {
        "step": "sample_processing",
        "unit_cost_inr": 350,
        "avg_life_years": 15,
        "num_units": 2,
        "capacity_type": "misc_capex",
    },

    # --- Pathogen Detection ---
    "centrifuge_2": {
        "step": "pathogen_detection",
        "unit_cost_inr": 250_000,
        "avg_life_years": 20,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 1,
        "time_per_batch_min": 30,
        "runs_per_week": 10,
        "shared_across_pathogens": True,
    },
    "rtpcr_machine": {
        "step": "pathogen_detection",
        "unit_cost_inr": 1_400_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 96,
        "time_per_batch_min": 80,
        "runs_per_week": 1,
        "shared_across_pathogens": True,
    },
    "pcr_cabinet": {
        "step": "pathogen_detection",
        "unit_cost_inr": 500_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 1,
        "time_per_batch_min": 15,
        "runs_per_week": 10,
        "shared_across_pathogens": True,
    },
    "freezer_minus80": {
        "step": "pathogen_detection",
        "unit_cost_inr": 800_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "volume",
        "equipment_volume_litres": 700,
        "sample_volume_litres": 0.12,
        "shared_across_pathogens": True,
    },

    # --- Reporting & Disposal ---
    "autoclave": {
        "step": "reporting_disposal",
        "unit_cost_inr": 600_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 40,
        "time_per_batch_min": 60,
        "runs_per_week": 1,
        "shared_across_pathogens": True,
    },
    "computer": {
        "step": "reporting_disposal",
        "unit_cost_inr": 100_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "time",
        "batch_size": 96,
        "time_per_batch_min": 80,
        "runs_per_week": 1,
        "shared_across_pathogens": True,
    },
    "printer": {
        "step": "reporting_disposal",
        "unit_cost_inr": 30_000,
        "avg_life_years": 10,
        "num_units": 1,
        "capacity_type": "misc_capex",
    },
    "dustbin_reporting": {
        "step": "reporting_disposal",
        "unit_cost_inr": 150,
        "avg_life_years": 15,
        "num_units": 1,
        "capacity_type": "misc_capex",
    },
}

# ---------------------------------------------------------------------------
# 5. CONSUMABLES
# Each entry: unit_cost, qty_per_sample, unit_of_measure
# For batch consumables add: batch_size (samples per batch)
# ---------------------------------------------------------------------------

CONSUMABLES = {
    # --- Sample Collection & Transportation ---
    "fuel": {
        "step": "sample_collection",
        "unit_cost_inr": 107,           # per litre
        "qty_per_sample": None,         # Computed dynamically from distance/mileage
        "fuel_consumption_km_per_litre": 25,
        "total_distance_per_week_km": 156.67,
        "unit": "per litre (petrol)",
    },
    "mask_collection": {
        "step": "sample_collection",
        "unit_cost_inr": 5,
        "qty_per_sample": 1,
        "unit": "each",
    },
    "gloves_collection": {
        "step": "sample_collection",
        "unit_cost_inr": 13,
        "qty_per_sample": 1,
        "unit": "1 pair",
    },
    "hdpe_bottle": {
        "step": "sample_collection",
        "unit_cost_inr": 94,
        "qty_per_sample": 1,
        "unit": "per 500ml",
    },
    "ice_pack": {
        "step": "sample_collection",
        "unit_cost_inr": 41.83,
        "qty_per_sample": None,         # Computed: ice_packs_per_container / samples_per_container
        "unit": "per pack",
    },
    "labels": {
        "step": "sample_collection",
        "unit_cost_inr": 0.5,
        "qty_per_sample": 12,
        "unit": "each",
    },
    "marker_collection": {
        "step": "sample_collection",
        "unit_cost_inr": 100,
        "qty_per_sample": 1,
        "unit": "each",
    },

    # --- Sample Processing ---
    "mask_processing_1": {
        "step": "sample_processing",
        "unit_cost_inr": 5,
        "qty_per_sample": 1,
        "unit": "each",
    },
    "gloves_processing_1": {
        "step": "sample_processing",
        "unit_cost_inr": 13,
        "qty_per_sample": 1,
        "unit": "1 pair",
    },
    "centrifuge_tube": {
        "step": "sample_processing",
        "unit_cost_inr": 30,
        "qty_per_sample": 3,
        "unit": "each",
    },
    "peg": {
        "step": "sample_processing",
        "unit_cost_inr": 12.818,        # per gram
        "qty_per_sample": 12,           # grams
        "unit": "per gm",
    },
    "nacl": {
        "step": "sample_processing",
        "unit_cost_inr": 14.45,         # per gram
        "qty_per_sample": 2.7,          # grams
        "unit": "per gm",
    },
    "mask_processing_2": {
        "step": "sample_processing",
        "unit_cost_inr": 5,
        "qty_per_sample": 1,
        "unit": "each",
    },
    "gloves_processing_2": {
        "step": "sample_processing",
        "unit_cost_inr": 13,
        "qty_per_sample": 1,
        "unit": "1 pair",
    },
    "ethanol_96pct": {
        "step": "sample_processing",
        "unit_cost_inr": 3.6,           # per ml
        "qty_per_sample": 0.56,         # ml
        "unit": "per ml",
    },
    "mc_tubes_1_7ml": {
        "step": "sample_processing",
        "unit_cost_inr": 2,
        "qty_per_sample": 3,
        "unit": "per tube",
    },
    "filter_pipette_tips": {
        "step": "sample_processing",
        "unit_cost_inr": 10,
        "qty_per_sample": 3,
        "unit": "per tube",
    },
    "serological_pipettes": {
        "step": "sample_processing",
        "unit_cost_inr": 20,
        "qty_per_sample": 3,
        "unit": "per tube",
    },
    "filter_micro_tips": {
        "step": "sample_processing",
        "unit_cost_inr": 10,
        "qty_per_sample": 3,
        "unit": "per tube",
    },
    "micro_centrifuge_tube_1_5ml": {
        "step": "sample_processing",
        "unit_cost_inr": 10,
        "qty_per_sample": 3,
        "unit": "per tube",
    },
    "test_tube_50ml": {
        "step": "sample_processing",
        "unit_cost_inr": 10,
        "qty_per_sample": 3,
        "unit": "per tube",
    },
    "test_tube_15ml": {
        "step": "sample_processing",
        "unit_cost_inr": 10,
        "qty_per_sample": 3,
        "unit": "per tube",
    },
    "cryo_box": {
        "step": "sample_processing",
        "unit_cost_inr": 85,
        "qty_per_sample": 1,
        "unit": "per box",
    },
    "qiagen_viral_rna_kit": {
        "step": "sample_processing",
        "unit_cost_inr": 100,
        "qty_per_sample": 3,            # 3 reactions per sample (one per aliquot)
        "unit": "reaction",
    },
    "filter_tips_1_20ul": {
        "step": "sample_processing",
        "unit_cost_inr": 3,
        "qty_per_sample": 5,
        "unit": "each",
    },
    "filter_tips_200ul": {
        "step": "sample_processing",
        "unit_cost_inr": 4,
        "qty_per_sample": 5,
        "unit": "each",
    },
    "filter_tips_1000ul": {
        "step": "sample_processing",
        "unit_cost_inr": 5,
        "qty_per_sample": 5,
        "unit": "each",
    },
    "ethanol_70pct_processing": {
        "step": "sample_processing",
        "unit_cost_inr": 0.56,
        "qty_per_sample": 20,           # ml
        "unit": "per ml",
    },
    "bleach_2pct": {
        "step": "sample_processing",
        "unit_cost_inr": 2,
        "qty_per_sample": 10,           # ml
        "unit": "per ml",
    },
    "tissue_roll_processing": {
        "step": "sample_processing",
        "unit_cost_inr": 1,
        "qty_per_sample": 20,
        "unit": "per roll",
    },
    "biosafety_bag_processing": {
        "step": "sample_processing",
        "unit_cost_inr": 2,
        "qty_per_sample": 4,
        "unit": "each bag",
    },

    # --- Pathogen Detection ---
    "pathogen_detection_kit": {
        "step": "pathogen_detection",
        "unit_cost_inr": 157.5,
        "qty_per_sample": 3,            # 3 reactions (one per pathogen)
        "unit": "per reaction",
    },
    "pcr_96well_plate": {
        "step": "pathogen_detection",
        "unit_cost_inr": 270,
        "qty_per_sample": None,         # Batch: 1 plate per 96-well run
        "batch_size": 96,
        "unit": "per well-plate",
    },
    "pcr_tubes_strips": {
        "step": "pathogen_detection",
        "unit_cost_inr": 32,
        "qty_per_sample": None,
        "batch_size": 96,
        "unit": "per PCR tube",
    },
    "plate_sealing_film": {
        "step": "pathogen_detection",
        "unit_cost_inr": 213,
        "qty_per_sample": None,
        "batch_size": 96,
        "unit": "per film",
    },
    "biosafety_bag_detection": {
        "step": "pathogen_detection",
        "unit_cost_inr": 2,
        "qty_per_sample": 2,
        "unit": "each bag",
    },

    # --- Reporting & Disposal ---
    "ethanol_70pct_reporting": {
        "step": "reporting_disposal",
        "unit_cost_inr": 0.56,
        "qty_per_sample": 50,           # ml
        "unit": "per ml",
    },
    "tissue_roll_reporting": {
        "step": "reporting_disposal",
        "unit_cost_inr": 1,
        "qty_per_sample": 20,
        "unit": "per roll",
    },
    "biosafety_bag_reporting": {
        "step": "reporting_disposal",
        "unit_cost_inr": 2,
        "qty_per_sample": 2,
        "unit": "each bag",
    },
    "paper_bundle": {
        "step": "reporting_disposal",
        "unit_cost_inr": 100,
        "qty_per_sample": 1,
        "unit": "each",
    },
    "marker_reporting": {
        "step": "reporting_disposal",
        "unit_cost_inr": 100,
        "qty_per_sample": 1,
        "unit": "each",
    },
    "bleach_reporting": {
        "step": "reporting_disposal",
        "unit_cost_inr": 2,
        "qty_per_sample": 10,
        "unit": "per ml",
    },
}

# ---------------------------------------------------------------------------
# 6. OVERHEAD COSTS (Monthly, INR)
# ---------------------------------------------------------------------------

OVERHEAD = {
    "electricity_per_month_inr": 10_000,
    "water_per_month_inr": 5_000,
    "internet_per_month_inr": 1_000,
    "lab_space_rent_per_month_inr": 50_000,
    "lab_management_per_month_inr": 125_000,
    "hr_training_per_year_per_person_inr": 0,
    "cloud_storage_per_year_inr": 0,
}

# ---------------------------------------------------------------------------
# 7. EQUIPMENT ANNUALIZATION ASSUMPTIONS
# ---------------------------------------------------------------------------

ANNUALIZATION = {
    "default_avg_life_years": 10,
    "discount_rate": 0.03,
    "maintenance_rate": 0.10,
}
