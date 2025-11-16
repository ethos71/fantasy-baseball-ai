"""
Factor Analysis Component

Displays factor weights and scores analysis with visualizations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px


def render_factor_analysis(df: pd.DataFrame):
    """
    Render factor analysis section with weights and heatmap
    
    Args:
        df: DataFrame with player data including factor scores and weights
    """
    col_header, col_help = st.columns([0.95, 0.05])
    with col_header:
        st.markdown('<div class="section-header-container"><h2>🔍 Factor Analysis</h2></div>', unsafe_allow_html=True)
    with col_help:
        with st.popover("ℹ️"):
            st.markdown("""
    ### Factor Analysis Legend
        
        **What Each Factor Means and Its Typical Impact:**
        
        **High Impact Factors (10-20%):**
        - **Vegas (15-20%):** Betting lines - O/U totals, implied runs, win probability
        - **Statcast (10-15%):** Advanced metrics - exit velocity, barrel rate, hard-hit %, xBA, xSLG
        
        **Medium-High Impact (8-12%):**
        - **Matchup (8-12%):** Historical performance vs specific pitcher/team
        - **Bullpen (8-12%):** Opponent bullpen strength and fatigue levels
        - **Platoon (8-12%):** L/R handedness matchup advantages
        
        **Medium Impact (5-8%):**
        - **Home/Away (5-8%):** Home field advantage and home/road splits
        - **Injury (5-8%):** Player health status, DTD, recently returned from IL
        - **Park (5-8%):** Ballpark factors (hitter/pitcher friendly dimensions)
        - **Recent Form (5-8%):** Last 7/14/30 day performance trends
        - **Wind (5-8%):** Wind speed/direction (out = hitter boost, in = pitcher boost)
        
        **Lower Impact (3-5%):**
        - **Rest (3-5%):** Days off since last game (fresher = better)
        - **Temperature (3-5%):** Warmer weather helps offense (ball travels farther)
        - **Lineup (3-5%):** Batting order position (1-3 = more ABs)
        - **Umpire (3-5%):** Umpire strike zone tendencies
        - **Pitch Mix (3-5%):** Pitcher's arsenal vs batter's strengths
        
        **Minimal Impact (1-3%):**
        - **Time (1-3%):** Day vs night game performance splits
        - **Humidity (1-3%):** Humidity and elevation effects on ball flight
        - **Defense (1-3%):** Defensive positioning shifts, opponent defense quality
        - **Monthly (1-3%):** Performance by month (Apr/May/Jun/Jul/Aug/Sep splits)
        - **Momentum (1-3%):** Team win/loss streaks and recent performance
        
        ---
        
        ### How to Interpret Scores:
        
        **Final Score Ranges:**
        - **+0.15+:** 🌟 Strong Start - Elite matchup, must start
        - **+0.05 to +0.15:** ✅ Favorable - Strong start candidate
        - **-0.05 to +0.05:** ⚖️ Neutral - Consider other factors
        - **-0.15 to -0.05:** ⚠️ Unfavorable - Bench candidate
        - **Below -0.15:** 🚫 Bench - Terrible matchup, sit if possible
        
        **Individual Factor Scores:**
        - **Positive:** Favorable conditions for this factor
        - **Negative:** Unfavorable conditions for this factor
        - **Near zero:** Neutral or not applicable
        
        ---
        
        ### Weight Optimization:
        
        Weights are **auto-tuned** based on historical performance data:
        - Calibrated using past game results
        - Optimized for your specific players
        - Updated when you run "⚖️ Calibrate Weights"
        - Reflects what actually predicts success for your roster
        
        ### Tips:
        - Focus on high-weight factors first
        - Multiple positive factors = stronger confidence
        - One negative high-weight factor can sink a recommendation
        - Weights vary by player type (power hitters vs speed, starters vs relievers)
        """)
    
    # Get all factor columns (those ending with _score and _weight)
    score_cols = [col for col in df.columns if col.endswith('_score') and col != 'final_score']
    weight_cols = [col for col in df.columns if col.endswith('_weight')]
    
    # Show factor weights
    if weight_cols:
        st.markdown("#### Factor Weights")
        
        # Get unique weights for each factor
        factor_weights = {}
        for col in weight_cols:
            factor_name = col.replace('_weight', '')
            # Get the first non-zero weight value
            weight_val = df[col].iloc[0]
            factor_weights[factor_name.title()] = weight_val
        
        # Create bar chart
        fig_weights = px.bar(
            x=list(factor_weights.keys()),
            y=list(factor_weights.values()),
            labels={'x': 'Factor', 'y': 'Weight'},
            title='Factor Importance Weights',
            color_discrete_sequence=['#2ca02c']
        )
        fig_weights.update_layout(showlegend=False)
        st.plotly_chart(fig_weights, use_container_width=True)
    
    st.markdown("---")
    
    # Factor Scores Heatmap
    if score_cols:
        st.markdown("#### Factor Scores by Player (Top 20)")
        
        # Prepare data for heatmap - top 20 players
        top_20 = df.nlargest(20, 'final_score')
        
        # Extract just the factor scores
        factor_data = top_20[['player_name'] + score_cols].copy()
        
        # Rename columns for display
        factor_data.columns = ['Player'] + [col.replace('_score', '').title() for col in score_cols]
        
        # Set player name as index
        factor_data = factor_data.set_index('Player')
        
        # Create heatmap
        fig_heatmap = px.imshow(
            factor_data.T,
            labels=dict(x="Player", y="Factor", color="Score"),
            x=factor_data.index,
            y=factor_data.columns,
            aspect="auto",
            color_continuous_scale='RdYlGn'
        )
        fig_heatmap.update_xaxes(side="bottom", tickangle=45)
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    st.markdown("---")
