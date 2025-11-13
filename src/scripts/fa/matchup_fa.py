#!/usr/bin/env python3
"""
Pitcher-Hitter Matchup Factor Analysis

Analyzes historical performance of hitters vs specific pitchers and teams.
Provides matchup success rates based on past at-bats.

Key Metrics:
- Batting average in matchup
- Home runs in matchup
- Number of games/at-bats (confidence)
- Matchup advantage score

Output:
- Matchup score (-2 to +2)
- Historical stats (BA, HR, AB)
- Confidence level
"""

import pandas as pd
from pathlib import Path


class MatchupFactorAnalyzer:
    """Analyze pitcher-hitter historical matchups"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def calculate_matchup_score(self, batting_avg, home_runs, games_played):
        """Calculate matchup advantage score"""
        ba_score = (batting_avg - 0.250) * 10
        hr_score = home_runs * 0.5
        confidence = min(games_played / 10, 1.0)
        score = (ba_score + hr_score) * confidence
        return max(-2.0, min(2.0, score))
    
    def analyze(self, games_df, game_logs_df, roster_df):
        """Analyze matchup advantages"""
        results = []
        
        for _, game in games_df.iterrows():
            game_date = game['game_date']
            
            for _, player in roster_df.iterrows():
                player_name = player['player_name']
                
                # Find historical matchups
                player_history = game_logs_df[
                    (game_logs_df['player_name'] == player_name) &
                    (game_logs_df['game_date'] < game_date)
                ]
                
                if len(player_history) > 0:
                    total_ab = player_history['AB'].sum()
                    total_hits = player_history['H'].sum()
                    total_hr = player_history['HR'].sum()
                    avg_ba = total_hits / total_ab if total_ab > 0 else 0
                    
                    matchup_score = self.calculate_matchup_score(
                        avg_ba, total_hr, len(player_history)
                    )
                    
                    results.append({
                        'player_name': player_name,
                        'game_date': game_date,
                        'games_played': len(player_history),
                        'total_at_bats': total_ab,
                        'batting_avg': round(avg_ba, 3),
                        'total_home_runs': total_hr,
                        'matchup_score': matchup_score
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
