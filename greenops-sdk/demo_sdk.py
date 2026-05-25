"""
GreenOps SDK — Demo Script

Demonstrates all three tracking methods:
1. Manual logging with greenops.log()
2. @greenops.track decorator
3. Direct tracker API

Then shows the terminal report and syncs to the backend.

Run with: python demo_sdk.py
"""

import sys
import time
import random

sys.stdout.reconfigure(encoding='utf-8')

import greenops

# ============================================================
# CONFIGURE
# ============================================================

greenops.configure(
    server_url="http://localhost:8000",
    project="sdk-demo",
    region="us_oregon",
    verbose=True,
    auto_sync=True,
    sync_batch_size=5,
)

print("=" * 60)
print("  GreenOps SDK Demo")
print("=" * 60)


# ============================================================
# METHOD 1: Manual Logging
# ============================================================

print("\n--- Method 1: Manual Logging ---\n")

# Simulate a chatbot conversation
models = ["gpt-4o", "gpt-4o-mini", "claude-sonnet-4-20250514", "gemini-2.5-flash"]
tasks = [
    ("Summarize this document", 2000, 500),
    ("Write a poem about AI", 100, 300),
    ("Explain quantum computing", 150, 800),
    ("Translate to French", 500, 450),
    ("Code review this PR", 3000, 1200),
    ("Generate test cases", 800, 1500),
    ("Analyze sentiment", 200, 50),
    ("Extract key points", 1500, 400),
]

for task_name, input_t, output_t in tasks:
    model = random.choice(models)
    latency = random.uniform(200, 2000)

    result = greenops.log(
        model,
        input_tokens=input_t,
        output_tokens=output_t,
        latency_ms=latency,
        metadata={"task": task_name},
    )

    time.sleep(0.1)  # Small delay for realism


# ============================================================
# METHOD 2: @track Decorator (simulated)
# ============================================================

print("\n--- Method 2: @track Decorator ---\n")


# Simulate an OpenAI-like response object
class FakeUsage:
    def __init__(self, prompt_tokens, completion_tokens):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens


class FakeResponse:
    def __init__(self, model, prompt_tokens, completion_tokens):
        self.model = model
        self.usage = FakeUsage(prompt_tokens, completion_tokens)
        self.choices = [{"message": {"content": "Hello!"}}]


@greenops.track
def ask_chatbot(prompt):
    """Simulated AI chatbot call."""
    time.sleep(random.uniform(0.1, 0.3))
    return FakeResponse(
        model="gpt-4o",
        prompt_tokens=len(prompt.split()) * 2,
        completion_tokens=random.randint(50, 300),
    )


@greenops.track(project="research")
def research_query(query):
    """Simulated research AI call."""
    time.sleep(random.uniform(0.2, 0.5))
    return FakeResponse(
        model="claude-sonnet-4-20250514",
        prompt_tokens=len(query.split()) * 3,
        completion_tokens=random.randint(200, 800),
    )


# Make some decorated calls
ask_chatbot("What is the weather today?")
ask_chatbot("Tell me a joke about programming")
ask_chatbot("How do I make pasta carbonara?")
research_query("Analyze the environmental impact of large language models on global energy consumption")
research_query("Compare transformer architectures for efficiency")


# ============================================================
# METHOD 3: Direct Tracker API
# ============================================================

print("\n--- Method 3: Direct Tracker ---\n")

tracker = greenops.get_tracker()

# Simulate batch processing
for i in range(5):
    tracker.log_call(
        model="gemini-2.5-flash",
        input_tokens=random.randint(100, 500),
        output_tokens=random.randint(50, 200),
        latency_ms=random.uniform(100, 500),
        project="batch-processing",
        metadata={"batch_id": i},
    )


# ============================================================
# REPORT
# ============================================================

print("\n" + "=" * 60)
print("  Generating Report...")
print("=" * 60)

# Show the beautiful terminal report
greenops.report()

# Show raw stats
print("\n--- Raw Stats ---")
stats = greenops.stats()
print(f"  Total calls:  {stats['total_calls']}")
print(f"  Total tokens: {stats['total_tokens']:,}")
print(f"  Total energy: {stats['total_energy_wh']:.6f} Wh")
print(f"  Total CO2:    {stats['total_co2_g']:.6f} g")
print(f"  Models used:  {', '.join(stats['models_used'])}")

# Sync remaining data to backend
print("\n--- Syncing to Backend ---")
sync_result = greenops.sync()
print(f"  Synced: {sync_result.get('synced', 0)} calls")

print("\n  Demo complete!")
