"""
Player Weight Breakdown Component

Displays factor weights for roster players and waiver wire prospects.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import glob
from .config import section_header_with_help


def render_player_weight_breakdown(df: pd.DataFrame):
    """
    Render player weight breakdown section with roster and waiver wire tabs
    
    Args:
        df: DataFrame with player data including factor scores and weights
    """
    section_header_with_help(
        "⚖️ Player Weight Breakdown",
        """
### What is Player Weight Breakdown?

View individual factor weights for roster players and top waiver wire prospects. This section allows you to drill down into exactly how each of the 20 factors contributes to a player's final sit/start recommendation.

### Factor Score

A **factor score** represents how favorable a specific matchup factor is for a player on a particular day.
- **Range:** Typically -1.0 to +2.0 (normalized scale)
- **Meaning:** 
  - Positive scores (>0) = Favorable conditions
  - Negative scores (<0) = Unfavorable conditions
  - Zero (0) = Neutral/average conditions
- **Example:** A wind factor score of +2.0 means strong wind blowing out (very favorable for hitters)

### Factor Weight

A **factor weight** represents how much importance/influence a specific factor has in the final recommendation.
- **Range:** 0.0 to 1.0 (percentage)
- **Purpose:** Determines how much each factor score contributes to the final decision
- **Calibrated:** Weights are optimized based on historical performance data for each player
- **Example:** If the wind factor has a weight of 0.15 (15%), it contributes 15% to the final score

### How They Work Together

**Final Score = Σ (Factor Score × Factor Weight)**

For each player, we:
1. Calculate 20 different factor scores (wind, umpire, park, etc.)
2. Multiply each score by its weight
3. Sum all weighted scores to get the final recommendation score

### Example Calculation

**Aaron Judge on a windy day:**
- Wind Score: +2.0, Weight: 0.15 → Contribution: +0.30
- Umpire Score: +0.7, Weight: 0.08 → Contribution: +0.056
- Park Score: -0.5, Weight: 0.12 → Contribution: -0.06
- *... (17 more factors)*
- **Final Score: +0.24 → 🌟 STRONG START**

### Using This Tool

1. **Select a Player:** Choose from your roster or top waiver prospects
2. **View Factor Weights:** See which factors matter most for this player
3. **View Factor Scores:** See today's conditions for each factor
4. **Weighted Contribution:** See the final impact (Score × Weight)
"""
    )
    
    # Create tabs for roster vs waiver wire
    tab1, tab2 = st.tabs(["📊 Roster Players", "🌟 Top 10 Waiver Wire"])
    
    with tab1:
        _render_roster_players_tab(df)
    
    with tab2:
        _render_waiver_wire_tab()


def _render_roster_players_tab(df):
    """Render roster players factor weight analysis"""
    st.markdown("#### Roster Players - Factor Weight Analysis")
    
    # Get all weight columns
    weight_cols = [col for col in df.columns if col.endswith('_weight')]
    
    if weight_cols:
        # Allow user to select a player
        selected_player = st.selectbox(
            "Select player to view detailed weights:",
            df['player_name'].tolist(),
            key="weight_breakdown_player"
        )
        
        if selected_player:
            player_row = df[df['player_name'] == selected_player].iloc[0]
            
            # Extract weights and scores for this player
            player_weights = {}
            player_scores = {}
            for col in weight_cols:
                factor_name = col.replace('_weight', '').title()
                weight_val = player_row[col]
                score_col = col.replace('_weight', '_score')
                score_val = player_row[score_col] if score_col in df.columns else 0
                
                if weight_val > 0:  # Only show factors with weight
                    player_weights[factor_name] = weight_val
                    player_scores[factor_name] = score_val
            
            # Create dual chart - weights and scores
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Factor Weights**")
                fig_weights = px.bar(
                    x=list(player_weights.keys()),
                    y=list(player_weights.values()),
                    labels={'x': 'Factor', 'y': 'Weight'},
                    color=list(player_weights.values()),
                    color_continuous_scale='Blues',
                    title=f'{selected_player} - Factor Weights'
                )
                fig_weights.update_layout(showlegend=False, xaxis_tickangle=-45)
                st.plotly_chart(fig_weights, use_container_width=True)
            
            with col2:
                st.markdown("**Factor Scores**")
                fig_scores = px.bar(
                    x=list(player_scores.keys()),
                    y=list(player_scores.values()),
                    labels={'x': 'Factor', 'y': 'Score'},
                    color=list(player_scores.values()),
                    color_continuous_scale='RdYlGn',
                    title=f'{selected_player} - Factor Scores'
                )
                fig_scores.update_layout(showlegend=False, xaxis_tickangle=-45)
                st.plotly_chart(fig_scores, use_container_width=True)
            
            # Show contribution breakdown
            st.markdown("**Weighted Contribution to Final Score**")
            
            contributions = {factor: score * player_weights.get(factor, 0) 
                           for factor, score in player_scores.items()}
            contrib_df = pd.DataFrame({
                'Factor': list(contributions.keys()),
                'Weight': [player_weights.get(f, 0) for f in contributions.keys()],
                'Score': [player_scores.get(f, 0) for f in contributions.keys()],
                'Contribution': list(contributions.values())
            })
            contrib_df = contrib_df.sort_values('Contribution', ascending=False)
            st.dataframe(contrib_df.style.format({
                'Weight': '{:.1%}',
                'Score': '{:.3f}',
                'Contribution': '{:.3f}'
            }).background_gradient(subset=['Contribution'], cmap='RdYlGn'), use_container_width=True)


def _render_waiver_wire_tab():
    """Render waiver wire prospects tab"""
    import glob
    import pandas as pd
    
    st.markdown("#### Top 10 Waiver Wire Prospects")
    
    # Load waiver wire data if available
    waiver_files = sorted(glob.glob('data/waiver_wire_*.csv'), reverse=True)
    
    if waiver_files:
        waiver_df = pd.read_csv(waiver_files[0])
        if len(waiver_df) > 0:
            # Show top 10 waiver wire options
            top_waiver = waiver_df.nlargest(10, 'final_score') if 'final_score' in waiver_df.columns else waiver_df.head(10)
            
            # Add Yahoo player links if available
            if 'player_key' in top_waiver.columns:
                top_waiver['yahoo_link'] = top_waiver['player_key'].apply(
                    lambda pk: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{pk.split('.')[-1]}" 
                    if pk and '.' in str(pk) else ''
                )
                st.dataframe(
                    top_waiver[['player_name', 'yahoo_link', 'final_score', 'recommendation']].head(10),
                    column_config={
                        "yahoo_link": st.column_config.LinkColumn("Yahoo", display_text="🔗")
                    },
                    use_container_width=True
                )
            else:
                st.dataframe(top_waiver[['player_name', 'final_score', 'recommendation']].head(10), use_container_width=True)
            
            # Allow selection for detailed view
            if len(top_waiver) > 0:
                # Get weight columns from waiver data
                weight_cols = [col for col in waiver_df.columns if col.endswith('_weight')]
                
                selected_fa = st.selectbox(
                    "Select waiver player for details:", 
                    top_waiver['player_name'].tolist(),
                    key="waiver_weight_breakdown"
                )
                
                if selected_fa and selected_fa in top_waiver['player_name'].values:
                    fa_row = top_waiver[top_waiver['player_name'] == selected_fa].iloc[0]
                    
                    # Extract weights and scores
                    fa_weights = {}
                    fa_scores = {}
                    for col in weight_cols:
                        factor_name = col.replace('_weight', '').title()
                        weight_val = fa_row[col] if col in fa_row else 0
                        score_col = col.replace('_weight', '_score')
                        score_val = fa_row[score_col] if score_col in fa_row else 0
                        
                        if weight_val > 0:
                            fa_weights[factor_name] = weight_val
                            fa_scores[factor_name] = score_val
                    
                    # Show chart
                    fig_fa = px.bar(
                        x=list(fa_weights.keys()),
                        y=list(fa_weights.values()),
                        labels={'x': 'Factor', 'y': 'Weight'},
                        title=f'{selected_fa} - Factor Weights',
                        color_discrete_sequence=['#ff7f0e']
                    )
                    fig_fa.update_layout(showlegend=False, xaxis_tickangle=-45)
                    st.plotly_chart(fig_fa, use_container_width=True)
        else:
            st.info("No waiver wire data available in this analysis")
    else:
        st.info("💡 Waiver wire analysis not yet run. Run with waiver wire analysis enabled to see top free agent prospects.")
