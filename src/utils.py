"""
utils.py
────────
Utility functions for the Traffic Impact System.
Includes caching, data loading, and display helpers.
"""

import os
import sys
import pandas as pd
import streamlit as st
from typing import Optional, Tuple, List


# ───────────────────────────────────────────────────────────────────────
# DATA LOADING
# ───────────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="Loading traffic data…")
def load_data() -> pd.DataFrame:
    """
    Loads the processed traffic events CSV.
    Searches multiple paths for robustness.
    """
    paths = [
        "processed_traffic_events.csv",
        "data/processed_traffic_events.csv",
        os.path.join(os.path.dirname(__file__), "..", "processed_traffic_events.csv"),
        os.path.join(os.path.dirname(__file__), "..", "data", "processed_traffic_events.csv"),
        "data/processed_traffic_events.csv",
    ]

    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p)
            return df

    st.error(
        "⚠️ Could not find `processed_traffic_events.csv`. "
        "Run the preprocessing script first: `python preprocess.py`"
    )
    st.stop()


# ───────────────────────────────────────────────────────────────────────
# COLUMN HELPERS
# ───────────────────────────────────────────────────────────────────────

def get_risk_column(df: pd.DataFrame) -> Optional[str]:
    """
    Returns the appropriate risk column name from the DataFrame.
    Prefers operational risk, falls back to data-driven.
    """
    for col in ["risk_level_operational", "risk_level_data", "risk_level"]:
        if col in df.columns:
            return col
    return None


def get_lat_lon_columns(df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    """
    Detects latitude and longitude column names in the DataFrame.
    """
    lat_col = None
    lon_col = None

    for col in df.columns:
        col_lower = col.lower()
        if "lat" in col_lower:
            lat_col = col
        if "lon" in col_lower or "lng" in col_lower:
            lon_col = col

    return lat_col, lon_col


def get_unique_values(df: pd.DataFrame, column: str) -> List[str]:
    """
    Returns sorted unique values for a column, handling NaN.
    """
    if column not in df.columns:
        return []
    return sorted(df[column].dropna().unique().tolist())


# ───────────────────────────────────────────────────────────────────────
# DISPLAY HELPERS
# ───────────────────────────────────────────────────────────────────────

def kpi_card_html(
    value: str,
    label: str,
    delta: str = "",
    color: str = "#0EA5E9"
) -> str:
    """
    Returns HTML for a KPI card.
    """
    return f"""
    <div class="kpi-card">
        <div class="kpi-accent" style="background:{color}"></div>
        <div class="kpi-value" style="color:{color}">{value}</div>
        <div class="kpi-label">{label}</div>
        {"" if not delta else f'<div class="kpi-delta">{delta}</div>'}
    </div>"""


def info_box_html(content: str, type: str = "info") -> str:
    """
    Returns HTML for an info or warning box.
    """
    if type == "warning":
        return f'<div class="warn-box">{content}</div>'
    return f'<div class="insight-box">{content}</div>'


def page_header(title: str, subtitle: str) -> None:
    """
    Renders a page header with title and subtitle.
    """
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-sub">{subtitle}</div>', unsafe_allow_html=True)


def section_header(title: str) -> None:
    """
    Renders a section header.
    """
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)