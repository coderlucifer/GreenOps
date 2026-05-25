"""Verify SDK calls were synced to the backend."""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import urllib.request, json

# Check calls from the sdk-demo project
r = urllib.request.urlopen('http://localhost:8000/api/calls?project=sdk-demo&limit=5')
data = json.loads(r.read())
print(f"SDK calls synced to backend: {data['total']} total")
print(f"Showing latest {len(data['calls'])}:")
for c in data['calls']:
    print(f"  {c['model_id']:<30} | {c['total_tokens']:>6} tokens | {c['energy_wh']:.6f} Wh | source={c['source']}")

# Check updated dashboard
r = urllib.request.urlopen('http://localhost:8000/api/dashboard?days=1')
dash = json.loads(r.read())
print(f"\nDashboard (today): {dash['totals']['total_calls']} calls, {dash['totals']['total_energy_wh']:.4f} Wh")
