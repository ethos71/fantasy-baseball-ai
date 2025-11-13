#!/usr/bin/env python3
"""
Temperature Analysis Factor

Analyzes temperature conditions and their impact on hitting/pitching performance.
Temperature affects ball flight distance, player stamina, and overall game dynamics.

Key Concepts:
- Warm temperatures (>75°F/24°C): Ball travels further, favors hitters
- Cold temperatures (<55°F/13°C): Ball doesn't carry as well, favors pitchers
- Optimal hitting temps: 75-95°F (24-35°C)
- Extreme heat (>95°F/35°C): Player fatigue, reduced performance
- Humidity combined with temperature affects ball flight

Output:
- Temperature in Celsius and Fahrenheit
- Temperature advantage score for hitters/pitchers
- Category (Cold, Cool, Moderate, Warm, Hot)
- Performance impact assessment
"""

import pandas as pd
from pathlib import Path


class TemperatureAnalyzer:
    """Analyze temperature impact on player performance"""
    
    # Temperature thresholds in Celsius
    COLD_THRESHOLD = 13      # < 55°F
    COOL_THRESHOLD = 18      # < 65°F
    MODERATE_LOW = 21        # < 70°F
    OPTIMAL_LOW = 24         # 75°F
    OPTIMAL_HIGH = 29        # 85°F
    WARM_HIGH = 35           # 95°F
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def celsius_to_fahrenheit(self, celsius):
        """Convert Celsius to Fahrenheit"""
        return (celsius * 9/5) + 32
    
    def calculate_temperature_advantage(self, temp_celsius):
        """Calculate temperature advantage for hitting/pitching"""
        temp_f = self.celsius_to_fahrenheit(temp_celsius)
        
        # Categorize temperature
        if temp_celsius < self.COLD_THRESHOLD:
            category = "Cold"
            advantage_score = -2.0  # Favors pitchers
            impact = "Significant advantage for pitchers - ball doesn't carry"
        elif temp_celsius < self.COOL_THRESHOLD:
            category = "Cool"
            advantage_score = -1.0  # Slight pitcher advantage
            impact = "Slight advantage for pitchers"
        elif temp_celsius < self.MODERATE_LOW:
            category = "Moderate"
            advantage_score = -0.5
            impact = "Neutral conditions, slight pitcher advantage"
        elif temp_celsius < self.OPTIMAL_LOW:
            category = "Comfortable"
            advantage_score = 0.0
            impact = "Neutral conditions"
        elif temp_celsius < self.OPTIMAL_HIGH:
            category = "Warm"
            advantage_score = 1.5  # Good hitter advantage
            impact = "Favorable for hitters - ball carries well"
        elif temp_celsius < self.WARM_HIGH:
            category = "Hot"
            advantage_score = 2.0  # Strong hitter advantage
            impact = "Very favorable for hitters - maximum ball flight"
        else:
            category = "Very Hot"
            advantage_score = 1.0  # Reduced due to fatigue
            impact = "Favorable for hitters but extreme heat affects stamina"
        
        return {
            'temp_celsius': temp_celsius,
            'temp_fahrenheit': temp_f,
            'category': category,
            'advantage_score': advantage_score,
            'impact': impact
        }
    
    def analyze(self, games_df, weather_df, roster_df):
        """Analyze temperature advantages for games"""
        results = []
        
        for _, game in games_df.iterrows():
            venue = game['venue']
            venue_weather = weather_df[weather_df['venue'] == venue]
            
            if venue_weather.empty:
                continue
            
            weather = venue_weather.iloc[0]
            temp_celsius = weather.get('temperature_celsius', weather.get('temperature', 20))
            
            temp_analysis = self.calculate_temperature_advantage(temp_celsius)
            
            # Find roster players in this game
            for _, player in roster_df.iterrows():
                player_team = player.get('mlb_team', '')
                if not player_team:
                    continue
                
                # Pitchers benefit from opposite conditions as hitters
                is_pitcher = player.get('position', '') in ['SP', 'RP', 'P']
                score = -temp_analysis['advantage_score'] if is_pitcher else temp_analysis['advantage_score']
                
                results.append({
                    'player_name': player['player_name'],
                    'game_date': game['game_date'],
                    'venue': venue,
                    'temp_celsius': temp_analysis['temp_celsius'],
                    'temp_fahrenheit': round(temp_analysis['temp_fahrenheit'], 1),
                    'temp_category': temp_analysis['category'],
                    'temp_score': score,
                    'impact': temp_analysis['impact']
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
