#!/usr/bin/env python3
"""
Park Factors Analysis

Analyzes how stadium characteristics affect performance.
Park factors measure scoring relative to league average.

Key Concepts:
- Park Factor > 1.0: Hitter-friendly
- Park Factor = 1.0: Neutral
- Park Factor < 1.0: Pitcher-friendly

Factors affected by:
- Dimensions (wall distance/height)
- Altitude (e.g., Coors Field)
- Weather patterns
- Playing surface

Output:
- Park score (-2 to +2)
- Runs/HR/Hits factors
- Stadium characteristics
"""

import pandas as pd
from pathlib import Path


class ParkFactorsAnalyzer:
    """Analyze park factors impact"""
    
    # Park factors (runs, hr, hits)
    PARK_FACTORS = {
        'Coors Field': (1.30, 1.35, 1.25),
        'Great American Ball Park': (1.15, 1.25, 1.12),
        'Globe Life Field': (1.12, 1.18, 1.10),
        'Fenway Park': (1.10, 1.15, 1.08),
        'Yankee Stadium': (1.08, 1.20, 1.05),
        'Citizens Bank Park': (1.08, 1.12, 1.06),
        'Oracle Park': (0.88, 0.75, 0.89),
        'Petco Park': (0.92, 0.80, 0.93),
        'T-Mobile Park': (0.91, 0.82, 0.92),
        'Tropicana Field': (0.90, 0.85, 0.91),
        # Add more as needed
    }
    
    TEAM_STADIUMS = {
        'Arizona Diamondbacks': 'Chase Field',
        'Atlanta Braves': 'Truist Park',
        'Baltimore Orioles': 'Oriole Park at Camden Yards',
        'Boston Red Sox': 'Fenway Park',
        'Colorado Rockies': 'Coors Field',
        # Add more as needed
    }
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def get_park_factors(self, stadium):
        """Get park factors for stadium"""
        return self.PARK_FACTORS.get(stadium, (1.0, 1.0, 1.0))
    
    def calculate_park_score(self, runs_factor, hr_factor, hits_factor, is_pitcher):
        """Calculate park advantage score"""
        combined = (runs_factor * 0.40) + (hr_factor * 0.35) + (hits_factor * 0.25)
        
        if is_pitcher:
            combined = 2.0 - combined
        
        score = (combined - 1.0) / 0.3
        return max(-2.0, min(2.0, score))
    
    def analyze(self, games_df, roster_df):
        """Analyze park factors"""
        results = []
        
        for _, game in games_df.iterrows():
            game_date = game['game_date']
            home_team = game.get('home_team', '')
            stadium = self.TEAM_STADIUMS.get(home_team, 'Unknown')
            
            runs_f, hr_f, hits_f = self.get_park_factors(stadium)
            
            for _, player in roster_df.iterrows():
                player_name = player['player_name']
                is_pitcher = player.get('position', '') in ['SP', 'RP', 'P']
                
                park_score = self.calculate_park_score(runs_f, hr_f, hits_f, is_pitcher)
                
                results.append({
                    'player_name': player_name,
                    'game_date': game_date,
                    'stadium': stadium,
                    'runs_factor': runs_f,
                    'hr_factor': hr_f,
                    'hits_factor': hits_f,
                    'score': park_score
                })
        
        return pd.DataFrame(results)
    
    def analyze_roster(self, roster_df, schedule_df, teams_df):
        """Wrapper for analyze to match interface"""
        return self.analyze(schedule_df, roster_df)
