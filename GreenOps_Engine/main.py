"""
GreenOps — Main Application

FastAPI application with all routes, database initialization, and CORS.
Run with: uvicorn main:app --reload --port 8000
"""

import sys
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the engine directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db
from routes.auth import router as auth_router
from routes.tracking import router as tracking_router
from routes.dashboard import router as dashboard_router
from routes.budget import router as budget_router
from routes.optimizer import router as optimizer_router
from routes.proxy import router as proxy_router
from routes.export import router as export_router
from routes.projects import router as projects_router


# ============================================================
# LIFESPAN — Initialize database on startup
# ============================================================

from services.simulator import start_simulator, stop_simulator

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, cleanup on shutdown."""
    init_db()
    start_simulator(5)  # Start generating demo data every 5 seconds
    print("[GreenOps] 🌿 Engine started and Simulator running")
    yield
    stop_simulator()
    print("[GreenOps] 🛑 Engine stopped")


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="GreenOps API",
    description="AI Sustainability Platform — Track, measure, and reduce the environmental impact of AI workloads",
    version="2.0.0",
    lifespan=lifespan,
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(tracking_router)
app.include_router(dashboard_router)
app.include_router(budget_router)
app.include_router(optimizer_router)
app.include_router(proxy_router)
app.include_router(export_router)
app.include_router(projects_router)


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    """Health check and API overview."""
    return {
        "service": "GreenOps",
        "version": "2.0.0",
        "status": "operational",
        "description": "AI Sustainability Platform",
        "endpoints": {
            "tracking": {
                "POST /api/track": "Track a single AI API call",
                "POST /api/track/batch": "Track multiple calls",
                "GET /api/calls": "List recent tracked calls",
            },
            "dashboard": {
                "GET /api/dashboard": "Aggregated metrics and trends",
                "GET /api/models/usage": "Per-model usage comparison",
                "GET /api/models/catalog": "All known model profiles",
                "POST /api/models/compare": "Compare models for a workload",
                "GET /api/trends/hourly": "Hourly call distribution",
                "GET /api/regions": "Supported regions with emission factors",
            },
            "budget": {
                "POST /api/budget": "Set a carbon budget",
                "GET /api/budget": "Check budget status",
            },
            "optimizer": {
                "POST /run": "Legacy optimization engine",
                "POST /api/simulate": "Enhanced simulation with equivalencies",
            },
            "proxy": {
                "ANY /proxy/openai/{path}": "Transparent OpenAI API proxy",
                "ANY /proxy/anthropic/{path}": "Transparent Anthropic API proxy",
                "ANY /proxy/google/{path}": "Transparent Google Gemini API proxy",
                "GET /proxy/status": "Proxy health and provider info",
            },
        },
    }


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)