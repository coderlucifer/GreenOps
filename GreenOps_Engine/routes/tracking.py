"""
GreenOps — Tracking Routes

POST /api/track       — Track a single AI API call
POST /api/track/batch — Track multiple calls at once
GET  /api/calls       — Get recent tracked calls
"""

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from datetime import datetime, timezone
from typing import Optional

from models import TrackCallRequest, TrackCallBatchRequest, TrackCallResponse
from services.model_profiles import get_model_profile, estimate_energy_for_call
from services.carbon_calculator import calculate_impact, get_equivalencies
from services.alerts import check_budget_and_alert
from database import insert_api_call, insert_api_calls_batch, get_recent_calls, get_call_count, create_project
from middleware.auth import get_current_user

router = APIRouter(prefix="/api", tags=["tracking"])


@router.post("/track", response_model=TrackCallResponse)
def track_call(req: TrackCallRequest, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    """
    Track a single AI API call.
    Automatically calculates energy, CO₂, and water from the model profile.
    """
    # Auto-create project if it doesn't exist
    if req.project:
        create_project(user["id"], req.project)

    # Look up model profile for energy estimation
    estimation = estimate_energy_for_call(
        model_id=req.model_id,
        input_tokens=req.input_tokens,
        output_tokens=req.output_tokens,
    )

    if estimation is None:
        # Unknown model — use a conservative default estimate
        total_tokens = req.input_tokens + req.output_tokens
        energy_wh = (total_tokens / 1000) * 0.004  # Conservative default
        impact = calculate_impact(energy_wh, region=req.region)
        estimation = {
            "model_id": req.model_id,
            "provider": req.provider,
            "display_name": req.model_id,
            "input_tokens": req.input_tokens,
            "output_tokens": req.output_tokens,
            "total_tokens": total_tokens,
            "energy_wh": energy_wh,
            "co2_g": impact.co2_g,
            "water_ml": impact.water_ml,
            "cost_usd": 0.0,
        }
    else:
        # Re-calculate with region-specific emission factor
        impact = calculate_impact(estimation["energy_wh"], region=req.region)
        estimation["co2_g"] = impact.co2_g
        estimation["water_ml"] = impact.water_ml

    # Build the database record
    call_data = {
        "call_id": req.call_id,
        "timestamp": req.timestamp or datetime.now(timezone.utc).isoformat(),
        "model_id": req.model_id,
        "provider": estimation.get("provider", req.provider),
        "input_tokens": req.input_tokens,
        "output_tokens": req.output_tokens,
        "total_tokens": estimation["total_tokens"],
        "energy_wh": estimation["energy_wh"],
        "co2_g": estimation["co2_g"],
        "water_ml": estimation["water_ml"],
        "cost_usd": estimation["cost_usd"],
        "latency_ms": req.latency_ms,
        "region": req.region,
        "source": req.source,
        "project": req.project,
        "metadata": req.metadata,
        "user_id": user["id"],
    }

    # Insert into database
    try:
        insert_api_call(call_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to track call: {str(e)}")

    # Calculate human-readable equivalencies
    equivalencies = get_equivalencies(
        co2_g=estimation["co2_g"],
        energy_wh=estimation["energy_wh"],
        water_ml=estimation["water_ml"],
    )

    background_tasks.add_task(check_budget_and_alert, user["id"], req.project or "default")

    return TrackCallResponse(
        call_id=req.call_id,
        model_id=req.model_id,
        provider=estimation.get("provider", req.provider),
        input_tokens=req.input_tokens,
        output_tokens=req.output_tokens,
        total_tokens=estimation["total_tokens"],
        energy_wh=round(estimation["energy_wh"], 6),
        co2_g=round(estimation["co2_g"], 6),
        water_ml=round(estimation["water_ml"], 6),
        cost_usd=round(estimation["cost_usd"], 6),
        equivalencies=equivalencies,
    )


@router.post("/track/batch")
def track_calls_batch(req: TrackCallBatchRequest, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    """
    Track multiple AI API calls in one request.
    Useful for SDK batch sync.
    """
    # Auto-create unique projects
    projects = {call.project for call in req.calls if call.project}
    for p in projects:
        create_project(user["id"], p)

    results = []
    for call in req.calls:
        estimation = estimate_energy_for_call(
            model_id=call.model_id,
            input_tokens=call.input_tokens,
            output_tokens=call.output_tokens,
        )

        total_tokens = call.input_tokens + call.output_tokens

        if estimation is None:
            energy_wh = (total_tokens / 1000) * 0.004
            impact = calculate_impact(energy_wh, region=call.region)
            co2_g = impact.co2_g
            water_ml = impact.water_ml
            cost_usd = 0.0
        else:
            energy_wh = estimation["energy_wh"]
            impact = calculate_impact(energy_wh, region=call.region)
            co2_g = impact.co2_g
            water_ml = impact.water_ml
            cost_usd = estimation["cost_usd"]

        results.append({
            "call_id": call.call_id,
            "timestamp": call.timestamp or datetime.now(timezone.utc).isoformat(),
            "model_id": call.model_id,
            "provider": call.provider,
            "input_tokens": call.input_tokens,
            "output_tokens": call.output_tokens,
            "total_tokens": total_tokens,
            "energy_wh": energy_wh,
            "co2_g": co2_g,
            "water_ml": water_ml,
            "cost_usd": cost_usd,
            "latency_ms": call.latency_ms,
            "region": call.region,
            "source": call.source,
            "project": call.project,
            "metadata": call.metadata,
        })

    count = insert_api_calls_batch(results, user_id=user["id"])

    for p in projects:
        background_tasks.add_task(check_budget_and_alert, user["id"], p)

    return {
        "tracked": count,
        "total_energy_wh": round(sum(r["energy_wh"] for r in results), 6),
        "total_co2_g": round(sum(r["co2_g"] for r in results), 6),
    }


@router.get("/calls")
def list_calls(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    project: Optional[str] = None,
    model_id: Optional[str] = None,
    provider: Optional[str] = None,
    user=Depends(get_current_user),
):
    """Get recent tracked API calls for the authenticated user."""
    calls = get_recent_calls(
        limit=limit,
        offset=offset,
        user_id=user["id"],
        project=project,
        model_id=model_id,
        provider=provider,
    )

    total = get_call_count(user_id=user["id"])

    return {
        "calls": calls,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
