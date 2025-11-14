#!/usr/bin/env python3
"""
Fantasy Baseball AI - Streamlit Sit/Start Report
Interactive dashboard for sit/start recommendations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import glob
import os
import subprocess
import time

# Page config
st.set_page_config(
    page_title="FB-AI Sit/Start Report",
    page_icon="⚾",
    layout="wide"
)

# Add custom CSS for section headers and progress bars
st.markdown("""
<style>
    .section-header-container {
        background-color: #f0f2f6;
        padding: 10px 15px;
        border-radius: 5px;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .section-header-container h2 {
        margin: 0;
        padding: 0;
    }
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
    time.sleep(0.1)  # Small delay to allow UI to update

# Check if waiver wire needs to be run (daily at 8am) - NON-BLOCKING
def check_and_run_daily_waiver():
    """Check if waiver wire analysis needs to run, show button if needed"""
    from datetime import datetime, time as dtime
    import os
    
    # Get the most recent waiver wire file
    waiver_files = sorted(glob.glob('data/waiver_wire_*.csv'), reverse=True)
    
    now = datetime.now()
    today_8am = datetime.combine(now.date(), dtime(8, 0))
    
    # Check if we need to run waiver analysis
    should_run = False
    
    if not waiver_files:
        # No waiver file exists and it's past 8am today
        if now >= today_8am:
            should_run = True
    else:
        # Get the timestamp from the most recent file
        latest_file = waiver_files[0]
        file_mtime = datetime.fromtimestamp(os.path.getmtime(latest_file))
        
        # If the file is from before today's 8am and we're past 8am, run it
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

# Check (but don't block) for daily waiver wire
check_and_run_daily_waiver()

# Title
st.title("⚾ Fantasy Baseball AI - Sit/Start Analysis")
st.markdown("### Last Week of 2025 Season (Sept 28, 2025)")

# Load roster to get team names
@st.cache_data
def load_roster_file():
    roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
    if roster_files:
        return pd.read_csv(roster_files[0])
    return None

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
            progress_bar = st.sidebar.progress(0)
            status_text = st.sidebar.empty()
            output_expander = st.sidebar.expander("📋 Progress Log", expanded=True)
            
            import subprocess
            import threading
            
            def run_analysis():
                return subprocess.Popen(
                    ["./fb-ai", "--date", "2025-09-28", "--quick"],
                    cwd="/home/dominick/workspace/fantasy-baseball-ai",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
            
            process = run_analysis()
            steps = [
                "Loading data...",
                "Running factor analyzers...",
                "Calculating scores...",
                "Generating recommendations...",
                "Finalizing..."
            ]
            
            output_lines = []
            step_idx = 0
            
            with output_expander:
                log_container = st.empty()
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    output_lines.append(line.strip())
                    log_container.code('\n'.join(output_lines[-10:]))  # Show last 10 lines
                    
                    # Update progress based on output
                    if "factor" in line.lower():
                        step_idx = min(1, step_idx)
                    elif "score" in line.lower() or "weight" in line.lower():
                        step_idx = min(2, step_idx)
                    elif "recommendation" in line.lower():
                        step_idx = min(3, step_idx)
                    
                    progress = min(0.9, (step_idx + 1) / len(steps))
                    progress_bar.progress(progress)
                    status_text.text(f"⏳ {steps[step_idx]}")
            
            returncode = process.wait()
            
            if returncode == 0:
                progress_bar.progress(1.0)
                status_text.text("✅ Complete!")
                st.sidebar.success("✅ Analysis complete! Refresh page to see results.")
            else:
                st.sidebar.error(f"❌ Error: Process exited with code {returncode}")
    
    with col2:
        if st.sidebar.button("🔍 Waiver Wire", help="Run waiver wire prospect analysis", use_container_width=True):
            progress_bar = st.sidebar.progress(0)
            status_text = st.sidebar.empty()
            output_expander = st.sidebar.expander("📋 Progress Log", expanded=True)
            
            import subprocess
            
            def run_waiver():
                return subprocess.Popen(
                    ["python3", "src/scripts/daily_sitstart.py", "--date", "2025-09-28", "--skip-tune"],
                    cwd="/home/dominick/workspace/fantasy-baseball-ai",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
            
            process = run_waiver()
            output_lines = []
            progress = 0
            
            with output_expander:
                log_container = st.empty()
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    output_lines.append(line.strip())
                    log_container.code('\n'.join(output_lines[-10:]))
                    
                    # Increment progress
                    progress = min(0.9, progress + 0.05)
                    progress_bar.progress(progress)
                    
                    if "waiver" in line.lower():
                        status_text.text("⏳ Analyzing waiver wire...")
                    elif "player" in line.lower():
                        status_text.text("⏳ Evaluating players...")
            
            returncode = process.wait()
            
            if returncode == 0:
                progress_bar.progress(1.0)
                status_text.text("✅ Complete!")
                st.sidebar.success("✅ Waiver analysis complete! Check waiver wire section below.")
            else:
                st.sidebar.error(f"❌ Error: Process exited with code {returncode}")
    
    # Add manual roster refresh button
    if st.sidebar.button("📥 Refresh Roster", help="Fetch latest roster from Yahoo Fantasy", use_container_width=True):
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        output_expander = st.sidebar.expander("📋 Progress Log", expanded=True)
        
        import subprocess
        
        status_text.text("⏳ Connecting to Yahoo...")
        progress_bar.progress(0.1)
        
        def run_refresh():
            return subprocess.Popen(
                ["python3", "src/scripts/scrape/yahoo_scrape.py"],
                cwd="/home/dominick/workspace/fantasy-baseball-ai",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        
        process = run_refresh()
        output_lines = []
        progress = 0.1
        
        with output_expander:
            log_container = st.empty()
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line.strip())
                log_container.code('\n'.join(output_lines[-10:]))
                
                # Update progress based on output
                if "OAuth" in line or "authentication" in line.lower():
                    progress = 0.2
                    status_text.text("⏳ Authenticating...")
                elif "Finding" in line or "team" in line.lower():
                    progress = 0.4
                    status_text.text("⏳ Finding teams...")
                elif "Fetching" in line:
                    progress = min(0.8, progress + 0.2)
                    status_text.text("⏳ Fetching roster...")
                elif "Exported" in line:
                    progress = 0.95
                    status_text.text("⏳ Saving data...")
                
                progress_bar.progress(progress)
        
        returncode = process.wait()
        
        if returncode == 0:
            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")
            st.sidebar.success("✅ Roster refreshed from Yahoo! Page will reload in 2 seconds...")
            time.sleep(2)
            st.rerun()
        else:
            st.sidebar.error(f"❌ Error refreshing roster")
    
    # Add weight calibration button (full width)
    if st.sidebar.button("⚖️ Calibrate Weights", help="Run weight optimization (takes 30+ minutes)", use_container_width=True):
        progress_bar = st.sidebar.progress(0)
        status_text = st.sidebar.empty()
        output_expander = st.sidebar.expander("📋 Progress Log", expanded=True)
        
        import subprocess
        
        status_text.text("⏳ Starting calibration...")
        progress_bar.progress(0.05)
        
        def run_calibration():
            return subprocess.Popen(
                ["python3", "src/scripts/daily_sitstart.py", "--date", "2025-09-28", "--tune-only"],
                cwd="/home/dominick/workspace/fantasy-baseball-ai",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
        
        process = run_calibration()
        output_lines = []
        progress = 0.05
        trials_completed = 0
        
        with output_expander:
            log_container = st.empty()
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                output_lines.append(line.strip())
                log_container.code('\n'.join(output_lines[-15:]))  # Show last 15 lines
                
                # Track optimization trials
                if "trial" in line.lower() or "iteration" in line.lower():
                    trials_completed += 1
                    # Assume ~100 trials total
                    progress = min(0.9, 0.1 + (trials_completed / 100) * 0.8)
                    progress_bar.progress(progress)
                    status_text.text(f"⏳ Optimizing weights... Trial {trials_completed}")
                elif "best" in line.lower() and "score" in line.lower():
                    status_text.text(f"⏳ Found better weights! Trial {trials_completed}")
        
        returncode = process.wait()
        
        if returncode == 0:
            progress_bar.progress(1.0)
            status_text.text("✅ Complete!")
            st.sidebar.success("✅ Weight calibration complete! Weights have been optimized.")
        else:
            st.sidebar.error(f"❌ Error during calibration")
else:
    selected_team = None

# Show placeholder immediately while data loads in background
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.df = None

# Load recommendations data early to show summary metrics
rec_files = sorted(glob.glob('data/sitstart_recommendations_*.csv'), reverse=True)

if rec_files:
    latest_file = rec_files[0]
    
    # Position abbreviation mapping (Yahoo style) - define globally
    # Use Yahoo roster data for SP/RP classification
    def abbreviate_position(pos, player_name='', yahoo_position=''):
        # If we have Yahoo position data with SP/RP, use it
        if yahoo_position:
            if 'SP' in yahoo_position and 'RP' in yahoo_position:
                return 'SP,RP'  # Both eligible
            elif 'SP' in yahoo_position:
                return 'SP'
            elif 'RP' in yahoo_position:
                return 'RP'
        
        # Fallback to MLB data position mapping
        abbrev_map = {
            'Catcher': 'C',
            'First Base': '1B',
            'Second Base': '2B',
            'Third Base': '3B',
            'Shortstop': 'SS',
            'Outfielder': 'OF',
            'Designated Hitter': 'DH',
            'Pitcher': 'P',
            'Infielder': 'IF',
            'Unknown': '?'
        }
        return abbrev_map.get(pos, pos)
    
    # Helper function to create Yahoo player link
    def create_yahoo_link(player_name, player_key=''):
        """Create Yahoo Fantasy player page link"""
        if player_key:
            # player_key format: {game_id}.p.{player_id}
            # Extract player_id from player_key
            player_id = player_key.split('.')[-1] if '.' in player_key else ''
            if player_id:
                url = f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{player_id}"
                return f'<a href="{url}" target="_blank">{player_name}</a>'
        return player_name
    
    # Load recommendations for summary
    df_summary = pd.read_csv(latest_file)
    
    # Filter by team if needed
    if selected_team:
        try:
            roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
            if roster_files:
                roster = pd.read_csv(roster_files[0])
                if 'fantasy_team' in roster.columns:
                    team_players = roster[roster['fantasy_team'] == selected_team]['player_name'].tolist()
                    df_summary = df_summary[df_summary['player_name'].isin(team_players)]
        except:
            pass
    
    # Display summary metrics
    st.markdown("---")
    
    # Summary metrics with help popup
    col1, col2, col3, col4, col_help = st.columns([2, 2, 2, 2, 1])
    
    with col1:
        st.metric("Total Players", len(df_summary))
    
    with col2:
        starts = len(df_summary[df_summary['recommendation'].str.contains('START', na=False)])
        st.metric("Recommended Starts", starts)
    
    with col3:
        sits = len(df_summary[df_summary['recommendation'].str.contains('SIT', na=False)])
        st.metric("Recommended Sits", sits)
    
    with col4:
        neutral = len(df_summary[df_summary['recommendation'].str.contains('NEUTRAL', na=False)])
        st.metric("Neutral", neutral)
    
    with col_help:
        st.write("")  # Spacer
        with st.popover("ℹ️"):
            st.markdown("""
            ### What These Numbers Mean
            
            **Total Players:** The complete count of players on your selected fantasy team roster.
            
            **Recommended Starts:** Players with favorable matchup conditions based on our 20-factor analysis.
            - **🌟 Strong Start** (score ≥ 0.15): Top-tier matchups, definitely start
            - **✅ Favorable** (score ≥ 0.05): Good matchups, strong start candidates
            
            **Recommended Sits:** Players with unfavorable matchup conditions.
            - **⚠️ Unfavorable** (score ≥ -0.15): Poor matchups, consider benching
            - **🚫 Bench** (score < -0.15): Very poor matchups, definitely bench
            
            **Neutral:** Players with average matchup conditions (score between -0.05 and +0.05).
            - Consider other factors like recent form, importance of game, roster constraints
            
            ### How We Calculate
            Each player receives a **final score** based on 20 factors:
            ```
            Final Score = Σ(Factor Score × Factor Weight)
            ```
            
            ### Real-World Example
            Aaron Judge with final score of +0.24:
            - Wind blowing out (+2.0 × 0.045) = +0.09
            - Favorable park (+0.5 × 0.056) = +0.028
            - Hot streak (+1.0 × 0.046) = +0.046
            - Plus 17 other factors...
            - **Total: +0.24 → 🌟 STRONG START**
            
            ### Decision Guidelines
            - **≥ 15 Starts recommended?** Good matchup week, be aggressive
            - **< 10 Starts recommended?** Tough week, be selective
            - **High Neutral count?** More decisions left to your judgment
            """)
    
    st.markdown("---")

# Load roster and game logs for stats
@st.cache_data
def load_roster_stats(team_filter):
    # Get latest roster
    roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
    if not roster_files:
        return None, None, None
    
    roster = pd.read_csv(roster_files[0])
    
    # Filter by fantasy team
    if team_filter and 'fantasy_team' in roster.columns:
        roster = roster[roster['fantasy_team'] == team_filter]
    
    # Load game logs
    try:
        game_logs = pd.read_csv('data/mlb_game_logs_2025.csv')
        game_logs['game_date'] = pd.to_datetime(game_logs['game_date'])
        
        # Calculate stats for last 7, 14, 30 days from Sept 28
        from datetime import timedelta
        target_date = pd.to_datetime('2025-09-28')
        
        stats_7d = calculate_period_stats(game_logs, roster, target_date, 7)
        stats_14d = calculate_period_stats(game_logs, roster, target_date, 14)
        stats_30d = calculate_period_stats(game_logs, roster, target_date, 30)
        
        return roster, (stats_7d, stats_14d, stats_30d)
    except:
        return roster, None

def calculate_period_stats(game_logs, roster, target_date, days):
    from datetime import timedelta
    cutoff = target_date - timedelta(days=days)
    
    period_logs = game_logs[
        (game_logs['game_date'] >= cutoff) & 
        (game_logs['game_date'] < target_date)
    ]
    
    # Load MLB players data for positions
    try:
        mlb_players = pd.read_csv('data/mlb_all_players_2025.csv')
        position_map = dict(zip(mlb_players['player_name'], mlb_players['position']))
    except:
        position_map = {}
    
    # Position abbreviation - uses Yahoo position data if available
    def abbreviate_position(pos, player_name='', yahoo_position=''):
        # If we have Yahoo position data with SP/RP, use it
        if yahoo_position:
            if 'SP' in yahoo_position and 'RP' in yahoo_position:
                return 'SP,RP'
            elif 'SP' in yahoo_position:
                return 'SP'
            elif 'RP' in yahoo_position:
                return 'RP'
        
        # Fallback to abbreviation map
        abbrev_map = {
            'Catcher': 'C',
            'First Base': '1B',
            'Second Base': '2B',
            'Third Base': '3B',
            'Shortstop': 'SS',
            'Outfielder': 'OF',
            'Designated Hitter': 'DH',
            'Pitcher': 'P',
            'Infielder': 'IF',
            'Unknown': '?'
        }
        return abbrev_map.get(pos, pos)
    
    stats_list = []
    for idx, player in roster.iterrows():
        player_name = player['player_name']
        player_logs = period_logs[period_logs['player_name'] == player_name]
        
        # Get position - prefer Yahoo position data for SP/RP
        yahoo_pos = player.get('position', '')
        mlb_position = position_map.get(player_name, 'Unknown')
        position_abbrev = abbreviate_position(mlb_position, player_name, yahoo_pos)
        
        if len(player_logs) > 0:
            # Determine if player is on bench (simple heuristic: last ~10 players in roster order are bench)
            # Typical Yahoo roster: ~20-25 active, rest are bench
            total_roster_size = len(roster)
            is_bench = idx >= (total_roster_size * 0.6)  # Last 40% considered bench
            
            stats = {
                'roster_order': idx,  # Preserve Yahoo roster order
                'player_name': player_name,
                'status': '🪑 Bench' if is_bench else '✅ Active',
                'position': position_abbrev,
                'team': player.get('mlb_team', ''),
                'games': len(player_logs),
                'ab': player_logs['AB'].sum(),
                'h': player_logs['H'].sum(),
                'r': player_logs['R'].sum(),
                'rbi': player_logs['RBI'].sum(),
                'hr': player_logs['HR'].sum(),
                'sb': player_logs['SB'].sum(),
                'bb': player_logs['BB'].sum(),
                'so': player_logs['SO'].sum(),
                'avg': player_logs['H'].sum() / player_logs['AB'].sum() if player_logs['AB'].sum() > 0 else 0,
                'obp': player_logs['OBP'].iloc[-1] if 'OBP' in player_logs.columns else 0,
                'slg': player_logs['SLG'].iloc[-1] if 'SLG' in player_logs.columns else 0,
                'ops': player_logs['OPS'].iloc[-1] if 'OPS' in player_logs.columns else 0,
            }
            stats_list.append(stats)
    
    df = pd.DataFrame(stats_list) if stats_list else pd.DataFrame()
    # Sort by roster order to match Yahoo
    if not df.empty and 'roster_order' in df.columns:
        df = df.sort_values('roster_order')
    return df

# Display roster stats
roster, period_stats = load_roster_stats(selected_team)

if roster is not None and period_stats is not None:
    # Header with help icon
    col_header, col_help = st.columns([0.95, 0.05])
    with col_header:
        st.markdown('<div class="section-header-container"><h2>📊 Current Roster Performance</h2></div>', unsafe_allow_html=True)
    with col_help:
        with st.popover("ℹ️"):
            st.markdown("""
        ### What You're Seeing
            
            This section shows your **actual performance statistics** over recent time periods (7/14/30 days).
            Unlike the sit/start recommendations which are **predictive**, these are **historical results**.
            
            ### Key Statistics Explained
            
            **Status:**
            - **✅ Active:** Players in your starting lineup (first ~60% of roster)
            - **🪑 Bench:** Players on your bench (last ~40% of roster)
            
            **Position:** Yahoo-style abbreviations (C, 1B, 2B, 3B, SS, OF, SP, RP, etc.)
            
            **Games:** Number of games the player appeared in during the period
            
            **Batting Stats (Hitters):**
            - **AB:** At Bats
            - **H:** Hits
            - **R:** Runs scored
            - **RBI:** Runs Batted In
            - **HR:** Home Runs
            - **SB:** Stolen Bases
            - **AVG:** Batting Average (H ÷ AB)
            - **OPS:** On-Base Plus Slugging (combines OBP + SLG)
            
            **OPS Color Gradient:**
            - 🟢 Green: High OPS (excellent performance)
            - 🟡 Yellow: Medium OPS (average performance)
            - 🔴 Red: Low OPS (poor performance)
            
            ### How to Use This Data
            
            **7-Day View:** Most recent form, use for immediate decisions
            - Hot streaks appear here first
            - Quick identification of slumping players
            
            **14-Day View:** Balanced view of recent performance
            - Filters out single-game outliers
            - Good for trend identification
            
            **30-Day View:** Broader performance context
            - Shows consistency vs volatility
            - Helps identify seasonal trends
            
            ### Real-World Example
            ```
            Player: Aaron Judge
            7-Day:  .350 AVG, 1.200 OPS (🟢 Hot - keep starting!)
            14-Day: .310 AVG, 1.050 OPS (🟢 Consistent performer)
            30-Day: .290 AVG, 0.950 OPS (🟢 Solid season)
            ```
            
            ### Tips
            - Compare across time periods to spot trends
            - Green OPS players = safer starts
            - Bench players with poor stats may need roster moves
            - Players in Yahoo roster order = same order as your Yahoo team
            """)
    
    stats_7d, stats_14d, stats_30d = period_stats
    
    # Create tabs for different periods
    tab1, tab2, tab3 = st.tabs(["Last 7 Days", "Last 14 Days", "Last 30 Days"])
    
    with tab1:
        if not stats_7d.empty:
            section_header("Last 7 Days (Yahoo Roster Order)", "")
            
            # Display all players in roster order with position and status
            # Add Yahoo player links
            stats_7d_display = stats_7d.copy()
            # Load player_key mapping from roster
            try:
                roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
                if roster_files:
                    yahoo_roster = pd.read_csv(roster_files[0])
                    if 'player_key' in yahoo_roster.columns:
                        player_key_map = dict(zip(yahoo_roster['player_name'], yahoo_roster['player_key']))
                        stats_7d_display['player_key'] = stats_7d_display['player_name'].map(player_key_map).fillna('')
                        stats_7d_display['yahoo_link'] = stats_7d_display['player_key'].apply(
                            lambda pk: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{pk.split('.')[-1]}" 
                            if pk and '.' in str(pk) else ''
                        )
            except:
                stats_7d_display['yahoo_link'] = ''
            
            display_cols = ['player_name', 'yahoo_link', 'status', 'position', 'team', 'games', 'ab', 'h', 'r', 'rbi', 'hr', 'sb', 'avg', 'ops']
            all_display = stats_7d_display[[col for col in display_cols if col in stats_7d_display.columns]].copy()
            if 'avg' in all_display.columns:
                all_display['avg'] = all_display['avg'].round(3)
            if 'ops' in all_display.columns:
                all_display['ops'] = all_display['ops'].round(3)
            
            st.dataframe(
                all_display,
                column_config={
                    "yahoo_link": st.column_config.LinkColumn("Yahoo", display_text="🔗"),
                    "avg": st.column_config.NumberColumn("avg", format="%.3f"),
                    "ops": st.column_config.NumberColumn("ops", format="%.3f"),
                },
                use_container_width=True,
                height=600
            )
        else:
            st.info("No stats available for last 7 days")
    
    with tab2:
        if not stats_14d.empty:
            section_header("Last 14 Days (Yahoo Roster Order)", "")
            
            # Add Yahoo player links
            stats_14d_display = stats_14d.copy()
            try:
                roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
                if roster_files:
                    yahoo_roster = pd.read_csv(roster_files[0])
                    if 'player_key' in yahoo_roster.columns:
                        player_key_map = dict(zip(yahoo_roster['player_name'], yahoo_roster['player_key']))
                        stats_14d_display['player_key'] = stats_14d_display['player_name'].map(player_key_map).fillna('')
                        stats_14d_display['yahoo_link'] = stats_14d_display['player_key'].apply(
                            lambda pk: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{pk.split('.')[-1]}" 
                            if pk and '.' in str(pk) else ''
                        )
            except:
                stats_14d_display['yahoo_link'] = ''
            
            display_cols = ['player_name', 'yahoo_link', 'status', 'position', 'team', 'games', 'ab', 'h', 'r', 'rbi', 'hr', 'sb', 'avg', 'ops']
            all_display = stats_14d_display[[col for col in display_cols if col in stats_14d_display.columns]].copy()
            if 'avg' in all_display.columns:
                all_display['avg'] = all_display['avg'].round(3)
            if 'ops' in all_display.columns:
                all_display['ops'] = all_display['ops'].round(3)
            
            st.dataframe(
                all_display,
                column_config={
                    "yahoo_link": st.column_config.LinkColumn("Yahoo", display_text="🔗"),
                    "avg": st.column_config.NumberColumn("avg", format="%.3f"),
                    "ops": st.column_config.NumberColumn("ops", format="%.3f"),
                },
                use_container_width=True,
                height=600
            )
        else:
            st.info("No stats available for last 14 days")
    
    with tab3:
        if not stats_30d.empty:
            section_header("Last 30 Days (Yahoo Roster Order)", "")
            
            # Add Yahoo player links
            stats_30d_display = stats_30d.copy()
            try:
                roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
                if roster_files:
                    yahoo_roster = pd.read_csv(roster_files[0])
                    if 'player_key' in yahoo_roster.columns:
                        player_key_map = dict(zip(yahoo_roster['player_name'], yahoo_roster['player_key']))
                        stats_30d_display['player_key'] = stats_30d_display['player_name'].map(player_key_map).fillna('')
                        stats_30d_display['yahoo_link'] = stats_30d_display['player_key'].apply(
                            lambda pk: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{pk.split('.')[-1]}" 
                            if pk and '.' in str(pk) else ''
                        )
            except:
                stats_30d_display['yahoo_link'] = ''
            
            display_cols = ['player_name', 'yahoo_link', 'status', 'position', 'team', 'games', 'ab', 'h', 'r', 'rbi', 'hr', 'sb', 'avg', 'ops']
            all_display = stats_30d_display[[col for col in display_cols if col in stats_30d_display.columns]].copy()
            if 'avg' in all_display.columns:
                all_display['avg'] = all_display['avg'].round(3)
            if 'ops' in all_display.columns:
                all_display['ops'] = all_display['ops'].round(3)
            
            st.dataframe(
                all_display,
                column_config={
                    "yahoo_link": st.column_config.LinkColumn("Yahoo", display_text="🔗"),
                    "avg": st.column_config.NumberColumn("avg", format="%.3f"),
                    "ops": st.column_config.NumberColumn("ops", format="%.3f"),
                },
                use_container_width=True,
                height=600
            )
        else:
            st.info("No stats available for last 30 days")
    
    st.markdown("---")

# Continue with detailed recommendations display
if not rec_files:
    st.error("❌ No recommendations files found!")
    st.stop()

# Get file metadata for sidebar
file_timestamp = latest_file.split('_')[-2] + '_' + latest_file.split('_')[-1].replace('.csv', '')
file_date = datetime.strptime(file_timestamp, '%Y%m%d_%H%M%S')

st.sidebar.markdown(f"**Analysis Date:** {file_date.strftime('%Y-%m-%d %I:%M %p')}")
st.sidebar.markdown(f"**File:** `{os.path.basename(latest_file)}`")

# Load data for detailed display
@st.cache_data
def load_data(filepath, team_filter):
    df = pd.read_csv(filepath)
    
    # Load Yahoo roster for position data (SP/RP) and player_key
    yahoo_positions = {}
    yahoo_player_keys = {}
    try:
        roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
        if roster_files:
            yahoo_roster = pd.read_csv(roster_files[0])
            yahoo_positions = dict(zip(yahoo_roster['player_name'], yahoo_roster['position']))
            if 'player_key' in yahoo_roster.columns:
                yahoo_player_keys = dict(zip(yahoo_roster['player_name'], yahoo_roster['player_key']))
    except:
        pass
    
    # Load player positions to categorize hitters vs pitchers and add position column
    try:
        players_2025 = pd.read_csv('data/mlb_all_players_2025.csv')
        # Merge to get position_type and position
        df = df.merge(
            players_2025[['player_name', 'position', 'position_type']], 
            on='player_name', 
            how='left'
        )
        # Categorize as Hitter or Pitcher
        df['player_type'] = df['position_type'].apply(
            lambda x: 'Pitcher' if x == 'Pitcher' else 'Hitter'
        )
        # Fill NaN with Hitter (assume hitter if unknown)
        df['player_type'].fillna('Hitter', inplace=True)
        # Clean up position column and abbreviate with Yahoo position for SP/RP distinction
        df['position'].fillna('Unknown', inplace=True)
        df['yahoo_pos'] = df['player_name'].map(yahoo_positions).fillna('')
        df['position'] = df.apply(lambda row: abbreviate_position(row['position'], row['player_name'], row['yahoo_pos']), axis=1)
        # Add player_key for Yahoo links
        df['player_key'] = df['player_name'].map(yahoo_player_keys).fillna('')
    except:
        # If player data not available, classify based on name patterns or default
        df['player_type'] = 'Hitter'
        df['position'] = 'Unknown'
        df['player_key'] = ''
    
    # Load roster to filter by fantasy team
    if team_filter:
        try:
            roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
            if roster_files:
                roster = pd.read_csv(roster_files[0])
                if 'fantasy_team' in roster.columns:
                    team_players = roster[roster['fantasy_team'] == team_filter]['player_name'].tolist()
                    df = df[df['player_name'].isin(team_players)]
        except:
            pass
    
    return df

# Load data with caching - only load once per session
if not st.session_state.data_loaded or st.session_state.df is None:
    with st.spinner("⏳ Loading data..."):
        df = load_data(latest_file, selected_team)
        st.session_state.df = df
        st.session_state.data_loaded = True
else:
    df = st.session_state.df

# Top Starts and Sits - Split by Hitters and Pitchers with help icon
st.markdown('<div class="section-header-container"><h2>🌟🚫 Top Starts & Bottom Sits</h2></div>', unsafe_allow_html=True)
with st.popover("" \
"ℹ️"):
        st.markdown("""
    ### How to Read These Recommendations
        
        This section shows your **best and worst matchups** for the selected game date, separated by position type.
        
        ### The 5 Recommendation Levels
        
        **🌟 Strong Start (≥ 0.15):**
        - Top-tier matchup with multiple favorable factors
        - **Action:** Start with high confidence
        - **Example:** Aaron Judge vs LHP, wind blowing out, favorable park
        
        **✅ Favorable (≥ 0.05):**
        - Good matchup with some positive factors
        - **Action:** Strong start candidate
        - **Example:** Most everyday players on average days
        
        **⚖️ Neutral (-0.05 to +0.05):**
        - Average matchup, mixed factors
        - **Action:** Use other context (roster needs, opponent strength)
        - **Example:** Backup catcher vs average pitcher
        
        **⚠️ Unfavorable (≥ -0.15):**
        - Poor matchup with negative factors
        - **Action:** Consider benching if you have alternatives
        - **Example:** Slumping hitter vs elite pitcher in pitcher's park
        
        **🚫 Bench (< -0.15):**
        - Very poor matchup, multiple unfavorable factors
        - **Action:** Bench unless no alternatives
        - **Example:** Cold hitter vs ace pitcher with bad umpire
        
        ### Why Separate Hitters and Pitchers?
        
        **Hitters:**
        - Evaluated on: park factors, pitcher matchup, weather, umpire, hot streaks
        - Top 5 = your best offensive plays
        - Bottom 5 = consider benching for better options
        
        **Pitchers (SP/RP):**
        - Evaluated on: opponent strength, park factors, recent performance
        - Top 5 = your best pitching matchups
        - Bottom 5 = risky starts, high blow-up potential
        
        ### The Math Behind It
        ```
        Player Score = Σ(Factor Score × Factor Weight)
        
        Example - Aaron Judge (+0.24):
        Wind:         +2.0 × 0.045 = +0.090
        Umpire:       +0.7 × 0.025 = +0.018
        Park:         +0.5 × 0.056 = +0.028
        Recent Form:  +1.0 × 0.046 = +0.046
        ... (16 more factors)
        = +0.24 → 🌟 STRONG START
        ```
        
        ### Real-World Strategy
        
        **When You See Strong Starts:**
        - Prioritize these players in your lineup
        - Consider them for DFS plays
        - High confidence plays
        
        **When You See Benches:**
        - Sit if you have alternatives
        - Don't panic-drop - it's just one day
        - May still be valuable ROS (rest of season)
        
        **Position Abbreviations:**
        - C = Catcher, 1B/2B/3B/SS = Infield, OF = Outfield
        - SP = Starting Pitcher, RP = Relief Pitcher
        
        ### Tips
        - Start your 🌟 and ✅ players whenever possible
        - Bench your 🚫 and ⚠️ players if you have better options
        - ⚖️ Neutral players? Use gut feeling or recent stats
        - Check opponent's pitcher (for hitters) or lineup (for pitchers)
        """)

# Separate hitters and pitchers
hitters_df = df[df['player_type'] == 'Hitter'].copy()
pitchers_df = df[df['player_type'] == 'Pitcher'].copy()

# Create two columns for starts/sits
col_starts, col_sits = st.columns(2)

with col_starts:
    st.markdown("### 🌟 Top 5 Starts")
    
    # Top 5 Hitters
    if len(hitters_df) > 0:
        st.markdown("**🔨 Hitters**")
        top_hitters = hitters_df.nlargest(5, 'final_score')[['player_name', 'player_key', 'position', 'final_score', 'recommendation']].copy()
        top_hitters.index = range(1, len(top_hitters) + 1)
        # Create Yahoo link
        top_hitters['player_link'] = top_hitters.apply(
            lambda row: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{row['player_key'].split('.')[-1]}" 
            if row['player_key'] and '.' in str(row['player_key']) else '', axis=1
        )
        display_df = top_hitters[['player_name', 'player_link', 'position', 'final_score', 'recommendation']].copy()
        display_df.columns = ['Player', 'Link', 'Position', 'Score', 'Recommendation']
        
        st.dataframe(
            display_df,
            column_config={
                "Link": st.column_config.LinkColumn("Yahoo", display_text="🔗"),
                "Score": st.column_config.NumberColumn("Score", format="%.3f")
            },
            use_container_width=True, 
            height=210
        )
    
    # Top 5 Pitchers
    if len(pitchers_df) > 0:
        st.markdown("**⚾ Pitchers**")
        top_pitchers = pitchers_df.nlargest(5, 'final_score')[['player_name', 'player_key', 'position', 'final_score', 'recommendation']].copy()
        top_pitchers.index = range(1, len(top_pitchers) + 1)
        # Create Yahoo link
        top_pitchers['player_link'] = top_pitchers.apply(
            lambda row: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{row['player_key'].split('.')[-1]}" 
            if row['player_key'] and '.' in str(row['player_key']) else '', axis=1
        )
        display_df = top_pitchers[['player_name', 'player_link', 'position', 'final_score', 'recommendation']].copy()
        display_df.columns = ['Player', 'Link', 'Position', 'Score', 'Recommendation']
        
        st.dataframe(
            display_df,
            column_config={
                "Link": st.column_config.LinkColumn("Yahoo", display_text="🔗"),
                "Score": st.column_config.NumberColumn("Score", format="%.3f")
            },
            use_container_width=True, 
            height=210
        )

with col_sits:
    st.markdown("### 🚫 Bottom 5 Sits")
    
    # Bottom 5 Hitters
    if len(hitters_df) > 0:
        st.markdown("**🔨 Hitters**")
        bottom_hitters = hitters_df.nsmallest(5, 'final_score')[['player_name', 'player_key', 'position', 'final_score', 'recommendation']].copy()
        bottom_hitters.index = range(1, len(bottom_hitters) + 1)
        # Create Yahoo link
        bottom_hitters['player_link'] = bottom_hitters.apply(
            lambda row: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{row['player_key'].split('.')[-1]}" 
            if row['player_key'] and '.' in str(row['player_key']) else '', axis=1
        )
        display_df = bottom_hitters[['player_name', 'player_link', 'position', 'final_score', 'recommendation']].copy()
        display_df.columns = ['Player', 'Link', 'Position', 'Score', 'Recommendation']
        
        st.dataframe(
            display_df,
            column_config={
                "Link": st.column_config.LinkColumn("Yahoo", display_text="🔗"),
                "Score": st.column_config.NumberColumn("Score", format="%.3f")
            },
            use_container_width=True, 
            height=210
        )
    
    # Bottom 5 Pitchers
    if len(pitchers_df) > 0:
        st.markdown("**⚾ Pitchers**")
        bottom_pitchers = pitchers_df.nsmallest(5, 'final_score')[['player_name', 'player_key', 'position', 'final_score', 'recommendation']].copy()
        bottom_pitchers.index = range(1, len(bottom_pitchers) + 1)
        # Create Yahoo link
        bottom_pitchers['player_link'] = bottom_pitchers.apply(
            lambda row: f"https://baseball.fantasysports.yahoo.com/b1/3119/3/{row['player_key'].split('.')[-1]}" 
            if row['player_key'] and '.' in str(row['player_key']) else '', axis=1
        )
        display_df = bottom_pitchers[['player_name', 'player_link', 'position', 'final_score', 'recommendation']].copy()
        display_df.columns = ['Player', 'Link', 'Position', 'Score', 'Recommendation']
        
        st.dataframe(
            display_df,
            column_config={
                "Link": st.column_config.LinkColumn("Yahoo", display_text="🔗"),
                "Score": st.column_config.NumberColumn("Score", format="%.3f")
            },
            use_container_width=True, 
            height=210
        )

st.markdown("---")

# Player Weight Breakdown Section
section_header("Player Weight Breakdown", "⚖️")
st.markdown("View individual factor weights for roster players and top waiver wire prospects")

# Create tabs for roster vs waiver wire
tab1, tab2 = st.tabs(["📊 Roster Players", "🌟 Top 10 Waiver Wire"])

with tab1:
    # Header with help icon
    col_header, col_help = st.columns([10, 1])
    with col_header:
        st.markdown("#### Roster Players - Factor Weight Analysis")
    with col_help:
        with st.popover("ℹ️"):
            st.markdown("""
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
            - **Calibrated:** Weights are optimized based on historical performance data
            - **Example:** If the wind factor has a weight of 0.15 (15%), it contributes 15% to the final score
            
            ### How They Work Together
            **Final Score = Σ (Factor Score × Factor Weight)**
            
            For each player, we:
            1. Calculate 20 different factor scores (wind, umpire, park, etc.)
            2. Multiply each score by its weight
            3. Sum all weighted scores to get the final recommendation score
            
            **Example Calculation:**
            - Wind Score: +2.0, Weight: 0.15 → Contribution: +0.30
            - Umpire Score: +0.7, Weight: 0.08 → Contribution: +0.056
            - Park Score: -0.5, Weight: 0.12 → Contribution: -0.06
            - *... (17 more factors)*
            - **Final Score: Sum of all contributions → Sit/Start recommendation**
            """)
    
    # Get all weight columns
    weight_cols = [col for col in df.columns if col.endswith('_weight')]
    
    if weight_cols:
        # Allow user to select a player
        selected_player = st.selectbox("Select player to view detailed weights:", df['player_name'].tolist())
        
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
            
            # Show contribution breakdown with help icon
            col_contrib, col_help_contrib = st.columns([10, 1])
            with col_contrib:
                st.markdown("**Weighted Contribution to Final Score**")
            with col_help_contrib:
                with st.popover("ℹ️"):
                    st.markdown("""
                    ### Understanding Contributions
                    
                    This table shows how each factor contributes to the player's final score.
                    
                    **Contribution Formula:**
                    ```
                    Contribution = Factor Score × Factor Weight
                    ```
                    
                    **Column Meanings:**
                    - **Factor:** The name of the analysis factor
                    - **Weight:** How important this factor is (0-100%)
                    - **Score:** The raw factor score for this matchup
                    - **Contribution:** The weighted impact on final score
                    
                    **Interpreting the Table:**
                    - **Positive Contributions (Green):** Help the player's ranking
                    - **Negative Contributions (Red):** Hurt the player's ranking
                    - **Largest Contributions:** Main drivers of recommendation
                    
                    **Example:**
                    ```
                    Factor: Wind
                    Weight: 15.0%
                    Score: +2.0 (strong wind blowing out)
                    Contribution: +0.30 (2.0 × 0.15)
                    → Wind is a major positive factor!
                    ```
                    
                    **Strategy:**
                    - Look for multiple positive contributions = confident start
                    - One big negative can override several positives
                    - Sum of all contributions = Final Score
                    """)
            
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

with tab2:
    st.markdown("#### Top 10 Waiver Wire Prospects")
    
    # Load waiver wire data if available
    import glob
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
                selected_fa = st.selectbox("Select waiver player for details:", top_waiver['player_name'].tolist())
                
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

st.markdown("---")

# Factor Analysis with help icon containing legend
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

# Full data table with help icon
col_header, col_help = st.columns([0.95, 0.05])
with col_header:
    st.markdown('<div class="section-header-container"><h2>📋 Full Player Rankings</h2></div>', unsafe_allow_html=True)
with col_help:
    with st.popover("ℹ️"):
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
df_display = df_display[cols_order]

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

# Waiver Wire Section
st.markdown("---")

col_header, col_help = st.columns([0.95, 0.05])
with col_header:
    st.markdown('<div class="section-header-container"><h2>🔍 Waiver Wire Prospects</h2></div>', unsafe_allow_html=True)
with col_help:
    with st.popover("ℹ️"):
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

# Load waiver wire data
waiver_files = sorted(glob.glob('data/waiver_wire_*.csv'), reverse=True)

if waiver_files:
    try:
        waiver_df = pd.read_csv(waiver_files[0])
        
        if len(waiver_df) > 0:
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
        else:
            st.info("No waiver wire data available yet. Click 'Waiver Wire' in the sidebar to run analysis.")
    except Exception as e:
        st.error(f"Error loading waiver wire data: {str(e)}")
else:
    st.info("🔍 No waiver wire data found. Click the **'Waiver Wire'** button in the sidebar to analyze available free agents.")
    st.markdown("""
    **What will happen when you run waiver wire analysis:**
    1. Fetches top 100 available players from Yahoo Fantasy
    2. Applies same 20-factor analysis as your roster
    3. Ranks players by matchup quality and projected performance
    4. Shows top pickup targets with recommendations
    """)

# Factor Analysis Legend Section
st.markdown("---")
section_header("Factor Analysis Legend", "📖")

st.markdown("""
### 💡 How to Use These Scores:

**Final Score Ranges:**
- **+2.0+:** Elite matchup - Must start
- **+0.5 to +2.0:** Favorable - Strong start candidate  
- **-0.5 to +0.5:** Neutral - Consider other factors
- **-2.0 to -0.5:** Unfavorable - Bench candidate
- **Below -2.0:** Terrible matchup - Bench

**Note:** Weights are auto-tuned based on historical performance for your specific players.

---

### 📊 What Each Factor Does

#### **High Impact Factors (10-20%)**

**🎰 Vegas (15-20%)** - Betting Market Intelligence  
Analyzes professional betting lines including over/under run totals, implied team runs, and win probabilities. Oddsmakers use sophisticated models and real money is at stake, making this one of the most predictive factors. High implied runs = favorable for hitters, low = favorable for pitchers.

**📊 Statcast (10-15%)** - Advanced Performance Metrics  
Uses MLB's tracking technology to measure exit velocity, barrel rate, hard-hit percentage, expected batting average (xBA), and expected slugging (xSLG). These "quality of contact" metrics predict future success better than traditional stats. High Statcast numbers indicate a player is hitting/pitching well regardless of recent luck.

#### **Medium-High Impact (8-12%)**

**⚔️ Matchup (8-12%)** - Historical Head-to-Head Performance  
Examines how a player has performed against specific opposing pitchers/teams historically. Some batters "own" certain pitchers, some pitchers dominate certain teams. Uses career stats, recent encounters, and team-level performance to identify favorable/unfavorable matchups.

**🔥 Bullpen (8-12%)** - Opponent Bullpen Quality & Fatigue  
Evaluates the opposing team's bullpen strength, recent usage patterns, and fatigue. A tired or weak bullpen helps hitters (especially late-game at-bats) and starters who can get pulled early. Tracks ERA, recent appearances, and back-to-back game usage.

**↔️ Platoon (8-12%)** - Left/Right Handedness Advantages  
Analyzes the batter vs pitcher handedness matchup (RHB vs LHP, LHB vs RHP, etc.). Most players have significant platoon splits - righties typically hit better against lefties and vice versa. Uses career and recent splits to determine advantage.

#### **Medium Impact (5-8%)**

**🏠 Home/Away (5-8%)** - Home Field Advantage & Splits  
Compares player performance at home vs on the road. Some players thrive at home due to familiarity, crowd support, and travel fatigue when away. Examines home/road batting averages, power numbers, and pitcher effectiveness.

**🩹 Injury (5-8%)** - Player Health Status  
Tracks injury reports, day-to-day designations, recently returned from IL, and playing through minor injuries. Players returning from injury often underperform initially. Also flags if a player is "questionable" which adds uncertainty to starting them.

**🏟️ Park (5-8%)** - Ballpark Dimensions & Effects  
Analyzes ballpark factors like dimensions, wall heights, altitude, and historical run-scoring environments. Coors Field (high altitude) favors hitters dramatically, while pitcher-friendly parks like Oracle Park suppress offense. Considers park-specific effects on fly balls, ground balls, and specific hit types.

**📈 Recent Form (5-8%)** - Short-Term Performance Trends  
Examines performance over last 7, 14, and 30 days including batting average, power, strikeouts, and other key stats. Players get hot and cold - this captures current momentum. A player hitting .400 over the last week is trusted more than season averages.

**💨 Wind (5-8%)** - Wind Speed & Direction  
Checks weather forecasts for wind speed and direction. Wind blowing out to center field significantly helps hitters (ball travels farther). Wind blowing in helps pitchers. Crosswinds can affect fly ball direction. Particularly impactful for power hitters and fly ball pitchers.

#### **Lower Impact (3-5%)**

**😴 Rest (3-5%)** - Days Since Last Game  
Tracks how many days off a player has had. Rest helps both hitters and pitchers recover, but too much rest can disrupt timing. Particularly important for older players, catchers, and pitchers who benefit from normal routine.

**🌡️ Temperature (3-5%)** - Game-Time Temperature  
Warmer weather (above 75°F) helps offense as the ball travels farther in hot air. Cold weather (below 55°F) suppresses offense and favors pitchers. Particularly important for power hitters relying on home runs.

**📋 Lineup (3-5%)** - Batting Order Position  
Higher in the order (1-3) means more at-bats per game. Leadoff and #2 hitters get an extra AB compared to #8-9 spots. Also considers protection (quality of hitters before/after in lineup) and RBI opportunities.

**👨‍⚖️ Umpire (3-5%)** - Home Plate Umpire Tendencies  
Different umpires have different strike zones. Some call a tight zone (helps hitters), others call wide (helps pitchers). Tracks historical data on each umpire's tendencies for high/low strikes and consistency.

**🎯 Pitch Mix (3-5%)** - Pitcher Arsenal vs Batter Strengths  
Analyzes what pitches the pitcher throws (fastball %, breaking balls, changeup) against what the batter handles well/poorly. A slider-heavy pitcher facing a batter who struggles with sliders = favorable for pitcher.

#### **Minimal Impact (1-3%)**

**🌅 Time (1-3%)** - Day vs Night Game Splits  
Some players perform differently in day games vs night games due to lighting, visibility, body rhythm, or schedule. Tracks historical day/night splits but generally has minimal predictive value.

**💧 Humidity (1-3%)** - Moisture & Elevation Effects  
High humidity makes air heavier (slightly suppresses offense), low humidity at high altitude (like Denver) helps offense. Combined with altitude data to fine-tune park factors.

**🛡️ Defense (1-3%)** - Opponent Defensive Quality  
Evaluates the opposing team's defensive shifts, positioning strategies, and overall defensive quality. Good defense converts more balls in play to outs, hurting hitters. Poor defense lets more balls through.

**📅 Monthly (1-3%)** - Seasonal Performance Patterns  
Some players are "April players" or "September players" based on historical monthly splits. Tracks if a player historically performs better/worse in specific months, though year-to-year consistency is low.

**📊 Momentum (1-3%)** - Team Win/Loss Streaks  
Team performance and morale from recent win/loss streaks. Teams on winning streaks may have better energy and confidence. Teams on losing streaks may struggle. Generally weak predictor for individual player performance.
""")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888;'>
    <p>Fantasy Baseball AI | Powered by 20+ Factor Analysis | Auto-Fetched Yahoo Rosters</p>
    <p>All scores range -2 to +2 | Higher = Better matchup | Weights optimized per player</p>
</div>
""", unsafe_allow_html=True)
