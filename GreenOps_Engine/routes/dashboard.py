"""
GreenOps — Dashboard Routes

GET /api/dashboard    — Aggregated metrics, trends, and breakdowns
GET /api/models       — Per-model usage comparison
GET /api/trends       — Daily/hourly distribution data
GET /api/regions      — Available regions with emission factors
"""

from fastapi import APIRouter, Query, Depends
from typing import Optional

from database import (
    get_dashboard_summary,
    get_model_comparison,
    get_hourly_distribution,
)
from services.carbon_calculator import get_equivalencies, get_available_regions
from services.model_profiles import (
    get_all_profiles,
    get_profiles_by_provider,
    estimate_energy_for_call,
)
from models import ModelComparisonRequest
from middleware.auth import get_current_user

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard")
def dashboard(
    project: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=365),
    user=Depends(get_current_user),
):
    """
    Get the main dashboard data for the authenticated user.
    """
    summary = get_dashboard_summary(user_id=user["id"], project=project, days=days)

    totals = summary["totals"]
    equivalencies = get_equivalencies(
        co2_g=totals["total_co2_g"],
        energy_wh=totals["total_energy_wh"],
        water_ml=totals["total_water_ml"],
    )
    summary["equivalencies"] = equivalencies

    return summary


@router.get("/models/usage")
def models_usage():
    """
    Get tracked usage comparison across all models.
    Shows which models have been used, how much energy they consumed, etc.
    """
    return {
        "models": get_model_comparison(),
    }


@router.get("/models/catalog")
def models_catalog(provider: Optional[str] = None):
    """
    Get the full catalog of known AI model profiles with energy estimates.
    Useful for the model comparison UI — shows ALL models, not just used ones.
    """
    if provider:
        profiles = get_profiles_by_provider(provider)
    else:
        profiles = get_all_profiles()

    return {
        "models": [p.to_dict() for p in profiles],
        "count": len(profiles),
    }


@router.post("/models/compare")
def compare_models(req: ModelComparisonRequest):
    """
    Compare all models for a specific workload.
    Returns estimated energy, CO₂, water, and cost for each model
    given the same input/output token count.
    """
    profiles = get_all_profiles()
    comparisons = []

    for profile in profiles:
        estimation = estimate_energy_for_call(
            model_id=profile.model_id,
            input_tokens=req.input_tokens,
            output_tokens=req.output_tokens,
        )

        if estimation:
            from services.carbon_calculator import calculate_impact
            impact = calculate_impact(estimation["energy_wh"], region=req.region)

            comparisons.append({
                "model_id": profile.model_id,
                "provider": profile.provider,
                "display_name": profile.display_name,
                "quality_score": profile.quality_score,
                "latency_tier": profile.latency_tier,
                "energy_wh": estimation["energy_wh"],
                "co2_g": impact.co2_g,
                "water_ml": impact.water_ml,
                "cost_usd": estimation["cost_usd"],
                "tags": profile.tags,
                # Sustainability score: quality per unit of energy
                "sustainability_score": round(
                    profile.quality_score / max(estimation["energy_wh"], 0.0001), 2
                ),
            })

    # Sort by sustainability score (best first)
    comparisons.sort(key=lambda x: x["sustainability_score"], reverse=True)

    return {
        "input_tokens": req.input_tokens,
        "output_tokens": req.output_tokens,
        "region": req.region,
        "models": comparisons,
        "greenest": comparisons[0]["model_id"] if comparisons else None,
        "most_efficient": max(comparisons, key=lambda x: x["sustainability_score"])["model_id"]
                          if comparisons else None,
    }


@router.get("/trends/hourly")
def hourly_trends():
    """Get call distribution by hour of day."""
    return {
        "distribution": get_hourly_distribution(),
    }


@router.get("/regions")
def list_regions():
    """Get all supported regions with emission factors."""
    return {
        "regions": get_available_regions(),
    }
