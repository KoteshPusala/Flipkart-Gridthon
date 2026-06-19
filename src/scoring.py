"""
scoring.py
──────────
Pure scoring logic for the Bengaluru Traffic Impact System.
No recommendations (→ recommend.py), no UI helpers (→ utils.py).
Import this module everywhere scoring math is needed.
"""

import pandas as pd
import numpy as np
from typing import Callable, Dict, List, Optional, Tuple, Any

# ───────────────────────────────────────────────────────────────────────
# SEVERITY MAP  (0–100)
# ───────────────────────────────────────────────────────────────────────

SEVERITY_MAP: Dict[str, int] = {
    "pot_holes":            20,
    "test_demo":            20,
    "vehicle_breakdown":    30,
    "debris":               30,
    "road_conditions":      35,
    "others":               40,
    "fog / low visibility": 50,
    "water_logging":        60,
    "accident":             70,
    "tree_fall":            75,
    "construction":         80,
    "congestion":           85,
    "public_event":         85,
    "procession":           90,
    "vip_movement":         95,
    "protest":             100,
}

# ───────────────────────────────────────────────────────────────────────
# COMPONENT MAPS
# ───────────────────────────────────────────────────────────────────────

PRIORITY_MAP: Dict[str, int] = {
    "high": 15,
    "low":   5,
}

EVENT_TYPE_SCORE_MAP: Dict[str, int] = {
    "planned":   10,
    "unplanned":  5,
}

# ───────────────────────────────────────────────────────────────────────
# RISK DISPLAY CONSTANTS
# ───────────────────────────────────────────────────────────────────────

RISK_ORDER: List[str] = ["Low", "Medium", "High", "Severe"]

RISK_COLORS: Dict[str, str] = {
    "Low":    "#22C55E",
    "Medium": "#F59E0B",
    "High":   "#F97316",
    "Severe": "#DC2626",
}

RISK_BADGE_CLASSES: Dict[str, str] = {
    "Low":    "badge-low",
    "Medium": "badge-medium",
    "High":   "badge-high",
    "Severe": "badge-severe",
}

# ───────────────────────────────────────────────────────────────────────
# RESOURCE TABLE  (pure constant — recommend.py uses this for logic,
# app.py uses it for display; kept here so both can import from one place)
# ───────────────────────────────────────────────────────────────────────

RESOURCE_TABLE: Dict[str, Dict[str, Any]] = {
    "Low": {
        "officers":          2,
        "barricades":        0,
        "patrol_vehicles":   1,
        "response_time":     "15 min",
        "response_priority": "Normal",
        "diversion":         "None",
        "diversion_required": False,
        "notes": (
            "Standard monitoring. Deploy one patrol vehicle. "
            "No immediate action required. Document for daily log."
        ),
    },
    "Medium": {
        "officers":          5,
        "barricades":        2,
        "patrol_vehicles":   2,
        "response_time":     "10 min",
        "response_priority": "High",
        "diversion":         "Monitor",
        "diversion_required": False,
        "notes": (
            "Place barricades on one side. Assign a traffic marshal. "
            "Monitor for escalation. Inform zone HQ."
        ),
    },
    "High": {
        "officers":          10,
        "barricades":        5,
        "patrol_vehicles":   3,
        "response_time":     "5 min",
        "response_priority": "Urgent",
        "diversion":         "Partial Diversion",
        "diversion_required": True,
        "notes": (
            "Implement partial diversion. Coordinate with nearest zone HQ. "
            "Rapid response team on standby. Notify ACP."
        ),
    },
    "Severe": {
        "officers":          20,
        "barricades":        10,
        "patrol_vehicles":   5,
        "response_time":     "Immediate",
        "response_priority": "Emergency",
        "diversion":         "Full Diversion",
        "diversion_required": True,
        "notes": (
            "Full road closure + diversion mandatory. Notify city control room. "
            "DCP approval needed. Emergency protocols active."
        ),
    },
}

def get_recommendation(risk_level: str) -> Dict[str, Any]:
    """Returns the resource recommendation dict for a given risk level."""
    return RESOURCE_TABLE.get(risk_level, RESOURCE_TABLE["Medium"])


# ───────────────────────────────────────────────────────────────────────
# WEIGHTS  (must sum to 1.00 — matches preprocess.py exactly)
# ───────────────────────────────────────────────────────────────────────

WEIGHTS: Dict[str, float] = {
    "severity":      0.35,
    "road_closure":  0.20,
    "priority":      0.15,
    "zone_risk":     0.10,
    "junction_risk": 0.10,
    "peak_hour":     0.07,   # binary 0/1
    "event_type":    0.02,
    "zone_recency":  0.01,
    # cause_frequency intentionally excluded from scoring (kept in CSV for EDA)
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"

# ───────────────────────────────────────────────────────────────────────
# PEAK HOUR HELPERS
# ───────────────────────────────────────────────────────────────────────

def is_peak_hour(hour: int) -> bool:
    """True if hour falls in AM rush (7–10) or PM rush (17–21)."""
    return (7 <= hour <= 10) or (17 <= hour <= 21)


def get_peak_hour_binary(hour: int) -> int:
    """
    Returns 1 during AM rush (7–10) or PM rush (17–21), else 0.
    Matches preprocess.py peak_hour() exactly.
    """
    return 1 if (7 <= hour <= 10) or (17 <= hour <= 21) else 0


# ───────────────────────────────────────────────────────────────────────
# CLASSIFICATION
# ───────────────────────────────────────────────────────────────────────

def classify_risk_operational(score: float) -> str:
    """
    Fixed-threshold classification on 0–100 normalized impact score.
    Use for: dashboards, operator decisions, recommendations.
    Avoids the forced-quartile problem (25% Severe even for minor events).
    Matches preprocess.py risk_level_operational exactly.
    """
    if score < 25:   return "Low"
    elif score < 50: return "Medium"
    elif score < 75: return "High"
    else:            return "Severe"


def make_quartile_classifier(
    df: pd.DataFrame,
) -> Tuple[Callable[[float], str], float, float, float]:
    """
    Builds a quartile-based classifier from the loaded dataset.
    Returns (classifier_fn, q1, q2, q3).
    Use for: EDA, statistical comparisons, dashboard distribution charts.
    Matches preprocess.py risk_level_data exactly.
    """
    q1 = df["impact_score"].quantile(0.25)
    q2 = df["impact_score"].quantile(0.50)
    q3 = df["impact_score"].quantile(0.75)

    def _classify(score: float) -> str:
        if score <= q1:   return "Low"
        elif score <= q2: return "Medium"
        elif score <= q3: return "High"
        else:             return "Severe"

    return _classify, q1, q2, q3


# ───────────────────────────────────────────────────────────────────────
# CORE SCORING FUNCTIONS
# ───────────────────────────────────────────────────────────────────────

def compute_raw_score(
    severity_score:     float,
    closure_score:      float,
    priority_score:     float,
    zone_score:         float,
    junction_score:     float,
    peak_hour_binary:   int,
    event_type_score:   float,
    zone_recency_score: float,
) -> float:
    """
    Weighted raw score — matches preprocess.py formula exactly.

    Args:
        severity_score:     0–100  (from SEVERITY_MAP)
        closure_score:      0 or 20 (road_closure_score in CSV)
        priority_score:     5 or 15 (low / high)
        zone_score:         0–15   (zone_risk_score in CSV)
        junction_score:     0–15   (junction_risk_score in CSV)
        peak_hour_binary:   0 or 1 (get_peak_hour_binary)
        event_type_score:   5 or 10 (EVENT_TYPE_SCORE_MAP)
        zone_recency_score: 0–10   (zone_recency_score in CSV)

    Returns:
        Raw (unnormalized) score — use normalize_score() to get 0–100.
    """
    return (
        WEIGHTS["severity"]      * severity_score
        + WEIGHTS["road_closure"]  * closure_score
        + WEIGHTS["priority"]      * priority_score
        + WEIGHTS["zone_risk"]     * zone_score
        + WEIGHTS["junction_risk"] * junction_score
        + WEIGHTS["peak_hour"]     * peak_hour_binary
        + WEIGHTS["event_type"]    * event_type_score
        + WEIGHTS["zone_recency"]  * zone_recency_score
    )


def normalize_score(raw: float, raw_min: float, raw_max: float) -> float:
    """
    Normalizes raw score to 0–100 using dataset min/max.
    Clips to [raw_min, raw_max] before normalizing so predictor
    values never exceed dataset bounds.
    Matches preprocess.py normalization exactly.
    """
    if raw_max == raw_min:
        return 50.0
    clipped = max(raw_min, min(raw_max, raw))
    return round((clipped - raw_min) / (raw_max - raw_min) * 100, 2)


def get_reference_raw_series(df: pd.DataFrame) -> pd.Series:
    """
    Recomputes the raw score series for the full dataset.
    Used by app.py to extract DATASET_RAW_MIN / DATASET_RAW_MAX
    so the predictor normalizes against the correct range.

    Expects columns: severity_score, road_closure_score, priority_score,
    zone_risk_score, junction_risk_score, peak_hour (binary),
    event_type_score, zone_recency_score.
    """
    return compute_raw_score(
        severity_score=     df["severity_score"],
        closure_score=      df["road_closure_score"],
        priority_score=     df["priority_score"],
        zone_score=         df["zone_risk_score"],
        junction_score=     df["junction_risk_score"],
        peak_hour_binary=   df["peak_hour"],
        event_type_score=   df["event_type_score"],
        zone_recency_score= df["zone_recency_score"],
    )


# ───────────────────────────────────────────────────────────────────────
# SCORE BREAKDOWN  (for Predictor bar chart)
# ───────────────────────────────────────────────────────────────────────

def score_breakdown(
    severity_score:     float,
    closure_score:      float,
    priority_score:     float,
    zone_score:         float,
    junction_score:     float,
    peak_hour_binary:   int,
    event_type_score:   float,
    zone_recency_score: float,
) -> List[Dict[str, Any]]:
    """
    Returns per-factor weighted contributions for bar chart display.
    Matches WEIGHTS exactly — safe to sum and compare to raw_score.
    """
    components = [
        ("Severity",       WEIGHTS["severity"],      severity_score),
        ("Road Closure",   WEIGHTS["road_closure"],  closure_score),
        ("Priority",       WEIGHTS["priority"],      priority_score),
        ("Zone Risk",      WEIGHTS["zone_risk"],     zone_score),
        ("Junction Risk",  WEIGHTS["junction_risk"], junction_score),
        ("Peak Hour",      WEIGHTS["peak_hour"],     float(peak_hour_binary)),
        ("Event Type",     WEIGHTS["event_type"],    event_type_score),
        ("Zone Recency",   WEIGHTS["zone_recency"],  zone_recency_score),
    ]
    return [
        {
            "Factor":       name,
            "Weight":       f"{w * 100:.0f}%",
            "Raw Value":    round(val, 2),
            "Contribution": round(w * val, 3),
        }
        for name, w, val in components
    ]


# ───────────────────────────────────────────────────────────────────────
# HOTSPOT SCORE  (zone + junction combined)
# ───────────────────────────────────────────────────────────────────────

def compute_hotspot_score(zone_score: float, junction_score: float) -> float:
    """
    Combined structural risk score (0–30).
    zone_score (0–15) + junction_score (0–15).
    Higher = historically congested corridor.
    """
    return round(zone_score + junction_score, 2)


# ───────────────────────────────────────────────────────────────────────
# SIMULATE EVENT  (main predictor entry-point used by app.py)
# ───────────────────────────────────────────────────────────────────────

def simulate_event(
    event_cause:         str,
    priority:            str,
    road_closure:        bool,
    zone_score:          float,
    junction_score:      float,
    hour:                int,
    event_type:          str,
    zone_recency_score:  float,
    ref_min:             float,
    ref_max:             float,
    quartile_classifier: Optional[Callable[[float], str]] = None,
) -> Dict[str, Any]:
    """
    End-to-end event simulation for the Impact Predictor page.
    Scoring matches preprocess.py exactly.

    Args:
        event_cause:         Key from SEVERITY_MAP (e.g. "accident")
        priority:            "High" or "Low"
        road_closure:        True / False
        zone_score:          0–15  (looked up from dataset value_counts)
        junction_score:      0–15  (looked up from dataset value_counts)
        hour:                0–23
        event_type:          "planned" or "unplanned"
        zone_recency_score:  0–10  ((1 - mins/999) * 10)
        ref_min:             DATASET_RAW_MIN from get_reference_raw_series
        ref_max:             DATASET_RAW_MAX from get_reference_raw_series
        quartile_classifier: Optional fn from make_quartile_classifier

    Returns dict with keys:
        impact_score          float  0–100 (normalized)
        raw_score             float  (pre-normalization)
        risk_level            str    operational classification
        risk_level_quartile   str | None
        severity_score        int
        hotspot_score         float
        breakdown             List[Dict]
        component_scores      Dict[str, float]
        normalization         Dict[str, float]
    """
    # Component scores
    severity_score    = SEVERITY_MAP.get(event_cause, 40)
    priority_score    = PRIORITY_MAP.get(priority.lower(), 5)
    closure_score     = 20 if road_closure else 0
    event_type_score  = EVENT_TYPE_SCORE_MAP.get(event_type.lower(), 5)
    peak_hour_bin     = get_peak_hour_binary(hour)
    hotspot_score     = compute_hotspot_score(zone_score, junction_score)

    # Raw → normalized impact score
    raw = compute_raw_score(
        severity_score=     severity_score,
        closure_score=      closure_score,
        priority_score=     priority_score,
        zone_score=         zone_score,
        junction_score=     junction_score,
        peak_hour_binary=   peak_hour_bin,
        event_type_score=   event_type_score,
        zone_recency_score= zone_recency_score,
    )
    impact_score = normalize_score(raw, ref_min, ref_max)

    # Risk classification
    risk_level          = classify_risk_operational(impact_score)
    risk_level_quartile = quartile_classifier(impact_score) if quartile_classifier else None

    return {
        "impact_score":        impact_score,
        "raw_score":           round(raw, 4),
        "risk_level":          risk_level,
        "risk_level_quartile": risk_level_quartile,
        "severity_score":      severity_score,
        "hotspot_score":       hotspot_score,
        "breakdown":           score_breakdown(
            severity_score, closure_score, priority_score,
            zone_score, junction_score, peak_hour_bin,
            event_type_score, zone_recency_score,
        ),
        "component_scores": {
            "severity":      severity_score,
            "closure":       closure_score,
            "priority":      priority_score,
            "zone":          zone_score,
            "junction":      junction_score,
            "peak_hour":     peak_hour_bin,
            "event_type":    event_type_score,
            "zone_recency":  zone_recency_score,
        },
        "normalization": {
            "ref_min": ref_min,
            "ref_max": ref_max,
        },
    }


# ───────────────────────────────────────────────────────────────────────
# HTML HELPERS  (inline badges / chips only — no layout, no cards)
# ───────────────────────────────────────────────────────────────────────

def risk_badge_html(level: str) -> str:
    """Inline HTML risk badge. CSS classes defined in app.py stylesheet."""
    cls = RISK_BADGE_CLASSES.get(level, "badge-low")
    return f'<span class="badge {cls}">{level}</span>'


def confidence_chip_html(label: str) -> str:
    """Inline HTML confidence chip. CSS classes defined in app.py stylesheet."""
    cls_map = {
        "High":                  "conf-high",
        "Medium":                "conf-medium",
        "Low (limited history)": "conf-low",
        "No history":            "conf-none",
    }
    return f'<span class="{cls_map.get(label, "conf-none")}">{label}</span>'