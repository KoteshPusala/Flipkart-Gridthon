import pandas as pd
import numpy as np

# =========================
# LOAD DATA
# =========================
df = pd.read_csv("raw.csv")


# =========================
# DROP USELESS COLUMNS
# =========================

drop_cols = [
    'id', 'client_id', 'created_by_id', 'last_modified_by_id',
    'assigned_to_police_id', 'citizen_accident_id', 'closed_by_id',
    'resolved_by_id', 'kgid', 'map_file', 'direction', 'veh_no'
]

df.drop(columns=[c for c in drop_cols if c in df.columns], inplace=True)

# NOTE: latitude & longitude are intentionally KEPT for downstream use:
#   - Heatmap visualization
#   - Cluster / hotspot detection
#   - Diversion route suggestions

# =========================
# NORMALIZE TEXT COLUMNS
# (prevents duplicate severity entries like "Debris" vs "debris")
# =========================

df["event_cause"] = df["event_cause"].astype(str).str.lower().str.strip()
df["event_type"]  = df["event_type"].astype(str).str.lower().str.strip()

# =========================
# DATETIME FEATURES
# =========================

df["start_datetime"] = pd.to_datetime(df["start_datetime"], errors="coerce")
df["hour"]    = df["start_datetime"].dt.hour
df["weekday"] = df["start_datetime"].dt.day_name()
df["month"]   = df["start_datetime"].dt.month_name()

# =========================
# PEAK HOUR FEATURE
# Morning rush: 7–10am | Evening rush: 5–9pm
# Events during these windows have amplified real-world impact
# =========================

def peak_hour(hour):
    if 7 <= hour <= 10:
        return 1
    elif 17 <= hour <= 21:
        return 1
    return 0

df["peak_hour"] = df["hour"].apply(peak_hour)

# =========================
# WEEKEND FEATURE
# Useful for crowd events: processions, public gatherings, VIP movements
# =========================

df["is_weekend"] = df["weekday"].isin(["Saturday", "Sunday"]).astype(int)

# =========================
# EVENT SEVERITY SCORE
# Scores reflect expected traffic disruption duration and road blockage
# likelihood, based on domain knowledge of urban traffic management.
# Scale: 20 (minor) → 100 (complete blockage / high public risk)
# =========================

severity_map = {
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

df["severity_score"] = df["event_cause"].map(severity_map).fillna(40)

# =========================
# PRIORITY SCORE
# =========================

priority_map = {"high": 15, "low": 5}
df["priority_score"] = df["priority"].astype(str).str.lower().str.strip().map(priority_map).fillna(5)

# =========================
# ROAD CLOSURE SCORE
# Guard: handles both boolean True and string "True"
# =========================

def parse_road_closure(val):
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() == "true"
    return False

df["road_closure_score"] = df["requires_road_closure"].apply(parse_road_closure).astype(int) * 20

# =========================
# ZONE RISK SCORE  (0–15)
# Zones with more historical events are higher risk corridors
# =========================

zone_counts   = df["zone"].value_counts()
max_zone      = zone_counts.max()
zone_risk_map = {z: round((c / max_zone) * 15, 2) for z, c in zone_counts.items()}
df["zone_risk_score"] = df["zone"].map(zone_risk_map).fillna(0)

# =========================
# JUNCTION RISK SCORE  (0–15)
# High-frequency junctions are structural chokepoints
# =========================

junc_counts   = df["junction"].value_counts()
max_junc      = junc_counts.max()
junc_risk_map = {j: round((c / max_junc) * 15, 2) for j, c in junc_counts.items()}
df["junction_risk_score"] = df["junction"].map(junc_risk_map).fillna(0)

# =========================
# EVENT TYPE SCORE
# Planned events involve structured crowd buildup (processions,
# construction, VIP routes) and warrant higher baseline vigilance.
# =========================

event_type_score_map = {"planned": 10, "unplanned": 5}
df["event_type_score"] = df["event_type"].map(event_type_score_map).fillna(5)

# =========================
# CAUSE FREQUENCY SCORE  (0–10)  — INVERTED
# Rare but severe events (protest, vip_movement) should not be
# underweighted just because they occur infrequently.
# Inversion: rarer cause → higher attention score.
# =========================

cause_counts = df["event_cause"].value_counts()
max_cause    = cause_counts.max()

cause_freq_score_map = {
    cause: round((1 - count / max_cause) * 10, 2)
    for cause, count in cause_counts.items()
}
df["cause_frequency_score"] = df["event_cause"].map(cause_freq_score_map).fillna(5)

# =========================
# TIME SINCE LAST EVENT IN ZONE  (in minutes)
# A zone that had a recent event is a live hotspot — higher risk.
# Capped at 999 min for normalization; new zones get 999 (no history).
# NOTE: Weight reduced to 0.01 — on a historical dataset this reflects
# data density more than real-time hotspot activity. Kept for EDA.
# =========================

df_sorted = df.sort_values(["zone", "start_datetime"]).copy()
df_sorted["prev_event_time"] = df_sorted.groupby("zone")["start_datetime"].shift(1)
df_sorted["mins_since_last_zone_event"] = (
    (df_sorted["start_datetime"] - df_sorted["prev_event_time"])
    .dt.total_seconds()
    .div(60)
    .clip(upper=999)
    .fillna(999)
    .round(2)
)

df["mins_since_last_zone_event"] = df_sorted["mins_since_last_zone_event"]

# Convert to a risk score: shorter gap → higher score (0–10)
df["zone_recency_score"] = (
    (1 - df["mins_since_last_zone_event"] / 999) * 10
).round(2)

# =========================
# EVENT CATEGORY  (Planned / Unplanned)
# =========================

planned_events = ["construction", "public_event", "procession", "vip_movement"]
df["event_category"] = np.where(df["event_cause"].isin(planned_events), "Planned", "Unplanned")

# =========================
# IMPACT SCORE — UPDATED FORMULA
# Weights rationale:
#   0.35  severity       — primary driver: type of disruption
#   0.20  road_closure   — binary but high impact when true
#   0.15  priority       — operator-assessed urgency
#   0.10  zone_risk      — structural hotspot weight
#   0.10  junction_risk  — chokepoint weight
#   0.07  peak_hour      — time-of-day amplifier (increased from 0.05)
#   0.02  event_type     — planned events need proactive response
#   0.01  zone_recency   — historical density signal (reduced; not real-time)
#   0.00  cause_freq     — kept in dataset, removed from score to avoid
#                          over-penalizing common events like breakdowns
# Total = 1.00
# NOTE: peak_hour kept as binary (0/1); weight raised to 0.07 to give
# it a meaningful nudge without distorting the score.
# =========================

raw_score = (
    0.35 * df["severity_score"]
    + 0.20 * df["road_closure_score"]
    + 0.15 * df["priority_score"]
    + 0.10 * df["zone_risk_score"]
    + 0.10 * df["junction_risk_score"]
    + 0.07 * df["peak_hour"]
    + 0.02 * df["event_type_score"]
    + 0.01 * df["zone_recency_score"]
)

# Normalize to 0–100
df["impact_score"] = (
    (raw_score - raw_score.min()) / (raw_score.max() - raw_score.min()) * 100
).round(2)

# =========================
# RISK LEVEL — DUAL LABEL SYSTEM
#
# risk_level_data:
#   Quartile-based (data-driven). Always yields 25% per bucket.
#   Use for: statistical analysis, EDA, distribution comparisons.
#   Limitation: a dataset of only vehicle_breakdowns would still
#   produce 25% "Severe" — misleading for operations.
#
# risk_level_operational:
#   Fixed absolute thresholds on the 0–100 normalized impact score.
#   Use for: operator dashboards, recommendations, judge presentations.
#   Advantage: meaningful even when event mix is skewed.
# =========================

# --- Data-driven (quartile) ---
q1 = df["impact_score"].quantile(0.25)
q2 = df["impact_score"].quantile(0.50)
q3 = df["impact_score"].quantile(0.75)

print(f"\nQuartile thresholds  →  Q1={q1:.2f}  Q2={q2:.2f}  Q3={q3:.2f}")

def classify_risk_data(score):
    if score <= q1:
        return "Low"
    elif score <= q2:
        return "Medium"
    elif score <= q3:
        return "High"
    else:
        return "Severe"

df["risk_level_data"] = df["impact_score"].apply(classify_risk_data)

# --- Operational (fixed thresholds) ---
def classify_risk_operational(score):
    if score < 25:
        return "Low"
    elif score < 50:
        return "Medium"
    elif score < 75:
        return "High"
    else:
        return "Severe"

df["risk_level_operational"] = df["impact_score"].apply(classify_risk_operational)

# =========================
# SIMILAR HISTORICAL EVENTS MODULE
# Finds past events with the same cause in the same zone.
# Used for: average impact, resource benchmarks, diversion frequency.
# Confidence is flagged by sample size — prevents false precision on
# sparse data (e.g. only 2 past protests in a zone).
# =========================

def get_similar_events_summary(cause, zone, current_index=None):
    """
    Returns a summary dict of past similar events (same cause + zone).
    Excludes the current row if current_index is provided.
    Confidence: High (n>=20) | Medium (n>=5) | Low (limited history)
    """
    mask = (df["event_cause"] == cause) & (df["zone"] == zone)

    if current_index is not None:
        mask = mask & (df.index != current_index)

    similar = df[mask]
    n = len(similar)

    if n == 0:
        return {
            "similar_event_count":      0,
            "avg_impact_score":         None,
            "pct_with_road_closure":    None,
            "pct_during_peak_hour":     None,
            "similarity_confidence":    "No history",
        }

    confidence = (
        "High"             if n >= 20 else
        "Medium"           if n >= 5  else
        "Low (limited history)"
    )

    return {
        "similar_event_count":   n,
        "avg_impact_score":      round(similar["impact_score"].mean(), 2),
        "pct_with_road_closure": round(
            similar["road_closure_score"].gt(0).mean() * 100, 1
        ),
        "pct_during_peak_hour":  round(
            similar["peak_hour"].mean() * 100, 1
        ),
        "similarity_confidence": confidence,
    }


# Apply to every row — builds historical context columns
print("\nBuilding similar historical events features...")

similarity_records = [
    get_similar_events_summary(row["event_cause"], row["zone"], idx)
    for idx, row in df.iterrows()
]

similarity_df = pd.DataFrame(similarity_records, index=df.index)
df = pd.concat([df, similarity_df], axis=1)

# =========================
# SAVE
# =========================

df.to_csv("processed_traffic_events.csv", index=False)

# =========================
# DIAGNOSTICS
# =========================

print("\nProcessed Shape:", df.shape)

print("\nNew columns added:")
new_cols = [
    "peak_hour", "is_weekend", "event_type_score",
    "cause_frequency_score", "mins_since_last_zone_event", "zone_recency_score",
    "risk_level_data", "risk_level_operational",
    "similar_event_count", "avg_impact_score",
    "pct_with_road_closure", "pct_during_peak_hour", "similarity_confidence",
]
print(new_cols)

print("\n--- Risk Level: Data-Driven (Quartile) ---")
print(df["risk_level_data"].value_counts())

print("\n--- Risk Level: Operational (Fixed Thresholds) ---")
print(df["risk_level_operational"].value_counts())

print("\nImpact Score Stats:")
print(df["impact_score"].describe())

print("\nPeak Hour Distribution:")
print(df["peak_hour"].value_counts())

print("\nEvent Type Score Distribution:")
print(df["event_type_score"].value_counts())

print("\nSimilarity Confidence Distribution:")
print(df["similarity_confidence"].value_counts())

print("\nSample Output (key columns):")
print(
    df[[
        "event_cause", "zone", "priority", "requires_road_closure",
        "hour", "peak_hour", "is_weekend",
        "impact_score", "risk_level_data", "risk_level_operational",
        "similar_event_count", "avg_impact_score",
        "pct_with_road_closure", "similarity_confidence",
    ]].head(10).to_string()
)

# =========================
# EXAMPLE: LOOKUP FOR A SINGLE EVENT  (demo / judge-facing)
# =========================

print("\n" + "="*55)
print("  SIMILAR EVENTS LOOKUP — DEMO (first row)")
print("="*55)

row0 = df.iloc[0]
print(f"  Cause     : {row0['event_cause']}")
print(f"  Zone      : {row0['zone']}")
print(f"  Impact    : {row0['impact_score']}  [{row0['risk_level_operational']}]")
print(f"  ─────────────────────────────────────────────")
print(f"  Past similar events   : {int(row0['similar_event_count']) if pd.notna(row0['similar_event_count']) else 'N/A'}")
print(f"  Avg historical impact : {row0['avg_impact_score']}")
print(f"  Road closure rate     : {row0['pct_with_road_closure']}%")
print(f"  Peak hour rate        : {row0['pct_during_peak_hour']}%")
print(f"  Confidence            : {row0['similarity_confidence']}")
print("="*55)