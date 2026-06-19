"""
historical.py
─────────────
Historical analysis functions for the Traffic Impact System.
Handles similarity search, zone profiling, and pattern detection.
All functions work with the processed data from preprocess.py.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Any, Tuple

# Import RISK_ORDER from scoring for consistency
from .scoring import RISK_ORDER


def get_similar_events(
    df: pd.DataFrame,
    cause: str,
    zone: str,
    current_index: Optional[int] = None,
) -> pd.DataFrame:
    """
    Returns DataFrame of past similar events.
    
    First tries: same cause + same zone
    If none found: same cause only (fallback)
    Excludes the current row if current_index is provided.
    
    Parameters:
        df: The processed DataFrame
        cause: Event cause (e.g., "accident", "congestion")
        zone: Zone name
        current_index: Optional index to exclude (for current event)
    
    Returns:
        DataFrame of similar events
    """
    # Handle missing values safely
    if pd.isna(cause):
        return pd.DataFrame()
    
    # First try: same cause + same zone
    mask = (df["event_cause"] == cause)
    if not pd.isna(zone) and zone:
        mask = mask & (df["zone"] == zone)
    
    if current_index is not None:
        mask = mask & (df.index != current_index)
    
    similar = df[mask]
    
    # Fallback: if no results and zone was specified, try just cause
    if similar.empty and not pd.isna(zone) and zone:
        mask_cause_only = (df["event_cause"] == cause)
        if current_index is not None:
            mask_cause_only = mask_cause_only & (df.index != current_index)
        similar = df[mask_cause_only]
    
    return similar


def get_similar_events_summary(
    df: pd.DataFrame,
    cause: str,
    zone: str,
    current_index: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Returns a summary dict of past similar events.
    
    First tries: same cause + same zone
    If none found: same cause only (fallback)
    
    Confidence levels:
        - High: n >= 20 events
        - Medium: n >= 5 events
        - Low (limited history): n < 5 events
        - No history: n = 0 events
    
    Parameters:
        df: The processed DataFrame
        cause: Event cause
        zone: Zone name
        current_index: Optional index to exclude
    
    Returns:
        Dictionary with summary statistics
    """
    similar = get_similar_events(df, cause, zone, current_index)
    n = len(similar)

    if n == 0:
        return {
            "similar_event_count": 0,
            "avg_impact_score": None,
            "pct_with_road_closure": None,
            "pct_during_peak_hour": None,
            "pct_high_priority": None,
            "most_common_risk_level": None,
            "avg_raw_score": None,
            "min_impact": None,
            "max_impact": None,
            "similarity_confidence": "No history",
            "matched_on_zone": False,
        }

    # Determine confidence level
    confidence = (
        "High" if n >= 20 else
        "Medium" if n >= 5 else
        "Low (limited history)"
    )

    # Check if we matched on zone or just cause
    matched_on_zone = False
    if not pd.isna(zone) and zone:
        zone_match = (similar["zone"] == zone).sum()
        matched_on_zone = zone_match > 0

    # Get most common risk level
    risk_col = next(
        (c for c in ["risk_level_operational", "risk_level_data", "risk_level"] 
         if c in similar.columns),
        None
    )
    most_common_risk = similar[risk_col].mode().iloc[0] if risk_col else None

    # Calculate priority percentage with safe handling of missing values
    pct_high_priority = None
    if "priority" in similar.columns:
        pct_high_priority = round(
            (similar["priority"]
             .fillna("")
             .str.lower()
             .eq("high")
             .mean()) * 100, 
            1
        )

    return {
        "similar_event_count": n,
        "avg_impact_score": round(similar["impact_score"].mean(), 2),
        "min_impact": round(similar["impact_score"].min(), 2),
        "max_impact": round(similar["impact_score"].max(), 2),
        "avg_raw_score": round(similar["raw_score"].mean(), 2) if "raw_score" in similar.columns else None,
        "pct_with_road_closure": round(
            similar["road_closure_score"].gt(0).mean() * 100, 1
        ) if "road_closure_score" in similar.columns else None,
        "pct_during_peak_hour": round(
            similar["peak_hour"].mean() * 100, 1
        ) if "peak_hour" in similar.columns else None,
        "pct_high_priority": pct_high_priority,
        "most_common_risk_level": most_common_risk,
        "similarity_confidence": confidence,
        "matched_on_zone": matched_on_zone,
    }


def zone_risk_profile(df: pd.DataFrame) -> pd.DataFrame:
    """
    Creates a comprehensive risk profile for each zone.
    
    Returns:
        DataFrame with columns:
            - zone: Zone name
            - Total_Events: Number of events
            - Avg_Impact: Average impact score
            - Max_Impact: Maximum impact score
            - Severe_Count: Number of severe events
            - Severe_Pct: Percentage of severe events
            - Low, Medium, High, Severe: Risk distribution percentages
            - zone_risk_score: Historical zone risk score (if available)
    """
    # Handle empty or missing zone data
    if df.empty or "zone" not in df.columns:
        return pd.DataFrame()
    
    # Filter out rows with missing zone
    df_valid = df[df["zone"].notna()].copy()
    if df_valid.empty:
        return pd.DataFrame()
    
    risk_col = next(
        (c for c in ["risk_level_operational", "risk_level_data", "risk_level"] 
         if c in df_valid.columns),
        None
    )
    
    if risk_col is None:
        # Return basic stats if no risk column
        profile = df_valid.groupby("zone").agg(
            Total_Events=("impact_score", "count"),
            Avg_Impact=("impact_score", "mean"),
            Max_Impact=("impact_score", "max"),
        ).round(2).reset_index()
        return profile.sort_values("Avg_Impact", ascending=False)

    # Pivot for risk distribution
    risk_pivot = pd.crosstab(
        df_valid["zone"],
        df_valid[risk_col],
        normalize="index"
    ).mul(100).round(1)

    # Ensure all risk levels are present
    for level in RISK_ORDER:
        if level not in risk_pivot.columns:
            risk_pivot[level] = 0.0
    risk_pivot = risk_pivot[RISK_ORDER]

    # Add metrics
    profile = df_valid.groupby("zone").agg(
        Total_Events=("impact_score", "count"),
        Avg_Impact=("impact_score", "mean"),
        Max_Impact=("impact_score", "max"),
        Severe_Count=(risk_col, lambda x: (x == "Severe").sum()),
    ).round(2)

    # Merge with risk distribution
    profile = profile.join(risk_pivot)
    profile = profile.reset_index()
    profile["Severe_Pct"] = profile["Severe"].round(1)

    # Add zone_risk_score if available
    if "zone_risk_score" in df_valid.columns:
        zone_risk = df_valid.groupby("zone")["zone_risk_score"].mean().round(2)
        profile = profile.merge(zone_risk.reset_index(), on="zone", how="left")

    # Add risk score classification
    profile["Risk_Score"] = (
        0.4 * profile["Severe_Pct"] / 100 +
        0.3 * profile["High"] / 100 +
        0.2 * profile["Medium"] / 100 +
        0.1 * profile["Low"] / 100
    ).round(3)

    return profile.sort_values("Avg_Impact", ascending=False)


def cause_pattern_summary(df: pd.DataFrame, n: int = 15) -> pd.DataFrame:
    """
    Returns summary of event types with average impact and counts.
    
    Parameters:
        df: The processed DataFrame
        n: Number of causes to return (top n by average impact)
    
    Returns:
        DataFrame with cause patterns and metrics
    """
    if df.empty or "event_cause" not in df.columns:
        return pd.DataFrame()
    
    # Handle missing values safely
    df_valid = df[df["event_cause"].notna()].copy()
    if df_valid.empty:
        return pd.DataFrame()
    
    summary = df_valid.groupby("event_cause").agg(
        Count=("impact_score", "count"),
        Avg_Impact=("impact_score", "mean"),
        Max_Impact=("impact_score", "max"),
        Min_Impact=("impact_score", "min"),
        Std_Impact=("impact_score", "std"),
        Pct_High_Priority=(
            "priority",
            lambda x: (x.fillna("")
                      .str.lower()
                      .eq("high")
                      .mean()) * 100 
            if "priority" in df_valid.columns else 0
        ),
        Pct_Road_Closure=(
            "road_closure_score",
            lambda x: (x.gt(0)).mean() * 100 
            if "road_closure_score" in df_valid.columns else 0
        ),
        Pct_Peak_Hour=(
            "peak_hour",
            lambda x: x.mean() * 100 
            if "peak_hour" in df_valid.columns else 0
        ),
        Pct_Severe=(
            "risk_level_operational",
            lambda x: (x == "Severe").mean() * 100 
            if "risk_level_operational" in df_valid.columns else 0
        ),
    ).round(2).sort_values("Avg_Impact", ascending=False).head(n)

    return summary.reset_index()


def top_hotspot_junctions(df: pd.DataFrame, n: int = 12) -> pd.DataFrame:
    """
    Identifies top junctions by event frequency and average impact.
    
    Parameters:
        df: The processed DataFrame
        n: Number of junctions to return
    
    Returns:
        DataFrame with junction hotspots and metrics
    """
    if df.empty or "junction" not in df.columns:
        return pd.DataFrame()
    
    # Filter out rows with missing junction
    df_valid = df[df["junction"].notna()].copy()
    if df_valid.empty:
        return pd.DataFrame()
    
    risk_col = next(
        (c for c in ["risk_level_operational", "risk_level_data", "risk_level"] 
         if c in df_valid.columns),
        None
    )
    
    summary = df_valid.groupby("junction").agg(
        Total_Events=("impact_score", "count"),
        Avg_Impact=("impact_score", "mean"),
        Max_Impact=("impact_score", "max"),
        Min_Impact=("impact_score", "min"),
        Severe_Count=(
            risk_col,
            lambda x: (x == "Severe").sum() if risk_col else 0
        ),
        Pct_Peak_Hour=(
            "peak_hour",
            lambda x: x.mean() * 100 if "peak_hour" in df_valid.columns else 0
        ),
    ).round(2)

    # Add junction_risk_score if available
    if "junction_risk_score" in df_valid.columns:
        junc_risk = df_valid.groupby("junction")["junction_risk_score"].mean().round(2)
        summary = summary.merge(junc_risk.reset_index(), on="junction", how="left")

    # Score = weighted combination of frequency and impact
    # Add safety checks for division by zero
    if len(summary) > 0:
        max_events = max(summary["Total_Events"].max(), 1)
        max_severe = max(summary["Severe_Count"].max(), 1)
        
        summary["Hotspot_Score"] = (
            0.4 * summary["Total_Events"] / max_events * 100
            + 0.4 * summary["Avg_Impact"]
            + 0.2 * summary["Severe_Count"] / max_severe * 100
        ).round(2)

    return summary.sort_values("Hotspot_Score", ascending=False).head(n).reset_index()


def hourly_event_pattern(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns hourly event counts for time-series analysis.
    
    Parameters:
        df: The processed DataFrame
    
    Returns:
        DataFrame with Hour and Count columns
    """
    if df.empty or "hour" not in df.columns:
        return pd.DataFrame()

    # Filter out rows with missing hour
    df_valid = df[df["hour"].notna()].copy()
    if df_valid.empty:
        return pd.DataFrame()

    hourly = (
        df_valid["hour"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    hourly.columns = ["Hour", "Count"]
    
    # Add peak hour markers
    hourly["is_peak"] = hourly["Hour"].apply(
        lambda h: 1 if (7 <= h <= 10) or (17 <= h <= 21) else 0
    )
    
    return hourly


def get_zone_timeline(df: pd.DataFrame, zone: str) -> pd.DataFrame:
    """
    Returns chronological events for a specific zone.
    
    Parameters:
        df: The processed DataFrame
        zone: Zone name
    
    Returns:
        DataFrame with chronological events
    """
    # Handle missing zone parameter
    if pd.isna(zone) or not zone:
        return pd.DataFrame()
    
    if df.empty or "zone" not in df.columns:
        return pd.DataFrame()

    if zone not in df["zone"].values:
        return pd.DataFrame()

    zone_df = df[df["zone"] == zone].sort_values("start_datetime")
    
    # Select relevant columns
    cols = ["start_datetime", "event_cause", "impact_score"]
    
    risk_col = next(
        (c for c in ["risk_level_operational", "risk_level_data", "risk_level"] 
         if c in df.columns),
        None
    )
    if risk_col:
        cols.append(risk_col)
    
    if "priority" in df.columns:
        cols.append("priority")
    
    if "road_closure_score" in df.columns:
        cols.append("road_closure_score")
    
    if "peak_hour" in df.columns:
        cols.append("peak_hour")
    
    # Only include columns that exist
    cols = [c for c in cols if c in zone_df.columns]
    
    return zone_df[cols]


def get_cause_severity_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns severity distribution for each event cause.
    
    Parameters:
        df: The processed DataFrame
    
    Returns:
        DataFrame with cause and severity percentages
    """
    if df.empty or "event_cause" not in df.columns:
        return pd.DataFrame()
    
    # Filter out rows with missing cause
    df_valid = df[df["event_cause"].notna()].copy()
    if df_valid.empty:
        return pd.DataFrame()
    
    risk_col = next(
        (c for c in ["risk_level_operational", "risk_level_data", "risk_level"] 
         if c in df_valid.columns),
        None
    )
    
    if risk_col is None:
        return pd.DataFrame()

    dist = (
        pd.crosstab(
            df_valid["event_cause"],
            df_valid[risk_col],
            normalize="index"
        )
        .mul(100)
        .round(1)
        .reset_index()
    )
    
    # Ensure all risk levels are present
    for level in RISK_ORDER:
        if level not in dist.columns:
            dist[level] = 0.0
    
    # Add total count
    counts = df_valid.groupby("event_cause").size().reset_index(name="Total_Events")
    dist = dist.merge(counts, on="event_cause", how="left")
    
    # Calculate severity score (weighted average of risk levels)
    risk_score_map = {"Low": 1, "Medium": 2, "High": 3, "Severe": 4}
    dist["Severity_Score"] = (
        (dist["Low"] * 1 + dist["Medium"] * 2 + dist["High"] * 3 + dist["Severe"] * 4) / 100
    ).round(2)
    
    return dist.sort_values("Severity_Score", ascending=False)


def get_zone_risk_trend(df: pd.DataFrame, zone: str, window: int = 30) -> pd.DataFrame:
    """
    Returns risk trend for a specific zone over time.
    
    Parameters:
        df: The processed DataFrame
        zone: Zone name
        window: Rolling window size for trend analysis
    
    Returns:
        DataFrame with time and rolling metrics
    """
    # Handle missing zone parameter
    if pd.isna(zone) or not zone:
        return pd.DataFrame()
    
    if df.empty or "zone" not in df.columns:
        return pd.DataFrame()
    
    if zone not in df["zone"].values:
        return pd.DataFrame()
    
    zone_df = df[df["zone"] == zone].sort_values("start_datetime")
    
    if zone_df.empty:
        return pd.DataFrame()
    
    if len(zone_df) < window:
        window = max(1, len(zone_df))
    
    result = pd.DataFrame()
    result["date"] = zone_df["start_datetime"]
    result["impact_score"] = zone_df["impact_score"]
    result["rolling_avg"] = zone_df["impact_score"].rolling(window=window, min_periods=1).mean()
    result["rolling_max"] = zone_df["impact_score"].rolling(window=window, min_periods=1).max()
    result["rolling_std"] = zone_df["impact_score"].rolling(window=window, min_periods=1).std()
    
    return result


def get_cause_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns frequency and average impact for each event cause.
    Useful for understanding which causes are most common vs most severe.
    
    Parameters:
        df: The processed DataFrame
    
    Returns:
        DataFrame with cause frequency and impact metrics
    """
    if df.empty or "event_cause" not in df.columns:
        return pd.DataFrame()
    
    # Filter out rows with missing cause
    df_valid = df[df["event_cause"].notna()].copy()
    if df_valid.empty:
        return pd.DataFrame()
    
    summary = df_valid.groupby("event_cause").agg(
        Count=("impact_score", "count"),
        Avg_Impact=("impact_score", "mean"),
        Max_Impact=("impact_score", "max"),
        Min_Impact=("impact_score", "min"),
        Pct_Of_Total=("impact_score", lambda x: len(x) / len(df_valid) * 100),
    ).round(2)
    
    summary = summary.reset_index()
    summary = summary.sort_values("Count", ascending=False)
    
    # Add frequency score (like preprocess.py)
    max_count = max(summary["Count"].max(), 1)
    summary["Frequency_Score"] = (1 - summary["Count"] / max_count).round(3)
    
    return summary


def get_high_risk_patterns(
    df: pd.DataFrame,
    min_impact: float = 75.0,
    min_severe_pct: float = 25.0  # Changed from 50 to 25 for better detection
) -> Dict[str, Any]:
    """
    Identifies high-risk patterns in the data.
    
    Parameters:
        df: The processed DataFrame
        min_impact: Minimum impact score to consider "high risk" (default: 75)
        min_severe_pct: Minimum percentage of severe events to flag (default: 25)
    
    Returns:
        Dictionary with high-risk patterns and recommendations
    """
    patterns = {
        "high_impact_causes": [],
        "high_risk_zones": [],
        "high_risk_junctions": [],
        "peak_hour_risk": {},
        "recommendations": []
    }
    
    if df.empty:
        return patterns
    
    # High impact causes
    cause_summary = cause_pattern_summary(df)
    if not cause_summary.empty:
        high_impact_causes = cause_summary[cause_summary["Avg_Impact"] >= min_impact]
        patterns["high_impact_causes"] = high_impact_causes.to_dict("records")
    
    # High risk zones
    zone_profile = zone_risk_profile(df)
    if not zone_profile.empty:
        high_risk_zones = zone_profile[
            (zone_profile["Avg_Impact"] >= min_impact) |
            (zone_profile["Severe_Pct"] >= min_severe_pct)
        ]
        patterns["high_risk_zones"] = high_risk_zones.to_dict("records")
    
    # High risk junctions
    junction_hotspots = top_hotspot_junctions(df)
    if not junction_hotspots.empty:
        patterns["high_risk_junctions"] = junction_hotspots.to_dict("records")
    
    # Peak hour risk
    if "peak_hour" in df.columns and "impact_score" in df.columns:
        peak_hour_events = df[df["peak_hour"] == 1]
        off_peak_events = df[df["peak_hour"] == 0]
        
        peak_avg = peak_hour_events["impact_score"].mean() if len(peak_hour_events) > 0 else 0
        off_peak_avg = off_peak_events["impact_score"].mean() if len(off_peak_events) > 0 else 0
        
        patterns["peak_hour_risk"] = {
            "peak_hour_avg_impact": round(peak_avg, 2),
            "off_peak_avg_impact": round(off_peak_avg, 2),
            "peak_hour_events": len(peak_hour_events),
            "off_peak_events": len(off_peak_events),
            "risk_multiplier": round(peak_avg / off_peak_avg, 2) if off_peak_avg > 0 else 1.0
        }
    
    # Generate recommendations
    if patterns["high_impact_causes"]:
        top_causes = [c["event_cause"] for c in patterns["high_impact_causes"][:3]]
        patterns["recommendations"].append(
            f"Focus on {len(patterns['high_impact_causes'])} high-impact cause types: "
            f"{', '.join(top_causes)}"
        )
    
    if patterns["high_risk_zones"]:
        top_zones = [z["zone"] for z in patterns["high_risk_zones"][:3]]
        patterns["recommendations"].append(
            f"Priority zones: {', '.join(top_zones)}"
        )
    
    if patterns["peak_hour_risk"].get("risk_multiplier", 0) > 1.5:
        patterns["recommendations"].append(
            f"Peak hour events are {patterns['peak_hour_risk']['risk_multiplier']:.1f}x "
            f"more impactful than off-peak. Increase peak hour patrols."
        )
    
    # Add general recommendation if no specific ones
    if not patterns["recommendations"]:
        patterns["recommendations"].append(
            "No critical risk patterns detected. Continue standard monitoring."
        )
    
    return patterns