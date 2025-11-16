"""
Full Player Rankings Component

Displays complete sortable table of all player rankings.
"""

import streamlit as st
import pandas as pd


def render_full_rankings(df: pd.DataFrame):
    """
    Render full player rankings table
    
    Args:
        df: DataFrame with player data including scores and recommendations
    """
    col_header, col_help = st.columns([0.95, 0.05])
    with col_header:
        st.markdown('<div class="section-header-container"><h2>📋 Full Player Rankings</h2></div>', unsafe_allow_html=True)
    with col_help:
        with st.popover("ℹ️"):
            _render_help_content()
    
    # Get score columns
    score_cols = [col for col in df.columns if col.endswith('_score') and col != 'final_score']
    
    # Add rank column
    df_display = df.copy()
    df_display['rank'] = range(1, len(df_display) + 1)
    
    # Add Yahoo player link
    df_display['yahoo_link'] = df_display.apply(
        lambda row: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{row['player_key'].split('.')[-1]}" 
        if 'player_key' in row and row['player_key'] and '.' in str(row['player_key']) else '', axis=1
    )
    
    # Reorder columns
    cols_order = ['rank', 'player_name', 'yahoo_link', 'final_score', 'recommendation'] + score_cols
    df_display = df_display[[col for col in cols_order if col in df_display.columns]]
    
    # Rename for display
    display_names = {
        'rank': 'Rank',
        'player_name': 'Player',
        'yahoo_link': 'Yahoo',
        'final_score': 'Score',
        'recommendation': 'Recommendation'
    }
    for col in score_cols:
        display_names[col] = col.replace('_score', '').title() + ' Score'
    
    df_display = df_display.rename(columns=display_names)
    
    # Show table with formatting
    st.dataframe(
        df_display,
        column_config={
            "Yahoo": st.column_config.LinkColumn(
                "Yahoo",
                help="Click to view Yahoo player page",
                display_text="🔗"
            ),
            "Score": st.column_config.NumberColumn("Score", format="%.3f"),
            **{col: st.column_config.NumberColumn(col, format="%.3f") for col in df_display.columns if 'Score' in col and col != 'Score'}
        },
        use_container_width=True,
        height=600
    )
    
    st.markdown("---")


def _render_help_content():
    """Render help popover content"""
    st.markdown("""
    ### What This Table Shows
        
        This is the **complete ranked list** of all players on your selected team, sorted by final score (best to worst).
        
        ### Table Columns Explained
        
        **Rank:** Position in the overall rankings (1 = best matchup, higher = worse matchup)
        
        **Player:** Player name
        
        **Score:** Final weighted score from all 20 factors
        - **Higher = Better matchup**
        - Typical range: -0.3 to +0.4
        - Elite matchups: > +0.20
        - Poor matchups: < -0.10
        
        **Recommendation:** The sit/start advice based on score
        - 🌟 Strong Start (≥ 0.15)
        - ✅ Favorable (≥ 0.05)
        - ⚖️ Neutral (-0.05 to +0.05)
        - ⚠️ Unfavorable (≥ -0.15)
        - 🚫 Bench (< -0.15)
        
        **Individual Factor Scores:** Raw scores for each of the 20 factors
        - Positive values = favorable for that factor
        - Negative values = unfavorable for that factor
        - Blank/NaN = factor not applicable
        
        ### The 20 Factors Analyzed
        
        **Weather Factors (4):**
        1. **Wind:** Direction and speed (blowing out = good for hitters)
        2. **Temperature:** Warmer = ball travels farther
        3. **Humidity:** Higher humidity = less ball flight
        4. **Precipitation:** Rain/weather delays
        
        **Matchup Factors (5):**
        5. **Platoon:** L/R matchup advantage
        6. **Pitcher vs Batter:** Historical head-to-head
        7. **Pitch Mix:** How batter performs vs pitcher's repertoire
        8. **Defense:** Opponent's defensive quality
        9. **Vegas:** Betting lines (run totals, win probability)
        
        **Park & Umpire (2):**
        10. **Park:** Hitter-friendly vs pitcher-friendly ballpark
        11. **Umpire:** Strike zone tendencies
        
        **Performance Trends (6):**
        12. **Recent Form:** Last 7-14 days performance
        13. **Momentum:** Hot/cold streak detection
        14. **Monthly Splits:** Performance in current month historically
        15. **Statcast:** Advanced metrics (exit velocity, barrel rate, etc.)
        16. **Rest Days:** Days since last game
        17. **Home/Away:** Performance splits
        
        **Opponent Analysis (3):**
        18. **Opponent Strength:** Team quality rating
        19. **Bullpen Quality:** Relief pitching strength
        20. **Injury Impact:** Key injuries affecting matchup
        
        ### How to Use This Table
        
        **Quick Scan:**
        - Top 10 = Your must-starts
        - Bottom 10 = Consider benching
        - Middle ranks = judgment calls
        
        **Deep Dive:**
        - Click into individual factor scores
        - Identify why a player is ranked where they are
        - Find exploitable matchups (multiple favorable factors)
        
        **Strategy:**
        - Sort by specific factors to find specialists
        - Compare similar-ranked players for tough lineup decisions
        - Use for DFS lineup construction
        
        ### Real-World Example
        ```
        Rank 1: Aaron Judge
        Score: +0.41
        🌟 STRONG START - Top tier matchup
        
        Why ranked #1?
        - Wind: +2.0 (blowing out to right field)
        - Park: +1.5 (Coors Field)
        - Recent Form: +1.0 (hitting .400 last 7 days)
        - Umpire: +0.7 (hitter-friendly zone)
        - Platoon: +1.0 (vs LHP, his strength)
        → Perfect storm of favorable factors!
        ```
        
        ### Color Coding
        - **Green highlights:** Positive factor scores (favorable)
        - **Red highlights:** Negative factor scores (unfavorable)
        - **No highlight:** Neutral or not applicable
        
        ### Tips
        - Don't fixate on one factor - it's the combination that matters
        - A player ranked #30 can still perform - these are probabilities
        - Use rankings as a tiebreaker, not gospel
        - Check updated rankings close to game time
        """)
