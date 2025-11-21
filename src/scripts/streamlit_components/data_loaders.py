"""Data loading utilities for Streamlit dashboard"""
import streamlit as st
import pandas as pd
import glob

@st.cache_data
def load_roster_file():
    """Load the most recent roster file"""
    roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
    if roster_files:
        return pd.read_csv(roster_files[0])
    return None

@st.cache_data
def load_recommendations(team_filter=None):
    """Load sit/start recommendations"""
    rec_files = sorted(glob.glob('data/sitstart_recommendations_*.csv'), reverse=True)
    if not rec_files:
        return None
    
    df = pd.read_csv(rec_files[0])
    
    # Filter by team if needed
    if team_filter:
        try:
            roster = load_roster_file()
            if roster is not None and 'fantasy_team' in roster.columns:
                team_players = roster[roster['fantasy_team'] == team_filter]['player_name'].tolist()
                df = df[df['player_name'].isin(team_players)]
        except:
            pass
    
    return df

@st.cache_data
def load_waiver_wire():
    """Load waiver wire recommendations"""
    waiver_files = sorted(glob.glob('data/waiver_wire_*.csv'), reverse=True)
    if waiver_files:
        return pd.read_csv(waiver_files[0])
    return None

def get_available_teams():
    """Get list of available fantasy teams"""
    roster = load_roster_file()
    if roster is not None and 'fantasy_team' in roster.columns:
        return sorted(roster['fantasy_team'].unique().tolist())
    return []


@st.cache_data
def load_recommendations_data(filepath, team_filter):
    """
    Load and process recommendations data with player types and positions
    
    Args:
        filepath: Path to recommendations CSV file
        team_filter: Fantasy team name to filter by (optional)
        
    Returns:
        DataFrame with processed data including player_type, position, etc.
    """
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
        # First check Yahoo position for SP/RP designation
        df['yahoo_pos'] = df['player_name'].map(yahoo_positions).fillna('')
        
        # Classify as Pitcher if either MLB position_type is Pitcher OR Yahoo position contains SP/RP/P
        df['player_type'] = df.apply(
            lambda row: 'Pitcher' if (
                row['position_type'] == 'Pitcher' or 
                any(p in str(row['yahoo_pos']) for p in ['SP', 'RP', ',P'])
            ) else 'Hitter',
            axis=1
        )
        
        # Fill NaN with Hitter (assume hitter if unknown)
        df['player_type'] = df['player_type'].fillna('Hitter')
        
        # Clean up position column - use Yahoo position as fallback if MLB position is missing
        df['position'] = df.apply(
            lambda row: row['yahoo_pos'] if (pd.isna(row['position']) or row['position'] == '') else row['position'],
            axis=1
        )
        df['position'] = df['position'].fillna('Unknown')
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


def abbreviate_position(pos, player_name='', yahoo_position=''):
    """Abbreviate position name, using Yahoo position for SP/RP distinction"""
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


from datetime import timedelta


def calculate_period_stats(game_logs, roster, target_date, days):
    """Calculate statistics for a given period"""
    from datetime import timedelta
    import pandas as pd
    
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
    
    # Load Yahoo positions
    try:
        roster_files = sorted(glob.glob('data/yahoo_fantasy_rosters_*.csv'), reverse=True)
        yahoo_positions = {}
        if roster_files:
            yahoo_roster = pd.read_csv(roster_files[0])
            yahoo_positions = dict(zip(yahoo_roster['player_name'], yahoo_roster['position']))
    except:
        yahoo_positions = {}
    
    stats_list = []
    for idx, player in roster.iterrows():
        player_name = player['player_name']
        player_logs = period_logs[period_logs['player_name'] == player_name]
        
        # Get position - prefer Yahoo position data for SP/RP
        yahoo_pos = player.get('position', '')
        if not yahoo_pos:
            yahoo_pos = yahoo_positions.get(player_name, '')
        mlb_position = position_map.get(player_name, 'Unknown')
        position_abbrev = abbreviate_position(mlb_position, player_name, yahoo_pos)
        
        if len(player_logs) > 0:
            # Determine if player is on bench (simple heuristic: last ~10 players in roster order are bench)
            total_roster_size = len(roster)
            is_bench = idx >= (total_roster_size * 0.6)  # Last 40% considered bench
            
            stats = {
                'roster_order': idx,
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

