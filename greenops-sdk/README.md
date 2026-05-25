# 🌿 GreenOps SDK

**Track the carbon footprint of your AI API calls.**

GreenOps SDK automatically measures the energy, CO₂, and water impact of every AI API call in your Python code — with zero friction.

## Installation

```bash
pip install greenops
```

## Quick Start

### Option 1: One-line manual tracking

```python
import greenops

greenops.configure(project="my-app")

# After any AI call, log it:
greenops.log("gpt-4o", input_tokens=500, output_tokens=200)

# View your impact:
greenops.report()
```

### Option 2: Decorator (auto-detect)

```python
import greenops

@greenops.track
def ask_ai(prompt):
    return client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

result = ask_ai("What is sustainability?")
greenops.report()
```

### Option 3: Drop-in OpenAI Client

```python
from greenops import OpenAIClient

# Replace openai.OpenAI() with OpenAIClient()
client = OpenAIClient(api_key="sk-...")

# Use exactly like the normal OpenAI client — tracking is automatic
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello!"}]
)

greenops.report()
```

## Configuration

```python
import greenops

greenops.configure(
    server_url="http://localhost:8000",  # GreenOps backend
    project="my-chatbot",               # Project grouping
    region="us_oregon",                  # For carbon calculations
    auto_sync=True,                     # Auto-sync to backend
    verbose=True,                       # Print tracking logs
)
```

Or use environment variables:

```bash
export GREENOPS_SERVER_URL=http://localhost:8000
export GREENOPS_PROJECT=my-chatbot
export GREENOPS_REGION=us_oregon
```

## Supported Models

18 models across 6 providers are supported with research-backed energy estimates:

| Provider  | Models                                    |
|-----------|-------------------------------------------|
| OpenAI    | GPT-4o, GPT-4o Mini, GPT-4 Turbo, o1, o3-mini |
| Anthropic | Claude Sonnet 4, Claude 3.5 Haiku, Claude 3 Opus |
| Google    | Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 2.0 Flash |
| Meta      | Llama 3.1 405B, 70B, 8B                  |
| Mistral   | Mistral Large, Mistral Small              |
| DeepSeek  | DeepSeek R1                               |

Unknown models are tracked with conservative default estimates.

## CLI

```bash
python -m greenops report    # Show tracking report
python -m greenops stats     # Show raw stats (JSON)
python -m greenops sync      # Sync local data to backend
```

## API Reference

| Function                     | Description                                  |
|------------------------------|----------------------------------------------|
| `greenops.configure(**opts)` | Set SDK configuration                        |
| `greenops.log(model, ...)`   | Log a single AI call                         |
| `greenops.track`             | Decorator for auto-tracking                  |
| `greenops.track_async`       | Async decorator for auto-tracking            |
| `greenops.OpenAIClient()`    | Drop-in OpenAI client with tracking          |
| `greenops.report()`          | Print terminal report                        |
| `greenops.stats()`           | Get session stats as dict                    |
| `greenops.sync()`            | Sync to backend                              |
| `greenops.reset()`           | Reset session tracker                        |

## License

MIT
