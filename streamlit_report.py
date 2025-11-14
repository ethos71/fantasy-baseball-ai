#!/usr/bin/env python3
"""
Fantasy Baseball AI - Streamlit Sit/Start Report (Refactored)
Interactive dashboard for sit/start recommendations
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import streamlit as st
from streamlit_components.config import setup_page_config, apply_custom_css, section_header
from streamlit_components.data_loaders import (
    load_roster_file, 
    load_recommendations, 
    load_waiver_wire,
    get_available_teams
)
from streamlit_components.sidebar import render_sidebar_controls
from streamlit_components.utils import abbreviate_position, create_yahoo_link

# Setup page
setup_page_config()
apply_custom_css()

# Auto-refresh every 5 minutes
st_autorefresh = st.sidebar.empty()
with st_autorefresh:
    st.markdown("🔄 Auto-refresh: 5 min")

# Title
st.title("⚾ Fantasy Baseball AI - Sit/Start Analysis")
st.subheader("Last Week of 2025 Season (Sept 28, 2025)")

# Team selection
available_teams = get_available_teams()
if available_teams:
    selected_team = st.sidebar.selectbox(
        "Select Fantasy Team",
        available_teams,
        index=0
    )
    render_sidebar_controls(selected_team)
else:
    selected_team = None
    st.warning("No roster data available. Please run roster fetch.")

# Load data
df_recommendations = load_recommendations(selected_team)

if df_recommendations is not None and len(df_recommendations) > 0:
    # Summary metrics
    st.markdown("---")
    col1, col2, col3, col4, col_help = st.columns([2, 2, 2, 2, 1])
    
    with col1:
        st.metric("Total Players", len(df_recommendations))
    
    with col2:
        starts = len(df_recommendations[df_recommendations['recommendation'].str.contains('START', na=False)])
        st.metric("Recommended Starts", starts)
    
    with col3:
        sits = len(df_recommendations[df_recommendations['recommendation'].str.contains('SIT', na=False)])
        st.metric("Recommended Sits", sits)
    
    with col4:
        neutral = len(df_recommendations[df_recommendations['recommendation'].str.contains('NEUTRAL', na=False)])
        st.metric("Neutral", neutral)
    
    with col_help:
        st.write("")
        with st.popover("ℹ️"):
            st.markdown("""
            ### Summary Metrics Help
            
            **Total Players:** Count of players on your roster
            
            **Recommended Starts:** Favorable matchups (score ≥ 0.05)
            
            **Recommended Sits:** Unfavorable matchups (score < -0.05)
            
            **Neutral:** Average matchups (between -0.05 and 0.05)
            """)
    
    st.markdown("---")
    
    # Display recommendations table
    section_header("Current Roster Recommendations", "📋")
    
    display_df = df_recommendations[['player_name', 'final_score', 'recommendation']].copy()
    display_df = display_df.sort_values('final_score', ascending=False)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=600,
        column_config={
            "player_name": "Player",
            "final_score": st.column_config.NumberColumn("Score", format="%.4f"),
            "recommendation": "Recommendation"
        }
    )
    
else:
    st.info("No recommendations available. Click 'Rerun Analysis' in the sidebar to generate recommendations.")

# Waiver wire section
st.markdown("---")
section_header("Waiver Wire Targets", "🔍")

df_waiver = load_waiver_wire()
if df_waiver is not None and len(df_waiver) > 0:
    st.dataframe(
        df_waiver.head(50),
        use_container_width=True,
        height=400
    )
else:
    st.info("No waiver wire data. Click 'Waiver Wire' button in sidebar to run analysis.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p>Fantasy Baseball AI | Powered by 20+ Factor Analysis</p>
</div>
""", unsafe_allow_html=True)
