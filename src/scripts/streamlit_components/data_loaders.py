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
