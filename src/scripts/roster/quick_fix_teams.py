#!/usr/bin/env python3
"""
Quick fix to add team mapping to roster and regenerate recommendations
"""
import pandas as pd
from pathlib import Path

data_dir = Path("data")

# Team abbreviation to full name mapping
TEAM_MAP = {
    'AZ': 'Arizona Diamondbacks',
    'ATL': 'Atlanta Braves',
    'ATH': 'Oakland Athletics',
    'BAL': 'Baltimore Orioles',
    'BOS': 'Boston Red Sox',
    'CHC': 'Chicago Cubs',
    'CHW': 'Chicago White Sox',
    'CIN': 'Cincinnati Reds',
    'CLE': 'Cleveland Guardians',
    'COL': 'Colorado Rockies',
    'DET': 'Detroit Tigers',
    'HOU': 'Houston Astros',
    'KC': 'Kansas City Royals',
    'LAA': 'Los Angeles Angels',
    'LAD': 'Los Angeles Dodgers',
    'MIA': 'Miami Marlins',
    'MIL': 'Milwaukee Brewers',
    'MIN': 'Minnesota Twins',
    'NYM': 'New York Mets',
    'NYY': 'New York Yankees',
    'OAK': 'Oakland Athletics',
    'PHI': 'Philadelphia Phillies',
    'PIT': 'Pittsburgh Pirates',
    'SD': 'San Diego Padres',
    'SEA': 'Seattle Mariners',
    'SF': 'San Francisco Giants',
    'STL': 'St. Louis Cardinals',
    'TB': 'Tampa Bay Rays',
    'TEX': 'Texas Rangers',
    'TOR': 'Toronto Blue Jays',
    'WSH': 'Washington Nationals',
}

# Load latest roster
roster_files = sorted(data_dir.glob('yahoo_fantasy_rosters_*.csv'), key=lambda x: x.stat().st_mtime, reverse=True)
if not roster_files:
    print("No roster found!")
    exit(1)

roster = pd.read_csv(roster_files[0])
print(f"Loaded roster: {roster_files[0].name}")
print(f"Players: {len(roster)}")

# Add team column
roster['team'] = roster['mlb_team'].map(TEAM_MAP)

# Check for unmapped teams
unmapped = roster[roster['team'].isna()]
if len(unmapped) > 0:
    print(f"\nWarning: {len(unmapped)} players have unmapped teams:")
    for _, player in unmapped.iterrows():
        print(f"  {player['player_name']}: {player['mlb_team']}")

# Save with team column
output_file = data_dir / f"roster_with_teams_{roster_files[0].stem.split('_')[-2]}_{roster_files[0].stem.split('_')[-1]}.csv"
roster.to_csv(output_file, index=False)

print(f"\nSaved to: {output_file.name}")
print(f"Sample teams: {roster['team'].dropna().unique()[:5]}")
