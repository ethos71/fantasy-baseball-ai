"""
Waiver Wire Section Component

Displays top available free agents with analysis.
"""

import streamlit as st
import pandas as pd
import glob


def render_waiver_wire():
    """
    Render waiver wire prospects section
    """
    col_header, col_help = st.columns([0.95, 0.05])
    with col_header:
        st.markdown('<div class="section-header-container"><h2>🔍 Waiver Wire Prospects</h2></div>', unsafe_allow_html=True)
    with col_help:
        with st.popover("ℹ️"):
            _render_help_content()
    
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


def _render_help_content():
    """Render help popover content"""
    st.markdown("""
### What This Section Shows

This displays the **top available free agents** based on the same 20-factor analysis used for your roster.

### How Waiver Wire Analysis Works

**Data Source:**
- Fetches top 100 available players from Yahoo Fantasy
- Filters to players not on any team in your league
- Runs same factor analysis as your roster

**Scoring:**
- Same 20 factors applied as your roster players
- Weighted scores based on player type (hitter/pitcher)
- Accounts for upcoming matchups and schedules

**Recommendations:**
- Players are ranked by final score (best to worst)
- Shows top 20 pickup targets by default
- Filter by position using the dropdown

### When to Use This

**Weekly Pickups:**
- Check before each matchup week starts
- Target high-scoring prospects for good matchups
- Stream pitchers for favorable schedules

**Injury Replacements:**
- Quick comparison of available players
- Find best available at specific position
- Prioritize players with upcoming favorable runs

**Strategic Adds:**
- Grab players before hot streaks
- Target players facing weak opponents
- Block opponents from good pickups

### How to Read Results

**Score Column:**
- Higher score = Better pickup target
- Scores > 0.15 = Strong pickup candidates
- Scores < 0 = Proceed with caution

**Recommendation Icons:**
- 🌟 = Elite pickup opportunity
- ✅ = Solid add for right matchup
- ⚖️ = Neutral, consider need/matchup
- ⚠️ = Risky, only if desperate
- 🚫 = Avoid unless specific need

### Real-World Example
```
Top Waiver Target:
Player: Luis Robert Jr. (OF)
Score: +0.32
🌟 STRONG PICKUP

Why?
- Upcoming series vs weak pitching
- Hot streak last 7 days (.385 AVG)
- Favorable park factors next week
- Multiple counting stats contributor
→ High-value add!
```

### Tips
- Run waiver analysis before weekly pickups
- Compare to your bench players (might be better to hold)
- Consider multi-game series for streaming
- Check player injury status before adding
- Use for DFS value plays
        """)


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
