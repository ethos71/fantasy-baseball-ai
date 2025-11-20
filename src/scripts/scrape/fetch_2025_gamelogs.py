#!/usr/bin/env python3
"""
Fetch 2025 Game Logs for Roster Players

This script fetches game-by-game stats for just the players on your roster
to generate the mlb_game_logs_2025.csv file needed for better scoring.
"""

import requests
import pandas as pd
from pathlib import Path
import time

def fetch_player_game_log(player_id, player_name, season=2025):
    """Fetch game log for a specific player"""
    url = f"https://statsapi.mlb.com/api/v1/people/{player_id}/stats"
    params = {
        'stats': 'gameLog',
        'season': season,
        'group': 'hitting'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'stats' not in data or len(data['stats']) == 0:
            return []
        
        splits = data['stats'][0].get('splits', [])
        
        games = []
        for split in splits:
            game = split.get('game', {})
            stat = split.get('stat', {})
            
            games.append({
                'player_id': player_id,
                'game_date': split.get('date'),
                'game_pk': game.get('gamePk'),
                'is_home': split.get('isHome', False),
                'is_win': split.get('isWin', False),
                'opponent': split.get('opponent', {}).get('name', ''),
                
                # Hitting stats
                'AB': stat.get('atBats', 0),
                'H': stat.get('hits', 0),
                'R': stat.get('runs', 0),
                'RBI': stat.get('rbi', 0),
                'HR': stat.get('homeRuns', 0),
                '2B': stat.get('doubles', 0),
                '3B': stat.get('triples', 0),
                'BB': stat.get('baseOnBalls', 0),
                'SO': stat.get('strikeOuts', 0),
                'SB': stat.get('stolenBases', 0),
                'AVG': stat.get('avg', '.000'),
                'OBP': stat.get('obp', '.000'),
                'SLG': stat.get('slg', '.000'),
                'OPS': stat.get('ops', '.000'),
                'player_name': player_name
            })
        
        return games
        
    except Exception as e:
        print(f"  Error: {e}")
        return []


def main():
    data_dir = Path('data')
    
    print("="*80)
    print("Fetching 2025 Game Logs for Roster Players".center(80))
    print("="*80 + "\n")
    
    # Load roster
    roster_files = sorted(data_dir.glob("yahoo_fantasy_rosters_*.csv"), 
                         key=lambda x: x.stat().st_mtime, reverse=True)
    if not roster_files:
        print("❌ No roster file found!")
        return
    
    roster = pd.read_csv(roster_files[0])
    print(f"✓ Loaded roster: {len(roster)} players\n")
    
    # Load 2025 players to get player_ids
    players_2025 = pd.read_csv(data_dir / 'mlb_all_players_2025.csv')
    
    # Match roster players to player IDs
    all_games = []
    fetched_count = 0
    
    for idx, row in roster.iterrows():
        player_name = row['player_name']
        
        # Find player in 2025 players database
        match = players_2025[players_2025['player_name'] == player_name]
        
        if len(match) == 0:
            print(f"[{idx+1:2d}/{len(roster)}] {player_name:<30} NOT FOUND in 2025 database")
            continue
        
        player_id = match.iloc[0]['player_id']
        
        print(f"[{idx+1:2d}/{len(roster)}] {player_name:<30} (ID: {player_id})...", end=' ')
        
        games = fetch_player_game_log(player_id, player_name, season=2025)
        
        if games:
            all_games.extend(games)
            fetched_count += 1
            print(f"✓ {len(games)} games")
        else:
            print("No data")
        
        # Rate limiting - be nice to MLB API
        if (idx + 1) % 10 == 0:
            time.sleep(1)
    
    # Save to CSV
    if all_games:
        df = pd.DataFrame(all_games)
        output_file = data_dir / "mlb_game_logs_2025.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n{'='*80}")
        print(f"✅ SUCCESS!")
        print(f"   Fetched data for {fetched_count}/{len(roster)} players")
        print(f"   Total game logs: {len(all_games)}")
        print(f"   Saved to: {output_file.name}")
        print(f"{'='*80}\n")
    else:
        print("\n❌ No game log data fetched")


if __name__ == "__main__":
    main()
