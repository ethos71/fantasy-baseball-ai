"""
Full Player Rankings Component

Displays complete sortable table of all player rankings.
"""

import streamlit as st
import pandas as pd
from .config import section_header_with_help


def render_full_rankings(df: pd.DataFrame):
    """
    Render full player rankings table
    
    Args:
        df: DataFrame with player data including scores and recommendations
    """
    section_header_with_help(
        "📋 Full Player Rankings",
        """
### Full Player Rankings

This table shows **all players** on your roster sorted by their final sit/start score. Use this to get a complete view of your lineup and make informed decisions.

### Features

**Searchable & Sortable:**
- Search for any player by name
- Click column headers to sort
- Filter by score range or recommendation

**Key Columns:**

**Rank:** Overall ranking (1 = best matchup)
**Player:** Player name
**Yahoo:** Direct link to player's Yahoo page
**Score:** Final recommendation score (-2.0 to +2.0)
**Recommendation:** Sit/start guidance (🌟/✅/⚖️/⚠️/🚫)
**Factor Scores:** Individual scores for each of the 20 factors

### How to Use

1. **Find Your Player:** Use search box or scroll
2. **Check Their Score:** Higher = better matchup
3. **View Recommendation:** Icon tells you sit/start guidance
4. **Drill Into Factors:** See which factors drove the score
5. **Click Yahoo Link:** Jump directly to Yahoo for lineup changes

### Score Interpretation

- **+0.15+:** 🌟 Strong Start
- **+0.05 to +0.15:** ✅ Favorable
- **-0.05 to +0.05:** ⚖️ Neutral
- **-0.15 to -0.05:** ⚠️ Unfavorable
- **Below -0.15:** 🚫 Bench

### Tips

- Sort by score to see best/worst matchups
- Use search to quickly find specific players
- Compare similar players to break ties
- Check factor scores to understand why
"""
    )
    
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
