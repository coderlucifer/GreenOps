from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from GreenOps import run_greenops_engine

app = FastAPI(title="GreenOps API")

# -----------------------------
# CORS (VERY IMPORTANT)
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# REQUEST MODEL
# -----------------------------
class GreenOpsRequest(BaseModel):
    baseline_energy_wh: float
    optimizations: List[str]

# -----------------------------
# API ENDPOINT
# -----------------------------
@app.post("/run")
def run_greenops(req: GreenOpsRequest):
    """
    Run GreenOps optimization engine and return environmental metrics.
    """
    result = run_greenops_engine(
        workload={"baseline_energy_wh": req.baseline_energy_wh},
        enabled_optimizations=req.optimizations
    )
    return result