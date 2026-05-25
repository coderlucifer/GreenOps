import httpx
from database import get_budget_status, get_db

async def check_budget_and_alert(user_id: int, project: str):
    """
    Checks if a project has exceeded 90% of its budget.
    If so, and a webhook is configured, it fires an alert.
    """
    if not project:
        project = "default"
        
    budgets = get_budget_status(user_id, project)
    if not budgets:
        return

    # Get webhook URL for project
    webhook_url = None
    with get_db() as conn:
        row = conn.execute("SELECT webhook_url FROM projects WHERE user_id = ? AND name = ?", (user_id, project)).fetchone()
        if row and row["webhook_url"]:
            webhook_url = row["webhook_url"]

    if not webhook_url:
        return

    # Check if any budget is >= 90%
    for b in budgets:
        if b["usage_percent"] >= 90.0:
            payload = {
                "alert": "Carbon Budget Warning",
                "project": project,
                "period": b["period"],
                "co2_used_g": b["co2_used_g"],
                "co2_limit_g": b["co2_limit_g"],
                "usage_percent": b["usage_percent"]
            }
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(webhook_url, json=payload, timeout=5.0)
                    print(f"[GreenOps] Webhook alert fired for project '{project}' ({b['usage_percent']}%)")
            except Exception as e:
                print(f"[GreenOps] Failed to send webhook to {webhook_url}: {e}")
            break # Only fire one alert per project check
