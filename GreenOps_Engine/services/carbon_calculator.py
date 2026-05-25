"""
GreenOps — Carbon Calculator Service

Centralized environmental calculation logic.
All conversion constants and formulas live here.
"""

from dataclasses import dataclass
from typing import Optional


# ============================================================
# CONSTANTS
# ============================================================

# Default grid emission factor — global average (IEA 2024)
# Source: International Energy Agency — CO2 Emissions from Electricity
DEFAULT_GRID_EMISSION_FACTOR_KG_PER_KWH = 0.094

# Default Water Usage Effectiveness — industry average for hyperscale data centers
# Source: Google Environmental Report, Microsoft Sustainability Report
DEFAULT_WUE_L_PER_KWH = 1.15

# Regional grid emission factors (kg CO₂ / kWh)
# Source: IEA, EPA eGRID, European Environment Agency
REGIONAL_EMISSION_FACTORS = {
    "global_average":   0.094,
    "us_average":       0.386,
    "us_virginia":      0.305,   # AWS us-east-1
    "us_oregon":        0.082,   # AWS us-west-2 (lots of hydro)
    "us_california":    0.210,
    "eu_average":       0.231,
    "eu_ireland":       0.296,   # AWS eu-west-1
    "eu_sweden":        0.013,   # Very clean grid (nuclear + hydro)
    "eu_germany":       0.338,
    "eu_france":        0.052,   # Nuclear-heavy
    "uk":               0.207,
    "india":            0.708,   # Coal-heavy grid
    "china":            0.555,
    "japan":            0.457,
    "singapore":        0.408,
    "australia":        0.530,
    "canada":           0.110,   # Hydro-heavy
    "brazil":           0.074,   # Hydro-heavy
    "south_korea":      0.415,
    "uae":              0.380,
}


@dataclass
class EnvironmentalImpact:
    """Environmental impact of an AI operation."""
    energy_wh: float
    co2_g: float
    water_ml: float
    region: str
    grid_emission_factor: float
    wue: float

    def to_dict(self):
        return {
            "energy_wh": round(self.energy_wh, 4),
            "co2_g": round(self.co2_g, 4),
            "water_ml": round(self.water_ml, 4),
            "region": self.region,
        }


# ============================================================
# CALCULATIONS
# ============================================================

def calculate_co2_grams(
    energy_wh: float,
    grid_emission_factor: float = DEFAULT_GRID_EMISSION_FACTOR_KG_PER_KWH,
) -> float:
    """
    Calculate CO₂ emissions in grams.

    Formula: CO₂ (g) = Energy (kWh) × EmissionFactor (kg/kWh) × 1000
    """
    energy_kwh = energy_wh / 1000
    return round(energy_kwh * grid_emission_factor * 1000, 6)


def calculate_water_ml(
    energy_wh: float,
    wue: float = DEFAULT_WUE_L_PER_KWH,
) -> float:
    """
    Calculate water usage in milliliters.

    Formula: Water (mL) = Energy (kWh) × WUE (L/kWh) × 1000
    """
    energy_kwh = energy_wh / 1000
    return round(energy_kwh * wue * 1000, 6)


def calculate_impact(
    energy_wh: float,
    region: str = "global_average",
) -> EnvironmentalImpact:
    """
    Calculate full environmental impact for a given energy consumption.
    """
    ef = REGIONAL_EMISSION_FACTORS.get(region, DEFAULT_GRID_EMISSION_FACTOR_KG_PER_KWH)
    wue = DEFAULT_WUE_L_PER_KWH

    return EnvironmentalImpact(
        energy_wh=energy_wh,
        co2_g=calculate_co2_grams(energy_wh, ef),
        water_ml=calculate_water_ml(energy_wh, wue),
        region=region,
        grid_emission_factor=ef,
        wue=wue,
    )


def get_available_regions():
    """Return all supported regions with their emission factors."""
    return [
        {"region": k, "emission_factor_kg_per_kwh": v}
        for k, v in sorted(REGIONAL_EMISSION_FACTORS.items(), key=lambda x: x[1])
    ]


# ============================================================
# EQUIVALENCY ENGINE — Make numbers tangible
# ============================================================

def get_equivalencies(co2_g: float, energy_wh: float, water_ml: float):
    """
    Convert abstract environmental metrics into relatable equivalencies.
    Makes sustainability data understandable for non-technical stakeholders.
    """
    equivalencies = {}

    # CO₂ equivalencies
    if co2_g > 0:
        # Average car emits ~120g CO₂/km (ICCT 2024)
        km_driven = co2_g / 120
        equivalencies["car_km"] = {
            "value": round(km_driven, 4),
            "label": f"Driving a car {round(km_driven * 1000)} meters" if km_driven < 1
                     else f"Driving a car {round(km_driven, 2)} km",
        }

        # A tree absorbs ~22kg CO₂/year → ~60g/day
        tree_minutes = (co2_g / 60) * 24 * 60
        equivalencies["tree_absorption"] = {
            "value": round(tree_minutes, 2),
            "label": f"A tree needs {round(tree_minutes, 1)} minutes to absorb this",
        }

        # Average human breath = ~0.04g CO₂
        breaths = co2_g / 0.04
        equivalencies["human_breaths"] = {
            "value": round(breaths),
            "label": f"Equivalent to {round(breaths)} human breaths",
        }

    # Energy equivalencies
    if energy_wh > 0:
        # Smartphone battery ~15 Wh
        phone_charges = energy_wh / 15
        equivalencies["phone_charges"] = {
            "value": round(phone_charges, 4),
            "label": f"Charging a smartphone {round(phone_charges * 100)}% of the way"
                     if phone_charges < 1
                     else f"Charging a smartphone {round(phone_charges, 2)} times",
        }

        # LED bulb ~10W → 10 Wh per hour
        led_hours = energy_wh / 10
        equivalencies["led_bulb_hours"] = {
            "value": round(led_hours, 4),
            "label": f"Powering an LED bulb for {round(led_hours * 60, 1)} minutes"
                     if led_hours < 1
                     else f"Powering an LED bulb for {round(led_hours, 2)} hours",
        }

    # Water equivalencies
    if water_ml > 0:
        # Glass of water ~250mL
        glasses = water_ml / 250
        equivalencies["glasses_of_water"] = {
            "value": round(glasses, 4),
            "label": f"About {round(water_ml)} mL — {round(glasses * 100)}% of a glass of water"
                     if glasses < 1
                     else f"About {round(glasses, 1)} glasses of water",
        }

    return equivalencies
