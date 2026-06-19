"""
src/__init__.py
────────────────
Makes the src directory a Python package.
Exports all modules for clean imports.
"""

from .scoring import *
from .historical import *
from .utils import *
from .recommend import *

__all__ = [
    # scoring
    "SEVERITY_MAP",
    "PRIORITY_MAP",
    "EVENT_TYPE_SCORE_MAP",
    "RISK_ORDER",
    "RISK_COLORS",
    "RISK_BADGE_CLASSES",
    "RESOURCE_TABLE",
    "WEIGHTS",
    "classify_risk_operational",
    "make_quartile_classifier",
    "is_peak_hour",
    "get_peak_hour_binary",
    "compute_raw_score",
    "normalize_score",
    "get_reference_raw_series",
    "compute_hotspot_score",
    "get_recommendation",
    "simulate_event",
    "score_breakdown",
    "risk_badge_html",
    "confidence_chip_html",
    # historical
    "get_similar_events",
    "get_similar_events_summary",
    "zone_risk_profile",
    "cause_pattern_summary",
    "top_hotspot_junctions",
    "hourly_event_pattern",
    "get_zone_timeline",
    "get_cause_severity_distribution",
    "get_zone_risk_trend",
    "get_cause_frequency",
    "get_high_risk_patterns",
    # recommend
    "generate_event_recommendations",
    "generate_diversion_plan",
    "generate_communication_plan",
    "get_cause_special_considerations",
    "generate_recommendation_summary",
    "get_zone_recommendations",
    "get_junction_recommendations",
    "get_trend_based_recommendations",
    "get_proactive_recommendations",
    # utils
    "load_data",
    "get_risk_column",
    "get_lat_lon_columns",
    "get_unique_values",
    "kpi_card_html",
    "info_box_html",
    "page_header",
    "section_header",
]