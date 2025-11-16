#!/usr/bin/env python3
"""
Fantasy Baseball AI - Streamlit Sit/Start Report (Modular Version)
Interactive dashboard for sit/start recommendations

This is the modular version - all major sections extracted into components.
"""

import streamlit as st
import pandas as pd
import sys
import glob
from datetime import datetime
import subprocess
import time

# Add src to path for imports
sys.path.insert(0, 'src')

# Import components
from scripts.streamlit_components.config import setup_page_config, apply_custom_css
from scripts.streamlit_components.data_loaders import (
    load_roster_file, 
    load_recommendations,
    get_available_teams,
    load_recommendations_data
)
from scripts.streamlit_components.summary_metrics import render_summary_metrics
from scripts.streamlit_components.current_roster_performance import render_current_roster_performance
from scripts.streamlit_components.top_starts_sits import render_top_starts_sits
from scripts.streamlit_components.player_weight_breakdown import render_player_weight_breakdown
from scripts.streamlit_components.factor_analysis import render_factor_analysis
from scripts.streamlit_components.full_rankings import render_full_rankings
from scripts.streamlit_components.waiver_wire_section import render_waiver_wire

# Page config
st.set_page_config(
    page_title="FB-AI Sit/Start Report",
    page_icon="⚾",
    layout="wide"
)

# Apply custom CSS
st.markdown("""
<style>
    /* Section container with border */
    .section-container {
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 0;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    
    /* Section header with border */
    .section-header-container {
        background-color: transparent;
        padding: 15px 20px;
        border-bottom: 2px solid #e0e0e0;
        margin: 0;
    }
    .section-header-container h2 {
        margin: 0;
        padding: 0;
        color: #1f1f1f;
    }
    
    /* Section content area */
    .section-content {
        padding: 20px;
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Helper function for styled section headers
def section_header(text, icon=""):
    st.markdown(f'<div class="section-header-container"><h2>{icon} {text}</h2></div>', unsafe_allow_html=True)

# Auto-refresh every 5 minutes
st_autorefresh = st.sidebar.empty()
with st_autorefresh:
    refresh_interval = 300  # 5 minutes in seconds
    st.markdown(f"🔄 Auto-refresh: {refresh_interval//60} min")
    time.sleep(0.1)

# Check if waiver wire needs to be run (daily at 8am) - NON-BLOCKING
def check_and_run_daily_waiver():
    """Check if waiver wire analysis needs to run, show button if needed"""
    from datetime import datetime, time as dtime
    import os
    
    waiver_files = sorted(glob.glob('data/waiver_wire_*.csv'), reverse=True)
    now = datetime.now()
    today_8am = datetime.combine(now.date(), dtime(8, 0))
    
    should_run = False
    
    if not waiver_files:
        if now >= today_8am:
            should_run = True
    else:
        latest_file = waiver_files[0]
        file_mtime = datetime.fromtimestamp(os.path.getmtime(latest_file))
        if file_mtime < today_8am and now >= today_8am:
            should_run = True
    
    if should_run:
        st.sidebar.warning("⚠️ Waiver wire data needs update")
        if st.sidebar.button("🔄 Run Waiver Wire Analysis"):
            with st.sidebar:
                with st.spinner("Running waiver wire analysis..."):
                    try:
                        subprocess.run(
                            ["python3", "src/scripts/daily_sitstart.py", "--date", "2025-09-28", "--skip-tune"],
                            cwd="/home/dominick/workspace/fantasy-baseball-ai",
                            check=True,
                            capture_output=True
                        )
                        st.success("✅ Daily waiver wire analysis complete!")
                        st.rerun()
                    except subprocess.CalledProcessError as e:
                        st.error(f"❌ Waiver wire analysis failed: {e}")

check_and_run_daily_waiver()

# Title
st.title("⚾ Fantasy Baseball AI - Sit/Start Analysis")
st.markdown("### Last Week of 2025 Season (Sept 28, 2025)")

# Get file metadata for sidebar (moved up to display at top)
rec_files_for_sidebar = sorted(glob.glob('data/sitstart_recommendations_*.csv'), reverse=True)
if rec_files_for_sidebar:
    latest_file_for_sidebar = rec_files_for_sidebar[0]
    file_timestamp = latest_file_for_sidebar.split('_')[-2] + '_' + latest_file_for_sidebar.split('_')[-1].replace('.csv', '')
    file_date = datetime.strptime(file_timestamp, '%Y%m%d_%H%M%S')
    
    st.sidebar.markdown(f"**Analysis Date:** {file_date.strftime('%Y-%m-%d %I:%M %p')}")
    st.sidebar.markdown(f"**File:** `{os.path.basename(latest_file_for_sidebar)}`")
    st.sidebar.markdown("---")

# Load roster to get team names
roster_data = load_roster_file()
if roster_data is not None and 'fantasy_team' in roster_data.columns:
    available_teams = sorted(roster_data['fantasy_team'].unique().tolist())
    selected_team = st.sidebar.selectbox(
        "Select Fantasy Team",
        available_teams,
        index=0
    )
    
    # Add Yahoo Fantasy link
    st.sidebar.markdown(f"**Team:** {selected_team}")
    st.sidebar.markdown("[🔗 Open Yahoo Fantasy Baseball](https://baseball.fantasysports.yahoo.com)")
    
    # Add action buttons
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Actions")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.sidebar.button("🔄 Rerun Analysis", help="Regenerate recommendations with current settings", use_container_width=True):
            st.sidebar.info("Rerun analysis functionality - implementation in progress")
    
    with col2:
        if st.sidebar.button("📥 Refresh Data", help="Reload data from files", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # Waiver Wire Button
    if st.sidebar.button("🔍 Waiver Wire", help="Analyze top free agents", use_container_width=True):
        st.sidebar.info("Running waiver wire analysis...")

else:
    st.error("❌ No roster data found! Please ensure Yahoo roster data is available.")
    st.stop()
    selected_team = None

# Load recommendations
rec_files = sorted(glob.glob('data/sitstart_recommendations_*.csv'), reverse=True)
if not rec_files:
    st.error("❌ No recommendations files found!")
    st.stop()

latest_file = rec_files[0]

# Load data for summary metrics
if 'df_summary' not in st.session_state:
    with st.spinner("Loading recommendations..."):
        st.session_state.df_summary = load_recommendations_data(latest_file, selected_team)

df_summary = st.session_state.df_summary

# SECTION 1: Summary Metrics
render_summary_metrics(df_summary)

st.markdown("---")

# SECTION 2: Current Roster Performance
render_current_roster_performance(selected_team)

# SECTION 3: Top Starts & Bottom Sits
render_top_starts_sits(df_summary)

# SECTION 4: Player Weight Breakdown
render_player_weight_breakdown(df_summary)

# SECTION 5: Factor Analysis
render_factor_analysis(df_summary)

# SECTION 6: Full Player Rankings
render_full_rankings(df_summary)

# SECTION 7: Waiver Wire
render_waiver_wire()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p><strong>Fantasy Baseball AI</strong> | Powered by 20+ Factor Analysis | Auto-Fetched Yahoo Rosters</p>
    <p style="font-size: 0.9em;">All scores range -2 to +2 | Higher = Better matchup | Weights optimized per player</p>
</div>
""", unsafe_allow_html=True)
