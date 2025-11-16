"""
Waiver Wire Section Component

Displays top available free agents with analysis.
"""

import streamlit as st
import pandas as pd
import glob
from .config import section_header_with_help


def render_waiver_wire():
    """
    Render waiver wire prospects section
    """
    section_header_with_help(
        "🔍 Waiver Wire Prospects",
        """
### Waiver Wire Analysis

Discover the **best available free agents** based on upcoming matchups and performance trends. This analysis helps you find hidden gems before your league-mates do!

### What This Shows

**Top Available Players:**
- Best free agents based on next 7 days of matchups
- Sorted by average projected score
- Includes recent performance stats
- Position eligibility and ownership %

### How It Works

1. **Pulls Free Agents:** Fetches top available players from Yahoo
2. **Analyzes Matchups:** Runs sit/start analysis on upcoming games
3. **Averages Scores:** Calculates 7-day average score
4. **Ranks Players:** Sorts by highest average matchup quality

### Key Metrics

**Avg Score:** Average sit/start score over next 7 days
- Higher = better upcoming matchups
- +0.15+ = elite matchup week
- -0.15+ = avoid, poor matchup week

**Position:** Eligible positions (C, 1B, 2B, SS, 3B, OF, SP, RP)

**Own%:** League-wide ownership percentage
- <5% = deep sleeper
- 5-25% = solid pickup opportunity  
- 25-50% = popular waiver target
- >50% = probably shouldn't be available

**Recent Stats:** Last 7/14/30 day performance
- Helps identify hot streaks
- Context for matchup scores

### Strategy Tips

**Buy Low on Hot Matchups:**
- Low ownership + high avg score = great pickup
- Player might be cold but has favorable schedule

**Stream Starting Pitchers:**
- SPs with +0.10+ scores are streamable
- Check their next start specifically

**Stash for Playoffs:**
- Look at matchups beyond 7 days
- Some players have elite playoff schedules

**Beat the Wire:**
- Run analysis early in week
- Grab players before others notice

### When to Use

**Weekly:** Check Sunday night before waivers clear
**Injuries:** When your player goes on IL
**Slumps:** When your starter is struggling
**Streaming:** For daily matchup exploitation

### Example

```
Player: Jorge Polanco
Position: 2B, SS
Avg Score: +0.18 (next 7 days)
Own%: 12%
Last 7d: .320 AVG, 2 HR, 8 RBI

Analysis: Hot hitter + favorable schedule!
Action: Strong waiver claim priority
```
"""
    )
    
    # Load waiver wire data
    waiver_files = sorted(glob.glob('data/waiver_wire_*.csv'), reverse=True)
    
    if waiver_files:
        try:
            waiver_df = pd.read_csv(waiver_files[0])
            
            if len(waiver_df) > 0:
                _render_waiver_table(waiver_df)
            else:
                st.info("No waiver wire data available yet. Click 'Waiver Wire' in the sidebar to run analysis.")
        except Exception as e:
            st.error(f"Error loading waiver wire data: {str(e)}")
    else:
        st.info("🔍 No waiver wire data found. Click the **'Waiver Wire'** button in the sidebar to analyze available free agents.")



def _render_waiver_table(waiver_df):
    """Render the waiver wire table"""
    # Add position filter
    st.markdown("**Filter by Position:**")
    positions = ['All'] + sorted(waiver_df['position'].unique().tolist() if 'position' in waiver_df.columns else [])
    selected_pos = st.selectbox("Position Filter", positions, key="waiver_pos_filter", label_visibility="collapsed")
    
    # Filter by position if selected
    if selected_pos != 'All':
        waiver_filtered = waiver_df[waiver_df['position'] == selected_pos].copy()
    else:
        waiver_filtered = waiver_df.copy()
    
    # Sort by final score
    if 'final_score' in waiver_filtered.columns:
        waiver_filtered = waiver_filtered.sort_values('final_score', ascending=False)
    
    # Take top 20
    top_waiver = waiver_filtered.head(20)
    
    # Add Yahoo links
    if 'player_key' in top_waiver.columns:
        top_waiver['yahoo_link'] = top_waiver['player_key'].apply(
            lambda x: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{x.split('.')[-1]}" if x and '.' in str(x) else ''
        )
    else:
        top_waiver['yahoo_link'] = ''
    
    # Add rank
    top_waiver['rank'] = range(1, len(top_waiver) + 1)
    
    # Select and reorder columns
    display_cols = ['rank', 'player_name']
    if 'yahoo_link' in top_waiver.columns:
        display_cols.append('yahoo_link')
    if 'position' in top_waiver.columns:
        display_cols.append('position')
    if 'final_score' in top_waiver.columns:
        display_cols.append('final_score')
    if 'recommendation' in top_waiver.columns:
        display_cols.append('recommendation')
    
    # Add available columns
    for col in top_waiver.columns:
        if col not in display_cols and col != 'player_key':
            display_cols.append(col)
    
    waiver_display = top_waiver[[col for col in display_cols if col in top_waiver.columns]].copy()
    
    # Rename columns
    rename_map = {
        'rank': 'Rank',
        'player_name': 'Player',
        'yahoo_link': 'Yahoo',
        'position': 'Pos',
        'final_score': 'Score',
        'recommendation': 'Recommendation'
    }
    waiver_display = waiver_display.rename(columns=rename_map)
    
    # Display table
    st.dataframe(
        waiver_display,
        column_config={
            "Yahoo": st.column_config.LinkColumn(
                "Yahoo",
                help="Click to view Yahoo player page",
                display_text="🔗"
            ),
            "Score": st.column_config.NumberColumn("Score", format="%.3f") if 'Score' in waiver_display.columns else None,
        },
        use_container_width=True,
        height=600
    )
    
    st.info(f"📊 Showing top {len(top_waiver)} available players" + (f" at {selected_pos}" if selected_pos != 'All' else ""))
