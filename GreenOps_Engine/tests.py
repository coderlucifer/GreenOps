"""
GreenOps — Backend Tests

Tests for the core engine, services, and API endpoints.
Run with: python -m pytest tests.py -v
"""

import sys
import os
import json
import uuid
import pytest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# TEST: Carbon Calculator
# ============================================================

from services.carbon_calculator import (
    calculate_co2_grams,
    calculate_water_ml,
    calculate_impact,
    get_equivalencies,
    get_available_regions,
    REGIONAL_EMISSION_FACTORS,
)


class TestCarbonCalculator:
    """Tests for the carbon calculator service."""

    def test_co2_calculation_basic(self):
        """1 kWh at default grid factor should produce 94g CO₂."""
        result = calculate_co2_grams(1000)  # 1000 Wh = 1 kWh
        assert abs(result - 94.0) < 0.01

    def test_co2_calculation_zero(self):
        result = calculate_co2_grams(0)
        assert result == 0

    def test_water_calculation_basic(self):
        """1 kWh at default WUE should use 1150 mL."""
        result = calculate_water_ml(1000)
        assert abs(result - 1150.0) < 0.01

    def test_water_calculation_zero(self):
        result = calculate_water_ml(0)
        assert result == 0

    def test_impact_returns_all_fields(self):
        impact = calculate_impact(100)
        assert impact.energy_wh == 100
        assert impact.co2_g > 0
        assert impact.water_ml > 0
        assert impact.region == "global_average"

    def test_impact_regional_variation(self):
        """India (coal-heavy) should produce more CO₂ than Sweden (clean)."""
        india = calculate_impact(1000, region="india")
        sweden = calculate_impact(1000, region="eu_sweden")
        assert india.co2_g > sweden.co2_g * 10  # India is ~50x dirtier

    def test_equivalencies_not_empty(self):
        equivs = get_equivalencies(co2_g=10, energy_wh=100, water_ml=500)
        assert len(equivs) > 0
        assert "car_km" in equivs
        assert "phone_charges" in equivs

    def test_equivalencies_zero_input(self):
        equivs = get_equivalencies(co2_g=0, energy_wh=0, water_ml=0)
        assert len(equivs) == 0

    def test_available_regions(self):
        regions = get_available_regions()
        assert len(regions) >= 15
        # Verify sorted by emission factor
        factors = [r["emission_factor_kg_per_kwh"] for r in regions]
        assert factors == sorted(factors)

    def test_regional_emission_factors_valid(self):
        for region, ef in REGIONAL_EMISSION_FACTORS.items():
            assert ef > 0, f"Region {region} has invalid emission factor"
            assert ef < 2.0, f"Region {region} has unreasonably high emission factor"


# ============================================================
# TEST: Model Profiles
# ============================================================

from services.model_profiles import (
    get_model_profile,
    get_all_profiles,
    get_profiles_by_provider,
    estimate_energy_for_call,
    MODEL_PROFILES,
)


class TestModelProfiles:
    """Tests for the AI model profiles service."""

    def test_all_profiles_loaded(self):
        profiles = get_all_profiles()
        assert len(profiles) >= 15

    def test_exact_model_lookup(self):
        profile = get_model_profile("gpt-4o")
        assert profile is not None
        assert profile.provider == "openai"
        assert profile.quality_score > 0

    def test_fuzzy_model_lookup(self):
        profile = get_model_profile("gpt-4o-2024")
        assert profile is not None

    def test_unknown_model_returns_none(self):
        profile = get_model_profile("nonexistent-model-xyz")
        assert profile is None

    def test_profiles_by_provider(self):
        openai_models = get_profiles_by_provider("openai")
        assert len(openai_models) >= 3
        assert all(m.provider == "openai" for m in openai_models)

    def test_energy_estimation(self):
        result = estimate_energy_for_call("gpt-4o", 1000, 500)
        assert result is not None
        assert result["energy_wh"] > 0
        assert result["co2_g"] > 0
        assert result["water_ml"] > 0

    def test_energy_estimation_unknown_model(self):
        result = estimate_energy_for_call("unknown-model", 1000, 500)
        assert result is None

    def test_model_profiles_have_required_fields(self):
        for model_id, profile in MODEL_PROFILES.items():
            assert profile.model_id == model_id
            assert profile.provider
            assert profile.display_name
            assert profile.energy_per_1k_input_tokens_wh > 0
            assert profile.energy_per_1k_output_tokens_wh > 0
            assert 0 <= profile.quality_score <= 100

    def test_output_energy_higher_than_input(self):
        """Output tokens generally require more energy than input tokens."""
        for profile in get_all_profiles():
            assert profile.energy_per_1k_output_tokens_wh >= profile.energy_per_1k_input_tokens_wh, \
                f"{profile.model_id}: output energy should be >= input energy"


# ============================================================
# TEST: GreenOps Engine (Legacy)
# ============================================================

from GreenOps import run_greenops_engine, ENERGY_FLOOR_WH, MAX_TOTAL_REDUCTION


class TestGreenOpsEngine:
    """Tests for the optimization engine."""

    def test_basic_optimization(self):
        result = run_greenops_engine(
            {"baseline_energy_wh": 1000},
            ["quantization"],
        )
        assert result["optimized_energy_wh"] < 1000
        assert result["reduction_percent"] > 0
        assert result["energy_saved_wh"] > 0

    def test_no_optimizations(self):
        result = run_greenops_engine({"baseline_energy_wh": 1000}, [])
        assert result["optimized_energy_wh"] == 1000
        assert result["reduction_percent"] == 0

    def test_all_balanced_optimizations(self):
        result = run_greenops_engine(
            {"baseline_energy_wh": 1000},
            ["quantization", "caching", "batching", "compilation"],
        )
        assert result["reduction_percent"] > 30
        assert result["reduction_percent"] < 85

    def test_energy_floor_protection(self):
        """Very low energy should not go below the floor."""
        result = run_greenops_engine(
            {"baseline_energy_wh": 0.1},
            ["quantization"],
        )
        assert result["optimized_energy_wh"] >= ENERGY_FLOOR_WH

    def test_missing_baseline_raises(self):
        with pytest.raises(ValueError):
            run_greenops_engine({}, ["quantization"])

    def test_negative_energy_raises(self):
        with pytest.raises(ValueError):
            run_greenops_engine({"baseline_energy_wh": -100}, ["quantization"])

    def test_co2_and_water_calculated(self):
        result = run_greenops_engine(
            {"baseline_energy_wh": 1000},
            ["batching"],
        )
        assert result["baseline_co2_g"] > 0
        assert result["baseline_water_ml"] > 0
        assert result["co2_saved_g"] > 0
        assert result["water_saved_ml"] > 0

    def test_applied_optimizations_tracked(self):
        result = run_greenops_engine(
            {"baseline_energy_wh": 1000},
            ["quantization", "batching"],
        )
        assert "quantization" in result["applied_optimizations"]
        assert "batching" in result["applied_optimizations"]

    def test_optimization_order_deterministic(self):
        """Same inputs should produce same outputs."""
        r1 = run_greenops_engine({"baseline_energy_wh": 1000}, ["batching", "quantization"])
        r2 = run_greenops_engine({"baseline_energy_wh": 1000}, ["quantization", "batching"])
        assert r1["optimized_energy_wh"] == r2["optimized_energy_wh"]


# ============================================================
# TEST: API Endpoints (via FastAPI TestClient)
# ============================================================

from fastapi.testclient import TestClient
from main import app


class TestAPI:
    """Tests for the API endpoints."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.client = TestClient(app)

    def test_root_health_check(self):
        res = self.client.get("/")
        assert res.status_code == 200
        data = res.json()
        assert data["service"] == "GreenOps"
        assert data["status"] == "operational"

    def test_track_call(self):
        res = self.client.post("/api/track", json={
            "call_id": str(uuid.uuid4()),
            "model_id": "gpt-4o",
            "provider": "openai",
            "input_tokens": 500,
            "output_tokens": 200,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["energy_wh"] > 0
        assert data["co2_g"] > 0

    def test_track_unknown_model(self):
        res = self.client.post("/api/track", json={
            "call_id": str(uuid.uuid4()),
            "model_id": "unknown-model-12345",
            "provider": "unknown",
            "input_tokens": 100,
            "output_tokens": 50,
        })
        assert res.status_code == 200
        # Should still track with conservative defaults
        assert res.json()["energy_wh"] > 0

    def test_dashboard(self):
        res = self.client.get("/api/dashboard?days=30")
        assert res.status_code == 200
        data = res.json()
        assert "totals" in data
        assert "models" in data
        assert "daily_trends" in data

    def test_calls_list(self):
        res = self.client.get("/api/calls?limit=5")
        assert res.status_code == 200
        data = res.json()
        assert "calls" in data
        assert "total" in data

    def test_model_catalog(self):
        res = self.client.get("/api/models/catalog")
        assert res.status_code == 200
        data = res.json()
        assert data["count"] >= 15

    def test_model_compare(self):
        res = self.client.post("/api/models/compare", json={
            "input_tokens": 1000,
            "output_tokens": 500,
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data["models"]) >= 15
        assert data["greenest"] is not None

    def test_budget_flow(self):
        # Set a budget
        res = self.client.post("/api/budget", json={
            "project": "test-project",
            "period": "daily",
            "co2_limit_g": 100,
        })
        assert res.status_code == 200

        # Check budget
        res = self.client.get("/api/budget?project=test-project")
        assert res.status_code == 200
        data = res.json()
        assert len(data["budgets"]) > 0

    def test_optimizer_legacy(self):
        res = self.client.post("/run", json={
            "baseline_energy_wh": 1000,
            "optimizations": ["quantization", "batching"],
        })
        assert res.status_code == 200
        data = res.json()
        assert data["reduction_percent"] > 0

    def test_simulator_enhanced(self):
        res = self.client.post("/api/simulate", json={
            "baseline_energy_wh": 1000,
            "optimizations": ["quantization"],
        })
        assert res.status_code == 200
        data = res.json()
        assert "savings_equivalencies" in data

    def test_regions(self):
        res = self.client.get("/api/regions")
        assert res.status_code == 200
        data = res.json()
        assert len(data["regions"]) >= 15

    def test_proxy_status(self):
        res = self.client.get("/proxy/status")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "operational"
        assert "openai" in data["providers"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
