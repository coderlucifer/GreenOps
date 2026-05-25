"""
GreenOps — Pydantic Models

Request/response models for all API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============================================================
# TRACKING
# ============================================================

class TrackCallRequest(BaseModel):
    """Request to track a single AI API call."""
    call_id: str = Field(..., description="Unique ID for this call (UUID)")
    model_id: str = Field(..., description="Model identifier (e.g., 'gpt-4o')")
    provider: str = Field(default="openai", description="Provider name")
    input_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    latency_ms: Optional[float] = Field(default=None, ge=0)
    region: str = Field(default="global_average")
    source: str = Field(default="sdk", description="'sdk', 'proxy', or 'manual'")
    project: str = Field(default="default")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[str] = Field(default=None, description="ISO 8601 timestamp")


class TrackCallBatchRequest(BaseModel):
    """Request to track multiple AI API calls at once."""
    calls: List[TrackCallRequest]


class TrackCallResponse(BaseModel):
    """Response after tracking a call — includes calculated environmental impact."""
    call_id: str
    model_id: str
    provider: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    energy_wh: float
    co2_g: float
    water_ml: float
    cost_usd: float
    equivalencies: Dict[str, Any] = {}


# ============================================================
# DASHBOARD
# ============================================================

class DashboardRequest(BaseModel):
    """Query params for dashboard data."""
    project: Optional[str] = None
    days: int = Field(default=30, ge=1, le=365)


# ============================================================
# BUDGET
# ============================================================

class SetBudgetRequest(BaseModel):
    """Request to set a carbon budget."""
    project: str = Field(default="default")
    period: str = Field(..., description="'daily', 'weekly', or 'monthly'")
    co2_limit_g: float = Field(..., gt=0, description="CO₂ limit in grams")
    energy_limit_wh: Optional[float] = Field(default=None, gt=0)


# ============================================================
# OPTIMIZER (LEGACY — backward compatible)
# ============================================================

class OptimizerRequest(BaseModel):
    """Request for the optimization engine (existing /run endpoint)."""
    baseline_energy_wh: float = Field(..., gt=0)
    optimizations: List[str]


# ============================================================
# MODELS
# ============================================================

class ModelComparisonRequest(BaseModel):
    """Request for comparing models on a specific task."""
    task: Optional[str] = Field(default=None, description="Task type filter")
    input_tokens: int = Field(default=1000, ge=1, description="Tokens for comparison")
    output_tokens: int = Field(default=500, ge=1)
    region: str = Field(default="global_average")
