"""
ColdBridge AI - Solar Adjustment Service (Simplified Simulation)

HONESTY & SIMULATION DISCLOSURE:
The solar fallback logic implemented here is a SIMPLIFIED PROTOTYPE SIMULATION
for the Avishkar competition. It computes:
  effective_mobile_capacity = available_capacity_kg * solar_reliability (0.0 to 1.0)
  reliability_penalty = 1.0 - solar_reliability (0.0 to 1.0)

This is an administrative simulation input, NOT a measured battery state, power
consumption, Peltier cooling load, temperature stability, or remaining operating time.
Hardware telemetry (ESP32, voltage/current sensors, solar irradiance meters) belongs
to a subsequent hardware integration phase and is strictly NOT part of this Phase 1 software MVP.
"""

def clamp_reliability(solar_reliability: float) -> float:
    """Clamp solar reliability factor to [0.0, 1.0]."""
    if solar_reliability is None:
        return 0.9
    try:
        val = float(solar_reliability)
        return max(0.0, min(1.0, val))
    except (ValueError, TypeError):
        return 0.9


def get_effective_capacity(
    available_capacity_kg: float,
    asset_type: str,
    solar_reliability: float = 1.0
) -> float:
    """
    Calculate effective available capacity in kg.
    - STATIC rooms: available_capacity_kg (no solar dependence)
    - MOBILE vans: available_capacity_kg * solar_reliability
    """
    avail = max(0.0, float(available_capacity_kg or 0.0))
    if asset_type == "MOBILE":
        factor = clamp_reliability(solar_reliability)
        return round(avail * factor, 2)
    return round(avail, 2)


def get_reliability_penalty(
    asset_type: str,
    solar_reliability: float = 1.0
) -> float:
    """
    Calculate reliability penalty (0.0 to 1.0) for reverse-auction scoring.
    - STATIC rooms: 0.0 (in Release 1)
    - MOBILE vans: 1.0 - solar_reliability (clamped to 0.0..1.0)
    """
    if asset_type == "MOBILE":
        factor = clamp_reliability(solar_reliability)
        return round(1.0 - factor, 4)
    return 0.0
