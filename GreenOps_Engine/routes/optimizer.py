"""
GreenOps — Optimizer Routes

POST /run             — Legacy optimization engine (backward compatible)
POST /api/simulate    — Enhanced simulation with equivalencies
"""

from fastapi import APIRouter, HTTPException

from models import OptimizerRequest
from GreenOps import run_greenops_engine
from services.carbon_calculator import get_equivalencies

router = APIRouter(tags=["optimizer"])


@router.post("/run")
def run_optimizer(req: OptimizerRequest):
    """
    Run the GreenOps optimization engine.
    Backward compatible with the existing frontend.
    """
    try:
        result = run_greenops_engine(
            workload={"baseline_energy_wh": req.baseline_energy_wh},
            enabled_optimizations=req.optimizations,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/api/simulate")
def simulate_optimization(req: OptimizerRequest):
    """
    Enhanced simulation — same engine but with human-readable equivalencies.
    """
    try:
        result = run_greenops_engine(
            workload={"baseline_energy_wh": req.baseline_energy_wh},
            enabled_optimizations=req.optimizations,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Add equivalencies for savings
    savings_equivalencies = get_equivalencies(
        co2_g=result["co2_saved_g"],
        energy_wh=result["energy_saved_wh"],
        water_ml=result["water_saved_ml"],
    )

    # Add equivalencies for baseline (to show "before")
    baseline_equivalencies = get_equivalencies(
        co2_g=result["baseline_co2_g"],
        energy_wh=result["baseline_energy_wh"],
        water_ml=result["baseline_water_ml"],
    )

    result["savings_equivalencies"] = savings_equivalencies
    result["baseline_equivalencies"] = baseline_equivalencies

    return result
