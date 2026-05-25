import urllib.request, json, sys

sys.stdout.reconfigure(encoding='utf-8')

# Test dashboard
r = urllib.request.urlopen('http://localhost:8000/api/dashboard?days=30')
data = json.loads(r.read())
print("=== DASHBOARD ===")
print(json.dumps(data['totals'], indent=2))
print(f"\nModels tracked: {len(data['models'])}")
for m in data['models']:
    print(f"  {m['model_id']}: {m['call_count']} calls, {m['total_energy_wh']:.4f} Wh")
print(f"\nTrend days: {len(data['daily_trends'])}")
print(f"Sources: {data['sources']}")

# Test model comparison
req = urllib.request.Request(
    'http://localhost:8000/api/models/compare',
    data=json.dumps({"input_tokens": 1000, "output_tokens": 500}).encode(),
    headers={"Content-Type": "application/json"},
)
r = urllib.request.urlopen(req)
comp = json.loads(r.read())
print(f"\n=== MODEL COMPARISON (1000 in, 500 out) ===")
print(f"Greenest model: {comp['greenest']}")
for m in comp['models'][:5]:
    print(f"  {m['display_name']}: {m['energy_wh']:.6f} Wh, {m['co2_g']:.6f}g CO2, ${m['cost_usd']:.4f}")

# Test budget
r = urllib.request.urlopen('http://localhost:8000/api/budget?project=default')
budgets = json.loads(r.read())
print(f"\n=== BUDGETS ===")
for b in budgets['budgets']:
    print(f"  {b['period']}: {b['co2_used_g']:.2f}g / {b['co2_limit_g']}g ({b['usage_percent']}%) [{b['status']}]")

print("\n ALL TESTS PASSED")
