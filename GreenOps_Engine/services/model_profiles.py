"""
GreenOps — AI Model Energy Profiles

Research-backed energy consumption estimates per AI model.
Sources:
  - IEA energy benchmarks for data centers
  - NVIDIA GPU power documentation (A100, H100 TDP)
  - Published inference benchmarks (tokens/sec per GPU)
  - Estimated Wh per 1K tokens = (GPU_TDP_W / tokens_per_sec) * 1000 / 3600

These are best-effort estimates for simulation purposes.
Actual consumption varies by hardware, batch size, quantization, and provider.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class ModelProfile:
    """Energy and metadata profile for an AI model."""
    model_id: str                    # Canonical ID (e.g., "gpt-4o")
    provider: str                    # Provider name (e.g., "openai")
    display_name: str                # Human-readable name
    family: str                      # Model family (e.g., "GPT-4")
    parameter_count: Optional[str]   # Estimated params (e.g., "~200B")
    energy_per_1k_input_tokens_wh: float   # Wh per 1K input tokens
    energy_per_1k_output_tokens_wh: float  # Wh per 1K output tokens
    cost_per_1k_input_tokens_usd: float    # $ per 1K input tokens
    cost_per_1k_output_tokens_usd: float   # $ per 1K output tokens
    quality_score: int               # Relative quality 0-100
    latency_tier: str                # "fast", "medium", "slow"
    tags: list                       # Categorization tags

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def estimate_energy_wh(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate total energy for a request."""
        input_energy = (input_tokens / 1000) * self.energy_per_1k_input_tokens_wh
        output_energy = (output_tokens / 1000) * self.energy_per_1k_output_tokens_wh
        return round(input_energy + output_energy, 6)

    def estimate_cost_usd(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate total cost for a request."""
        input_cost = (input_tokens / 1000) * self.cost_per_1k_input_tokens_usd
        output_cost = (output_tokens / 1000) * self.cost_per_1k_output_tokens_usd
        return round(input_cost + output_cost, 6)


# ============================================================
# MODEL REGISTRY
# ============================================================

MODEL_PROFILES: Dict[str, ModelProfile] = {}


def _register(profile: ModelProfile):
    MODEL_PROFILES[profile.model_id] = profile
    return profile


# ---- OpenAI Models ----

_register(ModelProfile(
    model_id="gpt-4o",
    provider="openai",
    display_name="GPT-4o",
    family="GPT-4",
    parameter_count="~200B",
    energy_per_1k_input_tokens_wh=0.0040,
    energy_per_1k_output_tokens_wh=0.0120,
    cost_per_1k_input_tokens_usd=0.0025,
    cost_per_1k_output_tokens_usd=0.0100,
    quality_score=95,
    latency_tier="medium",
    tags=["multimodal", "flagship", "reasoning"],
))

_register(ModelProfile(
    model_id="gpt-4o-mini",
    provider="openai",
    display_name="GPT-4o Mini",
    family="GPT-4",
    parameter_count="~8B",
    energy_per_1k_input_tokens_wh=0.0008,
    energy_per_1k_output_tokens_wh=0.0024,
    cost_per_1k_input_tokens_usd=0.000150,
    cost_per_1k_output_tokens_usd=0.000600,
    quality_score=82,
    latency_tier="fast",
    tags=["lightweight", "cost-effective"],
))

_register(ModelProfile(
    model_id="gpt-4-turbo",
    provider="openai",
    display_name="GPT-4 Turbo",
    family="GPT-4",
    parameter_count="~200B",
    energy_per_1k_input_tokens_wh=0.0066,
    energy_per_1k_output_tokens_wh=0.0198,
    cost_per_1k_input_tokens_usd=0.0100,
    cost_per_1k_output_tokens_usd=0.0300,
    quality_score=93,
    latency_tier="medium",
    tags=["legacy", "high-quality"],
))

_register(ModelProfile(
    model_id="gpt-3.5-turbo",
    provider="openai",
    display_name="GPT-3.5 Turbo",
    family="GPT-3.5",
    parameter_count="~20B",
    energy_per_1k_input_tokens_wh=0.0015,
    energy_per_1k_output_tokens_wh=0.0045,
    cost_per_1k_input_tokens_usd=0.0005,
    cost_per_1k_output_tokens_usd=0.0015,
    quality_score=75,
    latency_tier="fast",
    tags=["legacy", "cost-effective"],
))

_register(ModelProfile(
    model_id="o1",
    provider="openai",
    display_name="o1",
    family="o1",
    parameter_count="~200B",
    energy_per_1k_input_tokens_wh=0.0100,
    energy_per_1k_output_tokens_wh=0.0300,
    cost_per_1k_input_tokens_usd=0.0150,
    cost_per_1k_output_tokens_usd=0.0600,
    quality_score=97,
    latency_tier="slow",
    tags=["reasoning", "flagship"],
))

_register(ModelProfile(
    model_id="o3-mini",
    provider="openai",
    display_name="o3-mini",
    family="o3",
    parameter_count="~30B",
    energy_per_1k_input_tokens_wh=0.0025,
    energy_per_1k_output_tokens_wh=0.0075,
    cost_per_1k_input_tokens_usd=0.0011,
    cost_per_1k_output_tokens_usd=0.0044,
    quality_score=89,
    latency_tier="fast",
    tags=["reasoning", "cost-effective"],
))

# ---- Anthropic Models ----

_register(ModelProfile(
    model_id="claude-sonnet-4-20250514",
    provider="anthropic",
    display_name="Claude Sonnet 4",
    family="Claude 4",
    parameter_count="~70B",
    energy_per_1k_input_tokens_wh=0.0035,
    energy_per_1k_output_tokens_wh=0.0105,
    cost_per_1k_input_tokens_usd=0.0030,
    cost_per_1k_output_tokens_usd=0.0150,
    quality_score=94,
    latency_tier="medium",
    tags=["coding", "analysis", "flagship"],
))

_register(ModelProfile(
    model_id="claude-3-5-haiku-20241022",
    provider="anthropic",
    display_name="Claude 3.5 Haiku",
    family="Claude 3.5",
    parameter_count="~20B",
    energy_per_1k_input_tokens_wh=0.0010,
    energy_per_1k_output_tokens_wh=0.0030,
    cost_per_1k_input_tokens_usd=0.0008,
    cost_per_1k_output_tokens_usd=0.0040,
    quality_score=80,
    latency_tier="fast",
    tags=["lightweight", "cost-effective"],
))

_register(ModelProfile(
    model_id="claude-3-opus-20240229",
    provider="anthropic",
    display_name="Claude 3 Opus",
    family="Claude 3",
    parameter_count="~137B",
    energy_per_1k_input_tokens_wh=0.0060,
    energy_per_1k_output_tokens_wh=0.0180,
    cost_per_1k_input_tokens_usd=0.0150,
    cost_per_1k_output_tokens_usd=0.0750,
    quality_score=92,
    latency_tier="slow",
    tags=["legacy", "high-quality"],
))

# ---- Google Models ----

_register(ModelProfile(
    model_id="gemini-2.0-flash",
    provider="google",
    display_name="Gemini 2.0 Flash",
    family="Gemini 2.0",
    parameter_count="~30B",
    energy_per_1k_input_tokens_wh=0.0009,
    energy_per_1k_output_tokens_wh=0.0027,
    cost_per_1k_input_tokens_usd=0.0001,
    cost_per_1k_output_tokens_usd=0.0004,
    quality_score=85,
    latency_tier="fast",
    tags=["multimodal", "cost-effective", "fast"],
))

_register(ModelProfile(
    model_id="gemini-2.5-pro",
    provider="google",
    display_name="Gemini 2.5 Pro",
    family="Gemini 2.5",
    parameter_count="~175B",
    energy_per_1k_input_tokens_wh=0.0055,
    energy_per_1k_output_tokens_wh=0.0165,
    cost_per_1k_input_tokens_usd=0.00125,
    cost_per_1k_output_tokens_usd=0.0050,
    quality_score=96,
    latency_tier="medium",
    tags=["reasoning", "flagship", "multimodal"],
))

_register(ModelProfile(
    model_id="gemini-2.5-flash",
    provider="google",
    display_name="Gemini 2.5 Flash",
    family="Gemini 2.5",
    parameter_count="~30B",
    energy_per_1k_input_tokens_wh=0.0010,
    energy_per_1k_output_tokens_wh=0.0030,
    cost_per_1k_input_tokens_usd=0.000150,
    cost_per_1k_output_tokens_usd=0.000600,
    quality_score=88,
    latency_tier="fast",
    tags=["reasoning", "cost-effective"],
))

# ---- Open Source / Self-Hosted Models ----

_register(ModelProfile(
    model_id="llama-3.1-405b",
    provider="meta",
    display_name="Llama 3.1 405B",
    family="Llama 3.1",
    parameter_count="405B",
    energy_per_1k_input_tokens_wh=0.0080,
    energy_per_1k_output_tokens_wh=0.0240,
    cost_per_1k_input_tokens_usd=0.0000,
    cost_per_1k_output_tokens_usd=0.0000,
    quality_score=91,
    latency_tier="slow",
    tags=["open-source", "self-hosted", "large"],
))

_register(ModelProfile(
    model_id="llama-3.1-70b",
    provider="meta",
    display_name="Llama 3.1 70B",
    family="Llama 3.1",
    parameter_count="70B",
    energy_per_1k_input_tokens_wh=0.0040,
    energy_per_1k_output_tokens_wh=0.0120,
    cost_per_1k_input_tokens_usd=0.0000,
    cost_per_1k_output_tokens_usd=0.0000,
    quality_score=85,
    latency_tier="medium",
    tags=["open-source", "self-hosted"],
))

_register(ModelProfile(
    model_id="llama-3.1-8b",
    provider="meta",
    display_name="Llama 3.1 8B",
    family="Llama 3.1",
    parameter_count="8B",
    energy_per_1k_input_tokens_wh=0.0008,
    energy_per_1k_output_tokens_wh=0.0024,
    cost_per_1k_input_tokens_usd=0.0000,
    cost_per_1k_output_tokens_usd=0.0000,
    quality_score=72,
    latency_tier="fast",
    tags=["open-source", "lightweight", "edge"],
))

_register(ModelProfile(
    model_id="mistral-large",
    provider="mistral",
    display_name="Mistral Large",
    family="Mistral",
    parameter_count="123B",
    energy_per_1k_input_tokens_wh=0.0050,
    energy_per_1k_output_tokens_wh=0.0150,
    cost_per_1k_input_tokens_usd=0.0020,
    cost_per_1k_output_tokens_usd=0.0060,
    quality_score=88,
    latency_tier="medium",
    tags=["european", "enterprise"],
))

_register(ModelProfile(
    model_id="mistral-small",
    provider="mistral",
    display_name="Mistral Small",
    family="Mistral",
    parameter_count="22B",
    energy_per_1k_input_tokens_wh=0.0012,
    energy_per_1k_output_tokens_wh=0.0036,
    cost_per_1k_input_tokens_usd=0.0001,
    cost_per_1k_output_tokens_usd=0.0003,
    quality_score=78,
    latency_tier="fast",
    tags=["european", "cost-effective"],
))

_register(ModelProfile(
    model_id="deepseek-r1",
    provider="deepseek",
    display_name="DeepSeek R1",
    family="DeepSeek",
    parameter_count="671B (MoE)",
    energy_per_1k_input_tokens_wh=0.0045,
    energy_per_1k_output_tokens_wh=0.0135,
    cost_per_1k_input_tokens_usd=0.00055,
    cost_per_1k_output_tokens_usd=0.00219,
    quality_score=90,
    latency_tier="medium",
    tags=["reasoning", "open-source", "moe"],
))


# ============================================================
# LOOKUP FUNCTIONS
# ============================================================

def get_model_profile(model_id: str) -> Optional[ModelProfile]:
    """Get a model profile by exact ID or fuzzy match."""
    # Exact match
    if model_id in MODEL_PROFILES:
        return MODEL_PROFILES[model_id]

    # Fuzzy match — find models whose ID contains the query
    model_lower = model_id.lower()
    for key, profile in MODEL_PROFILES.items():
        if model_lower in key.lower() or key.lower() in model_lower:
            return profile

    return None


def get_all_profiles() -> List[ModelProfile]:
    """Return all registered model profiles."""
    return list(MODEL_PROFILES.values())


def get_profiles_by_provider(provider: str) -> List[ModelProfile]:
    """Return profiles filtered by provider."""
    return [p for p in MODEL_PROFILES.values() if p.provider == provider]


def estimate_energy_for_call(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
) -> Optional[Dict[str, float]]:
    """
    Estimate energy, CO₂, and water for a single API call.
    Returns None if model is not in the registry.
    """
    profile = get_model_profile(model_id)
    if profile is None:
        return None

    energy_wh = profile.estimate_energy_wh(input_tokens, output_tokens)
    cost_usd = profile.estimate_cost_usd(input_tokens, output_tokens)

    # Environmental conversions (same constants as GreenOps engine)
    GRID_EMISSION_FACTOR = 0.094   # kg CO₂ / kWh
    WUE = 1.15                     # L / kWh

    co2_g = round((energy_wh / 1000) * GRID_EMISSION_FACTOR * 1000, 6)
    water_ml = round((energy_wh / 1000) * WUE * 1000, 6)

    return {
        "model_id": model_id,
        "provider": profile.provider,
        "display_name": profile.display_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "energy_wh": energy_wh,
        "co2_g": co2_g,
        "water_ml": water_ml,
        "cost_usd": cost_usd,
    }
