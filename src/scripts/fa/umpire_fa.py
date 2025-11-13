#!/usr/bin/env python3
"""
Umpire Strike Zone Factor Analysis

Analyzes umpire strike zone tendencies and their impact on players.
Different umpires have different strike zone profiles:
- Large strike zone: Favors pitchers
- Small strike zone: Favors hitters
- Consistency: Important for both
- Pitcher/hitter bias

Key Metrics:
- Strike zone size (large/medium/small)
- Consistency rating
- Pitcher favoritism score
- Umpire advantage score

Output:
- Umpire score (-1.5 to +1.5)
- Strike zone characteristics
"""

import pandas as pd
import numpy as np
from pathlib import Path


class UmpireFactorAnalyzer:
    """Analyze umpire strike zone impacts"""
    
    # Known umpire profiles (synthetic data)
    UMPIRE_PROFILES = {
        'Angel Hernandez': {'strike_zone_size': 'small', 'consistency': 0.75, 'favor_pitcher': -0.3},
        'Joe West': {'strike_zone_size': 'large', 'consistency': 0.85, 'favor_pitcher': 0.4},
        'CB Bucknor': {'strike_zone_size': 'inconsistent', 'consistency': 0.70, 'favor_pitcher': 0.0},
        'Ron Kulpa': {'strike_zone_size': 'medium', 'consistency': 0.90, 'favor_pitcher': 0.1},
        'Pat Hoberg': {'strike_zone_size': 'medium', 'consistency': 0.95, 'favor_pitcher': 0.0},
        'Nic Lentz': {'strike_zone_size': 'large', 'consistency': 0.88, 'favor_pitcher': 0.3},
        'Lance Barksdale': {'strike_zone_size': 'small', 'consistency': 0.82, 'favor_pitcher': -0.2},
        'Marvin Hudson': {'strike_zone_size': 'medium', 'consistency': 0.87, 'favor_pitcher': 0.15},
        'Dan Bellino': {'strike_zone_size': 'large', 'consistency': 0.83, 'favor_pitcher': 0.25},
        'Tripp Gibson': {'strike_zone_size': 'small', 'consistency': 0.80, 'favor_pitcher': -0.15},
    }
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def calculate_umpire_score(self, zone_size, consistency, favor_pitcher, is_pitcher):
        """Calculate umpire advantage score"""
        zone_score = 0
        if zone_size == 'large':
            zone_score = 0.5 if is_pitcher else -0.5
        elif zone_size == 'small':
            zone_score = -0.5 if is_pitcher else 0.5
        elif zone_size == 'inconsistent':
            zone_score = -0.3
        
        favor_score = favor_pitcher if is_pitcher else -favor_pitcher
        consistency_bonus = (consistency - 0.8) * 0.5
        
        umpire_score = zone_score + favor_score + consistency_bonus
        return max(-1.5, min(1.5, umpire_score))
    
    def analyze(self, games_df, roster_df):
        """Analyze umpire strike zone advantages"""
        results = []
        
        for _, game in games_df.iterrows():
            game_date = game['game_date']
            opponent = game.get('opponent', '')
            
            # Assign umpire (deterministic based on game)
            np.random.seed(hash(str(game_date) + opponent) % 2**32)
            umpire_name = np.random.choice(list(self.UMPIRE_PROFILES.keys()))
            umpire = self.UMPIRE_PROFILES[umpire_name]
            
            for _, player in roster_df.iterrows():
                player_name = player['player_name']
                is_pitcher = player.get('position', '') in ['SP', 'RP', 'P']
                
                umpire_score = self.calculate_umpire_score(
                    umpire['strike_zone_size'],
                    umpire['consistency'],
                    umpire['favor_pitcher'],
                    is_pitcher
                )
                
                results.append({
                    'player_name': player_name,
                    'game_date': game_date,
                    'umpire_name': umpire_name,
                    'strike_zone_size': umpire['strike_zone_size'],
                    'consistency': umpire['consistency'],
                    'umpire_score': umpire_score
                })
        
        np.random.seed(None)
        return pd.DataFrame(results)


    def analyze_roster(self, roster_df, schedule_df, ):
        """Wrapper for analyze to match interface"""
        return self.analyze(schedule_df, roster_df)
    
    def _load_gamelogs(self):
        """Helper to load game logs if needed"""
        game_logs_file = self.data_dir / "mlb_game_logs_2024.csv"
        if game_logs_file.exists():
            import pandas as pd
            return pd.read_csv(game_logs_file)
        return pd.DataFrame()
