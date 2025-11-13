#!/usr/bin/env python3
"""
Injury/Recovery Tracking Factor Analysis

Tracks player performance after injury recovery.
Players returning from injury may show:
- Reduced performance initially
- Gradual improvement over time
- Full recovery after adjustment period

Key Metrics:
- Pre-injury performance
- Post-injury performance
- Days since return
- Games since return
- Recovery status

Output:
- Injury score (-2 to +2)
- Recovery status (recovering, healthy, etc.)
"""

import pandas as pd
from pathlib import Path


class InjuryFactorAnalyzer:
    """Analyze injury recovery performance impacts"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def calculate_injury_score(self, pre_ba, post_ba, days_since_return, games_since):
        """Calculate injury recovery score"""
        if pre_ba == 0 and post_ba == 0:
            return 0.0
        
        ba_diff = post_ba - pre_ba
        injury_score = ba_diff * 10
        
        # Penalty for recent return
        recency_factor = max(0.3, 1.0 - (days_since_return / 30.0))
        injury_score *= recency_factor
        
        # Confidence based on games back
        confidence = min(games_since / 5, 1.0)
        injury_score *= confidence
        
        return max(-2.0, min(2.0, injury_score))
    
    def analyze(self, games_df, game_logs_df, roster_df):
        """Analyze injury recovery impacts"""
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
                
                if len(player_history) >= 10:
                    # Calculate gaps (14+ days = likely injury)
                    player_history['days_gap'] = (
                        player_history['game_date'] - player_history['game_date'].shift(1)
                    ).dt.days.fillna(0)
                    
                    injury_gaps = player_history[player_history['days_gap'] >= 14]
                    
                    if len(injury_gaps) > 0:
                        # Most recent injury
                        return_date = injury_gaps['game_date'].iloc[-1]
                        days_since = (pd.to_datetime(game_date) - return_date).days
                        
                        if 0 <= days_since <= 30:
                            # In recovery period
                            pre_injury = player_history[player_history['game_date'] < return_date].tail(10)
                            post_injury = player_history[player_history['game_date'] >= return_date]
                            
                            pre_ba = pre_injury['hits'].sum() / pre_injury['at_bats'].sum() if len(pre_injury) > 0 else 0
                            post_ba = post_injury['hits'].sum() / post_injury['at_bats'].sum() if len(post_injury) > 0 else 0
                            
                            injury_score = self.calculate_injury_score(
                                pre_ba, post_ba, days_since, len(post_injury)
                            )
                            
                            results.append({
                                'player_name': player_name,
                                'game_date': game_date,
                                'days_since_return': days_since,
                                'games_since_return': len(post_injury),
                                'pre_injury_ba': round(pre_ba, 3),
                                'post_injury_ba': round(post_ba, 3),
                                'injury_score': injury_score
                            })
        
        return pd.DataFrame(results)


    def analyze_roster(self, roster_df, schedule_df, players_df=None):
        """Wrapper for analyze to match interface"""
        return self.analyze(schedule_df, self._load_gamelogs(), roster_df)
    
    def _load_gamelogs(self):
        """Helper to load game logs if needed"""
        game_logs_file = self.data_dir / "mlb_game_logs_2024.csv"
        if game_logs_file.exists():
            import pandas as pd
            return pd.read_csv(game_logs_file)
        return pd.DataFrame()
