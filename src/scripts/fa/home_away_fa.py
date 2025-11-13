#!/usr/bin/env python3
"""
Home/Away Venue Factor Analysis

Analyzes player performance differences between home and away games.
Some players perform significantly better at home due to:
- Familiarity with stadium
- Travel/routine disruption
- Fan support
- Stadium-specific factors

Key Metrics:
- Home batting average vs Away batting average
- Home/away game counts
- Venue advantage score

Output:
- Venue score (-2 to +2)
- Home vs away splits
"""

import pandas as pd
from pathlib import Path


class HomeAwayFactorAnalyzer:
    """Analyze home/away venue performance"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def calculate_venue_score(self, home_ba, away_ba, is_home_game, sample_size):
        """Calculate venue advantage score"""
        if away_ba == 0 and home_ba == 0:
            return 0.0
        
        if is_home_game:
            ba_diff = home_ba - away_ba if away_ba > 0 else 0
        else:
            ba_diff = away_ba - home_ba if home_ba > 0 else 0
        
        venue_score = ba_diff * 10
        confidence = min(sample_size / 10, 1.0)
        venue_score *= confidence
        
        return max(-2.0, min(2.0, venue_score))
    
    def analyze(self, games_df, game_logs_df, roster_df, schedule_df):
        """Analyze home/away advantages"""
        results = []
        
        for _, game in games_df.iterrows():
            game_date = game['game_date']
            
            for _, player in roster_df.iterrows():
                player_name = player['player_name']
                
                # Get player history
                player_history = game_logs_df[
                    (game_logs_df['player_name'] == player_name) &
                    (game_logs_df['game_date'] < game_date)
                ]
                
                if len(player_history) >= 5:
                    # Calculate home stats
                    home_games = player_history[player_history.get('is_home', False)]
                    home_ab = home_games['at_bats'].sum()
                    home_hits = home_games['hits'].sum()
                    home_ba = home_hits / home_ab if home_ab > 0 else 0
                    
                    # Calculate away stats
                    away_games = player_history[~player_history.get('is_home', True)]
                    away_ab = away_games['at_bats'].sum()
                    away_hits = away_games['hits'].sum()
                    away_ba = away_hits / away_ab if away_ab > 0 else 0
                    
                    # Determine if current game is home
                    is_home = True  # Simplified
                    
                    venue_score = self.calculate_venue_score(
                        home_ba, away_ba, is_home, len(player_history)
                    )
                    
                    results.append({
                        'player_name': player_name,
                        'game_date': game_date,
                        'home_games': len(home_games),
                        'home_ba': round(home_ba, 3),
                        'away_games': len(away_games),
                        'away_ba': round(away_ba, 3),
                        'venue_score': venue_score
                    })
        
        return pd.DataFrame(results)


    def analyze_roster(self, roster_df, schedule_df, players_df=None):
        """Wrapper for analyze to match interface"""
        return self.analyze(schedule_df, self._load_gamelogs(), roster_df, schedule_df)
    
    def _load_gamelogs(self):
        """Helper to load game logs if needed"""
        game_logs_file = self.data_dir / "mlb_game_logs_2024.csv"
        if game_logs_file.exists():
            import pandas as pd
            return pd.read_csv(game_logs_file)
        return pd.DataFrame()
