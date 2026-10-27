"""Predefined ground-truth data. The evaluation engine trusts ONLY this, never agent claims.

Costs are illustrative INR/m2 figures for the demo; replace with real regional data.
Embodied carbon in kgCO2e per m2 of building area contributed by the material choice.
Resilience is 0-10 (durability against heat, flood, seismic, etc.).
"""

# material -> properties
MATERIALS = {
    "reinforced_concrete": {"cost_per_m2": 24000, "carbon_per_m2": 420, "resilience": 9, "lifespan_years": 75},
    "red_brick":           {"cost_per_m2": 19000, "carbon_per_m2": 300, "resilience": 6, "lifespan_years": 60},
    "fly_ash_brick":       {"cost_per_m2": 17500, "carbon_per_m2": 190, "resilience": 6, "lifespan_years": 60},
    "aac_block":           {"cost_per_m2": 18500, "carbon_per_m2": 160, "resilience": 6, "lifespan_years": 55},
    "bamboo_composite":    {"cost_per_m2": 16000, "carbon_per_m2": 60,  "resilience": 5, "lifespan_years": 40},
    "rammed_earth":        {"cost_per_m2": 15000, "carbon_per_m2": 50,  "resilience": 4, "lifespan_years": 50},
    "steel_frame":         {"cost_per_m2": 28000, "carbon_per_m2": 520, "resilience": 8, "lifespan_years": 70},
    "cross_laminated_timber": {"cost_per_m2": 30000, "carbon_per_m2": 40, "resilience": 6, "lifespan_years": 60},
}

# add-on features -> effect (cost per m2, carbon delta per m2 (negative = saves), resilience delta,
# annual energy saving as fraction of baseline operational energy)
FEATURES = {
    "solar_panels":        {"cost_per_m2": 2500, "carbon_per_m2": 15,  "resilience": 0.5, "energy_saving": 0.35},
    "rainwater_harvesting": {"cost_per_m2": 600,  "carbon_per_m2": 2,   "resilience": 1.0, "energy_saving": 0.02},
    "green_roof":          {"cost_per_m2": 1800, "carbon_per_m2": 5,   "resilience": 0.5, "energy_saving": 0.10},
    "cool_roof_coating":   {"cost_per_m2": 400,  "carbon_per_m2": 1,   "resilience": 0.5, "energy_saving": 0.08},
    "insulation_upgrade":  {"cost_per_m2": 1200, "carbon_per_m2": 20,  "resilience": 0.5, "energy_saving": 0.18},
    "raised_plinth":       {"cost_per_m2": 900,  "carbon_per_m2": 25,  "resilience": 1.5, "energy_saving": 0.0},
    "seismic_bracing":     {"cost_per_m2": 1500, "carbon_per_m2": 30,  "resilience": 1.5, "energy_saving": 0.0},
    "battery_backup":      {"cost_per_m2": 1800, "carbon_per_m2": 25,  "resilience": 1.0, "energy_saving": 0.0},
}

# Baseline operational energy emissions (kgCO2e per m2 per year) with no energy features
BASELINE_OPERATIONAL_CARBON_PER_M2_YEAR = 45
OPERATIONAL_HORIZON_YEARS = 30

# Stress scenarios: multipliers/penalties applied by the engine.
SCENARIOS = {
    "baseline":        {"description": "Normal conditions", "cost_mult": 1.0, "flood": 0, "heat": 0, "quake": 0, "grid_outage": 0},
    "material_price_spike": {"description": "Base material costs +25%", "cost_mult": 1.25, "flood": 0, "heat": 0, "quake": 0, "grid_outage": 0},
    "heatwave":        {"description": "Extreme heat (+6C avg)", "cost_mult": 1.0, "flood": 0, "heat": 1, "quake": 0, "grid_outage": 0},
    "flood":           {"description": "Severe flooding event", "cost_mult": 1.0, "flood": 1, "heat": 0, "quake": 0, "grid_outage": 0},
    "earthquake":      {"description": "Moderate seismic event", "cost_mult": 1.0, "flood": 0, "heat": 0, "quake": 1, "grid_outage": 0},
    "grid_outage":     {"description": "72h power outage", "cost_mult": 1.0, "flood": 0, "heat": 0, "quake": 0, "grid_outage": 1},
}

# Default design problem for the demo
DEFAULT_PROBLEM = {
    "title": "Flood-ready community health centre | Demo scenario",
    "floor_area_m2": 800,
    "budget": 22_000_000,
    "max_carbon_kg_per_m2_lifetime": 2500,
    "min_resilience": 6.0,
    "max_annual_water_m3_per_m2": 1.0,
    "description": (
        "An illustrative 800 m2 community health centre for 40 daily patients in a "
        "hypothetical flood- and heat-exposed region with seasonal flooding, extreme "
        "summer heat and possible 72-hour outages. Prioritise affordable construction, "
        "water efficiency and essential-service continuity. Values are illustrative."
    ),
}
