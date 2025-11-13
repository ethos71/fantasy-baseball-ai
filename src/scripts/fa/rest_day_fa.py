#!/usr/bin/env python3
"""
Rest Day Impact Factor Analysis

Analyzes how days of rest affect player performance.
Players may perform differently when:
- Well-rested (2+ days off)
- Playing back-to-back games
- Long stretches without rest

Key Metrics:
- Rested performance (2+ days off)
- Back-to-back performance (0-1 days)
- Days since last game
- Rest advantage score

Output:
- Rest score (-2 to +2)
- Rested vs back-to-back splits
"""

import pandas as pd
from pathlib import Path


class RestDayFactorAnalyzer:
    """Analyze rest day performance impacts"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def calculate_rest_score(self, rested_ba, b2b_ba, is_rested, sample_size):
        """Calculate rest advantage score"""
        if rested_ba == 0 and b2b_ba == 0:
            return 0.0
        
        ba_diff = rested_ba - b2b_ba
        
        if is_rested:
            rest_score = ba_diff * 10
        else:
            rest_score = -ba_diff * 10
        
        confidence = min(sample_size / 10, 1.0)
        rest_score *= confidence
        
        return max(-2.0, min(2.0, rest_score))
    
    def analyze(self, games_df, game_logs_df, roster_df):
        """Analyze rest day advantages"""
        results = []
        
        for _, game in games_df.iterrows():
            game_date = game['game_date']
            
            for _, player in roster_df.iterrows():
                player_name = player['player_name']
                
                # Get player history
                player_history = game_logs_df[
                    (game_logs_df['player_name'] == player_name) &
                    (game_logs_df['game_date'] < game_date)
                ].sort_values('game_date')
                
                if len(player_history) >= 5:
                    # Calculate days between games
                    player_history['days_rest'] = (
                        player_history['game_date'] - player_history['game_date'].shift(1)
                    ).dt.days.fillna(0)
                    
                    # Rested games (2+ days)
                    rested = player_history[player_history['days_rest'] >= 2]
                    rested_ab = rested['at_bats'].sum()
                    rested_hits = rested['hits'].sum()
                    rested_ba = rested_hits / rested_ab if rested_ab > 0 else 0
                    
                    # Back-to-back games (0-1 days)
                    b2b = player_history[player_history['days_rest'] <= 1]
                    b2b_ab = b2b['at_bats'].sum()
                    b2b_hits = b2b['hits'].sum()
                    b2b_ba = b2b_hits / b2b_ab if b2b_ab > 0 else 0
                    
                    # Days since last game
                    last_game = player_history['game_date'].max()
                    days_since = (pd.to_datetime(game_date) - last_game).days
                    is_rested = days_since >= 2
                    
                    rest_score = self.calculate_rest_score(
                        rested_ba, b2b_ba, is_rested, len(player_history)
                    )
                    
                    results.append({
                        'player_name': player_name,
                        'game_date': game_date,
                        'days_since_last_game': days_since,
                        'rested_ba': round(rested_ba, 3),
                        'back_to_back_ba': round(b2b_ba, 3),
                        'rest_score': rest_score
                    })
        
        return pd.DataFrame(results)


    def analyze_roster(self, roster_df, schedule_df, ):
        """Wrapper for analyze to match interface"""
        return self.analyze(schedule_df, self._load_gamelogs(), roster_df)
    
    def _load_gamelogs(self):
        """Helper to load game logs if needed"""
        game_logs_file = self.data_dir / "mlb_game_logs_2024.csv"
        if game_logs_file.exists():
            import pandas as pd
            return pd.read_csv(game_logs_file)
        return pd.DataFrame()
