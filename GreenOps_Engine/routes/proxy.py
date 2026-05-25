"""
GreenOps — AI Carbon Proxy Routes

A transparent proxy that sits between developers and AI providers.
Developers change their API base_url to point here, and every call
is automatically forwarded + tracked with carbon metrics.

Supported Providers:
  - OpenAI: POST /proxy/openai/v1/chat/completions
  - Anthropic: POST /proxy/anthropic/v1/messages
  - Google: POST /proxy/google/v1/models/{model}:generateContent

Usage:
  # Instead of base_url="https://api.openai.com/v1"
  # Use:     base_url="http://localhost:8000/proxy/openai/v1"

  client = openai.OpenAI(
      api_key="sk-...",
      base_url="http://localhost:8000/proxy/openai/v1"
  )
  # Everything works exactly the same — but every call is tracked!
"""

import json
import uuid
import time
import httpx
from datetime import datetime, timezone
from typing import Optional
from urllib import request as urllib_request
from urllib.error import URLError, HTTPError

from fastapi import APIRouter, Request, HTTPException, Response, Depends, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse

from services.model_profiles import get_model_profile, estimate_energy_for_call
from services.carbon_calculator import calculate_impact
from services.alerts import check_budget_and_alert
from database import insert_api_call
from middleware.auth import get_current_user

router = APIRouter(prefix="/proxy", tags=["proxy"])


# ============================================================
# PROVIDER CONFIGURATIONS
# ============================================================

PROVIDERS = {
    "openai": {
        "base_url": "https://api.openai.com",
        "auth_header": "Authorization",
    },
    "anthropic": {
        "base_url": "https://api.anthropic.com",
        "auth_header": "x-api-key",
    },
    "google": {
        "base_url": "https://generativelanguage.googleapis.com",
        "auth_header": "x-goog-api-key",
    },
}


# ============================================================
# RESPONSE PARSERS — extract token usage from provider responses
# ============================================================

def _parse_openai_response(body: dict) -> dict:
    """Extract model and token usage from an OpenAI response."""
    usage = body.get("usage", {})
    return {
        "model_id": body.get("model", "unknown"),
        "provider": "openai",
        "input_tokens": usage.get("prompt_tokens", 0),
        "output_tokens": usage.get("completion_tokens", 0),
    }


def _parse_anthropic_response(body: dict) -> dict:
    """Extract model and token usage from an Anthropic response."""
    usage = body.get("usage", {})
    return {
        "model_id": body.get("model", "unknown"),
        "provider": "anthropic",
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }


def _parse_google_response(body: dict, model_hint: str = "") -> dict:
    """Extract token usage from a Google Gemini response."""
    metadata = body.get("usageMetadata", {})
    return {
        "model_id": model_hint or "gemini",
        "provider": "google",
        "input_tokens": metadata.get("promptTokenCount", 0),
        "output_tokens": metadata.get("candidatesTokenCount", 0),
    }


RESPONSE_PARSERS = {
    "openai": _parse_openai_response,
    "anthropic": _parse_anthropic_response,
    "google": _parse_google_response,
}


# ============================================================
# PROXY LOGIC
# ============================================================

async def track_call_async(
    user_id: int,
    provider_name: str,
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    elapsed_ms: float,
    upstream_url: str,
):
    total_tokens = input_tokens + output_tokens
    estimation = estimate_energy_for_call(model_id, input_tokens, output_tokens)

    if estimation:
        energy_wh = estimation["energy_wh"]
        cost_usd = estimation["cost_usd"]
    else:
        energy_wh = (total_tokens / 1000) * 0.004
        cost_usd = 0.0

    impact = calculate_impact(energy_wh)

    call_data = {
        "call_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_id": model_id,
        "provider": provider_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "energy_wh": energy_wh,
        "co2_g": impact.co2_g,
        "water_ml": impact.water_ml,
        "cost_usd": cost_usd,
        "latency_ms": round(elapsed_ms, 2),
        "region": "global_average",
        "source": "proxy",
        "project": "default",
        "metadata": {"proxy_provider": provider_name, "upstream_url": upstream_url, "streamed": True},
        "user_id": user_id,
    }

    try:
        insert_api_call(call_data)
        await check_budget_and_alert(user_id, "default")
    except Exception as e:
        print(f"[GreenOps] Proxy async tracking failed: {e}")

async def _proxy_request(
    provider_name: str,
    path: str,
    request: Request,
    user: dict,
    background_tasks: BackgroundTasks,
    model_hint: str = "",
) -> Response:
    """
    Forward a request to the AI provider, track the response, and return it.
    """
    provider = PROVIDERS.get(provider_name)
    if not provider:
        raise HTTPException(status_code=400, detail=f"Unknown provider: {provider_name}")

    # Build the upstream URL
    upstream_url = f"{provider['base_url']}/{path}"

    # Read the request body
    body_bytes = await request.body()

    # Forward headers (pass through auth + content-type)
    forward_headers = {}
    auth_header = provider["auth_header"]

    for key, value in request.headers.items():
        key_lower = key.lower()
        # Forward auth headers
        if key_lower == auth_header.lower():
            forward_headers[auth_header] = value
        elif key_lower == "authorization":
            forward_headers["Authorization"] = value
        elif key_lower == "content-type":
            forward_headers["Content-Type"] = value
        elif key_lower == "x-api-key":
            forward_headers["x-api-key"] = value
        elif key_lower == "anthropic-version":
            forward_headers["anthropic-version"] = value

    if "Content-Type" not in forward_headers:
        forward_headers["Content-Type"] = "application/json"

    # Parse the request body to detect stream
    is_stream = False
    req_model_id = model_hint or "unknown"
    req_input_tokens = 0
    try:
        if body_bytes:
            req_json = json.loads(body_bytes)
            is_stream = req_json.get("stream", False)
            req_model_id = req_json.get("model", req_model_id)
            if is_stream and provider_name == "openai":
                messages = req_json.get("messages", [])
                text_len = sum(len(m.get("content", "")) for m in messages if isinstance(m.get("content"), str))
                req_input_tokens = max(1, text_len // 4)
    except Exception:
        pass

    # Make the upstream request
    start_time = time.time()
    
    client = httpx.AsyncClient()
    
    try:
        req = client.build_request(
            method=request.method,
            url=upstream_url,
            headers=forward_headers,
            content=body_bytes,
            timeout=120.0
        )
        
        resp = await client.send(req, stream=True)
        
        if resp.status_code >= 400:
            await resp.aread()
            await client.aclose()
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers)
            )

        content_type = resp.headers.get("content-type", "")
        if is_stream or content_type.startswith("text/event-stream"):
            async def stream_generator():
                chunks_yielded = 0
                try:
                    async for chunk in resp.aiter_bytes():
                        if chunk:
                            chunks_yielded += 1
                            yield chunk
                finally:
                    elapsed_ms = (time.time() - start_time) * 1000
                    await client.aclose()
                    background_tasks.add_task(
                        track_call_async,
                        user_id=user["id"],
                        provider_name=provider_name,
                        model_id=req_model_id,
                        input_tokens=req_input_tokens,
                        output_tokens=chunks_yielded,
                        elapsed_ms=elapsed_ms,
                        upstream_url=upstream_url
                    )
            
            return StreamingResponse(
                stream_generator(),
                status_code=resp.status_code,
                headers={
                    "Content-Type": content_type or "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive"
                }
            )
        else:
            await resp.aread()
            response_bytes = resp.content
            await client.aclose()
            
            elapsed_ms = (time.time() - start_time) * 1000
            try:
                response_body = json.loads(response_bytes)
                parser = RESPONSE_PARSERS.get(provider_name)
                if parser:
                    parsed = parser(response_body, model_hint=model_hint) if provider_name == "google" else parser(response_body)
                    
                    background_tasks.add_task(
                        track_call_async,
                        user_id=user["id"],
                        provider_name=provider_name,
                        model_id=parsed["model_id"],
                        input_tokens=parsed["input_tokens"],
                        output_tokens=parsed["output_tokens"],
                        elapsed_ms=elapsed_ms,
                        upstream_url=upstream_url
                    )
                    extra_headers = {"X-GreenOps-Tracked": "true"}
                else:
                    extra_headers = {"X-GreenOps-Tracked": "false"}
            except Exception:
                extra_headers = {"X-GreenOps-Tracked": "false"}

            resp_headers = dict(resp.headers)
            for k in ["content-length", "content-encoding", "transfer-encoding"]:
                resp_headers.pop(k, None)
            resp_headers.update(extra_headers)

            return Response(
                content=response_bytes,
                status_code=resp.status_code,
                headers=resp_headers,
            )

    except httpx.RequestError as e:
        await client.aclose()
        raise HTTPException(
            status_code=502,
            detail=f"Failed to reach {provider_name}: {str(e)}"
        )


# ============================================================
# OPENAI PROXY ROUTES
# ============================================================

@router.api_route("/openai/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_openai(path: str, request: Request, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    """
    Proxy for OpenAI API.

    Usage:
        client = openai.OpenAI(
            api_key="sk-...",
            base_url="http://localhost:8000/proxy/openai/v1"
        )
    """
    return await _proxy_request("openai", path, request, user, background_tasks)


# ============================================================
# ANTHROPIC PROXY ROUTES
# ============================================================

@router.api_route("/anthropic/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_anthropic(path: str, request: Request, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    """
    Proxy for Anthropic API.

    Usage:
        client = anthropic.Anthropic(
            api_key="sk-ant-...",
            base_url="http://localhost:8000/proxy/anthropic"
        )
    """
    return await _proxy_request("anthropic", path, request, user, background_tasks)


# ============================================================
# GOOGLE PROXY ROUTES
# ============================================================

@router.api_route("/google/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_google(path: str, request: Request, background_tasks: BackgroundTasks, user=Depends(get_current_user)):
    """
    Proxy for Google Gemini API.
    """
    # Try to extract model name from path
    model_hint = ""
    if "models/" in path:
        parts = path.split("models/")
        if len(parts) > 1:
            model_hint = parts[1].split(":")[0].split("/")[0]

    return await _proxy_request("google", path, request, user, background_tasks, model_hint=model_hint)


# ============================================================
# PROXY STATUS
# ============================================================

@router.get("/status")
def proxy_status():
    """Check proxy health and list supported providers."""
    return {
        "status": "operational",
        "providers": {
            name: {
                "base_url": cfg["base_url"],
                "proxy_url": f"/proxy/{name}",
                "usage": f"Set base_url to http://localhost:8000/proxy/{name}/v1",
            }
            for name, cfg in PROVIDERS.items()
        },
        "features": [
            "Transparent request forwarding",
            "Automatic token counting",
            "Streaming support",
            "Energy/CO₂/water tracking per call",
            "X-GreenOps-* response headers",
            "Zero code changes (just change base_url)",
        ],
    }
