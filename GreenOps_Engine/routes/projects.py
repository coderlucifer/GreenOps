"""
GreenOps — Projects Routes

Manage user projects.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from database import get_user_projects, create_project, delete_project, get_db
from middleware.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str

class ProjectWebhook(BaseModel):
    webhook_url: str

@router.get("/", response_model=List[Dict[str, Any]])
def list_projects(user=Depends(get_current_user)):
    """List all projects for the authenticated user (Viewers & Admins)."""
    return get_user_projects(user["id"])

@router.post("/", response_model=Dict[str, Any])
def add_project(req: ProjectCreate, user=Depends(require_admin)):
    """Create a new project (Admin only)."""
    if not req.name or len(req.name) < 2:
        raise HTTPException(status_code=400, detail="Project name must be at least 2 characters.")
    
    project = create_project(user["id"], req.name)
    if not project:
        raise HTTPException(status_code=400, detail="Project already exists.")
    
    return project

@router.delete("/{name}")
def remove_project(name: str, user=Depends(require_admin)):
    """Delete a project (Admin only)."""
    if name == "default":
        raise HTTPException(status_code=400, detail="Cannot delete default project.")
    
    success = delete_project(user["id"], name)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found.")
    
    return {"status": "success", "message": f"Project '{name}' deleted."}

@router.put("/{name}/webhook")
def update_project_webhook(name: str, req: ProjectWebhook, user=Depends(require_admin)):
    """Update a project's webhook URL (Admin only)."""
    with get_db() as conn:
        cursor = conn.execute(
            "UPDATE projects SET webhook_url = ? WHERE user_id = ? AND name = ?",
            (req.webhook_url, user["id"], name)
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Project not found.")
    return {"status": "success", "webhook_url": req.webhook_url}
