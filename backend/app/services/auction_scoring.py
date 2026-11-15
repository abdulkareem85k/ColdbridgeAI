"""
ColdBridge AI - Reverse Auction Scoring Service (M5)

Implements the multi-criteria cross-asset reverse-auction scoring engine
specified in Document 1, Section G.3.

Formula:
  score = w_price * price_n
        + w_dist  * distance_n
        + w_time  * time_n
        + w_rel   * reliability_penalty
        + w_cap   * capacity_penalty
        - urgency_bonus

Lower score is better.
"""

import json
from pathlib import Path
from typing import List, Dict, Any
from app.services.solar_adjustment import get_reliability_penalty

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "matching_weights.json"

DEFAULT_WEIGHTS = {
    "price": 0.30,
    "distance": 0.15,
    "time": 0.20,
    "reliability": 0.20,
    "capacity": 0.15,
    "urgency_bonus_max": 0.15,
    "band_factor": {
        "HIGH": 1.0,
        "MEDIUM": 0.0,
        "LOW": 0.0
    }
}


def load_matching_weights() -> Dict[str, Any]:
    """Load matching weights from config/matching_weights.json and validate sum."""
    weights = DEFAULT_WEIGHTS.copy()
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                weights.update(loaded)
        except Exception:
            pass

    # Startup validation: core weights must sum to 1.0
    w_sum = (
        weights.get("price", 0.0) +
        weights.get("distance", 0.0) +
        weights.get("time", 0.0) +
        weights.get("reliability", 0.0) +
        weights.get("capacity", 0.0)
    )
    if abs(w_sum - 1.0) > 1e-5:
        raise ValueError(f"Matching weights must sum to 1.0 (current sum: {w_sum:.4f})")

    return weights


# Load on module import to validate immediately
MATCHING_CONFIG = load_matching_weights()


def compute_min_max(values: List[float]):
    """Returns (min_val, max_val) safely."""
    if not values:
        return 0.0, 0.0
    return min(values), max(values)


def normalize_metric(val: float, min_val: float, max_val: float) -> float:
    """
    Min-max normalisation: x_n = (x - min) / (max - min).
    0 = best, 1 = worst.
    If max == min, returns 0.0 for all. Never divides by zero.
    """
    if max_val <= min_val:
        return 0.0
    return (val - min_val) / (max_val - min_val)


def generate_explanation_reasons(
    asset_name: str,
    asset_type: str,
    price_total: float,
    distance_km: float,
    eta_minutes: float,
    components: Dict[str, float],
    is_winner: bool = False
) -> List[str]:
    """Generate 2-4 plain-English reasons explaining the score."""
    reasons = []

    # 1. Urgency / Farmgate mobility advantage
    if components["urgency_bonus"] > 0:
        reasons.append(
            f"Received full urgency bonus (-{components['urgency_bonus']:.3f}) for farmgate mobile response on high-perishability produce."
        )
    elif asset_type == "MOBILE":
        reasons.append("Mobile cooling dispatch directly to farmgate location.")
    else:
        reasons.append("Static temperature-controlled facility.")

    # 2. Travel & Dispatch
    if components["time_n"] == 0.0 or components["time_n"] <= 0.2:
        reasons.append(f"Fastest or near-fastest response time ({eta_minutes:.0f} mins ETA).")
    elif components["distance_n"] == 0.0 or components["distance_n"] <= 0.2:
        reasons.append(f"Closest proximity ({distance_km:.1f} km road distance).")
    elif components["time_n"] >= 0.8:
        reasons.append(f"Longer response time ({eta_minutes:.0f} mins ETA).")

    # 3. Pricing
    if components["price_n"] == 0.0 or components["price_n"] <= 0.2:
        reasons.append(f"Lowest or highly competitive storage rate (₹{price_total:,.2f}).")
    elif components["price_n"] >= 0.8:
        reasons.append(f"Higher total cost (₹{price_total:,.2f}) compared to alternative facilities.")

    # 4. Reliability / Solar Fallback
    if components["reliability_penalty"] > 0.0:
        reasons.append(
            f"Carries a {components['reliability_penalty']:.2f} reliability penalty due to simulated solar irradiance."
        )

    # 5. Overall pick
    if is_winner:
        reasons.append("Optimal multi-criteria match balancing urgency, response speed, and cost.")

    return reasons[:4]


def score_and_rank_offers(
    offers: List[Dict[str, Any]],
    requested_kg: float,
    sri_band: str = None,
    weights_config: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Computes scores for all eligible offers, sorts them ascending by unrounded score,
    applies tie-breaking, and returns detailed breakdowns and plain-English reasons.
    """
    if not offers:
        return []

    cfg = weights_config or MATCHING_CONFIG
    w_price = cfg.get("price", 0.30)
    w_dist = cfg.get("distance", 0.15)
    w_time = cfg.get("time", 0.20)
    w_rel = cfg.get("reliability", 0.20)
    w_cap = cfg.get("capacity", 0.15)
    urgency_max = cfg.get("urgency_bonus_max", 0.15)
    band_factors = cfg.get("band_factor", {"HIGH": 1.0, "MEDIUM": 0.0, "LOW": 0.0})

    prices = [float(o["price_total"]) for o in offers]
    distances = [float(o["distance_km"]) for o in offers]
    times = [float(o["eta_minutes"]) for o in offers]

    min_p, max_p = compute_min_max(prices)
    min_d, max_d = compute_min_max(distances)
    min_t, max_t = compute_min_max(times)

    scored_offers = []
    for offer in offers:
        asset_type = offer.get("asset_type", "STATIC")
        solar_rel = float(offer.get("solar_reliability", 1.0))
        effective_cap = float(offer.get("effective_available_kg", offer.get("available_capacity_kg", requested_kg)))

        # 1. Normalised metrics (0 = best, 1 = worst)
        price_n = normalize_metric(float(offer["price_total"]), min_p, max_p)
        distance_n = normalize_metric(float(offer["distance_km"]), min_d, max_d)
        time_n = normalize_metric(float(offer["eta_minutes"]), min_t, max_t)

        # 2. Reliability penalty
        rel_penalty = get_reliability_penalty(asset_type, solar_rel)

        # 3. Capacity penalty: requested_kg / effective_available_kg
        cap_penalty = requested_kg / effective_cap if effective_cap > 0 else 1.0

        # 4. Urgency bonus: mobile vans only when SRI band warrants it
        if asset_type == "MOBILE" and sri_band:
            band_mult = float(band_factors.get(str(sri_band).upper(), 0.0))
            urgency_bonus = urgency_max * band_mult
        else:
            urgency_bonus = 0.0

        # 5. Composite Score
        unrounded_score = (
            w_price * price_n +
            w_dist * distance_n +
            w_time * time_n +
            w_rel * rel_penalty +
            w_cap * cap_penalty -
            urgency_bonus
        )

        components = {
            "price_n": round(price_n, 4),
            "distance_n": round(distance_n, 4),
            "time_n": round(time_n, 4),
            "reliability_penalty": round(rel_penalty, 4),
            "capacity_penalty": round(cap_penalty, 4),
            "urgency_bonus": round(urgency_bonus, 4),
            "weighted_price": round(w_price * price_n, 4),
            "weighted_distance": round(w_dist * distance_n, 4),
            "weighted_time": round(w_time * time_n, 4),
            "weighted_reliability": round(w_rel * rel_penalty, 4),
            "weighted_capacity": round(w_cap * cap_penalty, 4)
        }

        entry = dict(offer)
        entry["unrounded_score"] = unrounded_score
        entry["score"] = round(unrounded_score, 3)
        entry["components"] = components
        scored_offers.append(entry)

    # Sort strictly by unrounded_score ASC, then price_total ASC, then eta_minutes ASC, then asset_id ASC
    scored_offers.sort(key=lambda x: (
        x["unrounded_score"],
        float(x["price_total"]),
        float(x["eta_minutes"]),
        str(x["asset_id"])
    ))

    # Add explanations and rank index
    for idx, o in enumerate(scored_offers, start=1):
        o["rank"] = idx
        o["is_winner"] = (idx == 1)
        o["reasons"] = generate_explanation_reasons(
            asset_name=o.get("asset_name", ""),
            asset_type=o.get("asset_type", "STATIC"),
            price_total=float(o["price_total"]),
            distance_km=float(o["distance_km"]),
            eta_minutes=float(o["eta_minutes"]),
            components=o["components"],
            is_winner=(idx == 1)
        )

    return scored_offers
