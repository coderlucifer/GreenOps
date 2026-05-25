"""
GreenOps Engine - Cloud Workload Environmental Optimization

A pure Python optimization engine that applies configurable optimization layers
to reduce energy consumption, CO2 emissions, and water usage for cloud workloads.
"""

from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


# ============================================================
# ENUMS & DATA MODELS
# ============================================================

class OptimizationLayer(Enum):
    CARBON_AWARE_SCHEDULING = "carbon_aware_scheduling"
    RIGHTSIZING = "rightsizing"
    SPOT_INSTANCE = "spot_instance"
    COOLING_OPTIMIZATION = "cooling_optimization"
    RENEWABLE_ROUTING = "renewable_routing"
    PRUNING = "pruning"
    QUANTIZATION = "quantization"
    DISTILLATION = "distillation"
    CACHING = "caching"
    BATCHING = "batching"
    COMPILATION = "compilation"


@dataclass
class ResourceMetrics:
    energy_wh: float
    co2_g: float
    water_ml: float

    def __sub__(self, other: "ResourceMetrics") -> "ResourceMetrics":
        return ResourceMetrics(
            energy_wh=self.energy_wh - other.energy_wh,
            co2_g=self.co2_g - other.co2_g,
            water_ml=self.water_ml - other.water_ml
        )


@dataclass
class OptimizationResult:
    original_metrics: ResourceMetrics
    optimized_metrics: ResourceMetrics
    savings: ResourceMetrics
    applied_layers: List[str]
    optimization_details: Dict[str, Any]


# CONSTANTS

DEFAULT_GRID_EMISSION_FACTOR = 0.094  # kg CO2 / kWh
DEFAULT_WUE = 1.15                   # L / kWh
ENERGY_FLOOR_WH = 0.05
MAX_TOTAL_REDUCTION = 0.85  # 85%
COST_PER_WH_USD = 0.0025    # Assumed blended GPU API cost ($2.50 per kWh)


# ENVIRONMENTAL CALCULATIONS (BOUNDARY CONVERSIONS ONLY)

def calculate_co2_g(energy_wh: float, ef: float = DEFAULT_GRID_EMISSION_FACTOR) -> float:
    return round((energy_wh / 1000) * ef * 1000, 4)


def calculate_water_ml(energy_wh: float, wue: float = DEFAULT_WUE) -> float:
    return round((energy_wh / 1000) * wue * 1000, 4)


# OPTIMIZATION FUNCTIONS (PURE, STATELESS)

def apply_pruning(e: float) -> float:       return e * 0.85
def apply_quantization(e: float) -> float:  return e * 0.65
def apply_distillation(e: float) -> float:  return e * 0.50
def apply_caching(e: float) -> float:       return e * 0.88
def apply_batching(e: float) -> float:      return e * 0.75
def apply_compilation(e: float) -> float:   return e * 0.92


OPTIMIZATION_ORDER = [
    "pruning",
    "quantization",
    "distillation",
    "caching",
    "batching",
    "compilation",
]

OPTIMIZATION_FUNCS = {
    "pruning": apply_pruning,
    "quantization": apply_quantization,
    "distillation": apply_distillation,
    "caching": apply_caching,
    "batching": apply_batching,
    "compilation": apply_compilation,
}


# DEMO ENGINE (UI)

def run_greenops_engine(
    workload: Dict[str, Any],
    enabled_optimizations: List[str],
    grid_emission_factor: float = DEFAULT_GRID_EMISSION_FACTOR,
    wue: float = DEFAULT_WUE,
) -> Dict[str, Any]:

    if "baseline_energy_wh" not in workload:
        raise ValueError("Missing 'baseline_energy_wh'")

    baseline_energy = workload["baseline_energy_wh"]

    if baseline_energy <= 0:
        raise ValueError("Energy must be positive")

    current_energy = baseline_energy
    applied = []

    for opt in OPTIMIZATION_ORDER:
        if opt in enabled_optimizations:
            current_energy = OPTIMIZATION_FUNCS[opt](current_energy)
            current_energy = max(current_energy, ENERGY_FLOOR_WH)
            applied.append(opt)

    reduction = (baseline_energy - current_energy) / baseline_energy
    if reduction > MAX_TOTAL_REDUCTION:
        raise ValueError("Total reduction exceeds realistic 85% limit")

    result = {
        "baseline_energy_wh": round(baseline_energy, 4),
        "optimized_energy_wh": round(current_energy, 4),
        "reduction_percent": round(reduction * 100, 2),
        "energy_saved_wh": round(baseline_energy - current_energy, 4),
        "baseline_co2_g": calculate_co2_g(baseline_energy, grid_emission_factor),
        "optimized_co2_g": calculate_co2_g(current_energy, grid_emission_factor),
        "baseline_water_ml": calculate_water_ml(baseline_energy, wue),
        "optimized_water_ml": calculate_water_ml(current_energy, wue),
        "baseline_cost_usd": round(baseline_energy * COST_PER_WH_USD, 4),
        "optimized_cost_usd": round(current_energy * COST_PER_WH_USD, 4),
        "applied_optimizations": applied,
    }

    result["co2_saved_g"] = round(
        result["baseline_co2_g"] - result["optimized_co2_g"], 4
    )
    result["water_saved_ml"] = round(
        result["baseline_water_ml"] - result["optimized_water_ml"], 4
    )
    result["cost_saved_usd"] = round(
        result["baseline_cost_usd"] - result["optimized_cost_usd"], 4
    )

    return result


# FULL ENTERPRISE ENGINE (CONCEPTUAL)

def optimize_workload(
    workload: Dict[str, Any],
    enabled_layers: List[OptimizationLayer] = None
) -> OptimizationResult:

    if enabled_layers is None:
        enabled_layers = list(OptimizationLayer)

    baseline_energy = workload.get("baseline_energy_wh", None)
    if baseline_energy is None or baseline_energy <= 0:
        raise ValueError("baseline_energy_wh must be provided and positive")

    base_metrics = ResourceMetrics(
        energy_wh=baseline_energy,
        co2_g=calculate_co2_g(baseline_energy),
        water_ml=calculate_water_ml(baseline_energy),
    )

    demo_result = run_greenops_engine(
        {"baseline_energy_wh": baseline_energy},
        [l.value for l in enabled_layers if l.value in OPTIMIZATION_FUNCS]
    )

    optimized_metrics = ResourceMetrics(
        energy_wh=demo_result["optimized_energy_wh"],
        co2_g=demo_result["optimized_co2_g"],
        water_ml=demo_result["optimized_water_ml"],
    )

    savings = base_metrics - optimized_metrics

    return OptimizationResult(
        original_metrics=base_metrics,
        optimized_metrics=optimized_metrics,
        savings=savings,
        applied_layers=demo_result["applied_optimizations"],
        optimization_details={"engine": "enterprise_wrapper"},
    )


# MINIMAL DEMO

if __name__ == "__main__":
    print("=== GreenOps Demo ===")

    workload = {"baseline_energy_wh": 2000.0}
    enabled = ["quantization", "batching", "compilation"]

    result = run_greenops_engine(workload, enabled)

    for k, v in result.items():
        print(f"{k}: {v}")