"""
GreenOps SDK — Report Generator

Beautiful terminal reports for AI carbon tracking.
Works without any external dependencies — pure Python formatting.
"""

import sys
from typing import Dict, Any, Optional, List

from .tracker import get_tracker


# ============================================================
# FORMATTING HELPERS
# ============================================================

# Box drawing characters
_TL = "\u250c"  # ┌
_TR = "\u2510"  # ┐
_BL = "\u2514"  # └
_BR = "\u2518"  # ┘
_H  = "\u2500"  # ─
_V  = "\u2502"  # │
_ML = "\u251c"  # ├
_MR = "\u2524"  # ┤


def _box_line(width: int, left: str, right: str, fill: str = _H) -> str:
    return f"{left}{fill * (width - 2)}{right}"


def _pad_line(text: str, width: int) -> str:
    inner = width - 4  # 2 for borders, 2 for padding
    return f"{_V} {text:<{inner}} {_V}"


def _center_line(text: str, width: int) -> str:
    inner = width - 4
    return f"{_V} {text:^{inner}} {_V}"


def _kv_line(key: str, value: str, width: int) -> str:
    inner = width - 4
    key_width = 22
    val_width = inner - key_width - 2
    return f"{_V} {key:<{key_width}}: {value:<{val_width}} {_V}"


def _divider(width: int) -> str:
    return _box_line(width, _ML, _MR)


# ============================================================
# EQUIVALENCY STRINGS
# ============================================================

def _get_equivalencies(co2_g: float, energy_wh: float, water_ml: float) -> List[str]:
    """Generate human-readable equivalency strings."""
    equivs = []

    if co2_g > 0:
        breaths = co2_g / 0.04
        equivs.append(f"= {round(breaths)} human breaths of CO2")

        km = co2_g / 120
        if km < 1:
            equivs.append(f"= driving a car {round(km * 1000)} meters")
        else:
            equivs.append(f"= driving a car {round(km, 2)} km")

    if energy_wh > 0:
        phone_pct = (energy_wh / 15) * 100
        if phone_pct < 100:
            equivs.append(f"= charging a phone {round(phone_pct, 1)}%")
        else:
            equivs.append(f"= charging a phone {round(energy_wh / 15, 1)}x")

    return equivs


# ============================================================
# REPORT GENERATORS
# ============================================================

def summary(source: str = "session"):
    """
    Print a beautiful summary report to the terminal.

    Args:
        source: "session" for current session only, "all" for full local history
    """
    tracker = get_tracker()

    if source == "all":
        data = tracker.get_full_summary()
        title = "GreenOps - All Time Report"
        totals = data.get("totals", {})
        models = data.get("models", [])
    else:
        data = tracker.get_session_stats()
        title = "GreenOps - Session Report"
        totals = data
        # Build model breakdown from session calls
        calls = data.get("calls", [])
        model_map = {}
        for c in calls:
            mid = c["model_id"]
            if mid not in model_map:
                model_map[mid] = {"model_id": mid, "call_count": 0, "total_tokens": 0, "total_energy_wh": 0, "total_co2_g": 0}
            model_map[mid]["call_count"] += 1
            model_map[mid]["total_tokens"] += c["total_tokens"]
            model_map[mid]["total_energy_wh"] += c["energy_wh"]
            model_map[mid]["total_co2_g"] += c["co2_g"]
        models = sorted(model_map.values(), key=lambda x: x["total_energy_wh"], reverse=True)

    total_calls = totals.get("total_calls", 0)

    if total_calls == 0:
        print("\n[GreenOps] No calls tracked yet.\n")
        return

    width = 52

    total_energy = totals.get("total_energy_wh", 0)
    total_co2 = totals.get("total_co2_g", 0)
    total_water = totals.get("total_water_ml", 0)
    total_tokens = totals.get("total_tokens", 0)
    total_input = totals.get("total_input_tokens", 0)
    total_output = totals.get("total_output_tokens", 0)

    equivs = _get_equivalencies(total_co2, total_energy, total_water)

    lines = []
    lines.append("")
    lines.append(_box_line(width, _TL, _TR))
    lines.append(_center_line(f"\033[1;32m{title}\033[0m", width + 9))  # +9 for ANSI codes
    lines.append(_divider(width))
    lines.append(_kv_line("Total calls", str(total_calls), width))
    lines.append(_kv_line("Total tokens", f"{total_tokens:,}", width))
    lines.append(_kv_line("  Input tokens", f"{total_input:,}", width))
    lines.append(_kv_line("  Output tokens", f"{total_output:,}", width))
    lines.append(_divider(width))
    lines.append(_kv_line("Energy used", f"{total_energy:.4f} Wh", width))
    lines.append(_kv_line("CO2 emitted", f"{total_co2:.4f} g", width))
    lines.append(_kv_line("Water used", f"{total_water:.4f} mL", width))

    if equivs:
        lines.append(_divider(width))
        lines.append(_center_line("\033[33mEquivalent to:\033[0m", width + 9))
        for eq in equivs:
            lines.append(_center_line(eq, width))

    if models:
        lines.append(_divider(width))
        lines.append(_center_line("\033[36mPer-Model Breakdown\033[0m", width + 9))
        lines.append(_divider(width))
        for m in models[:6]:
            mid = m.get("model_id", "?")
            count = m.get("call_count", 0)
            energy = m.get("total_energy_wh", 0)
            pct = (energy / total_energy * 100) if total_energy > 0 else 0

            # Simple bar chart
            bar_len = int(pct / 5)
            bar = "\033[32m" + "\u2588" * bar_len + "\033[0m" + "\u2591" * (20 - bar_len)
            lines.append(_pad_line(f"{mid[:18]:<18} {count:>4} calls", width))
            lines.append(_pad_line(f"  {bar} {pct:5.1f}%  {energy:.4f}Wh", width + 9))

    lines.append(_box_line(width, _BL, _BR))
    lines.append("")

    output = "\n".join(lines)

    try:
        print(output)
    except UnicodeEncodeError:
        # Fallback for terminals that can't handle Unicode
        clean = output.replace("\u250c", "+").replace("\u2510", "+")
        clean = clean.replace("\u2514", "+").replace("\u2518", "+")
        clean = clean.replace("\u2500", "-").replace("\u2502", "|")
        clean = clean.replace("\u251c", "+").replace("\u2524", "+")
        clean = clean.replace("\u2588", "#").replace("\u2591", ".")
        print(clean)


def quick_stats() -> Dict[str, Any]:
    """Return session stats as a dict (for programmatic use)."""
    return get_tracker().get_session_stats()


def print_call(call_data: Dict[str, Any]):
    """Print a single call's environmental impact."""
    model = call_data.get("model_id", "unknown")
    tokens = call_data.get("total_tokens", 0)
    energy = call_data.get("energy_wh", 0)
    co2 = call_data.get("co2_g", 0)

    print(
        f"[GreenOps] {model} | "
        f"{tokens:,} tokens | "
        f"{energy:.6f} Wh | "
        f"{co2:.6f}g CO2"
    )
