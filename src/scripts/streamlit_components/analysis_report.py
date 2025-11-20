#!/usr/bin/env python3
"""
Fantasy Baseball AI - Analysis Report Dashboard

Streamlit dashboard to visualize sit/start recommendations and analysis results.

Usage:
    streamlit run docs/analysis_report.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Page config
st.set_page_config(
    page_title="Fantasy Baseball AI - Analysis Report",
    page_icon="⚾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .favorable {
        color: #2ecc71;
        font-weight: bold;
    }
    .unfavorable {
        color: #e74c3c;
        font-weight: bold;
    }
    .neutral {
        color: #f39c12;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def load_latest_analysis(data_dir: Path):
    """Load the most recent analysis files"""
    
    # Find latest sit/start recommendations
    sitstart_files = sorted(data_dir.glob("sitstart_recommendations_*.csv"))
    
    # Find latest FA outputs
    fa_patterns = [
        'wind_analysis_*.csv',
        'matchup_analysis_*.csv',
        'home_away_analysis_*.csv',
        'rest_day_analysis_*.csv',
        'injury_analysis_*.csv',
        'umpire_analysis_*.csv',
        'platoon_analysis_*.csv',
        'temperature_analysis_*.csv',
        'pitch_mix_analysis_*.csv',
        'park_factors_analysis_*.csv',
        'lineup_position_analysis_*.csv',
        'time_of_day_analysis_*.csv',
        'defensive_positions_analysis_*.csv',
        'recent_form_analysis_*.csv',
        'bullpen_fatigue_analysis_*.csv',
        'humidity_elevation_analysis_*.csv',
        'monthly_splits_analysis_*.csv',
        'team_momentum_analysis_*.csv',
        'statcast_metrics_analysis_*.csv',
        'vegas_odds_analysis_*.csv',
    ]
    
    fa_files = {}
    for pattern in fa_patterns:
        files = sorted(data_dir.glob(pattern))
        if files:
            fa_name = pattern.replace('_analysis_*.csv', '')
            fa_files[fa_name] = files[-1]
    
    return {
        'sitstart': sitstart_files[-1] if sitstart_files else None,
        'fa_files': fa_files
    }


def get_recommendation_emoji(rec: str) -> str:
    """Get emoji for recommendation"""
    if 'VERY FAVORABLE' in rec:
        return '🌟'
    elif 'FAVORABLE' in rec:
        return '✅'
    elif 'NEUTRAL' in rec:
        return '⚖️'
    elif 'UNFAVORABLE' in rec and 'VERY' not in rec:
        return '⚠️'
    else:
        return '🚫'


def display_overview(df: pd.DataFrame):
    """Display overview metrics"""
    st.markdown("<h2>📊 Analysis Overview</h2>", unsafe_allow_html=True)
    
    # Calculate summary stats
    total_players = len(df)
    favorable = len(df[df['recommendation'].str.contains('FAVORABLE', na=False) & 
                      ~df['recommendation'].str.contains('UNFAVORABLE', na=False)])
    neutral = len(df[df['recommendation'].str.contains('NEUTRAL', na=False)])
    unfavorable = len(df[df['recommendation'].str.contains('UNFAVORABLE', na=False)])
    
    avg_score = df['final_score'].mean()
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Players", total_players)
    
    with col2:
        st.metric("Favorable", f"{favorable} ({favorable/total_players*100:.0f}%)")
    
    with col3:
        st.metric("Neutral", f"{neutral} ({neutral/total_players*100:.0f}%)")
    
    with col4:
        st.metric("Unfavorable", f"{unfavorable} ({unfavorable/total_players*100:.0f}%)")
    
    with col5:
        st.metric("Avg Score", f"{avg_score:.2f}")


def display_recommendations_table(df: pd.DataFrame):
    """Display sit/start recommendations table"""
    st.markdown("<h2>🎯 Sit/Start Recommendations</h2>", unsafe_allow_html=True)
    
    # Add emoji column
    df['Status'] = df['recommendation'].apply(get_recommendation_emoji)
    
    # Select columns to display
    display_cols = ['Status', 'player_name', 'final_score', 'recommendation']
    
    # Add factor scores if available
    factor_cols = [col for col in df.columns if col.endswith('_score') and col != 'final_score']
    if factor_cols:
        # Get top 5 weighted factors
        weight_cols = [col for col in df.columns if col.endswith('_weight')]
        if weight_cols:
            # Calculate average weight for each factor
            avg_weights = df[weight_cols].mean()
            top_factors = avg_weights.nlargest(5)
            top_factor_names = [col.replace('_weight', '_score') for col in top_factors.index]
            display_cols.extend([col for col in top_factor_names if col in df.columns])
    
    # Sort by final score
    df_display = df[display_cols].sort_values('final_score', ascending=False)
    
    # Style the dataframe
    def highlight_scores(val):
        if isinstance(val, (int, float)):
            if val >= 1.5:
                return 'background-color: #d4edda; color: #155724'
            elif val >= 0.5:
                return 'background-color: #d1ecf1; color: #0c5460'
            elif val >= -0.5:
                return 'background-color: #fff3cd; color: #856404'
            elif val >= -1.5:
                return 'background-color: #f8d7da; color: #721c24'
            else:
                return 'background-color: #f5c6cb; color: #721c24'
        return ''
    
    # Display
    st.dataframe(
        df_display.style.applymap(highlight_scores, subset=['final_score']),
        use_container_width=True,
        height=600
    )


def display_score_distribution(df: pd.DataFrame):
    """Display score distribution chart"""
    st.markdown("<h2>📈 Score Distribution</h2>", unsafe_allow_html=True)
    
    # Create histogram
    fig = px.histogram(
        df,
        x='final_score',
        nbins=30,
        title='Distribution of Player Scores',
        labels={'final_score': 'Final Score', 'count': 'Number of Players'},
        color_discrete_sequence=['#1f77b4']
    )
    
    # Add vertical lines for thresholds
    fig.add_vline(x=1.5, line_dash="dash", line_color="green", 
                  annotation_text="Very Favorable")
    fig.add_vline(x=0.5, line_dash="dash", line_color="lightgreen", 
                  annotation_text="Favorable")
    fig.add_vline(x=-0.5, line_dash="dash", line_color="orange", 
                  annotation_text="Unfavorable")
    fig.add_vline(x=-1.5, line_dash="dash", line_color="red", 
                  annotation_text="Very Unfavorable")
    
    st.plotly_chart(fig, use_container_width=True)


def display_factor_analysis(df: pd.DataFrame):
    """Display factor analysis breakdown"""
    st.markdown("<h2>🔍 Factor Analysis Breakdown</h2>", unsafe_allow_html=True)
    
    # Get factor scores
    factor_cols = [col for col in df.columns if col.endswith('_score') and col != 'final_score']
    weight_cols = [col for col in df.columns if col.endswith('_weight')]
    
    if not factor_cols:
        st.warning("No factor analysis data available")
        return
    
    # Calculate average scores for each factor
    factor_averages = df[factor_cols].mean()
    factor_averages = factor_averages.sort_values(ascending=False)
    
    # Get weights
    factor_weights = {}
    for col in factor_cols:
        weight_col = col.replace('_score', '_weight')
        if weight_col in df.columns:
            factor_weights[col] = df[weight_col].iloc[0]
    
    # Create DataFrame for display
    factor_df = pd.DataFrame({
        'Factor': [col.replace('_score', '').replace('_', ' ').title() 
                  for col in factor_averages.index],
        'Avg Score': factor_averages.values,
        'Weight': [factor_weights.get(col, 0) * 100 for col in factor_averages.index]
    })
    
    # Create horizontal bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=factor_df['Factor'],
        x=factor_df['Avg Score'],
        orientation='h',
        marker=dict(
            color=factor_df['Avg Score'],
            colorscale='RdYlGn',
            cmin=-2,
            cmax=2,
            colorbar=dict(title="Score")
        ),
        text=factor_df['Avg Score'].round(2),
        textposition='auto',
        hovertemplate='<b>%{y}</b><br>Avg Score: %{x:.2f}<br>Weight: %{customdata:.1f}%<extra></extra>',
        customdata=factor_df['Weight']
    ))
    
    fig.update_layout(
        title='Average Factor Scores Across All Players',
        xaxis_title='Average Score',
        yaxis_title='Factor',
        height=600
    )
    
    st.plotly_chart(fig, use_container_width=True)


def display_top_performers(df: pd.DataFrame):
    """Display top and bottom performers"""
    st.markdown("<h2>⭐ Top & Bottom Performers</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🌟 Top 10 Starts")
        top_10 = df.nlargest(10, 'final_score')[['player_name', 'final_score', 'recommendation']]
        top_10['Rank'] = range(1, 11)
        top_10 = top_10[['Rank', 'player_name', 'final_score', 'recommendation']]
        st.dataframe(top_10, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("### 🚫 Top 10 Sits")
        bottom_10 = df.nsmallest(10, 'final_score')[['player_name', 'final_score', 'recommendation']]
        bottom_10['Rank'] = range(1, 11)
        bottom_10 = bottom_10[['Rank', 'player_name', 'final_score', 'recommendation']]
        st.dataframe(bottom_10, use_container_width=True, hide_index=True)


def display_player_details(df: pd.DataFrame):
    """Display detailed player analysis"""
    st.markdown("<h2>👤 Player Details</h2>", unsafe_allow_html=True)
    
    # Player selector
    player = st.selectbox(
        "Select a player to view detailed analysis:",
        options=sorted(df['player_name'].unique())
    )
    
    if player:
        player_data = df[df['player_name'] == player].iloc[0]
        
        # Display main metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Final Score", f"{player_data['final_score']:.2f}")
        
        with col2:
            st.metric("Recommendation", player_data['recommendation'])
        
        with col3:
            emoji = get_recommendation_emoji(player_data['recommendation'])
            st.markdown(f"<h1 style='text-align: center;'>{emoji}</h1>", 
                       unsafe_allow_html=True)
        
        # Factor breakdown
        st.markdown("### Factor Breakdown")
        
        factor_cols = [col for col in df.columns if col.endswith('_score') and col != 'final_score']
        weight_cols = [col for col in df.columns if col.endswith('_weight')]
        
        if factor_cols:
            factor_data = []
            for col in factor_cols:
                factor_name = col.replace('_score', '').replace('_', ' ').title()
                score = player_data[col]
                weight_col = col.replace('_score', '_weight')
                weight = player_data[weight_col] * 100 if weight_col in player_data.index else 0
                contribution = score * (weight / 100)
                
                factor_data.append({
                    'Factor': factor_name,
                    'Score': score,
                    'Weight': weight,
                    'Contribution': contribution
                })
            
            factor_df = pd.DataFrame(factor_data).sort_values('Contribution', ascending=False)
            
            # Create radar chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=factor_df['Score'].values,
                theta=factor_df['Factor'].values,
                fill='toself',
                name=player
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[-2, 2]
                    )
                ),
                showlegend=False,
                title=f"{player} - Factor Analysis"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Factor table
            st.dataframe(
                factor_df.style.background_gradient(cmap='RdYlGn', subset=['Score']),
                use_container_width=True,
                hide_index=True
            )


def main():
    """Main Streamlit app"""
    
    # Header
    st.markdown("<h1 class='main-header'>⚾ Fantasy Baseball AI</h1>", 
                unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Sit/Start Analysis Report</h3>", 
                unsafe_allow_html=True)
    
    # Load data
    data_dir = Path(__file__).parent.parent / "data"
    
    with st.spinner("Loading latest analysis..."):
        files = load_latest_analysis(data_dir)
    
    if files['sitstart'] is None:
        st.error("❌ No analysis data found!")
        st.info("""
        **To generate analysis data:**
        
        1. Run the sit/start analysis:
           ```bash
           ./fb-ai
           ```
        
        2. This will create analysis files in the `data/` directory
        
        3. Refresh this page to view the results
        """)
        return
    
    # Load sit/start recommendations
    df = pd.read_csv(files['sitstart'])
    
    # File info in sidebar
    st.sidebar.markdown("## 📁 Analysis Info")
    file_time = datetime.fromtimestamp(files['sitstart'].stat().st_mtime)
    st.sidebar.info(f"**Generated:** {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
    st.sidebar.info(f"**Players Analyzed:** {len(df)}")
    st.sidebar.info(f"**Factors Used:** 20")
    
    # Navigation
    st.sidebar.markdown("## 🧭 Navigation")
    page = st.sidebar.radio(
        "Select View:",
        ["Overview", "Recommendations", "Score Distribution", "Factor Analysis", 
         "Top Performers", "Player Details"]
    )
    
    # Display selected page
    if page == "Overview":
        display_overview(df)
        st.markdown("---")
        display_top_performers(df)
    
    elif page == "Recommendations":
        display_recommendations_table(df)
    
    elif page == "Score Distribution":
        display_score_distribution(df)
    
    elif page == "Factor Analysis":
        display_factor_analysis(df)
    
    elif page == "Top Performers":
        display_top_performers(df)
    
    elif page == "Player Details":
        display_player_details(df)
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### About
    
    This dashboard visualizes the Fantasy Baseball AI sit/start analysis results.
    
    **Analysis includes:**
    - 20 factor analyses
    - Optimized weights
    - Comprehensive scoring
    
    **Refresh** this page after running new analyses.
    """)


if __name__ == "__main__":
    main()
