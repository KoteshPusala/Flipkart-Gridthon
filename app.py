# app.py - FULLY UPDATED with Resource Score including ALL operational factors
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import time

st.set_page_config(
    page_title="Bengaluru Traffic Intelligence",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============= ALL CSS STYLES (KEPT EXACTLY AS IS) =============
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background: #F4F6F8 !important;
    color: #1A1F2E !important;
}
#MainMenu, footer, header, .stDeployButton { display: none !important; }
.block-container { padding: 2rem 2.25rem 4rem 2.25rem !important; max-width: 1440px !important; }

/* SIDEBAR */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E6EA !important;
    min-width: 220px !important; max-width: 235px !important;
}
[data-testid="stSidebar"] * { color: #6B7280 !important; }
[data-testid="stSidebar"] .stRadio > label { display: none !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 1px !important; }
[data-testid="stSidebar"] .stRadio label {
    display: flex !important; align-items: center !important;
    padding: 0.55rem 0.85rem !important; border-radius: 7px !important;
    font-size: 0.82rem !important; font-weight: 500 !important;
    color: #6B7280 !important; cursor: pointer !important;
    transition: all 0.12s !important; margin: 1px 0 !important;
}
[data-testid="stSidebar"] .stRadio label:hover { background: #F0FBF5 !important; color: #0F6E56 !important; }
[data-testid="stSidebar"] hr { border-color: #E2E6EA !important; margin: 0.65rem 0 !important; }

/* PAGE HEADER */
.pg-eyebrow { font-size:0.65rem; font-weight:600; letter-spacing:0.12em; text-transform:uppercase; color:#1D9E75; margin-bottom:0.3rem; }
.pg-title { font-size:1.75rem; font-weight:700; color:#0F172A; letter-spacing:-0.02em; line-height:1.2; margin-bottom:0.25rem; }
.pg-sub { font-size:0.85rem; color:#6B7280; margin-bottom:1.75rem; line-height:1.6; }

/* KPI CARDS */
.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(155px,1fr)); gap:0.85rem; margin-bottom:1.75rem; }
.kpi { background:#FFFFFF; border:0.5px solid #E2E6EA; border-left:3px solid #1D9E75; border-radius:8px; padding:1.1rem 1rem 0.9rem; transition:box-shadow 0.15s; }
.kpi:hover { box-shadow:0 2px 12px rgba(0,0,0,0.07); }
.kpi-lbl { font-size:0.62rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#9CA3AF; margin-bottom:0.35rem; }
.kpi-val { font-family:'JetBrains Mono',monospace; font-size:1.75rem; font-weight:700; line-height:1.1; color:#0F172A; }
.kpi-sub { font-size:0.68rem; color:#9CA3AF; margin-top:0.2rem; }

/* SECTION HEADER */
.sec { font-size:0.72rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#9CA3AF; padding-bottom:0.5rem; border-bottom:1px solid #E2E6EA; margin:1.5rem 0 0.85rem; }

/* RISK BADGES */
.badge { display:inline-flex; align-items:center; padding:0.14rem 0.6rem; border-radius:999px; font-size:0.65rem; font-weight:700; letter-spacing:0.05em; text-transform:uppercase; }
.badge-Low    { background:#E1F5EE; color:#0F6E56; }
.badge-Medium { background:#FFF3CD; color:#854F0B; }
.badge-High   { background:#FEE9D7; color:#993C1D; }
.badge-Severe { background:#FEE2E2; color:#A32D2D; }

/* INFO / WARN BOXES */
.info-box { background:#F0FBF5; border:0.5px solid #9FE1CB; border-left:3px solid #1D9E75; border-radius:8px; padding:0.85rem 1rem; font-size:0.82rem; color:#374151; line-height:1.7; margin:0.65rem 0; }
.info-box b { color:#0F172A; }
.warn-box { background:#FFFBEB; border:0.5px solid #FDE68A; border-left:3px solid #EF9F27; border-radius:8px; padding:0.85rem 1rem; font-size:0.82rem; color:#78350F; line-height:1.7; margin:0.65rem 0; }

/* PREDICTOR */
.result-header { background:#FFFFFF; border:0.5px solid #E2E6EA; border-radius:10px; padding:1.5rem; margin-top:1.25rem; }
.result-score { font-family:'JetBrains Mono',monospace; font-size:3.5rem; font-weight:700; line-height:1; letter-spacing:-0.03em; }
.result-risk { font-size:0.68rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; margin-top:0.35rem; }
.factor-row { display:flex; justify-content:space-between; align-items:center; padding:0.35rem 0; border-bottom:0.5px solid #F3F4F6; font-size:0.78rem; }
.factor-name { color:#6B7280; }
.factor-val { font-family:'JetBrains Mono',monospace; font-weight:600; color:#0F172A; }

/* PEAK TAG */
.peak-on  { display:inline-flex;align-items:center;gap:5px;background:#FEE9D7;color:#993C1D;border-radius:999px;padding:0.2rem 0.7rem;font-size:0.7rem;font-weight:600; }
.peak-off { display:inline-flex;align-items:center;gap:5px;background:#E1F5EE;color:#0F6E56;border-radius:999px;padding:0.2rem 0.7rem;font-size:0.7rem;font-weight:600; }

/* RESOURCE CARDS */
.res-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:0.85rem; margin:1.1rem 0; }
.res-card { background:#FFFFFF; border:0.5px solid #E2E6EA; border-radius:10px; padding:1.1rem 0.75rem; text-align:center; transition:box-shadow 0.15s; }
.res-card:hover { box-shadow:0 2px 10px rgba(0,0,0,0.07); }
.res-icon { font-size:1.5rem; margin-bottom:0.3rem; }
.res-val  { font-family:'JetBrains Mono',monospace; font-size:1.6rem; font-weight:700; color:#0F172A; line-height:1.1; }
.res-lbl  { font-size:0.6rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#9CA3AF; margin-top:0.25rem; }

/* ACTION BOX */
.action-box { background:#F8FAFC; border:0.5px solid #E2E6EA; border-radius:10px; padding:1.1rem 1.25rem; margin-top:0.85rem; font-size:0.83rem; color:#374151; line-height:1.8; }
.action-tag { font-size:0.6rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:#9CA3AF; margin-bottom:0.5rem; }

/* STAT ITEMS */
.stat-item { text-align:center; padding:0.5rem; }
.stat-val { font-family:'JetBrains Mono',monospace; font-size:1.3rem; font-weight:700; color:#0F172A; }
.stat-lbl { font-size:0.6rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; color:#9CA3AF; margin-top:0.15rem; }

/* BUTTONS */
.stButton > button {
    background: #1D9E75 !important; color: #FFFFFF !important; border: none !important;
    border-radius: 7px !important; font-weight: 600 !important; font-size: 0.84rem !important;
    padding: 0.6rem 1.4rem !important; font-family: 'Inter', sans-serif !important;
    transition: all 0.15s !important; letter-spacing: 0.01em !important;
}
.stButton > button:hover { background: #0F6E56 !important; box-shadow: 0 2px 8px rgba(29,158,117,0.3) !important; transform: translateY(-1px) !important; }

/* FORM ELEMENTS */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: #FFFFFF !important; border: 1px solid #D1D5DB !important;
    border-radius: 7px !important; color: #1A1F2E !important; font-size: 0.84rem !important;
}
[data-testid="stSelectbox"] label,
[data-testid="stSlider"] label,
[data-testid="stCheckbox"] label,
[data-testid="stMultiSelect"] label {
    font-size: 0.75rem !important; font-weight: 600 !important;
    color: #374151 !important; letter-spacing: 0.03em !important;
}

/* DATAFRAME */
[data-testid="stDataFrame"] { border: 0.5px solid #E2E6EA !important; border-radius: 8px !important; overflow: hidden !important; background: #FFFFFF !important; }

/* SCROLLBAR */
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:#F4F6F8; }
::-webkit-scrollbar-thumb { background:#D1D5DB; border-radius:999px; }
::-webkit-scrollbar-thumb:hover { background:#9CA3AF; }

.js-plotly-plot .plotly .modebar { display:none !important; }

@media (max-width:768px) {
    .block-container { padding:1rem !important; }
    .pg-title { font-size:1.35rem; }
    .result-score { font-size:2.5rem; }
}

/* NEW: EXPLANATION BOXES */
.explain-box {
    background:#F8FAFC;
    border:0.5px solid #E2E6EA;
    border-radius:10px;
    padding:1rem 1.25rem;
    margin:0.65rem 0;
    font-size:0.82rem;
    color:#374151;
    line-height:1.8;
}
.explain-box strong { color:#0F172A; }
.explain-highlight {
    background:#F0FBF5;
    border-left:3px solid #1D9E75;
    padding:0.5rem 0.8rem;
    margin:0.25rem 0;
    border-radius:4px;
}
.op-factor-box {
    background:#F8FAFC;
    border:0.5px solid #E2E6EA;
    border-radius:8px;
    padding:0.75rem 1rem;
    margin:0.35rem 0;
    font-size:0.78rem;
    line-height:1.6;
}
.op-factor-box .factor-label {
    font-weight:600;
    color:#0F172A;
}
.op-factor-box .factor-boost {
    color:#1D9E75;
    font-weight:600;
}
.op-factor-box .factor-boost-active {
    color:#D85A30;
    font-weight:700;
}
</style>
""", unsafe_allow_html=True)


# ============= DATA LOADING =============
@st.cache_data
def load_data():
    return pd.read_csv("processed_traffic_events.csv")

df = load_data()

q1 = df["impact_score"].quantile(0.25)
q2 = df["impact_score"].quantile(0.50)
q3 = df["impact_score"].quantile(0.75)

RISK_COLORS = {"Low": "#1D9E75", "Medium": "#EF9F27", "High": "#D85A30", "Severe": "#E24B4A"}
RISK_BG     = {"Low": "#E1F5EE", "Medium": "#FFF3CD", "High": "#FEE9D7", "Severe": "#FEE2E2"}
RISK_ORDER  = ["Low", "Medium", "High", "Severe"]

SEVERITY_MAP = {
    "pot_holes": 20, "vehicle_breakdown": 30, "road_conditions": 35, "others": 40,
    "water_logging": 60, "accident": 70, "tree_fall": 75, "construction": 80,
    "congestion": 85, "public_event": 85, "procession": 90, "vip_movement": 95, "protest": 100,
}

# ============= RESOURCE TABLE (UPDATED with ALL resource types) =============
RESOURCE_TABLE = {
    "Low": {
        "officers": 2, "patrol_vehicles": 1, "barricades": 0,
        "tow_trucks": 0, "ambulance": 0, "emergency_teams": 0,
        "time": "15 min", "diversion": "None",
        "priority": "NORMAL",
        "notes": "Standard monitoring. Deploy one patrol vehicle for observation. No barricades required. Log event and monitor via CCTV. Escalate if situation changes."
    },
    "Medium": {
        "officers": 5, "patrol_vehicles": 2, "barricades": 2,
        "tow_trucks": 1, "ambulance": 0, "emergency_teams": 0,
        "time": "10 min", "diversion": "Monitor",
        "priority": "ELEVATED",
        "notes": "Position barricades on approach roads. Assign a senior traffic marshal. Coordinate with nearest PCR van. Review every 30 minutes — escalate to High if congestion grows."
    },
    "High": {
        "officers": 10, "patrol_vehicles": 3, "barricades": 5,
        "tow_trucks": 2, "ambulance": 1, "emergency_teams": 1,
        "time": "7 min", "diversion": "Partial",
        "priority": "URGENT",
        "notes": "Activate partial diversion on primary approach. Alert Zone HQ and request rapid response unit on standby. Coordinate signal timing with traffic control centre."
    },
    "Severe": {
        "officers": 20, "patrol_vehicles": 5, "barricades": 12,
        "tow_trucks": 4, "ambulance": 2, "emergency_teams": 2,
        "time": "3 min", "diversion": "Full Required",
        "priority": "EMERGENCY",
        "notes": "Immediate full road closure and diversion mandatory. Notify Joint Commissioner. Activate all PCR vans in zone. Coordinate with BBMP for barricade support. Issue public advisory."
    },
}

PLANNED = ["construction", "public_event", "procession", "vip_movement"]
PRIORITY_COLORS = {"NORMAL": "#1D9E75", "ELEVATED": "#EF9F27", "URGENT": "#D85A30", "EMERGENCY": "#E24B4A"}

# ============= EVENT-TYPE RESOURCE SCORES =============
EVENT_TYPE_RESOURCE_SCORE = {
    "pot_holes": 10, "vehicle_breakdown": 30, "road_conditions": 25, "others": 20,
    "water_logging": 45, "accident": 75, "tree_fall": 55, "construction": 50,
    "congestion": 40, "public_event": 60, "procession": 70, "vip_movement": 65,
    "protest": 90, "fog / low visibility": 35, "debris": 30, "test_demo": 10,
}

# ============= BASE PROFILES (UPDATED with ALL resources) =============
BASE_PROFILES = {
    "accident": {
        "officers": 6, "patrol_vehicles": 2, "barricades": 3,
        "tow_trucks": 2, "ambulance": 1, "emergency_teams": 1,
        "icon": "🚗", "label": "Accident",
        "diversion": "Partial",
        "primary_resources": ["Officers", "Patrol Vehicles", "Tow Trucks", "Ambulance"],
    },
    "vehicle_breakdown": {
        "officers": 3, "patrol_vehicles": 1, "barricades": 2,
        "tow_trucks": 2, "ambulance": 0, "emergency_teams": 0,
        "icon": "🚛", "label": "Vehicle / Truck Breakdown",
        "diversion": "Monitor",
        "primary_resources": ["Officers", "Tow Trucks"],
    },
    "construction": {
        "officers": 4, "patrol_vehicles": 2, "barricades": 8,
        "tow_trucks": 0, "ambulance": 0, "emergency_teams": 0,
        "icon": "🏗️", "label": "Road Construction",
        "diversion": "Partial",
        "primary_resources": ["Officers", "Barricades"],
    },
    "congestion": {
        "officers": 5, "patrol_vehicles": 2, "barricades": 4,
        "tow_trucks": 0, "ambulance": 0, "emergency_teams": 0,
        "icon": "🚦", "label": "Traffic Congestion",
        "diversion": "Monitor",
        "primary_resources": ["Officers", "Patrol Vehicles", "Barricades"],
    },
    "public_event": {
        "officers": 8, "patrol_vehicles": 3, "barricades": 10,
        "tow_trucks": 0, "ambulance": 1, "emergency_teams": 1,
        "icon": "🎭", "label": "Public Event",
        "diversion": "Full",
        "primary_resources": ["Officers", "Barricades", "Emergency Teams"],
    },
    "procession": {
        "officers": 10, "patrol_vehicles": 4, "barricades": 12,
        "tow_trucks": 0, "ambulance": 1, "emergency_teams": 1,
        "icon": "🚶", "label": "Procession / March",
        "diversion": "Full",
        "primary_resources": ["Officers", "Barricades", "Patrol Vehicles"],
    },
    "vip_movement": {
        "officers": 15, "patrol_vehicles": 5, "barricades": 12,
        "tow_trucks": 0, "ambulance": 1, "emergency_teams": 2,
        "icon": "🛡️", "label": "VIP Movement",
        "diversion": "Full",
        "primary_resources": ["Officers", "Patrol Vehicles", "Emergency Teams"],
    },
    "protest": {
        "officers": 15, "patrol_vehicles": 5, "barricades": 15,
        "tow_trucks": 0, "ambulance": 2, "emergency_teams": 2,
        "icon": "📢", "label": "Protest / Demonstration",
        "diversion": "Full Required",
        "primary_resources": ["Officers", "Barricades", "Patrol Vehicles", "Ambulance"],
    },
    "water_logging": {
        "officers": 4, "patrol_vehicles": 2, "barricades": 6,
        "tow_trucks": 1, "ambulance": 0, "emergency_teams": 1,
        "icon": "💧", "label": "Water Logging / Flooding",
        "diversion": "Partial",
        "primary_resources": ["Officers", "Barricades"],
    },
    "tree_fall": {
        "officers": 4, "patrol_vehicles": 2, "barricades": 5,
        "tow_trucks": 1, "ambulance": 0, "emergency_teams": 0,
        "icon": "🌳", "label": "Tree Fall",
        "diversion": "Partial",
        "primary_resources": ["Officers", "Barricades"],
    },
    "_default": {
        "officers": 2, "patrol_vehicles": 1, "barricades": 1,
        "tow_trucks": 0, "ambulance": 0, "emergency_teams": 0,
        "icon": "⚠️", "label": "General Event",
        "diversion": "None",
        "primary_resources": ["Officers", "Patrol Vehicles"],
    },
}

RESOURCE_ICONS = {
    "officers": ("👮", "Officers"),
    "patrol_vehicles": ("🚔", "Patrol Vehicles"),
    "barricades": ("🚧", "Barricades"),
    "tow_trucks": ("🚛", "Tow Trucks"),
    "ambulance": ("🚑", "Ambulance"),
    "emergency_teams": ("🆘", "Emergency Teams"),
}


# ======================================================================
# ⭐ IMPROVED: calculate_resource_score with ALL operational factors
# ======================================================================
def calculate_resource_score(
    impact_score, severity_score, road_closure_score,
    zone_risk_score, junction_risk_score, event_cause, 
    df_ref, 
    peak_hour=False, 
    similar_event_count=0, 
    avg_impact_score=0
):
    """
    Composite resource requirement score (0-100).
    
    NOW INCLUDES ALL OPERATIONAL FACTORS:
    - Impact (35%) - primary demand signal
    - Severity (15%) - event severity
    - Road Closure (10%) - closure complexity
    - Zone Risk (10%) - location risk
    - Junction Risk (10%) - junction complexity
    - Event Type (10%) - event-type resource intensity
    - Peak Hour (5%) - time-of-day amplifier ⭐ NEW
    - Historical Similarity (3%) - experience factor ⭐ NEW
    - Historical Impact (2%) - past severity signal ⭐ NEW
    Total = 100%
    """
    def _norm(val, col):
        mn = df_ref[col].min()
        mx = df_ref[col].max()
        if mx == mn:
            return 50.0
        return float(np.clip((val - mn) / (mx - mn) * 100, 0, 100))

    # ── Base components ──
    et_raw = EVENT_TYPE_RESOURCE_SCORE.get(event_cause, 20)
    impact_norm = float(np.clip(impact_score, 0, 100))
    severity_norm = _norm(severity_score, "severity_score")
    road_closure_norm = _norm(road_closure_score, "road_closure_score")
    zone_norm = _norm(zone_risk_score, "zone_risk_score")
    junction_norm = _norm(junction_risk_score, "junction_risk_score")
    et_norm = float(np.clip(et_raw, 0, 100))

    # ── Operational factors ──
    # Peak Hour: 0-100 scale (0 or 100)
    peak_hour_score = 100 if peak_hour else 0
    
    # Historical Similarity: 0-100 based on count
    if similar_event_count > 30:
        similarity_score = 100
    elif similar_event_count > 15:
        similarity_score = 70
    elif similar_event_count > 5:
        similarity_score = 40
    else:
        similarity_score = 10
    
    # Historical Impact: 0-100 based on avg impact
    if avg_impact_score > 75:
        history_impact_score = 100
    elif avg_impact_score > 60:
        history_impact_score = 70
    elif avg_impact_score > 40:
        history_impact_score = 40
    else:
        history_impact_score = 10

    # ── Weighted composite ──
    raw = (
        0.35 * impact_norm +           # Primary demand
        0.15 * severity_norm +         # Event severity
        0.10 * road_closure_norm +     # Closure complexity
        0.10 * zone_norm +             # Location risk
        0.10 * junction_norm +         # Junction complexity
        0.10 * et_norm +               # Event-type intensity
        0.05 * peak_hour_score +       # ⭐ Time-of-day amplifier
        0.03 * similarity_score +      # ⭐ Experience factor
        0.02 * history_impact_score    # ⭐ Past severity signal
    )
    
    return round(float(np.clip(raw, 0, 100)), 1)


def get_base_resources(event_cause):
    return BASE_PROFILES.get(event_cause, BASE_PROFILES["_default"]).copy()


def scale_resources(base, resource_score, risk_level, 
                    peak_hour=False, road_closure=False, 
                    junction_risk_score=0, zone_risk_score=0,
                    similar_event_count=0, avg_impact_score=0):
    """
    Scales base deployment using ALL operational factors.
    """
    scaled = base.copy()
    rs = resource_score

    # ── BASE SCALING from resource_score ──
    scaled["officers"] = base["officers"] + round(rs / 15)
    scaled["barricades"] = base["barricades"] + round(rs / 20)
    scaled["patrol_vehicles"] = base["patrol_vehicles"] + round(rs / 25)
    scaled["tow_trucks"] = base["tow_trucks"] + round(rs / 35)
    scaled["ambulance"] = base["ambulance"] + round(rs / 45)
    scaled["emergency_teams"] = base["emergency_teams"] + round(rs / 35)

    # ── 1. PEAK HOUR ─────────────────────────────────────────────
    if peak_hour:
        scaled["officers"] += 2
        scaled["patrol_vehicles"] += 1
        scaled["barricades"] += 2

    # ── 2. ROAD CLOSURE ──────────────────────────────────────────
    if road_closure:
        scaled["barricades"] += 5
        scaled["officers"] += 2
        scaled["patrol_vehicles"] += 1

    # ── 3. JUNCTION RISK (0-100) ────────────────────────────────
    if junction_risk_score > 80:
        scaled["officers"] += 2
        scaled["barricades"] += 2
    elif junction_risk_score > 60:
        scaled["officers"] += 1
        scaled["barricades"] += 1

    # ── 4. ZONE RISK (0-100) ─────────────────────────────────────
    if zone_risk_score > 70:
        scaled["patrol_vehicles"] += 1
        scaled["officers"] += 1
    elif zone_risk_score > 50:
        scaled["patrol_vehicles"] += 1

    # ── 5. HISTORICAL SIMILARITY ────────────────────────────────
    if similar_event_count > 30:
        scaled["officers"] += 1
        scaled["patrol_vehicles"] += 1
    elif similar_event_count > 15:
        scaled["officers"] += 1

    # ── 6. HISTORICAL IMPACT ────────────────────────────────────
    if avg_impact_score > 75:
        scaled["ambulance"] += 1
        scaled["emergency_teams"] += 1
    elif avg_impact_score > 60:
        scaled["ambulance"] += 1

    # ── 7. SEVERE RISK FLOOR ────────────────────────────────────
    if risk_level == "Severe":
        scaled["officers"] = max(scaled["officers"], int(base["officers"] * 1.5))
        scaled["patrol_vehicles"] = max(scaled["patrol_vehicles"], int(base["patrol_vehicles"] * 1.5))
        scaled["ambulance"] = max(scaled["ambulance"], 2)

    # ── HARD CAPS ────────────────────────────────────────────────
    caps = {
        "officers": 30, "patrol_vehicles": 10, "barricades": 25,
        "tow_trucks": 6, "ambulance": 5, "emergency_teams": 6,
    }
    for k, cap in caps.items():
        if k in scaled:
            scaled[k] = min(scaled[k], cap)

    return scaled


def get_deployment_tier(resource_score):
    if resource_score < 30:
        return "minimal", "#9CA3AF", "Minimal Deployment"
    elif resource_score < 60:
        return "moderate", "#EF9F27", "Moderate Deployment"
    elif resource_score < 80:
        return "major", "#D85A30", "Major Deployment"
    else:
        return "critical", "#E24B4A", "Critical Deployment"


def generate_resource_explanation(event_cause, risk_level, impact_score, resource_score,
                                   resources, peak_hour=False, road_closure=False,
                                   zone=None, junction=None,
                                   junction_risk_score=0, zone_risk_score=0,
                                   similar_event_count=0, avg_impact_score=0):
    """
    Generates natural-language justification with ALL operational factors.
    """
    cause_display = event_cause.replace("_", " ").title()
    loc_parts = []
    if junction and junction != "(Not Selected)":
        loc_parts.append(f"at {junction}")
    if zone and zone != "(Not Selected)":
        loc_parts.append(f"in {zone} zone")
    loc_str = " ".join(loc_parts) if loc_parts else "at the incident site"
    peak_str = " during peak traffic hours" if peak_hour else ""

    res_parts = []
    for key, (icon, label) in RESOURCE_ICONS.items():
        val = resources.get(key, 0)
        if val and val > 0:
            res_parts.append(f"{val} {label.lower()}")

    if len(res_parts) > 1:
        res_str = ", ".join(res_parts[:-1]) + f", and {res_parts[-1]}"
    elif res_parts:
        res_str = res_parts[0]
    else:
        res_str = "standard patrol resources"

    tier_key, _, tier_label = get_deployment_tier(resource_score)

    risk_adj = {
        "Low": "Low-impact", "Medium": "Moderate-impact",
        "High": "High-impact", "Severe": "Critical",
    }.get(risk_level, "")

    tier_context = {
        "minimal": "Standard monitoring protocols apply.",
        "moderate": "Moderate coordination with zone HQ required.",
        "major": "Rapid response unit activation recommended.",
        "critical": "Emergency protocols active — notify DCP immediately.",
    }.get(tier_key, "")

    # ── BUILD THE EXPLANATION WITH ALL FACTORS ──
    factors = []

    if impact_score > 75:
        factors.append(f"• High impact score ({impact_score:.1f}/100) indicates severe disruption potential.")
    elif impact_score > 50:
        factors.append(f"• Moderate impact score ({impact_score:.1f}/100) suggests manageable disruption.")
    else:
        factors.append(f"• Low impact score ({impact_score:.1f}/100) — standard response sufficient.")

    severity_display = {
        20: "Minor", 30: "Moderate", 35: "Moderate", 40: "Elevated",
        60: "Significant", 70: "High", 75: "Very High", 80: "Severe",
        85: "Severe", 90: "Critical", 95: "Critical", 100: "Extreme"
    }.get(SEVERITY_MAP.get(event_cause, 40), "Moderate")
    factors.append(f"• Severity level: <strong>{severity_display}</strong> ({SEVERITY_MAP.get(event_cause, 40)}/100)")

    if peak_hour:
        factors.append("• ⏰ <strong>PEAK HOUR</strong> — +2 officers, +1 patrol, +2 barricades deployed")

    if road_closure:
        factors.append("• 🚧 <strong>ROAD CLOSURE</strong> — +5 barricades, +2 officers, +1 patrol deployed")

    if junction_risk_score > 80:
        factors.append(f"• ⚠️ <strong>HIGH JUNCTION RISK</strong> ({junction_risk_score:.0f}/100) — +2 officers, +2 barricades")
    elif junction_risk_score > 60:
        factors.append(f"• ⚠️ <strong>ELEVATED JUNCTION RISK</strong> ({junction_risk_score:.0f}/100) — +1 officer, +1 barricade")

    if zone_risk_score > 70:
        factors.append(f"• 📍 <strong>HIGH ZONE RISK</strong> ({zone_risk_score:.0f}/100) — +1 patrol, +1 officer")
    elif zone_risk_score > 50:
        factors.append(f"• 📍 <strong>ELEVATED ZONE RISK</strong> ({zone_risk_score:.0f}/100) — +1 patrol")

    if similar_event_count > 30:
        factors.append(f"• 📊 <strong>{similar_event_count} similar events</strong> — +1 officer, +1 patrol (high confidence)")
    elif similar_event_count > 15:
        factors.append(f"• 📊 <strong>{similar_event_count} similar events</strong> — +1 officer (moderate confidence)")

    if avg_impact_score > 75:
        factors.append(f"• 🚑 <strong>Historical avg impact {avg_impact_score:.0f}/100</strong> — +1 ambulance, +1 emergency team")
    elif avg_impact_score > 60:
        factors.append(f"• 🚑 <strong>Historical avg impact {avg_impact_score:.0f}/100</strong> — +1 ambulance")

    factors.append(f"• Risk level: <strong>{risk_level}</strong> — dictates response urgency")

    return (
        f"{risk_adj} <b>{cause_display}</b> detected {loc_str}{peak_str}. "
        f"Resource Score: <b>{resource_score}/100</b> — {tier_label.lower()} warranted. "
        f"Recommended deployment includes {res_str}. {tier_context}<br><br>"
        f"<strong>Why this recommendation?</strong><br>"
        + "<br>".join(factors)
    )


@st.cache_data
def compute_dataset_resource_scores(df_in):
    """Pre-compute resource scores for dataset sample."""
    mn = {c: df_in[c].min() for c in ["impact_score","severity_score","road_closure_score","zone_risk_score","junction_risk_score"]}
    mx = {c: df_in[c].max() for c in ["impact_score","severity_score","road_closure_score","zone_risk_score","junction_risk_score"]}

    def norm(v, col):
        if mx[col] == mn[col]:
            return 50.0
        return float(np.clip((v - mn[col]) / (mx[col] - mn[col]) * 100, 0, 100))

    scores = []
    for _, row in df_in.iterrows():
        et = EVENT_TYPE_RESOURCE_SCORE.get(row.get("event_cause", "others"), 20)
        raw = (
            0.35 * norm(row["impact_score"], "impact_score")
            + 0.15 * norm(row["severity_score"], "severity_score")
            + 0.10 * norm(row["road_closure_score"], "road_closure_score")
            + 0.10 * norm(row["zone_risk_score"], "zone_risk_score")
            + 0.10 * norm(row["junction_risk_score"], "junction_risk_score")
            + 0.10 * float(np.clip(et, 0, 100))
            + 0.05 * (100 if row.get("peak_hour", 0) else 0)
        )
        scores.append(round(float(np.clip(raw, 0, 100)), 1))
    return scores


def get_risk(score):
    if score <= q1: return "Low"
    elif score <= q2: return "Medium"
    elif score <= q3: return "High"
    else: return "Severe"


def is_peak(h):
    return (7 <= h <= 10) or (17 <= h <= 21)


def pdef(t=8):
    return dict(
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        font=dict(family="Inter, sans-serif", size=11, color="#6B7280"),
        margin=dict(l=0, r=0, t=t, b=0),
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor="#E2E6EA",
                        font=dict(family="Inter", size=12, color="#1A1F2E")),
    )


def sec(label):
    st.markdown(f'<div class="sec">{label}</div>', unsafe_allow_html=True)


def badge(risk):
    return f'<span class="badge badge-{risk}">{risk}</span>'


# ============= SIDEBAR =============
with st.sidebar:
    st.markdown("""
    <div style="padding:0.75rem 0.85rem 0.5rem">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
        <div style="width:28px;height:28px;background:#E1F5EE;border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:14px">🚦</div>
        <div>
          <div style="font-size:0.88rem;font-weight:700;color:#0F172A;letter-spacing:-0.01em">BTP · Traffic Intel</div>
          <div style="font-size:0.62rem;color:#9CA3AF;letter-spacing:0.04em">BENGALURU TRAFFIC POLICE</div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio("nav", [
        "📊  Dashboard",
        "🔮  Impact Predictor",
        "🛡️  Resource Planner",
        "🕵️  Historical Insights",
        "🗺️  Risk Heatmap",
        "📋  Recommendation Explainer",
        "🚦  Live Incident Simulator",
    ], label_visibility="collapsed")

    st.markdown("---")

    total_ev = len(df)
    sev_n = int((df["risk_level_operational"] == "Severe").sum())
    peak_n = int(df["peak_hour"].sum()) if "peak_hour" in df.columns else 0

    st.markdown(f"""
    <div style="padding:0 0.85rem;font-size:0.72rem;color:#9CA3AF;line-height:2">
      <div style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#D1D5DB;margin-bottom:3px">Dataset</div>
      <span style="color:#374151;font-weight:500">{total_ev:,}</span> total events<br>
      <span style="color:#E24B4A;font-weight:500">{sev_n:,}</span> severe risk events<br>
      <span style="color:#D85A30;font-weight:500">{peak_n:,}</span> peak-hour events
      <br>
      <div style="font-size:0.6rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#D1D5DB;margin:8px 0 3px">Quartile Thresholds</div>
      Q1 <span style="color:#1D9E75;font-family:'JetBrains Mono',monospace;font-weight:600">{q1:.1f}</span> ·
      Q2 <span style="color:#EF9F27;font-family:'JetBrains Mono',monospace;font-weight:600">{q2:.1f}</span> ·
      Q3 <span style="color:#E24B4A;font-family:'JetBrains Mono',monospace;font-weight:600">{q3:.1f}</span>
    </div>""", unsafe_allow_html=True)


# ======================================================================
# PAGE 1 — DASHBOARD
# ======================================================================

if page == "📊  Dashboard":
    st.markdown('<div class="pg-eyebrow">Live Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">Traffic Event Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Bengaluru road event intelligence across 8,173 recorded incidents — risk distribution, hotspots, and temporal patterns.</div>', unsafe_allow_html=True)

    total = len(df)
    sev_n = int((df["risk_level_operational"] == "Severe").sum())
    high_n = int((df["risk_level_operational"] == "High").sum())
    cls_n = int(df["requires_road_closure"].sum())
    peak_n = int(df["peak_hour"].sum()) if "peak_hour" in df.columns else 0
    avg_imp = round(df["impact_score"].mean(), 1)

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi" style="border-left-color:#1D9E75">
        <div class="kpi-lbl">Total Events</div>
        <div class="kpi-val">{total:,}</div>
        <div class="kpi-sub">All recorded incidents</div>
      </div>
      <div class="kpi" style="border-left-color:#E24B4A">
        <div class="kpi-lbl">Severe Risk</div>
        <div class="kpi-val" style="color:#A32D2D">{sev_n:,}</div>
        <div class="kpi-sub">{sev_n/total*100:.1f}% of total</div>
      </div>
      <div class="kpi" style="border-left-color:#D85A30">
        <div class="kpi-lbl">High Risk</div>
        <div class="kpi-val" style="color:#993C1D">{high_n:,}</div>
        <div class="kpi-sub">{high_n/total*100:.1f}% of total</div>
      </div>
      <div class="kpi" style="border-left-color:#EF9F27">
        <div class="kpi-lbl">Road Closures</div>
        <div class="kpi-val" style="color:#854F0B">{cls_n:,}</div>
        <div class="kpi-sub">{cls_n/total*100:.1f}% required</div>
      </div>
      <div class="kpi" style="border-left-color:#7F77DD">
        <div class="kpi-lbl">Peak-Hour Events</div>
        <div class="kpi-val" style="color:#534AB7">{peak_n:,}</div>
        <div class="kpi-sub">7–10am · 5–9pm</div>
      </div>
      <div class="kpi" style="border-left-color:#1D9E75">
        <div class="kpi-lbl">Avg Impact Score</div>
        <div class="kpi-val" style="color:#0F6E56">{avg_imp}</div>
        <div class="kpi-sub">out of 100</div>
      </div>
    </div>""", unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2], gap="medium")
    with c1:
        sec("Event Type Breakdown")
        cdf = df["event_cause"].value_counts().reset_index()
        cdf.columns = ["Cause", "Count"]
        cdf["Cause"] = cdf["Cause"].str.replace("_", " ").str.title()
        fig = px.bar(cdf, x="Count", y="Cause", orientation="h",
                     color="Count", color_continuous_scale=[[0, "#9FE1CB"], [1, "#0F6E56"]], height=410)
        fig.update_layout(**pdef(), coloraxis_showscale=False,
                          xaxis=dict(gridcolor="#F3F4F6", title=""),
                          yaxis=dict(gridcolor="rgba(0,0,0,0)", title=""))
        fig.update_traces(marker_line_width=0)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        sec("Risk Distribution")
        rd = df["risk_level_operational"].value_counts().reindex(RISK_ORDER).fillna(0).reset_index()
        rd.columns = ["Risk", "Count"]
        fig2 = px.pie(rd, names="Risk", values="Count", color="Risk",
                      color_discrete_map=RISK_COLORS, height=410, hole=0.48)
        fig2.update_traces(textposition="outside", textinfo="percent+label", textfont=dict(size=11),
                           pull=[0.05 if r == "Severe" else 0 for r in RISK_ORDER],
                           marker=dict(line=dict(color="#F4F6F8", width=2)))
        fig2.update_layout(**pdef(), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns([3, 2], gap="medium")
    with c3:
        sec("Top 12 Zones by Event Count")
        zc = df["zone"].dropna().value_counts().head(12).reset_index()
        zc.columns = ["Zone", "Count"]
        fig3 = px.bar(zc, x="Zone", y="Count",
                      color="Count", color_continuous_scale=[[0, "#B5D4F4"], [1, "#185FA5"]], height=320)
        fig3.update_layout(**pdef(), coloraxis_showscale=False,
                           xaxis=dict(tickangle=-30, gridcolor="rgba(0,0,0,0)"),
                           yaxis=dict(gridcolor="#F3F4F6", title=""))
        fig3.update_traces(marker_line_width=0)
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        sec("Planned vs Unplanned")
        if "event_category" in df.columns:
            pc = df["event_category"].value_counts().reset_index()
            pc.columns = ["Cat", "Count"]
            fig4 = px.pie(pc, names="Cat", values="Count",
                          color_discrete_map={"Planned": "#1D9E75", "Unplanned": "#EF9F27"},
                          height=320, hole=0.48)
            fig4.update_traces(textposition="outside", textinfo="percent+label", textfont=dict(size=11),
                               marker=dict(line=dict(color="#F4F6F8", width=2)))
            fig4.update_layout(**pdef(), showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

    sec("Hourly Event Pattern — Peak Windows")
    if "hour" in df.columns:
        hdf = df["hour"].dropna().value_counts().sort_index().reset_index()
        hdf.columns = ["Hour", "Count"]
        fig5 = go.Figure()
        for x0, x1, lbl in [(7, 10, "AM Rush"), (17, 21, "PM Rush")]:
            fig5.add_vrect(x0=x0, x1=x1, fillcolor="#FAEEDA", opacity=0.55, line_width=0,
                           annotation_text=lbl, annotation_position="top left",
                           annotation_font_size=9, annotation_font_color="#854F0B")
        fig5.add_trace(go.Scatter(
            x=hdf["Hour"], y=hdf["Count"], mode="lines+markers",
            line=dict(color="#1D9E75", width=2.5),
            marker=dict(size=7, color="#1D9E75", line=dict(width=2, color="#FFFFFF")),
            fill="tozeroy", fillcolor="rgba(29,158,117,0.08)", name="Events",
        ))
        fig5.update_layout(**pdef(20), height=230,
                           xaxis=dict(title="Hour of Day", dtick=2, gridcolor="#F3F4F6", tickfont=dict(size=10)),
                           yaxis=dict(title="Events", gridcolor="#F3F4F6", tickfont=dict(size=10)))
        st.plotly_chart(fig5, use_container_width=True)

    c5, c6 = st.columns(2, gap="medium")
    with c5:
        sec("Impact Score Distribution")
        fig6 = go.Figure()
        fig6.add_trace(go.Histogram(x=df["impact_score"], nbinsx=40,
                                    marker_color="#9FE1CB", marker_line_width=0, opacity=0.9))
        for val, clr, lbl in [(q1, "#1D9E75", f"Q1·{q1:.0f}"), (q2, "#EF9F27", f"Q2·{q2:.0f}"), (q3, "#E24B4A", f"Q3·{q3:.0f}")]:
            fig6.add_vline(x=val, line_dash="dash", line_color=clr, line_width=1.5,
                           annotation_text=lbl, annotation_font_size=9, annotation_font_color=clr)
        fig6.update_layout(**pdef(), height=250, bargap=0.04,
                           xaxis=dict(title="Impact Score", gridcolor="#F3F4F6"),
                           yaxis=dict(title="Events", gridcolor="#F3F4F6"), showlegend=False)
        st.plotly_chart(fig6, use_container_width=True)

    with c6:
        sec("Avg Impact by Event Type")
        cp = df.groupby("event_cause")["impact_score"].mean().sort_values().reset_index()
        cp.columns = ["Event", "Avg"]
        cp["Event"] = cp["Event"].str.replace("_", " ").str.title()
        fig7 = px.bar(cp, x="Avg", y="Event", orientation="h",
                      color="Avg", color_continuous_scale=[[0, "#9FE1CB"], [0.5, "#FAC775"], [1, "#F09595"]],
                      height=250, text="Avg")
        fig7.update_traces(texttemplate="%{text:.1f}", textposition="outside",
                           textfont=dict(color="#9CA3AF", size=9), marker_line_width=0)
        fig7.update_layout(**pdef(), coloraxis_showscale=False,
                           xaxis=dict(title="Score", gridcolor="#F3F4F6"),
                           yaxis=dict(title="", tickfont=dict(size=9.5)))
        st.plotly_chart(fig7, use_container_width=True)


# ======================================================================
# PAGE 2 — IMPACT PREDICTOR
# ======================================================================

elif page == "🔮  Impact Predictor":
    st.markdown('<div class="pg-eyebrow">7-Factor Scoring Model</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">Impact Predictor</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Enter event details. The model weighs severity, location history, peak hour, and event type to compute impact.</div>', unsafe_allow_html=True)

    cl, cr = st.columns(2, gap="large")
    with cl:
        sec("Event Details")
        event_cause = st.selectbox("Event Type", list(SEVERITY_MAP.keys()),
                                    format_func=lambda x: x.replace("_", " ").title())
        priority = st.selectbox("Priority Level", ["High", "Low"])
        road_closure = st.checkbox("Requires Road Closure?")
        hour = st.slider("Hour of Day", 0, 23, 8, format="%d:00")
        event_type = "Planned" if event_cause in PLANNED else "Unplanned"
        st.markdown(f'<div style="font-size:0.72rem;color:#9CA3AF;margin-top:4px">Auto-detected category: <b style="color:#374151">{event_type}</b></div>', unsafe_allow_html=True)

    with cr:
        sec("Location")
        zone_opts = ["(Not Selected)"] + sorted(df["zone"].dropna().unique().tolist())
        junc_opts = ["(Not Selected)"] + sorted(df["junction"].dropna().unique().tolist())
        sel_zone = st.selectbox("Zone", zone_opts)
        sel_junc = st.selectbox("Junction", junc_opts)

    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("⚡  Compute Impact Score", use_container_width=True)

    if run:
        sev_sc = SEVERITY_MAP.get(event_cause, 40)
        pri_sc = 15 if priority == "High" else 5
        clo_sc = 20 if road_closure else 0
        ph_sc = 15 if is_peak(hour) else 0
        et_sc = 10 if event_type == "Planned" else 15
        zc = df["zone"].value_counts()
        zone_sc = round((zc.get(sel_zone, 0) / zc.max()) * 15, 2) if sel_zone != "(Not Selected)" else 0
        jc = df["junction"].value_counts()
        junc_sc = round((jc.get(sel_junc, 0) / jc.max()) * 15, 2) if sel_junc != "(Not Selected)" else 0

        raw = 0.35 * sev_sc + 0.20 * clo_sc + 0.15 * pri_sc + 0.08 * zone_sc + 0.08 * junc_sc + 0.07 * ph_sc + 0.07 * et_sc
        all_raw = (0.35 * df["severity_score"] + 0.20 * df["road_closure_score"] +
                   0.15 * df["priority_score"] + 0.08 * df["zone_risk_score"] +
                   0.08 * df["junction_risk_score"] + 0.07 * df["peak_hour"] +
                   0.07 * df["event_type_score"])
        impact = round(((raw - all_raw.min()) / (all_raw.max() - all_raw.min())) * 100, 1)
        impact = max(0.0, min(100.0, impact))
        rlevel = get_risk(impact)
        clr = RISK_COLORS[rlevel]

        st.session_state.update({"last_risk": rlevel, "last_impact": impact, "last_cause": event_cause})
        st.markdown("---")

        r1, r2 = st.columns([2, 3], gap="large")
        with r1:
            peak_html = f'<span class="peak-on">▲ Peak Hour</span>' if is_peak(hour) else f'<span class="peak-off">● Off-Peak</span>'
            st.markdown(f"""
            <div class="result-header" style="border-left:3px solid {clr}">
              <div style="font-size:0.62rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#9CA3AF;margin-bottom:0.4rem">Impact Score</div>
              <div class="result-score" style="color:{clr}">{impact:.1f}</div>
              <div class="result-risk" style="color:{clr}">{rlevel} Risk</div>
              <div style="margin-top:0.75rem">{peak_html}</div>
              <div style="margin-top:1.1rem">
                <div class="factor-row"><span class="factor-name">Severity</span><span class="factor-val">{sev_sc}</span></div>
                <div class="factor-row"><span class="factor-name">Priority</span><span class="factor-val">{pri_sc}</span></div>
                <div class="factor-row"><span class="factor-name">Road Closure</span><span class="factor-val">{clo_sc}</span></div>
                <div class="factor-row"><span class="factor-name">Zone Risk</span><span class="factor-val">{zone_sc}</span></div>
                <div class="factor-row"><span class="factor-name">Junction Risk</span><span class="factor-val">{junc_sc}</span></div>
                <div class="factor-row"><span class="factor-name">Peak Hour</span><span class="factor-val">{ph_sc}</span></div>
                <div class="factor-row" style="border:none"><span class="factor-name">Event Type</span><span class="factor-val">{et_sc}</span></div>
              </div>
            </div>""", unsafe_allow_html=True)

        with r2:
            breakdown = {
                "Severity (35%)": round(0.35 * sev_sc, 2),
                "Road Closure (20%)": round(0.20 * clo_sc, 2),
                "Priority (15%)": round(0.15 * pri_sc, 2),
                "Zone Risk (8%)": round(0.08 * zone_sc, 2),
                "Junction Risk (8%)": round(0.08 * junc_sc, 2),
                "Peak Hour (7%)": round(0.07 * ph_sc, 2),
                "Event Type (7%)": round(0.07 * et_sc, 2),
            }
            bdf = pd.DataFrame(list(breakdown.items()), columns=["Factor", "Contribution"])
            bdf = bdf.sort_values("Contribution")
            fig_b = px.bar(bdf, x="Contribution", y="Factor", orientation="h",
                           color="Contribution", color_continuous_scale=[[0, "#E1F5EE"], [1, clr]],
                           height=310, text="Contribution")
            fig_b.update_traces(texttemplate="%{text:.2f}", textposition="outside",
                                textfont=dict(color="#9CA3AF", size=9), marker_line_width=0)
            fig_b.update_layout(**pdef(30), coloraxis_showscale=False,
                                title=dict(text="Weighted Score Breakdown", font=dict(size=11.5, color="#6B7280")),
                                xaxis=dict(title="Contribution", gridcolor="#F3F4F6"),
                                yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10)))
            st.plotly_chart(fig_b, use_container_width=True)

            fig_g = go.Figure(go.Indicator(
                mode="gauge+number", value=impact,
                number={"font": {"size": 32, "color": clr, "family": "JetBrains Mono"}},
                gauge={
                    "axis": {"range": [0, 100], "tickfont": {"size": 9}},
                    "bar": {"color": clr, "thickness": 0.2},
                    "bgcolor": "#FFFFFF",
                    "steps": [
                        {"range": [0, q1], "color": "#E1F5EE"},
                        {"range": [q1, q2], "color": "#FFF3CD"},
                        {"range": [q2, q3], "color": "#FEE9D7"},
                        {"range": [q3, 100], "color": "#FEE2E2"},
                    ],
                    "threshold": {"line": {"color": clr, "width": 3}, "thickness": 0.7, "value": impact},
                },
            ))
            fig_g.update_layout(height=200, paper_bgcolor="#FFFFFF",
                                margin=dict(l=10, r=10, t=30, b=10), font=dict(family="Inter"))
            st.plotly_chart(fig_g, use_container_width=True)

        if sel_zone != "(Not Selected)":
            sec("Historical Context — Same Cause + Zone")
            sim = df[(df["event_cause"] == event_cause) & (df["zone"] == sel_zone)]
            n_sim = len(sim)
            if n_sim == 0:
                st.markdown('<div class="warn-box">⚠️ No historical records for this cause + zone combination.</div>', unsafe_allow_html=True)
            else:
                hp = int((sim["priority"] == "High").sum())
                rc = int(sim["requires_road_closure"].sum())
                ai = round(sim["impact_score"].mean(), 1)
                st.markdown(f"""
                <div class="info-box">
                  Found <b>{n_sim}</b> past events with same cause + zone.
                  <b>{hp}</b> were High priority ({round(hp/n_sim*100,1)}%).
                  <b>{rc}</b> required road closure ({round(rc/n_sim*100,1)}%).
                  Historical avg impact: <b>{ai}/100</b>.
                </div>""", unsafe_allow_html=True)
                cols_s = st.columns(5)
                for col, val, lbl in zip(cols_s,
                    [n_sim, hp, rc, ai, sim["risk_level_operational"].mode()[0]],
                    ["Past Events", "High Priority", "Road Closures", "Avg Impact", "Typical Risk"]):
                    with col:
                        st.markdown(f'<div class="stat-item"><div class="stat-val">{val}</div><div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="info-box" style="margin-top:1.25rem">💡 Go to <b>Resource Planner</b> for the full dynamic deployment plan for this event type and risk level.</div>', unsafe_allow_html=True)


# ======================================================================
# PAGE 3 — RESOURCE PLANNER (FULLY UPDATED WITH IMPROVED RESOURCE SCORE)
# ======================================================================

elif page == "🛡️  Resource Planner":
    st.markdown('<div class="pg-eyebrow">Dynamic Deployment Protocol</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">Resource Planner</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="pg-sub">Event-aware resource recommendations driven by a composite Resource Score — '
        'different event types at the same risk level receive different deployment plans. '
        'Calibrated on 8,173 historical events.</div>',
        unsafe_allow_html=True,
    )

    def_risk = st.session_state.get("last_risk", "Medium")
    def_impact = st.session_state.get("last_impact", None)
    def_cause = st.session_state.get("last_cause", None)

    if def_impact is not None:
        st.markdown(
            f'<div class="info-box">📥 From Impact Predictor — Score: <b>{def_impact:.1f}/100</b> · '
            f'Risk: {badge(def_risk)}'
            f'{"· Cause: <b>" + def_cause.replace("_"," ").title() + "</b>" if def_cause else ""}'
            f"</div>",
            unsafe_allow_html=True,
        )

    ctrl1, ctrl2, ctrl3 = st.columns([2, 2, 1], gap="medium")

    with ctrl1:
        cause_opts = sorted(EVENT_TYPE_RESOURCE_SCORE.keys())
        default_c_idx = (
            cause_opts.index(def_cause)
            if def_cause and def_cause in cause_opts
            else (cause_opts.index("accident") if "accident" in cause_opts else 0)
        )
        event_cause_sel = st.selectbox(
            "Event Type", cause_opts,
            index=default_c_idx,
            format_func=lambda x: x.replace("_", " ").title(),
        )

    with ctrl2:
        risk_sel = st.selectbox("Risk Level", RISK_ORDER, index=RISK_ORDER.index(def_risk))

    with ctrl3:
        peak_sel = st.checkbox("Peak Hour?", value=False)

    with st.expander("📍 Location Context (optional)", expanded=False):
        lc1, lc2 = st.columns(2)
        with lc1:
            zone_opts_rp = ["(Not Selected)"] + sorted(df["zone"].dropna().unique().tolist())
            sel_zone_rp = st.selectbox("Zone", zone_opts_rp, key="rp_zone")
        with lc2:
            junc_opts_rp = ["(Not Selected)"] + sorted(df["junction"].dropna().unique().tolist())
            sel_junc_rp = st.selectbox("Junction", junc_opts_rp, key="rp_junc")

    st.button("⚡  Generate Resource Plan", use_container_width=True)

    # ── Get reference data ──
    e_mask = df["event_cause"] == event_cause_sel
    r_mask = df["risk_level_operational"] == risk_sel
    combo = df[e_mask & r_mask]
    e_only = df[e_mask]
    ref_df = combo if len(combo) >= 5 else (e_only if len(e_only) >= 3 else df)

    use_predictor = (
        def_impact is not None
        and def_risk == risk_sel
        and def_cause == event_cause_sel
    )
    rep_impact = float(def_impact) if use_predictor else float(ref_df["impact_score"].mean())
    rep_severity = float(ref_df["severity_score"].mean())
    rep_closure = float(ref_df["road_closure_score"].mean())
    rep_zone = float(ref_df["zone_risk_score"].mean())
    rep_junc = float(ref_df["junction_risk_score"].mean())

    clr = RISK_COLORS[risk_sel]

    # ── Get ALL operational factors ──
    peak_hour_active = peak_sel

    base = get_base_resources(event_cause_sel)
    road_closure_required = base.get("diversion") not in ["None", "Monitor"]

    # Junction risk score from dataset (0-100)
    if sel_junc_rp != "(Not Selected)":
        junction_risk_value = float(df[df["junction"] == sel_junc_rp]["junction_risk_score"].mean())
    else:
        junction_risk_value = rep_junc

    # Zone risk score from dataset (0-100)
    if sel_zone_rp != "(Not Selected)":
        zone_risk_value = float(df[df["zone"] == sel_zone_rp]["zone_risk_score"].mean())
    else:
        zone_risk_value = rep_zone

    # Historical similarity
    similar_mask = (df["event_cause"] == event_cause_sel)
    if sel_zone_rp != "(Not Selected)":
        similar_mask &= (df["zone"] == sel_zone_rp)
    similar_count = len(df[similar_mask])
    similar_avg_impact = float(df[similar_mask]["impact_score"].mean()) if similar_count > 0 else 0

    # ── ⭐ Calculate Resource Score with ALL operational factors ──
    r_score = calculate_resource_score(
        impact_score=rep_impact,
        severity_score=rep_severity,
        road_closure_score=rep_closure,
        zone_risk_score=rep_zone,
        junction_risk_score=rep_junc,
        event_cause=event_cause_sel,
        df_ref=df,
        peak_hour=peak_hour_active,           # ⭐ Now in Resource Score
        similar_event_count=similar_count,    # ⭐ Now in Resource Score
        avg_impact_score=similar_avg_impact   # ⭐ Now in Resource Score
    )

    # ── Scale resources with ALL operational factors ──
    resources = scale_resources(
        base=base,
        resource_score=r_score,
        risk_level=risk_sel,
        peak_hour=peak_hour_active,
        road_closure=road_closure_required,
        junction_risk_score=junction_risk_value,
        zone_risk_score=zone_risk_value,
        similar_event_count=similar_count,
        avg_impact_score=similar_avg_impact
    )

    tier_key, tier_clr, tier_label = get_deployment_tier(r_score)

    # ===== AI RESOURCE RECOMMENDATION CARD =====
    sec("AI Resource Recommendation")

    explanation = generate_resource_explanation(
        event_cause=event_cause_sel,
        risk_level=risk_sel,
        impact_score=rep_impact,
        resource_score=r_score,
        resources=resources,
        peak_hour=peak_hour_active,
        road_closure=road_closure_required,
        zone=sel_zone_rp,
        junction=sel_junc_rp,
        junction_risk_score=junction_risk_value,
        zone_risk_score=zone_risk_value,
        similar_event_count=similar_count,
        avg_impact_score=similar_avg_impact
    )

    st.markdown(f"""
    <div style="background:#FFFFFF;border:0.5px solid #E2E6EA;border-left:4px solid {tier_clr};
                border-radius:10px;padding:1.25rem 1.5rem;margin-bottom:1rem;">
      <div style="display:flex;align-items:center;gap:1.25rem;flex-wrap:wrap;margin-bottom:1rem;">
        <div>
          <div style="font-size:0.58rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#9CA3AF;">Event Type</div>
          <div style="font-size:0.9rem;font-weight:600;color:#0F172A;">{base["icon"]} {base["label"]}</div>
        </div>
        <div>
          <div style="font-size:0.58rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#9CA3AF;">Risk Level</div>
          <div style="font-size:0.9rem;font-weight:600;color:{clr};">{risk_sel}</div>
        </div>
        <div>
          <div style="font-size:0.58rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#9CA3AF;">Impact Score</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:0.9rem;font-weight:700;color:#0F172A;">{rep_impact:.1f} / 100</div>
        </div>
        <div>
          <div style="font-size:0.58rem;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#9CA3AF;">Resource Score</div>
          <div style="font-family:'JetBrains Mono',monospace;font-size:1.6rem;font-weight:700;color:{tier_clr};">{r_score}</div>
        </div>
        <div style="margin-left:auto;">
          <span style="background:{tier_clr}22;color:{tier_clr};border:1px solid {tier_clr}55;
                       border-radius:999px;padding:0.28rem 0.9rem;font-size:0.68rem;font-weight:700;
                       letter-spacing:0.07em;text-transform:uppercase;">{tier_label}</span>
        </div>
      </div>
      <div style="font-size:0.82rem;color:#374151;line-height:1.75;
                  background:#F8FAFC;border-radius:7px;padding:0.85rem 1rem;">
        {explanation}
      </div>
    </div>""", unsafe_allow_html=True)

    # ===== ⭐ SHOW RESOURCE SCORE WEIGHTED BREAKDOWN =====
    sec("Resource Score — Weighted Breakdown")
    
    # Calculate contribution of each factor to the Resource Score
    def calc_factor_contribution(weight, value, max_value=100):
        return round(weight * (value / max_value) * 100, 1)
    
    impact_contrib = calc_factor_contribution(0.35, rep_impact)
    severity_contrib = calc_factor_contribution(0.15, rep_severity)
    closure_contrib = calc_factor_contribution(0.10, rep_closure)
    zone_contrib = calc_factor_contribution(0.10, rep_zone)
    junction_contrib = calc_factor_contribution(0.10, rep_junc)
    et_contrib = calc_factor_contribution(0.10, EVENT_TYPE_RESOURCE_SCORE.get(event_cause_sel, 20))
    peak_contrib = calc_factor_contribution(0.05, 100 if peak_hour_active else 0)
    
    # Historical similarity contribution
    if similar_count > 30:
        sim_score = 100
    elif similar_count > 15:
        sim_score = 70
    elif similar_count > 5:
        sim_score = 40
    else:
        sim_score = 10
    sim_contrib = calc_factor_contribution(0.03, sim_score)
    
    # Historical impact contribution
    if similar_avg_impact > 75:
        hist_impact_score = 100
    elif similar_avg_impact > 60:
        hist_impact_score = 70
    elif similar_avg_impact > 40:
        hist_impact_score = 40
    else:
        hist_impact_score = 10
    hist_contrib = calc_factor_contribution(0.02, hist_impact_score)
    
    breakdown_data = pd.DataFrame([
        {"Factor": "Impact", "Weight": "35%", "Value": rep_impact, "Contribution": impact_contrib, "Status": "Base"},
        {"Factor": "Severity", "Weight": "15%", "Value": rep_severity, "Contribution": severity_contrib, "Status": "Base"},
        {"Factor": "Road Closure", "Weight": "10%", "Value": rep_closure, "Contribution": closure_contrib, "Status": "Base"},
        {"Factor": "Zone Risk", "Weight": "10%", "Value": rep_zone, "Contribution": zone_contrib, "Status": "Base"},
        {"Factor": "Junction Risk", "Weight": "10%", "Value": rep_junc, "Contribution": junction_contrib, "Status": "Base"},
        {"Factor": "Event Type", "Weight": "10%", "Value": EVENT_TYPE_RESOURCE_SCORE.get(event_cause_sel, 20), "Contribution": et_contrib, "Status": "Base"},
        {"Factor": "Peak Hour", "Weight": "5%", "Value": 100 if peak_hour_active else 0, "Contribution": peak_contrib, "Status": "⭐ Operational"},
        {"Factor": "Historical Similarity", "Weight": "3%", "Value": sim_score, "Contribution": sim_contrib, "Status": "⭐ Operational"},
        {"Factor": "Historical Impact", "Weight": "2%", "Value": hist_impact_score, "Contribution": hist_contrib, "Status": "⭐ Operational"},
    ])
    
    # Color code: Base factors in green, Operational factors in orange
    color_map = {"Base": "#1D9E75", "⭐ Operational": "#D85A30"}
    
    fig_breakdown = px.bar(breakdown_data, x="Contribution", y="Factor", orientation="h",
                           color="Status", color_discrete_map=color_map,
                           text="Contribution", height=350)
    fig_breakdown.update_traces(texttemplate="%{text:.1f} pts", textposition="outside",
                                textfont=dict(color="#6B7280", size=9), marker_line_width=0)
    fig_breakdown.update_layout(**pdef(20), barmode="group",
                                xaxis=dict(title="Contribution to Resource Score", range=[0, 40], gridcolor="#F3F4F6"),
                                yaxis=dict(gridcolor="rgba(0,0,0,0)"),
                                legend=dict(orientation="h", y=-0.15, font=dict(size=10)))
    st.plotly_chart(fig_breakdown, use_container_width=True)
    
    st.markdown(f"""
    <div class="info-box" style="border-left-color:{tier_clr};">
      <strong>Resource Score: {r_score}/100</strong> — 
      Base factors contribute <strong>{sum([c for c in breakdown_data.iloc[:6]['Contribution']]):.1f}</strong> points, 
      Operational factors contribute <strong>{sum([c for c in breakdown_data.iloc[6:]['Contribution']]):.1f}</strong> points.
      {f'Peak hour alone adds <strong>{peak_contrib:.1f}</strong> points.' if peak_hour_active else 'No peak hour boost.'}
      {f'Historical data adds <strong>{sim_contrib + hist_contrib:.1f}</strong> points.' if (sim_score > 10 or hist_impact_score > 10) else ''}
    </div>
    """, unsafe_allow_html=True)


    # ===== RESOURCE SCORE GAUGE + TIER BANDS =====
    sec("Resource Score & Deployment Tier")

    gc1, gc2 = st.columns([1, 2], gap="medium")

    with gc1:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=r_score,
            number={"font": {"size": 34, "color": tier_clr, "family": "JetBrains Mono"}, "suffix": "/100"},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"size": 9}},
                "bar": {"color": tier_clr, "thickness": 0.22},
                "bgcolor": "#FFFFFF",
                "steps": [
                    {"range": [0, 30], "color": "#F3F4F6"},
                    {"range": [30, 60], "color": "#FFF3CD"},
                    {"range": [60, 80], "color": "#FEE9D7"},
                    {"range": [80, 100], "color": "#FEE2E2"},
                ],
                "threshold": {"line": {"color": tier_clr, "width": 3}, "thickness": 0.75, "value": r_score},
            },
        ))
        fig_gauge.update_layout(
            height=220, paper_bgcolor="#FFFFFF",
            margin=dict(l=10, r=10, t=40, b=10),
            font=dict(family="Inter"),
            title=dict(text="Resource Score", font=dict(size=11, color="#6B7280"), x=0.5),
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

    with gc2:
        fig_tier = go.Figure()
        tier_bands = [
            ("Minimal (< 30)", 30, "#9CA3AF"),
            ("Moderate (30–60)", 30, "#EF9F27"),
            ("Major (60–80)", 20, "#D85A30"),
            ("Critical (80+)", 20, "#E24B4A"),
        ]
        start = 0
        for t_label, t_range, t_color in tier_bands:
            is_active = (
                (t_label.startswith("Minimal") and r_score < 30) or
                (t_label.startswith("Moderate") and 30 <= r_score < 60) or
                (t_label.startswith("Major") and 60 <= r_score < 80) or
                (t_label.startswith("Critical") and r_score >= 80)
            )
            fig_tier.add_trace(go.Bar(
                x=[t_range], y=["Tier"],
                orientation="h",
                marker_color=t_color if is_active else "rgba(156,163,175,0.2)",
                marker_line_width=0,
                name=t_label,
                text=t_label if is_active else "",
                textposition="inside",
                textfont=dict(color="#FFFFFF" if is_active else "rgba(0,0,0,0)", size=10),
                width=0.5,
                base=start,
            ))
            start += t_range

        fig_tier.add_vline(x=r_score, line_color=tier_clr, line_width=2.5,
                           annotation_text=f"  {r_score}", annotation_font_color=tier_clr,
                           annotation_font_size=11)
        fig_tier.update_layout(
            **pdef(30), height=110, barmode="stack", showlegend=False,
            title=dict(text="Score Tier Bands", font=dict(size=11, color="#6B7280")),
            xaxis=dict(range=[0, 100], title="Resource Score", gridcolor="#F3F4F6"),
            yaxis=dict(showticklabels=False),
        )
        st.plotly_chart(fig_tier, use_container_width=True)

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;margin-top:0.5rem;">
          <div style="background:#F8FAFC;border-radius:7px;padding:0.6rem;text-align:center;">
            <div style="font-size:0.58rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#9CA3AF;">Impact</div>
            <div style="font-family:'JetBrains Mono',monospace;font-weight:700;color:#0F172A;font-size:1rem;">{rep_impact:.1f}</div>
          </div>
          <div style="background:#F8FAFC;border-radius:7px;padding:0.6rem;text-align:center;">
            <div style="font-size:0.58rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#9CA3AF;">Severity</div>
            <div style="font-family:'JetBrains Mono',monospace;font-weight:700;color:#0F172A;font-size:1rem;">{rep_severity:.1f}</div>
          </div>
          <div style="background:#F8FAFC;border-radius:7px;padding:0.6rem;text-align:center;">
            <div style="font-size:0.58rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#9CA3AF;">Zone Risk</div>
            <div style="font-family:'JetBrains Mono',monospace;font-weight:700;color:#0F172A;font-size:1rem;">{zone_risk_value:.0f}</div>
          </div>
          <div style="background:#F8FAFC;border-radius:7px;padding:0.6rem;text-align:center;">
            <div style="font-size:0.58rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#9CA3AF;">Junction Risk</div>
            <div style="font-family:'JetBrains Mono',monospace;font-weight:700;color:#0F172A;font-size:1rem;">{junction_risk_value:.0f}</div>
          </div>
        </div>""", unsafe_allow_html=True)

    # ===== RECOMMENDED DEPLOYMENT CARDS =====
    sec("Recommended Deployment")

    card_html = '<div class="res-grid">'
    for key, (icon, label) in RESOURCE_ICONS.items():
        val = resources.get(key, 0)
        if val and val > 0:
            card_html += f"""
            <div class="res-card" style="border-top:2px solid {tier_clr}">
              <div class="res-icon">{icon}</div>
              <div class="res-val" style="color:{tier_clr}">{val}</div>
              <div class="res-lbl">{label}</div>
            </div>"""

    diversion_str = base.get("diversion", "None")
    if risk_sel == "Severe":
        diversion_str = "Full Required"
    elif risk_sel == "High" and diversion_str == "None":
        diversion_str = "Partial"

    resp_times = {"Low": "15 min", "Medium": "10 min", "High": "5 min", "Severe": "Immediate"}

    card_html += f"""
      <div class="res-card" style="border-top:2px solid {clr}">
        <div class="res-icon">🔀</div>
        <div class="res-val" style="color:{clr};font-size:0.85rem;margin-top:0.3rem">{diversion_str}</div>
        <div class="res-lbl">Diversion</div>
      </div>
      <div class="res-card" style="border-top:2px solid {clr}">
        <div class="res-icon">⏱️</div>
        <div class="res-val" style="color:{clr};font-size:1rem;margin-top:0.3rem">{resp_times[risk_sel]}</div>
        <div class="res-lbl">Response Time</div>
      </div>
    </div>"""
    st.markdown(card_html, unsafe_allow_html=True)

    p_clr = PRIORITY_COLORS.get(RESOURCE_TABLE[risk_sel]["priority"], "#9CA3AF")
    p_lbl = RESOURCE_TABLE[risk_sel]["priority"]

    st.markdown(f"""
    <div class="action-box">
      <div class="action-tag">Action Protocol ·
        <span style="color:{p_clr};font-weight:700">{p_lbl}</span> ·
        <span style="color:#9CA3AF;">Priority Level</span>
      </div>
      {RESOURCE_TABLE[risk_sel]["notes"]}
      <div style="margin-top:0.65rem;font-size:0.78rem;color:#6B7280;border-top:0.5px solid #E2E6EA;padding-top:0.55rem;">
        Primary resources for <b>{base["label"]}</b>:
        {", ".join(base["primary_resources"])}.
      </div>
    </div>""", unsafe_allow_html=True)

    # ===== VISUAL ANALYTICS =====
    sec("Visual Analytics")

    va1, va2 = st.columns(2, gap="medium")

    with va1:
        st.markdown(
            '<div style="font-size:0.68rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;'
            'letter-spacing:0.07em;margin-bottom:0.5rem;">A · Resource Score Distribution</div>',
            unsafe_allow_html=True,
        )
        sample_df = df.sample(min(2000, len(df)), random_state=42).copy()
        sample_df["resource_score"] = compute_dataset_resource_scores(sample_df)

        fig_dist = go.Figure()
        fig_dist.add_trace(go.Histogram(
            x=sample_df["resource_score"], nbinsx=35,
            marker_color="#9FE1CB", marker_line_width=0, opacity=0.9,
        ))
        fig_dist.add_vline(
            x=r_score, line_color=tier_clr, line_width=2.5, line_dash="dash",
            annotation_text=f"  Current: {r_score}",
            annotation_font_color=tier_clr, annotation_font_size=10,
        )
        fig_dist.update_layout(
            **pdef(), height=250, bargap=0.04,
            xaxis=dict(title="Resource Score", gridcolor="#F3F4F6"),
            yaxis=dict(title="Events", gridcolor="#F3F4F6"), showlegend=False,
        )
        st.plotly_chart(fig_dist, use_container_width=True)

    with va2:
        st.markdown(
            '<div style="font-size:0.68rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;'
            'letter-spacing:0.07em;margin-bottom:0.5rem;">B · Officers by Event Type (High Risk)</div>',
            unsafe_allow_html=True,
        )
        type_rows = []
        for cause in sorted(EVENT_TYPE_RESOURCE_SCORE.keys()):
            b_t = get_base_resources(cause)
            rs_t = calculate_resource_score(
                impact_score=60, severity_score=rep_severity,
                road_closure_score=rep_closure, zone_risk_score=rep_zone,
                junction_risk_score=rep_junc, event_cause=cause, df_ref=df,
                peak_hour=False, similar_event_count=0, avg_impact_score=0
            )
            sc_t = scale_resources(b_t, rs_t, "High")
            type_rows.append({
                "Event": cause.replace("_", " ").title(),
                "Officers": sc_t["officers"],
                "Active": cause == event_cause_sel,
            })

        tod_df = pd.DataFrame(type_rows).sort_values("Officers")
        clr_lst = [tier_clr if row["Active"] else "#9FE1CB" for _, row in tod_df.iterrows()]

        fig_type = go.Figure(go.Bar(
            x=tod_df["Officers"], y=tod_df["Event"], orientation="h",
            marker_color=clr_lst, marker_line_width=0,
            text=tod_df["Officers"], textposition="outside",
            textfont=dict(color="#9CA3AF", size=9),
        ))
        fig_type.update_layout(
            **pdef(), height=250,
            xaxis=dict(title="Officers (High Risk)", gridcolor="#F3F4F6"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=9)),
        )
        st.plotly_chart(fig_type, use_container_width=True)

    va3, va4 = st.columns(2, gap="medium")

    with va3:
        st.markdown(
            '<div style="font-size:0.68rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;'
            'letter-spacing:0.07em;margin-bottom:0.5rem;">C · Avg Resource Score by Zone — Top 12</div>',
            unsafe_allow_html=True,
        )
        zone_rs = sample_df.groupby("zone")["resource_score"].mean().sort_values(ascending=False).head(12).reset_index()
        zone_rs.columns = ["Zone", "Avg_Resource_Score"]

        fig_zone = px.bar(
            zone_rs, x="Zone", y="Avg_Resource_Score",
            color="Avg_Resource_Score",
            color_continuous_scale=[[0, "#9FE1CB"], [0.5, "#FAC775"], [1, "#F09595"]],
            height=250,
        )
        fig_zone.update_layout(
            **pdef(), coloraxis_showscale=False,
            xaxis=dict(tickangle=-35, gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(title="Avg Resource Score", gridcolor="#F3F4F6"),
        )
        fig_zone.update_traces(marker_line_width=0)
        st.plotly_chart(fig_zone, use_container_width=True)

    with va4:
        st.markdown(
            f'<div style="font-size:0.68rem;font-weight:700;color:#9CA3AF;text-transform:uppercase;'
            f'letter-spacing:0.07em;margin-bottom:0.5rem;">D · Resource Demand by Risk Level '
            f'— {event_cause_sel.replace("_"," ").title()}</div>',
            unsafe_allow_html=True,
        )
        demand_rows = []
        for rl in RISK_ORDER:
            rl_mask = df["risk_level_operational"] == rl
            rl_e = df[e_mask & rl_mask]
            if len(rl_e) == 0:
                rl_e = df[rl_mask]
            b_rl = get_base_resources(event_cause_sel)
            rs_rl = calculate_resource_score(
                impact_score=float(rl_e["impact_score"].mean()),
                severity_score=float(rl_e["severity_score"].mean()),
                road_closure_score=float(rl_e["road_closure_score"].mean()),
                zone_risk_score=float(rl_e["zone_risk_score"].mean()),
                junction_risk_score=float(rl_e["junction_risk_score"].mean()),
                event_cause=event_cause_sel,
                df_ref=df,
                peak_hour=False,
                similar_event_count=0,
                avg_impact_score=0
            )
            sc_rl = scale_resources(b_rl, rs_rl, rl)
            demand_rows.append({
                "Risk Level": rl,
                "Officers": sc_rl["officers"],
                "Patrol Vehicles": sc_rl["patrol_vehicles"],
                "Barricades": sc_rl["barricades"],
                "Tow Trucks": sc_rl["tow_trucks"],
                "Ambulance": sc_rl["ambulance"],
            })

        demand_df = pd.DataFrame(demand_rows)
        fig_dem = go.Figure()
        for metric, color in [
            ("Officers", "#1D9E75"),
            ("Patrol Vehicles", "#7F77DD"),
            ("Barricades", "#EF9F27"),
            ("Tow Trucks", "#D85A30"),
        ]:
            fig_dem.add_trace(go.Bar(
                name=metric, x=demand_df["Risk Level"], y=demand_df[metric],
                marker_color=color, marker_line_width=0,
                text=demand_df[metric], textposition="outside",
                textfont=dict(size=9, color="#9CA3AF"),
            ))
        fig_dem.update_layout(
            **pdef(30), height=250, barmode="group",
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),
            yaxis=dict(gridcolor="#F3F4F6"),
            legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
        )
        st.plotly_chart(fig_dem, use_container_width=True)

    # ===== SEVERE RISK — EVENT TYPE COMPARISON TABLE =====
    sec("Severe Risk — Event Type Comparison")
    st.markdown(
        '<div class="info-box">Different <b>Severe</b> events receive <b>different</b> resource '
        'recommendations. This replaces the previous static allocation where all severe events '
        'received identical resources.</div>',
        unsafe_allow_html=True,
    )

    severe_mask = df["risk_level_operational"] == "Severe"
    compare_causes = [
        "accident", "vehicle_breakdown", "construction",
        "protest", "water_logging", "vip_movement", "procession", "congestion",
    ]
    compare_rows = []
    for cc in compare_causes:
        cc_e = df[(df["event_cause"] == cc) & severe_mask]
        if len(cc_e) == 0:
            cc_e = df[severe_mask]
        b_cc = get_base_resources(cc)
        rs_cc = calculate_resource_score(
            impact_score=float(cc_e["impact_score"].mean()),
            severity_score=float(cc_e["severity_score"].mean()),
            road_closure_score=float(cc_e["road_closure_score"].mean()),
            zone_risk_score=float(cc_e["zone_risk_score"].mean()),
            junction_risk_score=float(cc_e["junction_risk_score"].mean()),
            event_cause=cc,
            df_ref=df,
            peak_hour=False,
            similar_event_count=0,
            avg_impact_score=0
        )
        sc_cc = scale_resources(b_cc, rs_cc, "Severe")
        _, t_c, t_l = get_deployment_tier(rs_cc)
        compare_rows.append({
            "Event Type": f"{b_cc['icon']} {b_cc['label']}",
            "Resource Score": rs_cc,
            "Tier": t_l,
            "Officers": sc_cc["officers"],
            "Patrol Vehicles": sc_cc["patrol_vehicles"],
            "Barricades": sc_cc["barricades"],
            "Tow Trucks": sc_cc.get("tow_trucks", 0),
            "Ambulance": sc_cc.get("ambulance", 0),
            "Diversion": b_cc["diversion"],
        })

    st.dataframe(
        pd.DataFrame(compare_rows).sort_values("Resource Score", ascending=False),
        use_container_width=True,
        hide_index=True,
    )


# ======================================================================
# PAGE 4 — HISTORICAL INSIGHTS (UNCHANGED)
# ======================================================================

elif page == "🕵️  Historical Insights":
    st.markdown('<div class="pg-eyebrow">Post-Event Learning · Pattern Recognition</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">Historical Insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Query 8,173 past events to surface risk benchmarks, patterns, and hotspot intelligence.</div>', unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns(4)
    with f1:
        sel_cause = st.selectbox("Event Type", ["(Any)"] + sorted(df["event_cause"].dropna().unique().tolist()),
                                 format_func=lambda x: x if x == "(Any)" else x.replace("_", " ").title())
    with f2:
        sel_zone = st.selectbox("Zone", ["(Any)"] + sorted(df["zone"].dropna().unique().tolist()))
    with f3:
        sel_junc = st.selectbox("Junction", ["(Any)"] + sorted(df["junction"].dropna().unique().tolist()))
    with f4:
        hr_range = st.slider("Hour Range", 0, 23, (0, 23)) if "hour" in df.columns else (0, 23)

    m1, m2 = st.columns(2)
    with m1:
        sel_risk = st.multiselect("Risk Level Filter", RISK_ORDER)
    with m2:
        peak_only = st.checkbox("Peak Hours Only (7–10am, 5–9pm)")

    search = st.button("🔍  Search Events", use_container_width=True)

    if search:
        mask = pd.Series(True, index=df.index)
        if sel_cause != "(Any)": mask &= df["event_cause"] == sel_cause
        if sel_zone != "(Any)": mask &= df["zone"] == sel_zone
        if sel_junc != "(Any)": mask &= df["junction"] == sel_junc
        if "hour" in df.columns: mask &= df["hour"].between(hr_range[0], hr_range[1])
        if sel_risk: mask &= df["risk_level_operational"].isin(sel_risk)
        if peak_only and "peak_hour" in df.columns: mask &= df["peak_hour"] == 1

        sub = df[mask].copy()
        n = len(sub)
        st.markdown("---")

        if n == 0:
            st.markdown('<div class="warn-box">⚠️ No events match these filters. Try broadening your search.</div>', unsafe_allow_html=True)
        else:
            hp = int((sub["priority"] == "High").sum())
            rc = int(sub["requires_road_closure"].sum())
            ai = round(sub["impact_score"].mean(), 1)
            sp = round((sub["risk_level_operational"] == "Severe").mean() * 100, 1)

            st.markdown(f"""
            <div class="kpi-row">
              <div class="kpi" style="border-left-color:#1D9E75">
                <div class="kpi-lbl">Events Found</div><div class="kpi-val">{n:,}</div>
              </div>
              <div class="kpi" style="border-left-color:#7F77DD">
                <div class="kpi-lbl">High Priority</div>
                <div class="kpi-val" style="color:#534AB7">{hp:,}</div>
                <div class="kpi-sub">{round(hp/n*100,1)}%</div>
              </div>
              <div class="kpi" style="border-left-color:#EF9F27">
                <div class="kpi-lbl">Road Closures</div>
                <div class="kpi-val" style="color:#854F0B">{rc:,}</div>
                <div class="kpi-sub">{round(rc/n*100,1)}%</div>
              </div>
              <div class="kpi" style="border-left-color:#1D9E75">
                <div class="kpi-lbl">Avg Impact</div>
                <div class="kpi-val" style="color:#0F6E56">{ai}</div>
              </div>
              <div class="kpi" style="border-left-color:#E24B4A">
                <div class="kpi-lbl">Severe Rate</div>
                <div class="kpi-val" style="color:#A32D2D">{sp}%</div>
              </div>
            </div>""", unsafe_allow_html=True)

            st.markdown(f"""
            <div class="info-box">
              <b>{n:,} events matched</b> — {hp} high priority ({round(hp/n*100,1)}%),
              {rc} road closures ({round(rc/n*100,1)}%),
              avg impact <b>{ai}/100</b>, severe rate <b>{sp}%</b>.
            </div>""", unsafe_allow_html=True)

            ch1, ch2 = st.columns(2, gap="medium")
            with ch1:
                sec("Risk Distribution")
                rd2 = sub["risk_level_operational"].value_counts().reindex(RISK_ORDER).fillna(0).reset_index()
                rd2.columns = ["Risk", "Count"]
                fig_r = px.pie(rd2, names="Risk", values="Count", color="Risk",
                               color_discrete_map=RISK_COLORS, height=270, hole=0.45)
                fig_r.update_traces(textinfo="percent+label", textfont_size=11,
                                    marker=dict(line=dict(color="#F4F6F8", width=2)))
                fig_r.update_layout(**pdef(), showlegend=False)
                st.plotly_chart(fig_r, use_container_width=True)

            with ch2:
                sec("Hourly Pattern")
                if "hour" in sub.columns:
                    hd = sub["hour"].dropna().value_counts().sort_index().reset_index()
                    hd.columns = ["Hour", "Count"]
                    fig_h = px.bar(hd, x="Hour", y="Count",
                                   color_discrete_sequence=["#1D9E75"], height=270)
                    fig_h.update_layout(**pdef(), xaxis=dict(gridcolor="rgba(0,0,0,0)"),
                                        yaxis=dict(gridcolor="#F3F4F6"))
                    fig_h.update_traces(marker_line_width=0)
                    st.plotly_chart(fig_h, use_container_width=True)

            sec("Top 10 Highest-Impact Events")
            show = [c for c in ["event_cause", "zone", "junction", "hour", "impact_score",
                                 "risk_level_operational", "priority", "requires_road_closure"] if c in sub.columns]
            st.dataframe(sub.nlargest(10, "impact_score")[show].reset_index(drop=True),
                         use_container_width=True, hide_index=True)

    sec("Top 12 Hotspot Junctions")
    hj = df.groupby("junction")["impact_score"].agg(["mean", "count"]).round(2)
    hj.columns = ["Avg_Impact", "Total_Events"]
    hj = hj.sort_values("Avg_Impact", ascending=True).tail(12).reset_index()
    fig_j = px.bar(hj, x="Avg_Impact", y="junction", orientation="h",
                   color="Avg_Impact", color_continuous_scale=[[0, "#9FE1CB"], [0.5, "#FAC775"], [1, "#F09595"]],
                   height=330, text="Total_Events")
    fig_j.update_traces(texttemplate="n=%{text}", textposition="outside",
                        textfont=dict(color="#9CA3AF", size=9), marker_line_width=0)
    fig_j.update_layout(**pdef(), coloraxis_showscale=False,
                        xaxis=dict(title="Avg Impact Score", gridcolor="#F3F4F6"),
                        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(size=10)))
    st.plotly_chart(fig_j, use_container_width=True)


# ======================================================================
# PAGE 5 — RISK HEATMAP (UNCHANGED)
# ======================================================================

elif page == "🗺️  Risk Heatmap":
    st.markdown('<div class="pg-eyebrow">Geospatial Intelligence · Bengaluru</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">Risk Heatmap</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Geographical distribution of traffic events. Bubble size = impact score. Color = risk level.</div>', unsafe_allow_html=True)

    lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
    lon_col = next((c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()), None)

    if lat_col and lon_col:
        map_df = df[[lat_col, lon_col, "risk_level_operational", "impact_score", "event_cause", "zone"]].dropna()
        map_df = map_df.rename(columns={lat_col: "lat", lon_col: "lon", "risk_level_operational": "risk_level"})

        fc1, fc2, fc3 = st.columns(3)
        with fc1: risk_f = st.multiselect("Risk Level", RISK_ORDER, default=["High", "Severe"])
        with fc2: cause_f = st.multiselect("Event Type", list(SEVERITY_MAP.keys()),
                                           format_func=lambda x: x.replace("_", " ").title())
        with fc3: min_imp = st.slider("Min Impact Score", 0, 100, 0)

        plot_df = map_df.copy()
        if risk_f: plot_df = plot_df[plot_df["risk_level"].isin(risk_f)]
        if cause_f: plot_df = plot_df[plot_df["event_cause"].isin(cause_f)]
        plot_df = plot_df[plot_df["impact_score"] >= min_imp]

        st.markdown(f'<div style="font-size:0.78rem;color:#9CA3AF;margin:0.5rem 0 0.75rem">Showing <b style="color:#374151">{len(plot_df):,}</b> events on map</div>', unsafe_allow_html=True)

        if len(plot_df) == 0:
            st.markdown('<div class="warn-box">⚠️ No events match these filters.</div>', unsafe_allow_html=True)
        else:
            fig_map = px.scatter_mapbox(
                plot_df, lat="lat", lon="lon",
                color="risk_level", color_discrete_map=RISK_COLORS,
                size="impact_score", size_max=16, opacity=0.78,
                hover_data={"event_cause": True, "impact_score": True, "risk_level": True,
                            "zone": True, "lat": False, "lon": False},
                zoom=10, height=560, mapbox_style="carto-positron",
                category_orders={"risk_level": RISK_ORDER},
            )
            fig_map.update_layout(
                margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="#F4F6F8",
                legend=dict(orientation="v", x=0.01, y=0.97,
                            bgcolor="rgba(255,255,255,0.92)", bordercolor="#E2E6EA", borderwidth=1,
                            font=dict(family="Inter", size=11, color="#374151")),
            )
            st.plotly_chart(fig_map, use_container_width=True)

    else:
        st.markdown('<div class="warn-box">⚠️ Latitude / Longitude columns not found. Showing zone-level fallback analysis.</div>', unsafe_allow_html=True)

        sec("Average Impact by Zone — Top 20")
        zrp = df.groupby("zone")["impact_score"].agg(["mean", "count"]).round(2)
        zrp.columns = ["Avg_Impact", "Total"]
        zrp = zrp.sort_values("Avg_Impact", ascending=False).head(20).reset_index()
        fig_fz = px.bar(zrp, x="zone", y="Avg_Impact", color="Avg_Impact",
                        color_continuous_scale=[[0, "#9FE1CB"], [0.5, "#FAC775"], [1, "#F09595"]],
                        height=370, text="Avg_Impact")
        fig_fz.update_traces(texttemplate="%{text:.1f}", textposition="outside",
                             textfont=dict(color="#9CA3AF", size=9), marker_line_width=0)
        fig_fz.update_layout(**pdef(), coloraxis_showscale=False,
                             xaxis=dict(tickangle=-35, gridcolor="rgba(0,0,0,0)"),
                             yaxis=dict(title="Avg Impact", gridcolor="#F3F4F6"))
        st.plotly_chart(fig_fz, use_container_width=True)

        sec("Risk Mix by Zone — Top 15")
        top_z = df["zone"].value_counts().head(15).index
        zrisk = df[df["zone"].isin(top_z)].groupby(["zone", "risk_level_operational"]).size().reset_index(name="Count")
        zrisk.columns = ["Zone", "Risk Level", "Count"]
        fig_zs = px.bar(zrisk, x="Zone", y="Count", color="Risk Level",
                        color_discrete_map=RISK_COLORS, barmode="stack",
                        height=320, category_orders={"Risk Level": RISK_ORDER})
        fig_zs.update_layout(**pdef(), xaxis=dict(tickangle=-35, gridcolor="rgba(0,0,0,0)"),
                             yaxis=dict(gridcolor="#F3F4F6"), legend_title="Risk Level")
        fig_zs.update_traces(marker_line_width=0)
        st.plotly_chart(fig_zs, use_container_width=True)

        st.dataframe(zrp, use_container_width=True, hide_index=True)


# ======================================================================
# PAGE 6 — RECOMMENDATION EXPLAINER
# ======================================================================

elif page == "📋  Recommendation Explainer":
    st.markdown('<div class="pg-eyebrow">Why This Recommendation?</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">Recommendation Explainer</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Transparent breakdown of how resource recommendations are generated — similar to ML explainability, but rule-based with full traceability.</div>', unsafe_allow_html=True)

    exp_col1, exp_col2 = st.columns(2, gap="large")

    with exp_col1:
        sec("Test Scenario")
        test_cause = st.selectbox("Event Type", list(EVENT_TYPE_RESOURCE_SCORE.keys()),
                                  format_func=lambda x: x.replace("_", " ").title())
        test_risk = st.selectbox("Risk Level", RISK_ORDER, index=2)
        test_peak = st.checkbox("Peak Hour?", value=True)

    with exp_col2:
        sec("Location Context")
        test_zone = st.selectbox("Zone", ["(Not Selected)"] + sorted(df["zone"].dropna().unique().tolist()))
        test_junc = st.selectbox("Junction", ["(Not Selected)"] + sorted(df["junction"].dropna().unique().tolist()))

    if st.button("🔍  Explain This Recommendation", use_container_width=True):
        test_e_mask = df["event_cause"] == test_cause
        test_r_mask = df["risk_level_operational"] == test_risk
        test_combo = df[test_e_mask & test_r_mask]
        test_ref = test_combo if len(test_combo) >= 5 else df

        test_impact = float(test_ref["impact_score"].mean())
        test_severity = float(test_ref["severity_score"].mean())
        test_closure = float(test_ref["road_closure_score"].mean())
        test_zone_score = float(test_ref["zone_risk_score"].mean())
        test_junc_score = float(test_ref["junction_risk_score"].mean())

        # Get historical similarity
        sim_mask = (df["event_cause"] == test_cause)
        if test_zone != "(Not Selected)":
            sim_mask &= (df["zone"] == test_zone)
        test_sim_count = len(df[sim_mask])
        test_sim_impact = float(df[sim_mask]["impact_score"].mean()) if test_sim_count > 0 else 0

        test_r_score = calculate_resource_score(
            impact_score=test_impact,
            severity_score=test_severity,
            road_closure_score=test_closure,
            zone_risk_score=test_zone_score,
            junction_risk_score=test_junc_score,
            event_cause=test_cause,
            df_ref=df,
            peak_hour=test_peak,
            similar_event_count=test_sim_count,
            avg_impact_score=test_sim_impact
        )

        test_base = get_base_resources(test_cause)
        test_resources = scale_resources(test_base, test_r_score, test_risk)
        test_tier, test_tier_clr, test_tier_label = get_deployment_tier(test_r_score)

        st.markdown("---")

        st.markdown(f"""
        <div style="background:#FFFFFF;border:0.5px solid #E2E6EA;border-radius:10px;padding:1.5rem;">
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;">
            <div>
              <div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;color:#9CA3AF;letter-spacing:0.08em;">Resource Score</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:2.2rem;font-weight:700;color:{test_tier_clr};">{test_r_score}</div>
              <div style="font-size:0.75rem;color:{test_tier_clr};font-weight:600;">{test_tier_label}</div>
            </div>
            <div>
              <div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;color:#9CA3AF;letter-spacing:0.08em;">Impact Score</div>
              <div style="font-family:'JetBrains Mono',monospace;font-size:2.2rem;font-weight:700;color:#0F172A;">{test_impact:.1f}</div>
              <div style="font-size:0.75rem;color:#6B7280;">{test_risk} Risk Level</div>
            </div>
            <div>
              <div style="font-size:0.6rem;font-weight:700;text-transform:uppercase;color:#9CA3AF;letter-spacing:0.08em;">Event Type</div>
              <div style="font-size:1.1rem;font-weight:600;color:#0F172A;">{test_base['icon']} {test_base['label']}</div>
              <div style="font-size:0.75rem;color:#6B7280;">Primary: {', '.join(test_base['primary_resources'])}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        sec("Score Breakdown — What Drives This Recommendation?")

        severity_val = SEVERITY_MAP.get(test_cause, 40)
        severity_weighted = round(0.35 * severity_val, 1)
        closure_val = test_closure * 20 / 100
        closure_weighted = round(0.15 * closure_val, 1)
        zone_weighted = round(0.10 * test_zone_score, 1)
        junc_weighted = round(0.10 * test_junc_score, 1)
        peak_weighted = round(0.07 * (1 if test_peak else 0), 1)

        breakdown_data = pd.DataFrame([
            {"Factor": "Severity", "Weight": "35%", "Value": severity_val, "Contribution": severity_weighted, "Why": "Primary driver — event type determines resource intensity"},
            {"Factor": "Road Closure", "Weight": "15%", "Value": round(closure_val, 1), "Contribution": closure_weighted, "Why": "Road closures require additional barricades and officers"},
            {"Factor": "Zone Risk", "Weight": "10%", "Value": test_zone_score, "Contribution": zone_weighted, "Why": f"Historical risk score for this zone — {len(df[df['zone'] == test_zone]) if test_zone != '(Not Selected)' else 'N/A'} past events"},
            {"Factor": "Junction Risk", "Weight": "10%", "Value": test_junc_score, "Contribution": junc_weighted, "Why": "Complex junctions require more traffic management"},
            {"Factor": "Peak Hour", "Weight": "7%", "Value": 1 if test_peak else 0, "Contribution": peak_weighted, "Why": f"{'▲' if test_peak else '●'} Peak hour {'increases' if test_peak else 'does not increase'} resource demand"},
        ])

        fig_exp = px.bar(breakdown_data, x="Contribution", y="Factor", orientation="h",
                         color="Contribution", color_continuous_scale=[[0, "#9FE1CB"], [1, test_tier_clr]],
                         text="Contribution", height=280)
        fig_exp.update_traces(texttemplate="%{text:.1f}", textposition="outside",
                              textfont=dict(color="#6B7280", size=10), marker_line_width=0)
        fig_exp.update_layout(**pdef(20), coloraxis_showscale=False,
                              xaxis=dict(title="Weighted Contribution", range=[0, 40], gridcolor="#F3F4F6"),
                              yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_exp, use_container_width=True)

        sec("Historical Context — Why These Numbers?")

        if test_zone != "(Not Selected)":
            sim_count = len(df[(df["event_cause"] == test_cause) & (df["zone"] == test_zone)])
            sim_avg_impact = df[(df["event_cause"] == test_cause) & (df["zone"] == test_zone)]["impact_score"].mean()
            sim_closure_rate = df[(df["event_cause"] == test_cause) & (df["zone"] == test_zone)]["requires_road_closure"].mean() * 100
        else:
            sim_count = len(df[df["event_cause"] == test_cause])
            sim_avg_impact = df[df["event_cause"] == test_cause]["impact_score"].mean()
            sim_closure_rate = df[df["event_cause"] == test_cause]["requires_road_closure"].mean() * 100

        confidence = "High" if sim_count >= 20 else ("Medium" if sim_count >= 5 else "Low")

        st.markdown(f"""
        <div class="explain-box">
          <div style="margin-bottom:0.75rem;">
            <strong>📊 Historical Data for "{test_cause.replace('_', ' ').title()}"</strong>
          </div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:0.75rem;">
            <div class="explain-highlight">
              <div style="font-size:0.65rem;color:#9CA3AF;">Similar Events</div>
              <div style="font-size:1.2rem;font-weight:700;color:#0F172A;">{sim_count}</div>
              <div style="font-size:0.65rem;color:#6B7280;">Confidence: {confidence}</div>
            </div>
            <div class="explain-highlight">
              <div style="font-size:0.65rem;color:#9CA3AF;">Average Impact</div>
              <div style="font-size:1.2rem;font-weight:700;color:#0F172A;">{sim_avg_impact:.1f}/100</div>
              <div style="font-size:0.65rem;color:#6B7280;">Benchmark for this event type</div>
            </div>
            <div class="explain-highlight">
              <div style="font-size:0.65rem;color:#9CA3AF;">Road Closure Rate</div>
              <div style="font-size:1.2rem;font-weight:700;color:#0F172A;">{sim_closure_rate:.1f}%</div>
              <div style="font-size:0.65rem;color:#6B7280;">Dictates barricade needs</div>
            </div>
          </div>
          <div style="margin-top:0.75rem;font-size:0.8rem;color:#6B7280;border-top:0.5px solid #E2E6EA;padding-top:0.65rem;">
            💡 <b>How this is used:</b> Historical patterns inform baseline resource allocation. 
            The system combines event severity, zone risk, and historical data to generate 
            recommendations — similar to how ML models use training data, but fully transparent.
          </div>
        </div>
        """, unsafe_allow_html=True)


# ======================================================================
# PAGE 7 — LIVE INCIDENT SIMULATOR
# ======================================================================

elif page == "🚦  Live Incident Simulator":
    st.markdown('<div class="pg-eyebrow">Real-Time Event Simulation</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-title">Live Incident Simulator</div>', unsafe_allow_html=True)
    st.markdown('<div class="pg-sub">Simulate a live incident feed with real-time recommendations. Uses historical patterns to generate realistic events.</div>', unsafe_allow_html=True)

    sim_col1, sim_col2, sim_col3 = st.columns(3)

    with sim_col1:
        sim_speed = st.select_slider(
            "Simulation Speed",
            options=["Slow", "Medium", "Fast"],
            value="Medium"
        )
        speed_multiplier = {"Slow": 3, "Medium": 1.5, "Fast": 0.5}[sim_speed]

    with sim_col2:
        sim_zone_focus = st.selectbox(
            "Focus Zone",
            ["All Zones"] + sorted(df["zone"].dropna().unique().tolist())
        )

    with sim_col3:
        sim_duration = st.selectbox(
            "Simulation Duration",
            ["10 Events", "25 Events", "50 Events"],
            index=0
        )
        max_events = int(sim_duration.split()[0])

    if st.button("▶️  Start Live Simulation", use_container_width=True):
        events_generated = []
        event_types = list(EVENT_TYPE_RESOURCE_SCORE.keys())
        zones = df["zone"].dropna().unique().tolist()
        junctions = df["junction"].dropna().unique().tolist()

        historical_dist = df["event_cause"].value_counts(normalize=True)

        for i in range(max_events):
            if sim_zone_focus != "All Zones":
                zone_events = df[df["zone"] == sim_zone_focus]
                if len(zone_events) > 0:
                    cause = zone_events["event_cause"].sample(1).iloc[0]
                    zone = sim_zone_focus
                else:
                    cause = historical_dist.sample(1).index[0]
                    zone = random.choice(zones)
            else:
                cause = historical_dist.sample(1).index[0]
                zone = random.choice(zones)

            junction = random.choice(junctions) if random.random() > 0.3 else None
            hour = random.randint(0, 23)
            peak_hour_flag= is_peak(hour)

            cause_mask = df["event_cause"] == cause
            zone_mask = df["zone"] == zone
            combo_mask = cause_mask & zone_mask

            if len(df[combo_mask]) > 0:
                ref = df[combo_mask]
            elif len(df[cause_mask]) > 0:
                ref = df[cause_mask]
            else:
                ref = df

            impact = float(ref["impact_score"].mean()) + random.uniform(-10, 10)
            impact = max(0, min(100, impact))
            risk = get_risk(impact)

            # Get historical similarity
            sim_count = len(df[cause_mask & zone_mask])
            sim_avg_impact = float(df[cause_mask & zone_mask]["impact_score"].mean()) if sim_count > 0 else 0

            r_score = calculate_resource_score(
                impact_score=impact,
                severity_score=float(ref["severity_score"].mean()),
                road_closure_score=float(ref["road_closure_score"].mean()),
                zone_risk_score=float(ref["zone_risk_score"].mean()),
                junction_risk_score=float(ref["junction_risk_score"].mean()),
                event_cause=cause,
                df_ref=df,
                peak_hour=peak_hour_flag,
                similar_event_count=sim_count,
                avg_impact_score=sim_avg_impact
            )

            base = get_base_resources(cause)
            road_closure_required = base.get("diversion") not in ["None", "Monitor"]
            
            resources = scale_resources(
                base=base,
                resource_score=r_score,
                risk_level=risk,
                peak_hour=peak_hour_flag,
                road_closure=road_closure_required,
                junction_risk_score=float(ref["junction_risk_score"].mean()),
                zone_risk_score=float(ref["zone_risk_score"].mean()),
                similar_event_count=sim_count,
                avg_impact_score=sim_avg_impact
            )

            events_generated.append({
                "Event": f"#{i+1}",
                "Type": cause.replace("_", " ").title(),
                "Zone": zone,
                "Junction": junction or "N/A",
                "Hour": f"{hour:02d}:00",
                "Impact": round(impact, 1),
                "Risk": risk,
                "Resource Score": r_score,
                "Officers": resources["officers"],
                "Patrol": resources["patrol_vehicles"],
                "Barricades": resources["barricades"],
                "Tow Trucks": resources["tow_trucks"],
                "Ambulance": resources["ambulance"],
                "Status": "Active",
                "Time Since": f"{random.randint(1, 15)} min",
            })

            time.sleep(0.3 * speed_multiplier)

        events_df = pd.DataFrame(events_generated)

        st.markdown("---")
        st.markdown(f"""
        <div class="info-box" style="border-left-color:#1D9E75;">
          ✅ Simulated <b>{len(events_generated)}</b> live events in <b>{sim_zone_focus}</b>.
          <span style="display:inline-block;margin-left:1rem;background:#E1F5EE;padding:0.1rem 0.6rem;border-radius:999px;font-size:0.7rem;">🔴 LIVE</span>
        </div>
        """, unsafe_allow_html=True)

        avg_impact = events_df["Impact"].mean()
        severe_count = len(events_df[events_df["Risk"] == "Severe"])
        high_count = len(events_df[events_df["Risk"] == "High"])
        avg_officers = events_df["Officers"].mean()
        avg_resource_score = events_df["Resource Score"].mean()

        st.markdown(f"""
        <div class="kpi-row">
          <div class="kpi" style="border-left-color:#1D9E75;">
            <div class="kpi-lbl">Events Simulated</div>
            <div class="kpi-val">{len(events_generated)}</div>
            <div class="kpi-sub">Live feed</div>
          </div>
          <div class="kpi" style="border-left-color:#E24B4A;">
            <div class="kpi-lbl">Severe Events</div>
            <div class="kpi-val" style="color:#A32D2D">{severe_count}</div>
            <div class="kpi-sub">{severe_count/len(events_generated)*100:.1f}%</div>
          </div>
          <div class="kpi" style="border-left-color:#D85A30;">
            <div class="kpi-lbl">High Risk</div>
            <div class="kpi-val" style="color:#993C1D">{high_count}</div>
            <div class="kpi-sub">{high_count/len(events_generated)*100:.1f}%</div>
          </div>
          <div class="kpi" style="border-left-color:#7F77DD;">
            <div class="kpi-lbl">Avg Impact</div>
            <div class="kpi-val" style="color:#534AB7">{avg_impact:.1f}</div>
            <div class="kpi-sub">Score</div>
          </div>
          <div class="kpi" style="border-left-color:#1D9E75;">
            <div class="kpi-lbl">Avg Resource Score</div>
            <div class="kpi-val" style="color:#0F6E56">{avg_resource_score:.0f}</div>
            <div class="kpi-sub">Composite</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        sec("Live Incident Feed")

        def style_risk(row):
            colors = {"Low": "#E1F5EE", "Medium": "#FFF3CD", "High": "#FEE9D7", "Severe": "#FEE2E2"}
            return [f'background-color: {colors.get(row["Risk"], "#FFFFFF")}'] * len(row)

        st.dataframe(
            events_df.style.apply(style_risk, axis=1),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Event": st.column_config.TextColumn("Event"),
                "Type": st.column_config.TextColumn("Event Type"),
                "Zone": st.column_config.TextColumn("Zone"),
                "Junction": st.column_config.TextColumn("Junction"),
                "Hour": st.column_config.TextColumn("Time"),
                "Impact": st.column_config.NumberColumn("Impact", format="%.1f"),
                "Risk": st.column_config.TextColumn("Risk"),
                "Resource Score": st.column_config.NumberColumn("Score", format="%.0f"),
                "Officers": st.column_config.NumberColumn("👮"),
                "Patrol": st.column_config.NumberColumn("🚔"),
                "Barricades": st.column_config.NumberColumn("🚧"),
                "Tow Trucks": st.column_config.NumberColumn("🚛"),
                "Ambulance": st.column_config.NumberColumn("🚑"),
                "Status": st.column_config.TextColumn("Status"),
                "Time Since": st.column_config.TextColumn("Active"),
            }
        )

        sec("Resource Demand Summary")

        res_summary = events_df.groupby("Type").agg({
            "Officers": "sum",
            "Patrol": "sum",
            "Barricades": "sum",
            "Tow Trucks": "sum",
            "Ambulance": "sum",
            "Event": "count"
        }).reset_index()
        res_summary.columns = ["Event Type", "Total Officers", "Total Patrol", "Total Barricades",
                               "Total Tow Trucks", "Total Ambulance", "Events"]

        fig_summary = px.bar(res_summary, x="Events", y="Event Type", orientation="h",
                             color="Total Officers", color_continuous_scale=[[0, "#9FE1CB"], [1, "#1D9E75"]],
                             height=300, text="Total Officers")
        fig_summary.update_traces(texttemplate="%{text} officers", textposition="outside",
                                  textfont=dict(color="#6B7280", size=9), marker_line_width=0)
        fig_summary.update_layout(**pdef(), coloraxis_showscale=False,
                                  xaxis=dict(title="Events", gridcolor="#F3F4F6"),
                                  yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_summary, use_container_width=True)

        st.markdown("---")
        st.markdown("""
        <div style="background:#F0FBF5;border:0.5px solid #9FE1CB;border-radius:10px;padding:1rem 1.25rem;">
          <div style="display:flex;align-items:center;gap:0.75rem;">
            <span style="font-size:1.2rem;">🔔</span>
            <div>
              <div style="font-weight:600;color:#0F172A;">Real-Time Simulation Active</div>
              <div style="font-size:0.78rem;color:#6B7280;">
                This demonstrates how the system would respond to live incidents.
                In production, this would connect to actual incident feeds from
                traffic control rooms, GPS trackers, and citizen reports.
              </div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)