# 🌿 GreenOps — AI Sustainability Platform

<div align="center">

**Track, measure, and reduce the environmental impact of your AI workloads.**

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://react.dev)
[![Tests](https://img.shields.io/badge/tests-40%2F40-brightgreen.svg)](#tests)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## The Problem

Every AI API call consumes energy, emits CO₂, and uses water for cooling. A single GPT-4 query uses **10x more energy** than a Google search. With billions of AI calls per day, this invisible cost adds up fast.

**GreenOps makes it visible — and actionable.**

## What GreenOps Does

| Feature | Description |
|---------|-------------|
| 🔍 **Track** | Automatically log every AI call with energy, CO₂, and water metrics |
| 🔐 **Auth** | Full multi-tenant authentication system with secure API key management |
| 📊 **Dashboard** | Premium dark-mode dashboard with real-time charts and trends |
| 🏆 **Compare** | Rank 18 AI models by sustainability — find the greenest option |
| 💰 **Budget** | Set daily/weekly/monthly carbon limits with alerts |
| 🔌 **Proxy** | Transparent API proxy — zero code changes, automatic tracking |
| 📦 **SDK** | `pip install greenops` — track with one line of Python |
| 🎭 **Demo** | Live simulator mode for demonstrations and public previews |

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                     GreenOps Platform                         │
├─────────────┬──────────────┬──────────────┬──────────────────┤
│  React      │  FastAPI     │  Python SDK  │  Carbon Proxy    │
│  Dashboard  │  Backend     │  (pip pkg)   │  (transparent)   │
│             │              │              │                  │
│  • Metrics  │  • REST APIs │  • @track    │  • OpenAI        │
│  • Charts   │  • SQLite DB │  • log()     │  • Anthropic     │
│  • Budget   │  • 20 APIs   │  • report()  │  • Google        │
│  • Compare  │  • 40 tests  │  • sync()    │  • Auto-track    │
└─────────────┴──────────────┴──────────────┴──────────────────┘
```

## Quick Start

### 1. Backend

```bash
cd GreenOps_Engine
pip install -r requirements.txt
python seed_data.py          # Seed with demo data and demo user
python main.py               # Starts on http://localhost:8000
```

### 2. Frontend

```bash
cd GreenOps
npm install
npm run dev                  # Starts on http://localhost:5173
```

Open `http://localhost:5173` in your browser. You can create a new account, or click "Try Demo" to log in as the demo user and watch the live simulator.

### 3. SDK (Optional)

```bash
pip install -e greenops-sdk  # Install the SDK locally

# Then in your Python code:
import greenops
greenops.configure(project="my-app")
greenops.log("gpt-4o", input_tokens=500, output_tokens=200)
greenops.report()
```

### 4. Proxy (Optional)

```python
import openai

# Just change base_url and add your GreenOps API Key
client = openai.OpenAI(
    api_key="sk-...",
    base_url="http://localhost:8000/proxy/openai/v1",
    default_headers={
        "x-api-key": "YOUR_GREENOPS_API_KEY" # Generate in Settings
    }
)

# Every call is now automatically tracked with carbon metrics!
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)
# Check response headers: X-GreenOps-Energy-Wh, X-GreenOps-CO2-G
```

---

## API Endpoints (20+)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/track` | POST | Track a single AI API call |
| `/api/track/batch` | POST | Track multiple calls at once |
| `/api/calls` | GET | List recent tracked calls (paginated) |
| `/api/dashboard` | GET | Aggregated metrics + trends |
| `/api/models/catalog` | GET | All 18 model profiles |
| `/api/models/compare` | POST | Rank models by sustainability |
| `/api/models/usage` | GET | Per-model usage breakdown |
| `/api/budget` | POST/GET | Set and check carbon budgets |
| `/api/simulate` | POST | Run optimization simulation |
| `/api/regions` | GET | 20 supported grid regions |
| `/api/trends/hourly` | GET | Hourly call distribution |
| `/proxy/openai/{path}` | ANY | Transparent OpenAI proxy |
| `/proxy/anthropic/{path}` | ANY | Transparent Anthropic proxy |
| `/proxy/google/{path}` | ANY | Transparent Google proxy |
| `/proxy/status` | GET | Proxy health check |

## Supported AI Models (18)

| Provider | Models |
|----------|--------|
| **OpenAI** | GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5 Turbo, o1, o3-mini, o4-mini |
| **Anthropic** | Claude Sonnet 4, Claude 3.5 Haiku, Claude 3 Opus |
| **Google** | Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 2.0 Flash |
| **Meta** | Llama 3.1 405B, 70B, 8B |
| **Mistral** | Mistral Large, Mistral Small |
| **DeepSeek** | DeepSeek R1 |

## SDK Usage (3 Methods)

```python
import greenops

# Method 1: Manual logging
greenops.log("gpt-4o", input_tokens=500, output_tokens=200)

# Method 2: Decorator (auto-detects OpenAI/Anthropic/Google responses)
@greenops.track
def ask_ai(prompt):
    return client.chat.completions.create(model="gpt-4o", messages=[...])

# Method 3: Drop-in client (zero code changes)
from greenops import OpenAIClient
client = OpenAIClient(api_key="sk-...")
```

## Tests

```bash
cd GreenOps_Engine
python -m pytest tests.py -v
```

```
40 passed in 0.73s
├── TestCarbonCalculator (10 tests)
├── TestModelProfiles (9 tests)
├── TestGreenOpsEngine (9 tests)
└── TestAPI (12 tests)
```

## Project Structure

```
GreenOps/                    # React frontend (Vite + Tailwind)
├── src/
│   ├── components/
│   │   ├── Sidebar.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── ModelsPage.jsx
│   │   ├── BudgetPage.jsx
│   │   └── SimulatorPage.jsx
│   ├── utils/api.js
│   ├── App.jsx
│   └── index.css            # 800-line design system
│
GreenOps_Engine/             # FastAPI backend
├── main.py                  # App entry point
├── database.py              # SQLite with WAL mode
├── models.py                # Pydantic schemas
├── GreenOps.py              # Original optimization engine
├── tests.py                 # 40 tests
├── seed_data.py             # 897-record demo data generator
├── routes/
│   ├── tracking.py          # Call tracking APIs
│   ├── dashboard.py         # Analytics APIs
│   ├── budget.py            # Carbon budget APIs
│   ├── optimizer.py         # Simulation APIs
│   └── proxy.py             # AI provider proxy
└── services/
    ├── model_profiles.py    # 18 AI model energy profiles
    └── carbon_calculator.py # 20 regional emission factors
│
greenops-sdk/                # Python SDK package
├── greenops/
│   ├── __init__.py          # Public API
│   ├── tracker.py           # Core tracking logic
│   ├── decorators.py        # @track decorator
│   ├── client.py            # OpenAI wrapper
│   ├── report.py            # Terminal reports
│   ├── config.py            # Configuration
│   └── _store.py            # Local SQLite storage
├── pyproject.toml
└── README.md
```

## Technology Stack

- **Frontend**: React 18 + Vite + Tailwind CSS v4 + Recharts
- **Backend**: FastAPI + SQLite + Pydantic
- **SDK**: Pure Python (zero dependencies)
- **Design**: Dark mode, glassmorphism, Inter + JetBrains Mono fonts

## License

MIT
