"""
GreenOps — Budget Routes

POST /api/budget      — Set a carbon budget
GET  /api/budget      — Get current budget status
"""

from fastapi import APIRouter, Query, Depends, HTTPException

from models import SetBudgetRequest
from database import set_budget, get_budget_status, create_project
from middleware.auth import get_current_user

router = APIRouter(prefix="/api", tags=["budget"])


@router.post("/budget")
def create_budget(req: SetBudgetRequest, user=Depends(get_current_user)):
    """
    Set or update a carbon budget for a project.
    Supports daily, weekly, and monthly periods.
    """
    if req.period not in ("daily", "weekly", "monthly"):
        raise HTTPException(
            status_code=400,
            detail="Period must be 'daily', 'weekly', or 'monthly'"
        )

    if user.get("is_demo"):
        raise HTTPException(status_code=403, detail="Demo users cannot modify budgets")

    # Auto-create the project if it doesn't exist
    create_project(user["id"], req.project)

    set_budget(
        user_id=user["id"],
        project=req.project,
        period=req.period,
        co2_limit_g=req.co2_limit_g,
        energy_limit_wh=req.energy_limit_wh,
    )

    return {
        "status": "ok",
        "message": f"{req.period.capitalize()} budget set for '{req.project}': {req.co2_limit_g}g CO₂",
        "project": req.project,
        "period": req.period,
        "co2_limit_g": req.co2_limit_g,
    }


@router.get("/budget")
def check_budget(project: str = Query(default="default"), user=Depends(get_current_user)):
    """
    Check current budget status for the authenticated user.
    """
    budgets = get_budget_status(user_id=user["id"], project=project)

    if not budgets:
        return {
            "project": project,
            "budgets": [],
            "message": "No budgets configured. Use POST /api/budget to set one.",
        }

    return {
        "project": project,
        "budgets": budgets,
        "any_exceeded": any(b["status"] == "exceeded" for b in budgets),
        "any_warning": any(b["status"] == "warning" for b in budgets),
    }
