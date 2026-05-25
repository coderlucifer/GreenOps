"""
GreenOps — Seed Script

Populates the database with realistic demo data for dashboard testing.
Simulates 30 days of AI API usage across multiple models and projects.

Run with: python seed_data.py
"""

import sys
import os
import uuid
import random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, insert_api_calls_batch, set_budget
from services.model_profiles import get_all_profiles, estimate_energy_for_call
from services.carbon_calculator import calculate_impact


def generate_seed_data():
    """Generate 30 days of realistic API call data."""

    profiles = get_all_profiles()
    # Weight some models more heavily (simulating real usage patterns)
    weighted_models = []
    weights = {
        "gpt-4o": 25,
        "gpt-4o-mini": 20,
        "claude-sonnet-4-20250514": 15,
        "gemini-2.5-flash": 15,
        "claude-3-5-haiku-20241022": 10,
        "gpt-3.5-turbo": 5,
        "deepseek-r1": 5,
        "llama-3.1-8b": 3,
        "mistral-small": 2,
    }

    for model_id, weight in weights.items():
        weighted_models.extend([model_id] * weight)

    projects = ["chatbot", "fraud-detection", "document-processing", "research", "default"]
    project_weights = [35, 20, 25, 10, 10]
    regions = ["us_virginia", "us_oregon", "eu_ireland", "global_average", "india"]
    region_weights = [30, 25, 20, 15, 10]

    calls = []
    now = datetime.now(timezone.utc)

    # Generate calls for the last 30 days
    for day_offset in range(30, 0, -1):
        base_date = now - timedelta(days=day_offset)

        # More calls on weekdays, fewer on weekends
        is_weekend = base_date.weekday() >= 5
        daily_calls = random.randint(5, 15) if is_weekend else random.randint(20, 60)

        for _ in range(daily_calls):
            # Random time during the day (business hours weighted)
            hour = random.choices(
                range(24),
                weights=[1,1,1,1,1,2,4,8,10,12,12,10,10,12,12,10,8,6,4,3,2,1,1,1],
            )[0]
            minute = random.randint(0, 59)
            second = random.randint(0, 59)

            timestamp = base_date.replace(
                hour=hour, minute=minute, second=second, microsecond=0
            )

            model_id = random.choice(weighted_models)
            project = random.choices(projects, weights=project_weights)[0]
            region = random.choices(regions, weights=region_weights)[0]

            # Realistic token ranges based on project type
            if project == "chatbot":
                input_tokens = random.randint(50, 500)
                output_tokens = random.randint(100, 800)
            elif project == "fraud-detection":
                input_tokens = random.randint(200, 1000)
                output_tokens = random.randint(50, 200)
            elif project == "document-processing":
                input_tokens = random.randint(500, 4000)
                output_tokens = random.randint(200, 2000)
            elif project == "research":
                input_tokens = random.randint(1000, 8000)
                output_tokens = random.randint(500, 4000)
            else:
                input_tokens = random.randint(100, 1000)
                output_tokens = random.randint(50, 500)

            estimation = estimate_energy_for_call(model_id, input_tokens, output_tokens)
            if estimation is None:
                continue

            impact = calculate_impact(estimation["energy_wh"], region=region)

            latency_base = {"fast": 200, "medium": 800, "slow": 2000}
            from services.model_profiles import get_model_profile
            profile = get_model_profile(model_id)
            base_lat = latency_base.get(profile.latency_tier, 500) if profile else 500
            latency = base_lat + random.randint(-100, 500) + (output_tokens * 0.5)

            calls.append({
                "call_id": str(uuid.uuid4()),
                "timestamp": timestamp.isoformat(),
                "model_id": model_id,
                "provider": estimation["provider"],
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "energy_wh": estimation["energy_wh"],
                "co2_g": impact.co2_g,
                "water_ml": impact.water_ml,
                "cost_usd": estimation["cost_usd"],
                "latency_ms": round(latency, 2),
                "region": region,
                "source": random.choice(["sdk", "proxy", "manual"]),
                "project": project,
                "metadata": {},
            })

    return calls


def main():
    print("🌿 GreenOps — Seeding Database")
    print("=" * 50)

    # Initialize DB (creates demo user)
    init_db()

    # Get the demo user's ID
    from database import get_demo_user_id
    demo_uid = get_demo_user_id()
    if not demo_uid:
        print("❌ Demo user not found! Cannot seed data.")
        return

    print(f"👤 Demo user ID: {demo_uid}")

    # Generate and insert seed data under the demo user
    calls = generate_seed_data()
    count = insert_api_calls_batch(calls, user_id=demo_uid)

    print(f"✅ Inserted {count} API call records for demo user")

    # Summarize
    total_energy = sum(c["energy_wh"] for c in calls)
    total_co2 = sum(c["co2_g"] for c in calls)
    total_water = sum(c["water_ml"] for c in calls)
    total_cost = sum(c["cost_usd"] for c in calls)

    print(f"📊 Total energy:  {total_energy:.2f} Wh")
    print(f"💨 Total CO₂:     {total_co2:.2f} g")
    print(f"💧 Total water:   {total_water:.2f} mL")
    print(f"💰 Total cost:    ${total_cost:.2f}")
    print(f"📈 Unique models: {len(set(c['model_id'] for c in calls))}")
    print(f"📁 Projects:      {len(set(c['project'] for c in calls))}")

    # Set demo user budgets
    print("\n📋 Setting demo user budgets...")
    set_budget(demo_uid, "default", "daily", co2_limit_g=50, energy_limit_wh=500)
    set_budget(demo_uid, "default", "weekly", co2_limit_g=300, energy_limit_wh=3000)
    set_budget(demo_uid, "default", "monthly", co2_limit_g=1000, energy_limit_wh=10000)
    set_budget(demo_uid, "chatbot", "daily", co2_limit_g=100, energy_limit_wh=1000)
    set_budget(demo_uid, "research", "monthly", co2_limit_g=500, energy_limit_wh=5000)
    print("✅ Budgets configured")

    print("\n🚀 Database seeded! Start the server with:")
    print("   python main.py")


if __name__ == "__main__":
    main()
