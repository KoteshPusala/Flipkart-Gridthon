"""
recommend.py
────────────
Intelligent recommendation engine for the Traffic Impact System.
Provides context-aware recommendations based on:
- Risk level and impact score
- Event type and pattern
- Historical similarity
- Zone and junction characteristics
- Time of day and peak hour considerations
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .scoring import (
    RISK_ORDER,
    RESOURCE_TABLE,
    get_recommendation,
    risk_badge_html,
)
from .historical import (
    get_similar_events_summary,
    zone_risk_profile,
    top_hotspot_junctions,
)


def generate_event_recommendations(
    event_cause: str,
    risk_level: str,
    impact_score: float,
    zone: Optional[str] = None,
    junction: Optional[str] = None,
    hour: int = 8,
    road_closure: bool = False,
    priority: Optional[str] = None,  # Changed: None default, only High or Low
    similar_events: Optional[Dict] = None,
    zone_profile: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Generates comprehensive recommendations for a specific event.
    
    Parameters:
        event_cause: Type of event
        risk_level: Low, Medium, High, Severe
        impact_score: 0-100
        zone: Zone name (optional)
        junction: Junction name (optional)
        hour: Hour of day (0-23)
        road_closure: Whether road closure is required
        priority: Priority level (High or Low) - optional
        similar_events: Summary of similar historical events (optional)
        zone_profile: Zone risk profile (optional)
    
    Returns:
        Dictionary with recommendations
    """
    # Base resource recommendations - COPY to avoid mutating global
    resources = get_recommendation(risk_level).copy()
    
    # Initialize recommendations
    recommendations = {
        "risk_level": risk_level,
        "impact_score": impact_score,
        "priority": priority,  # Store actual priority
        "resources": resources,
        "immediate_actions": [],
        "short_term_actions": [],
        "long_term_actions": [],
        "communication": [],
        "escalation": [],
        "diversion_plan": None,
        "special_considerations": [],
        "priority_rating": "Normal",
    }
    
    # ── Immediate Actions (based on risk level) ──
    if risk_level == "Severe":
        recommendations["immediate_actions"].extend([
            "🚨 ACTIVATE EMERGENCY PROTOCOL - Notify DCP immediately",
            "📢 Issue public alert via traffic management system",
            "🚑 Coordinate with emergency services if applicable",
            "🔒 Implement FULL road closure at all access points",
            "📋 Assign incident commander",
        ])
        recommendations["priority_rating"] = "CRITICAL"
        recommendations["escalation"].append("DCP Level - Immediate approval required")
        
    elif risk_level == "High":
        recommendations["immediate_actions"].extend([
            "📞 Notify ACP and zone HQ immediately",
            "🚧 Deploy barricades and reroute traffic",
            "👮 Assign 10+ officers to manage traffic",
            "📢 Issue traffic advisory",
            "🔍 Deploy rapid response team",
        ])
        recommendations["priority_rating"] = "URGENT"
        recommendations["escalation"].append("ACP Level - Rapid approval required")
        
    elif risk_level == "Medium":
        recommendations["immediate_actions"].extend([
            "👮 Deploy 5 officers to the location",
            "🚧 Place 2 barricades if needed",
            "📞 Coordinate with zone HQ",
            "👁️ Monitor situation closely",
        ])
        recommendations["priority_rating"] = "HIGH"
        
    else:  # Low
        recommendations["immediate_actions"].extend([
            "👮 Deploy 2 officers for monitoring",
            "📝 Document the incident",
            "👁️ Standard observation protocol",
        ])
        recommendations["priority_rating"] = "Normal"
    
    # ── Priority-based adjustments ──
    if priority == "High":
        recommendations["priority_rating"] = "URGENT"
        recommendations["immediate_actions"].insert(0, 
            "⚡ HIGH PRIORITY - Expedite all actions"
        )
        # Add extra resources for high priority
        resources["officers"] = min(resources["officers"] + 3, 25)
    
    # ── Road Closure Actions ──
    if road_closure:
        recommendations["immediate_actions"].insert(0, "🚧 IMPLEMENT ROAD CLOSURE")
        recommendations["diversion_plan"] = generate_diversion_plan(
            zone, junction, risk_level
        )
        recommendations["special_considerations"].append(
            "Road closure in effect - ensure alternative routes are clearly marked"
        )
    
    # ── Short Term Actions (1-2 hours) ──
    recommendations["short_term_actions"] = [
        "📊 Monitor traffic flow and adjust resources as needed",
        "📝 Log all actions and observations",
        "🔄 Update control room every 30 minutes",
        "📢 Communicate status to affected stakeholders",
    ]
    
    if risk_level in ["High", "Severe"]:
        recommendations["short_term_actions"].append(
            "🔄 Prepare for potential escalation"
        )
    
    # ── Long Term Actions (Post-event) ──
    recommendations["long_term_actions"] = [
        "📋 Document incident response and outcomes",
        "📊 Review what worked and what didn't",
        "🔍 Identify if there's a pattern in this zone",
        "🔄 Update response protocols if needed",
    ]
    
    # ── Communication Requirements ──
    recommendations["communication"] = generate_communication_plan(
        risk_level, event_cause, zone
    )
    
    # ── Special Considerations ──
    # Based on event type
    cause_special = get_cause_special_considerations(event_cause)
    if cause_special:
        recommendations["special_considerations"].extend(cause_special)
    
    # Based on time
    if 7 <= hour <= 10:
        recommendations["special_considerations"].append(
            "⚠️ During AM peak hour - expect higher traffic volume"
        )
        resources["officers"] += 2
    elif 17 <= hour <= 21:
        recommendations["special_considerations"].append(
            "⚠️ During PM peak hour - expect higher traffic volume"
        )
        resources["officers"] += 2
    
    # Based on zone profile
    if zone_profile:
        zone_risk = zone_profile.get("zone_risk_score", 0)
        if zone_risk > 10:
            recommendations["special_considerations"].append(
                f"⚠️ High-risk zone (score: {zone_risk}/15) - extra caution needed"
            )
            resources["officers"] += 2
    
    # ── Historical Insights ──
    if similar_events and similar_events.get("similar_event_count", 0) > 0:
        n = similar_events["similar_event_count"]
        avg_impact = similar_events.get("avg_impact_score", 0)
        closure_rate = similar_events.get("pct_with_road_closure", 0)
        
        recommendations["historical_insights"] = {
            "similar_events": n,
            "avg_impact": avg_impact,
            "closure_rate": closure_rate,
            "confidence": similar_events.get("similarity_confidence", "Unknown"),
        }
        
        if avg_impact and avg_impact > 75:
            recommendations["special_considerations"].append(
                f"📊 Similar past events averaged {avg_impact}/100 impact - treat seriously"
            )
        
        if closure_rate and closure_rate > 50:
            recommendations["special_considerations"].append(
                f"🚧 {closure_rate}% of similar events required road closure"
            )
    
    # ── Cap Officer Recommendations ──
    # Prevent excessive officer counts (max 25 for practical deployment)
    resources["officers"] = min(resources["officers"], 25)
    resources["officers"] = max(resources["officers"], 1)  # Minimum 1 officer
    
    # ── Final Summary ──
    recommendations["summary"] = generate_recommendation_summary(
        risk_level,
        len(recommendations["immediate_actions"]),
        len(recommendations["communication"]),
        road_closure,
        recommendations["priority_rating"]
    )
    
    return recommendations


def generate_diversion_plan(
    zone: Optional[str],
    junction: Optional[str],
    risk_level: str
) -> Dict[str, Any]:
    """
    Generates a diversion plan based on location and risk level.
    """
    # Fixed: removed "or True" - now properly conditional
    required = risk_level in ["High", "Severe"]
    
    plan = {
        "required": required,
        "type": "Full Diversion" if risk_level == "Severe" else "Partial Diversion" if required else "None",
        "routes": [],
        "signage_required": 2 if risk_level == "Low" else 4 if risk_level == "Medium" else 8,
        "officers_required": 2 if risk_level == "Low" else 4 if risk_level == "Medium" else 10,
    }
    
    # If not required, return minimal plan
    if not required:
        plan["routes"] = ["No diversion required - standard traffic management"]
        plan["signage_required"] = 0
        plan["officers_required"] = 0
        return plan
    
    if junction:
        plan["routes"] = [
            f"Alternative route via alternate roads around {junction}",
            f"Use main arterial roads to bypass {junction}",
            f"Local roads for last-mile connectivity",
        ]
    elif zone:
        plan["routes"] = [
            f"Alternative routes within {zone} zone",
            f"Use ring roads to bypass {zone}",
        ]
    else:
        plan["routes"] = [
            "Use alternate arterial roads",
            "Local diversions as per traffic flow",
        ]
    
    if risk_level == "Severe":
        plan["routes"].append("🚨 EMERGENCY ROUTES - Priority for emergency vehicles")
        plan["signage_required"] = 12
        plan["officers_required"] = 15
    
    return plan


def generate_communication_plan(
    risk_level: str,
    event_cause: str,
    zone: Optional[str]
) -> List[str]:
    """
    Generates communication requirements based on risk level.
    """
    communications = []
    
    cause_display = event_cause.replace("_", " ").title()
    
    if risk_level == "Severe":
        communications.extend([
            "🔴 URGENT: Broadcast to all traffic control rooms",
            "📢 Public alert via traffic management system",
            "📞 Direct line to DCP's office",
            "📧 Email to all zone HQs",
            "📱 SMS alert to all patrol units",
        ])
    elif risk_level == "High":
        communications.extend([
            "📞 Call zone HQ immediately",
            "📢 Traffic advisory to public",
            "📧 Email to relevant stakeholders",
            "📱 Alert nearby patrol units",
        ])
    elif risk_level == "Medium":
        communications.extend([
            "📞 Coordinate with zone HQ",
            "📧 Update to traffic management system",
        ])
    else:
        communications.extend([
            "📝 Log the incident",
            "📧 Regular update to system",
        ])
    
    # Add location-specific communication
    if zone:
        communications.append(f"📍 Coordinate with {zone} zone office")
    
    # Add cause-specific communication
    if event_cause in ["accident", "protest", "vip_movement"]:
        communications.append("📢 Media advisory required")
    
    return communications


def get_cause_special_considerations(event_cause: str) -> List[str]:
    """
    Returns special considerations for specific event types.
    """
    cause_map = {
        "accident": [
            "🚑 Coordinate with ambulance services",
            "🔄 Plan for medical evacuation route",
            "📸 Document accident scene",
        ],
        "protest": [
            "👮 Need additional crowd control",
            "📢 Coordinate with law enforcement",
            "🔄 Plan for potential escalation",
        ],
        "vip_movement": [
            "🛡️ Security detail required",
            "🚦 Special traffic arrangement",
            "📋 Coordinate with security agencies",
        ],
        "construction": [
            "🚧 Coordinate with construction team",
            "📋 Review traffic diversion plan",
            "🔦 Ensure night-time safety measures",
        ],
        "public_event": [
            "👥 Crowd management required",
            "🚧 Set up designated gathering areas",
            "📋 Coordinate with event organizers",
        ],
        "procession": [
            "🚶‍♂️ Pedestrian management required",
            "🚧 Special traffic arrangements",
            "📋 Coordinate with religious/community leaders",
        ],
        "water_logging": [
            "💧 Coordinate with BBMP for drainage",
            "🚧 Identify safe alternative routes",
            "⚠️ Alert about water logging areas",
        ],
        "tree_fall": [
            "🌳 Coordinate with BBMP for clearance",
            "🚧 Barricade the area",
            "⚠️ Check for electrical wires",
        ],
        "congestion": [
            "🚦 Coordinate with traffic signals",
            "🔄 Implement green wave corridor if possible",
            "📢 Alert drivers about congestion",
        ],
    }
    
    return cause_map.get(event_cause, [])


def generate_recommendation_summary(
    risk_level: str,
    immediate_actions: int,
    communications: int,
    road_closure: bool,
    priority_rating: str
) -> str:
    """
    Generates a concise summary of recommendations.
    """
    severity_emoji = {
        "Low": "🟢",
        "Medium": "🟡", 
        "High": "🟠",
        "Severe": "🔴",
    }
    
    summary_parts = [
        f"{severity_emoji.get(risk_level, '🟢')} {risk_level} Risk Level",
        f"📋 {immediate_actions} immediate actions required",
        f"📢 {communications} communication channels",
    ]
    
    if road_closure:
        summary_parts.append("🚧 Road closure required")
    
    summary_parts.append(f"⚡ Priority: {priority_rating}")
    
    return " | ".join(summary_parts)


def get_zone_recommendations(
    df: pd.DataFrame,
    zone: str,
    min_events: int = 5
) -> Dict[str, Any]:
    """
    Generates recommendations for a specific zone based on historical data.
    
    Parameters:
        df: Processed DataFrame
        zone: Zone name
        min_events: Minimum events required for recommendations
    
    Returns:
        Dictionary with zone recommendations
    """
    recommendations = {
        "zone": zone,
        "risk_profile": {},
        "recommendations": [],
        "hotspots": [],
        "peak_hours": [],
        "common_causes": [],
        "resource_needs": [],
        "long_term_actions": [],
    }
    
    # Get zone data
    zone_df = df[df["zone"] == zone]
    if len(zone_df) < min_events:
        recommendations["recommendations"].append(
            f"⚠️ Insufficient data ({len(zone_df)} events). Need {min_events} events for analysis."
        )
        return recommendations
    
    # Risk profile
    profile = zone_risk_profile(df)
    zone_profile = profile[profile["zone"] == zone]
    if not zone_profile.empty:
        recommendations["risk_profile"] = zone_profile.iloc[0].to_dict()
        
        # Recommendations based on risk profile
        severe_pct = zone_profile.iloc[0].get("Severe_Pct", 0)
        avg_impact = zone_profile.iloc[0].get("Avg_Impact", 0)
        
        if severe_pct > 20:
            recommendations["recommendations"].append(
                f"🔴 {severe_pct:.1f}% severe events - increase patrol frequency"
            )
            recommendations["resource_needs"].append("Additional officers needed")
        
        if avg_impact > 60:
            recommendations["recommendations"].append(
                f"📊 High average impact ({avg_impact:.1f}/100) - prioritize this zone"
            )
    
    # Common causes
    cause_counts = zone_df["event_cause"].value_counts().head(5)
    recommendations["common_causes"] = [
        {"cause": c, "count": int(v)} 
        for c, v in cause_counts.items()
    ]
    
    # Peak hours
    if "hour" in zone_df.columns:
        peak_hours = zone_df.groupby("hour").size().sort_values(ascending=False).head(3)
        recommendations["peak_hours"] = [
            {"hour": int(h), "events": int(v)}
            for h, v in peak_hours.items()
        ]
        
        if not peak_hours.empty:
            top_hour = peak_hours.index[0]
            recommendations["recommendations"].append(
                f"⏰ Peak hour: {top_hour}:00 - {top_hour+1}:00 ({peak_hours.iloc[0]} events)"
            )
    
    # Hotspots within zone
    if "junction" in zone_df.columns:
        hotspots = zone_df["junction"].value_counts().head(3)
        for junction, count in hotspots.items():
            if pd.notna(junction):
                recommendations["hotspots"].append({
                    "junction": junction,
                    "events": int(count)
                })
        
        if not hotspots.empty:
            recommendations["recommendations"].append(
                f"📍 Hotspot: {hotspots.index[0]} ({hotspots.iloc[0]} events)"
            )
    
    # Resource needs
    avg_impact = zone_df["impact_score"].mean()
    if avg_impact > 50:
        recommendations["resource_needs"].append("🚦 Enhanced traffic signal coordination")
    if "road_closure_score" in zone_df.columns:
        closure_rate = zone_df["road_closure_score"].gt(0).mean()
        if closure_rate > 0.3:
            recommendations["resource_needs"].append("🚧 Additional barricades")
    
    # Long term actions
    recommendations["long_term_actions"] = [
        "📊 Monthly review of zone performance",
        "🔄 Update traffic management plan based on patterns",
        "📋 Train officers on common incident types",
        "🔍 Conduct root cause analysis for recurring issues",
    ]
    
    return recommendations


def get_junction_recommendations(
    df: pd.DataFrame,
    junction: str,
    min_events: int = 3
) -> Dict[str, Any]:
    """
    Generates recommendations for a specific junction based on historical data.
    
    Parameters:
        df: Processed DataFrame
        junction: Junction name
        min_events: Minimum events required for recommendations
    
    Returns:
        Dictionary with junction recommendations
    """
    recommendations = {
        "junction": junction,
        "risk_level": "Unknown",
        "recommendations": [],
        "common_causes": [],
        "peak_hours": [],
        "resource_needs": [],
    }
    
    # Get junction data
    junction_df = df[df["junction"] == junction]
    if len(junction_df) < min_events:
        recommendations["recommendations"].append(
            f"⚠️ Insufficient data ({len(junction_df)} events). Need {min_events} events for analysis."
        )
        return recommendations
    
    # Risk assessment
    avg_impact = junction_df["impact_score"].mean()
    if avg_impact > 75:
        recommendations["risk_level"] = "High"
    elif avg_impact > 50:
        recommendations["risk_level"] = "Medium"
    else:
        recommendations["risk_level"] = "Low"
    
    # Common causes
    cause_counts = junction_df["event_cause"].value_counts().head(3)
    recommendations["common_causes"] = [
        {"cause": c, "count": int(v)}
        for c, v in cause_counts.items()
    ]
    
    # Peak hours
    if "hour" in junction_df.columns:
        peak_hours = junction_df.groupby("hour").size().sort_values(ascending=False).head(2)
        recommendations["peak_hours"] = [
            {"hour": int(h), "events": int(v)}
            for h, v in peak_hours.items()
        ]
    
    # Recommendations based on patterns
    if avg_impact > 60:
        recommendations["recommendations"].append(
            f"🟠 High average impact ({avg_impact:.1f}/100) - consider signal optimization"
        )
        recommendations["resource_needs"].append("🚦 Traffic signal review")
    
    if len(junction_df) > 10:
        recommendations["recommendations"].append(
            f"📊 {len(junction_df)} total events - high traffic junction"
        )
        recommendations["resource_needs"].append("👮 Regular patrol presence")
    
    # Road closure frequency
    if "road_closure_score" in junction_df.columns:
        closure_rate = junction_df["road_closure_score"].gt(0).mean()
        if closure_rate > 0.4:
            recommendations["recommendations"].append(
                f"🚧 {closure_rate*100:.0f}% events require road closure"
            )
            recommendations["resource_needs"].append("🚧 Barricade storage nearby")
    
    return recommendations


def get_trend_based_recommendations(
    df: pd.DataFrame,
    lookback_days: int = 30
) -> Dict[str, Any]:
    """
    Generates recommendations based on recent trends.
    
    Parameters:
        df: Processed DataFrame
        lookback_days: Number of days to look back
    
    Returns:
        Dictionary with trend-based recommendations
    """
    recommendations = {
        "increasing_risk_zones": [],
        "emerging_hotspots": [],
        "event_pattern_changes": [],
        "recommendations": [],
    }
    
    if df.empty or "start_datetime" not in df.columns:
        return recommendations
    
    # Ensure datetime
    df = df.copy()
    df["start_datetime"] = pd.to_datetime(df["start_datetime"], errors="coerce")
    df = df.dropna(subset=["start_datetime"])
    
    if df.empty:
        return recommendations
    
    # Recent data
    recent_date = df["start_datetime"].max() - pd.Timedelta(days=lookback_days)
    recent_df = df[df["start_datetime"] >= recent_date]
    older_df = df[df["start_datetime"] < recent_date]
    
    if recent_df.empty or older_df.empty:
        return recommendations
    
    # Compare zone trends
    recent_zones = recent_df["zone"].value_counts()
    older_zones = older_df["zone"].value_counts()
    
    for zone in recent_zones.index:
        if pd.isna(zone):
            continue
        recent_count = recent_zones.get(zone, 0)
        older_count = older_zones.get(zone, 0)
        
        if recent_count > 0 and older_count == 0:
            recommendations["emerging_hotspots"].append(zone)
        elif recent_count > older_count * 2 and recent_count > 3:
            recommendations["increasing_risk_zones"].append({
                "zone": zone,
                "increase": recent_count - older_count,
                "recent_events": recent_count,
            })
    
    # Pattern changes - compare cause distributions
    recent_causes = recent_df["event_cause"].value_counts(normalize=True)
    older_causes = older_df["event_cause"].value_counts(normalize=True)
    
    for cause in recent_causes.index:
        if pd.isna(cause):
            continue
        recent_pct = recent_causes.get(cause, 0)
        older_pct = older_causes.get(cause, 0)
        
        if recent_pct > older_pct * 2 and recent_pct > 0.05:
            recommendations["event_pattern_changes"].append({
                "cause": cause,
                "increase": (recent_pct - older_pct) * 100,
                "recent_pct": recent_pct * 100,
            })
    
    # Generate recommendations
    if recommendations["increasing_risk_zones"]:
        top_zone = recommendations["increasing_risk_zones"][0]
        recommendations["recommendations"].append(
            f"📈 Increasing risk in {top_zone['zone']} - {top_zone['increase']} more events"
        )
    
    if recommendations["emerging_hotspots"]:
        recommendations["recommendations"].append(
            f"🆕 New hotspots: {', '.join(recommendations['emerging_hotspots'][:3])}"
        )
    
    if recommendations["event_pattern_changes"]:
        top_change = recommendations["event_pattern_changes"][0]
        recommendations["recommendations"].append(
            f"🔄 {top_change['cause'].replace('_', ' ').title()} events up {top_change['increase']:.1f}%"
        )
    
    if not recommendations["recommendations"]:
        recommendations["recommendations"].append(
            "✅ No significant trend changes detected. Continue standard monitoring."
        )
    
    return recommendations


def get_proactive_recommendations(
    df: pd.DataFrame,
    current_hour: Optional[int] = None,
    current_day: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates proactive recommendations based on expected patterns.
    
    Parameters:
        df: Processed DataFrame
        current_hour: Current hour (0-23)
        current_day: Current day name
    
    Returns:
        Dictionary with proactive recommendations
    """
    recommendations = {
        "time_based": [],
        "historical_patterns": [],
        "resource_allocation": [],
        "areas_to_monitor": [],
    }
    
    if current_hour is None:
        current_hour = datetime.now().hour
    
    if current_day is None:
        current_day = datetime.now().strftime("%A")
    
    # Time-based recommendations
    if 7 <= current_hour <= 10:
        recommendations["time_based"].append(
            "🚦 AM PEAK HOUR - Deploy additional officers at major intersections"
        )
        recommendations["resource_allocation"].append(
            "👮 +20% officers during 8-9 AM rush"
        )
    elif 17 <= current_hour <= 21:
        recommendations["time_based"].append(
            "🚦 PM PEAK HOUR - Prepare for high traffic volume"
        )
        recommendations["resource_allocation"].append(
            "👮 +20% officers during 6-7 PM rush"
        )
    elif 0 <= current_hour <= 5:
        recommendations["time_based"].append(
            "🌙 LATE NIGHT - Monitor for VIP movements and unusual activity"
        )
    
    # Day-based recommendations
    if current_day in ["Saturday", "Sunday"]:
        recommendations["time_based"].append(
            "🏙️ WEEKEND - Prepare for increased public events and congestion"
        )
        recommendations["resource_allocation"].append(
            "👮 Weekend patrol schedule active"
        )
    
    # Historical patterns - check what typically happens at this hour
    if "hour" in df.columns and "event_cause" in df.columns:
        hour_events = df[df["hour"] == current_hour]
        if not hour_events.empty:
            common_causes = hour_events["event_cause"].value_counts().head(3)
            if not common_causes.empty:
                top_cause = common_causes.index[0]
                count = common_causes.iloc[0]
                recommendations["historical_patterns"].append(
                    f"📊 Typically {count} {top_cause.replace('_', ' ').title()} events at this hour"
                )
    
    # Areas to monitor based on historical data
    if "zone" in df.columns and "hour" in df.columns:
        zone_hour_counts = df[df["hour"] == current_hour]["zone"].value_counts().head(3)
        for zone, count in zone_hour_counts.items():
            if pd.notna(zone):
                recommendations["areas_to_monitor"].append({
                    "zone": zone,
                    "expected_events": int(count),
                })
    
    return recommendations