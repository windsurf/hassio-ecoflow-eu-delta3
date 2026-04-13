"""Device registry — maps serial number prefix to device model.

Usage:
    from .devices.registry import detect_model
    model = detect_model("D361ZEH49GAR0848")
    # returns "Delta 3 1500"

When a SN prefix is unknown, returns "Unknown EcoFlow Device".
Platform files (sensor.py, switch.py, etc.) use the model string
to look up the correct description tuples.
"""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

# SN prefix → (model name, device family)
# Sorted longest-prefix-first at lookup time for specificity.
# Sources: EcoFlow developer docs, live MQTT analysis, tolwi/hassio-ecoflow-cloud
_SN_PREFIX_MAP: dict[str, str] = {
    # ── Delta 3 series ───────────────────────────────────────────────────
    "D361":  "Delta 3 1500",
    "D362":  "Delta 3 Plus",
    "D381":  "Delta 3 Max",

    # ── Delta Pro series ─────────────────────────────────────────────────
    "DGEA":  "Delta Pro 3",
    "DGEB":  "Delta Pro Ultra",
    "DAEB":  "Delta Pro",

    # ── Delta 2 series ───────────────────────────────────────────────────
    "R331":  "Delta 2",
    "R351":  "Delta 2 Max",

    # ── Delta 1 series ───────────────────────────────────────────────────
    "DCAB":  "Delta Max",
    "DAAZ":  "Delta Mini",

    # ── River 3 series ───────────────────────────────────────────────────
    "R641":  "River 3",
    "R651":  "River 3 Plus",

    # ── River 2 series ───────────────────────────────────────────────────
    "R621":  "River 2",
    "R631":  "River 2 Max",
    "R622":  "River 2 Pro",

    # ── River 1 series ───────────────────────────────────────────────────
    "R601":  "River Max",
    "R602":  "River Pro",
    "R501":  "River Mini",

    # ── PowerStream / Solar ──────────────────────────────────────────────
    "HW51":  "PowerStream 600W",
    "HW52":  "PowerStream 800W",
    "BKW":   "PowerStream",

    # ── Smart devices ────────────────────────────────────────────────────
    "SP10":  "Smart Plug",

    # ── Climate ──────────────────────────────────────────────────────────
    "BX11":  "Glacier",
    "KT21":  "Wave 2",
}

# Default model for unknown devices
UNKNOWN_MODEL = "Unknown EcoFlow Device"


def detect_model(sn: str) -> str:
    """Detect device model name from serial number prefix.

    Tries longest prefix match first so D361 matches before D36.
    Returns UNKNOWN_MODEL if no prefix matches.
    """
    sn_upper = sn.upper()

    # Sort prefixes longest-first for most specific match
    for prefix in sorted(_SN_PREFIX_MAP.keys(), key=len, reverse=True):
        if sn_upper.startswith(prefix):
            model = _SN_PREFIX_MAP[prefix]
            _LOGGER.info(
                "EcoFlow: detected %s for SN %s (prefix %s)",
                model, sn, prefix,
            )
            return model

    _LOGGER.warning(
        "EcoFlow: no device profile for SN prefix of %s — using diagnostic mode",
        sn,
    )
    return UNKNOWN_MODEL


def get_supported_models() -> list[str]:
    """Return list of unique supported model names (for UI display)."""
    return sorted(set(_SN_PREFIX_MAP.values()))
