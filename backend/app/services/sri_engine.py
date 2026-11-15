import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "crops.json"

def load_crop_rules() -> Dict[str, Any]:
    """Load crop rules and perishability classes from crops.json."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Crop configuration file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_sri(
    crop_code: str,
    hours_since_harvest: float,
    ambient_temp_c: float
) -> Dict[str, Any]:
    """
    Transparent rule-based Spoilage Risk Index (SRI) engine.
    
    IMPORTANT DISCLAIMER:
    This is a prototype heuristic calculation for the Avishkar competition demo,
    NOT a scientifically validated microbiological decay model.
    """
    # 1. Input Validation
    if hours_since_harvest < 0:
        raise ValueError("Hours since harvest cannot be negative")
    if ambient_temp_c < -20.0 or ambient_temp_c > 65.0:
        raise ValueError(f"Ambient temperature ({ambient_temp_c}°C) is outside realistic range (-20°C to 65°C)")

    rules = load_crop_rules()
    crop_key = crop_code.lower().strip()
    crops_dict = rules.get("crops", {})
    if crop_key not in crops_dict:
        raise ValueError(f"Unknown or unsupported crop code: '{crop_code}'")

    crop_info = crops_dict[crop_key]
    crop_class = crop_info["class"]
    threshold_temp = crop_info["threshold_ambient_temp_c"]
    class_rules = rules["perishability_classes"][crop_class]
    rule_version = rules.get("rule_version", "prototype-1")
    disclaimer = rules.get("disclaimer", "Prototype estimate - not a validated spoilage prediction")

    base_decay = class_rules["base_decay_rate"]
    temp_sensitivity = class_rules["temp_sensitivity_factor"]
    max_safe_hours = class_rules["max_safe_hours_at_25c"]

    # 2. Time-Based Degradation Component (0 to 60 points)
    # Scaled by max_safe_hours for this crop's perishability class
    time_ratio = min(hours_since_harvest / max_safe_hours, 2.0)
    time_points = time_ratio * 40.0

    # 3. Thermal Stress Component (0 to 40 points)
    # Extra degradation if ambient temperature exceeds the crop's threshold
    temp_delta = max(0.0, ambient_temp_c - threshold_temp)
    heat_stress_points = min(temp_delta * temp_sensitivity * 2.5, 40.0)

    # 4. Total Raw Score (0 to 100)
    raw_score = time_points + heat_stress_points
    score = round(min(100.0, max(0.0, raw_score)), 1)

    # 5. Risk Category Categorization
    if score >= 65.0:
        risk_category = "HIGH"
        recommended_action = "Urgent action required: prioritize immediate farmgate mobile cooling van dispatch."
    elif score >= 35.0:
        risk_category = "MEDIUM"
        recommended_action = "Moderate urgency: reserve static room or mobile cooling within standard transit window."
    else:
        risk_category = "LOW"
        recommended_action = "Low urgency: batch is stable for standard road transport and static room storage."

    # 6. Plain-English Human Explainability Reasons
    reasons: List[str] = []
    reasons.append(f"Crop '{crop_info['name']}' has {crop_class} perishability class with {max_safe_hours}h base threshold.")
    
    if hours_since_harvest > (max_safe_hours * 0.5):
        reasons.append(f"{hours_since_harvest:.1f} hours have elapsed since harvest ({int((hours_since_harvest / max_safe_hours) * 100)}% of safe ambient window).")
    else:
        reasons.append(f"Fresh harvest: only {hours_since_harvest:.1f} hours since harvest.")

    if ambient_temp_c > threshold_temp:
        reasons.append(f"Ambient collection temperature ({ambient_temp_c:.1f}°C) exceeds safe threshold ({threshold_temp:.1f}°C) by {temp_delta:.1f}°C.")
    else:
        reasons.append(f"Ambient temperature ({ambient_temp_c:.1f}°C) is within acceptable range (<= {threshold_temp:.1f}°C).")

    factors = {
        "crop_code": crop_key,
        "crop_class": crop_class,
        "hours_since_harvest": hours_since_harvest,
        "ambient_temp_c": ambient_temp_c,
        "threshold_temp_c": threshold_temp,
        "time_score_component": round(time_points, 1),
        "thermal_score_component": round(heat_stress_points, 1),
        "max_safe_hours": max_safe_hours
    }

    return {
        "score": score,
        "risk_category": risk_category,
        "reasons": reasons,
        "factors": factors,
        "recommended_action": recommended_action,
        "rule_version": rule_version,
        "disclaimer": disclaimer
    }
