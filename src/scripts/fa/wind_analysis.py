#!/usr/bin/env python3
"""
Wind Analysis Factor

Analyzes wind conditions and their impact on hitting/pitching performance.
Wind direction and speed significantly affect ball flight and scoring.

Key Concepts:
- Tailwind (pitcher → home): Favorable for hitters, ball carries further
- Headwind (home → pitcher): Favorable for pitchers, ball held back
- Crosswinds: Affect ball trajectory sideways
- Wind speed amplifies these effects

Output:
- Wind component (tailwind/headwind in km/h)
- Crosswind component (km/h)
- Advantage score for hitters/pitchers
- Weather conditions
"""

import pandas as pd
import numpy as np
from pathlib import Path


class WindAnalyzer:
    """Analyze wind impact on player performance"""
    
    # Stadium orientations (pitcher mound → home plate direction in degrees)
    STADIUM_ORIENTATIONS = {
        'Chase Field': 20,
        'Truist Park': 15,
        'Oriole Park at Camden Yards': 54,
        'Fenway Park': 287,
        'Wrigley Field': 190,
        'Guaranteed Rate Field': 18,
        'Great American Ball Park': 235,
        'Progressive Field': 95,
        'Coors Field': 5,
        'Comerica Park': 55,
        'Minute Maid Park': 350,
        'Kauffman Stadium': 80,
        'Angel Stadium': 210,
        'Dodger Stadium': 330,
        'LoanDepot Park': 235,
        'American Family Field': 205,
        'Target Field': 235,
        'Citi Field': 45,
        'Yankee Stadium': 282,
        'Oakland Coliseum': 325,
        'Citizens Bank Park': 5,
        'PNC Park': 325,
        'Petco Park': 320,
        'Oracle Park': 310,
        'T-Mobile Park': 47,
        'Busch Stadium': 240,
        'Tropicana Field': 5,
        'Globe Life Field': 355,
        'Rogers Centre': 198,
        'Nationals Park': 325,
        'Sutter Health Park': 45,
    }
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def calculate_wind_advantage(self, wind_direction, wind_speed, stadium_orientation):
        """Calculate wind advantage for hitting/pitching"""
        relative_direction = (wind_direction - stadium_orientation) % 360
        if relative_direction > 180:
            relative_direction -= 360
        
        wind_component = np.cos(np.radians(relative_direction)) * wind_speed
        
        if wind_component > 10:
            advantage_score = 2.0
        elif wind_component > 5:
            advantage_score = 1.0
        elif wind_component > -5:
            advantage_score = 0.0
        elif wind_component > -10:
            advantage_score = -1.0
        else:
            advantage_score = -2.0
        
        crosswind = abs(np.sin(np.radians(relative_direction)) * wind_speed)
        
        return {
            'wind_component_kmh': wind_component,
            'crosswind_kmh': crosswind,
            'advantage_score': advantage_score,
            'relative_wind_dir': relative_direction
        }
    
    def analyze(self, games_df, weather_df, roster_df):
        """Analyze wind advantages for games"""
        results = []
        
        for _, game in games_df.iterrows():
            venue = game['venue']
            venue_weather = weather_df[weather_df['venue'] == venue]
            
            if venue_weather.empty:
                continue
            
            weather = venue_weather.iloc[0]
            orientation = self.STADIUM_ORIENTATIONS.get(venue, 0)
            
            advantage = self.calculate_wind_advantage(
                weather['wind_direction_degrees'],
                weather['wind_speed_kmh'],
                orientation
            )
            
            # Find roster players in this game
            for _, player in roster_df.iterrows():
                player_team = player.get('mlb_team', '')
                if not player_team:
                    continue
                
                # Match player to game (simplified)
                is_pitcher = player.get('position', '') in ['SP', 'RP', 'P']
                score = -advantage['advantage_score'] if is_pitcher else advantage['advantage_score']
                
                results.append({
                    'player_name': player['player_name'],
                    'game_date': game['game_date'],
                    'venue': venue,
                    'wind_speed_kmh': weather['wind_speed_kmh'],
                    'wind_direction': weather['wind_direction_cardinal'],
                    'wind_component_kmh': advantage['wind_component_kmh'],
                    'crosswind_kmh': advantage['crosswind_kmh'],
                    'wind_score': score
                })
        
        return pd.DataFrame(results)


    def analyze_roster(self, roster_df, schedule_df, weather_df=None):
        """Wrapper for analyze to match interface"""
        return self.analyze(schedule_df, weather_df, roster_df)
    
    def _load_gamelogs(self):
        """Helper to load game logs if needed"""
        game_logs_file = self.data_dir / "mlb_game_logs_2024.csv"
        if game_logs_file.exists():
            import pandas as pd
            return pd.read_csv(game_logs_file)
        return pd.DataFrame()
