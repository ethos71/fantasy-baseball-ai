#!/usr/bin/env python3
"""
MLB Game Log Scraper

Fetches game-by-game performance data for players to enable recent form analysis.
This provides the granular data needed to calculate hot/cold streaks.

API Endpoint: https://statsapi.mlb.com/api/v1/people/{playerId}/stats
Parameters: stats=gameLog&season=2024&group=hitting

Output: Individual game logs with hitting stats per game
"""

import requests
import pandas as pd
from pathlib import Path
from datetime import datetime
import time


def fetch_player_game_log(player_id, season=2024):
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
            })
        
        return games
        
    except Exception as e:
        print(f"  Error fetching game log for player {player_id}: {e}")
        return []


def fetch_all_player_gamelogs(players_df, season=2024, output_dir=None):
    """Fetch game logs for all players"""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent.parent / "data"
    
    all_games = []
    total_players = len(players_df)
    
    print(f"\nFetching game logs for {total_players} players (season {season})...")
    print("This may take several minutes...\n")
    
    for idx, (_, player) in enumerate(players_df.iterrows(), 1):
        player_id = player.get('player_id')
        player_name = player.get('player_name', 'Unknown')
        
        if pd.isna(player_id):
            continue
        
        print(f"[{idx}/{total_players}] {player_name} (ID: {player_id})...", end=' ')
        
        games = fetch_player_game_log(int(player_id), season)
        
        if games:
            # Add player name to each game
            for game in games:
                game['player_name'] = player_name
            all_games.extend(games)
            print(f"{len(games)} games")
        else:
            print("No data")
        
        # Rate limiting
        if idx % 10 == 0:
            time.sleep(1)  # Be nice to MLB API
    
    # Convert to DataFrame
    if all_games:
        df = pd.DataFrame(all_games)
        
        # Save to CSV
        output_file = output_dir / f"mlb_game_logs_{season}.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n✓ Fetched {len(all_games)} total game logs")
        print(f"✓ Saved to: {output_file.name}")
        
        return df
    else:
        print("\n❌ No game log data fetched")
        return pd.DataFrame()


def main():
    """Main execution"""
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data"
    
    print("="*80)
    print("MLB Game Log Scraper".center(80))
    print("="*80)
    
    # Load player database
    try:
        players_2024 = pd.read_csv(data_dir / "mlb_all_players_2024.csv")
        print(f"\n✓ Loaded {len(players_2024)} players from 2024 roster")
    except FileNotFoundError:
        print("\n❌ Player database not found!")
        print("   Run: python src/scripts/scrape/mlb_scrape.py first")
        return
    
    # Fetch 2024 game logs
    fetch_all_player_gamelogs(players_2024, season=2024, output_dir=data_dir)
    
    print("\n" + "="*80)
    print("Game log scraping complete!")
    print("="*80)


if __name__ == "__main__":
    main()
