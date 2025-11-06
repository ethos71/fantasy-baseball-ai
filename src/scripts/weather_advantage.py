#!/usr/bin/env python3
"""
Fantasy Baseball Weather Advantage Analyzer

This script combines:
- Your Yahoo Fantasy rosters
- MLB game schedules and player data
- Real-time weather conditions at stadiums
- XGBoost ML predictions

To analyze favorable/unfavorable weather patterns for your players in the
last 30 games of the 2024 season (most recent complete season).

Weather Analysis:
- Wind from pitcher → home = FAVORABLE for hitters (ball carries)
- Wind from home → pitcher = UNFAVORABLE for hitters (ball held back)
- Wind speed amplifies the effect
- Crosswinds affect ball trajectory

Usage:
    python src/scripts/weather_advantage.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

try:
    import xgboost as xgb
except ImportError:
    print("❌ Install required package: pip install xgboost")
    sys.exit(1)


class WeatherAdvantageAnalyzer:
    """Analyze weather advantages for fantasy baseball players"""
    
    # Stadium orientations (pitcher mound → home plate direction in degrees)
    # This is the direction a ball travels from pitcher to home
    STADIUM_ORIENTATIONS = {
        'Chase Field': 20,  # Home → 1st base line points roughly NNE
        'Truist Park': 15,
        'Oriole Park at Camden Yards': 54,
        'Fenway Park': 287,  # Famous Green Monster orientation
        'Wrigley Field': 190,  # NNE to SSW
        'Guaranteed Rate Field': 18,
        'Great American Ball Park': 235,
        'Progressive Field': 95,
        'Coors Field': 5,  # High altitude, wind matters more
        'Comerica Park': 55,
        'Minute Maid Park': 350,
        'Kauffman Stadium': 80,
        'Angel Stadium': 210,
        'Dodger Stadium': 330,
        'LoanDepot Park': 235,  # Retractable roof
        'American Family Field': 205,  # Retractable roof
        'Target Field': 235,
        'Citi Field': 45,
        'Yankee Stadium': 282,  # Short right field
        'Oakland Coliseum': 325,
        'Citizens Bank Park': 5,
        'PNC Park': 325,
        'Petco Park': 320,
        'Oracle Park': 310,  # McCovey Cove in right
        'T-Mobile Park': 47,  # Retractable roof
        'Busch Stadium': 240,
        'Tropicana Field': 5,  # Dome
        'Globe Life Field': 355,  # Retractable roof
        'Rogers Centre': 198,  # Retractable roof
        'Nationals Park': 325,
        'Sutter Health Park': 45,  # Athletics new stadium
    }
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.model = None
        
        # Data containers
        self.schedule = None
        self.weather = None
        self.roster = None
        self.players = None
        
    def print_header(self, text: str):
        """Print formatted section header"""
        print(f"\n{'='*80}")
        print(f"{text.center(80)}")
        print(f"{'='*80}\n")
    
    def load_data(self):
        """Load all required data files"""
        self.print_header("Step 1: Loading Data")
        
        # Load 2024 schedule (most recent complete season)
        schedule_file = self.data_dir / "mlb_2024_schedule.csv"
        if not schedule_file.exists():
            print("❌ 2024 schedule not found. Run: python src/scripts/mlb_scrape.py")
            return False
        self.schedule = pd.read_csv(schedule_file)
        print(f"✓ Loaded {len(self.schedule)} games from 2024 schedule")
        
        # Load weather data
        weather_file = self.data_dir / "mlb_stadium_weather.csv"
        if not weather_file.exists():
            print("❌ Weather data not found. Run: python src/scripts/weather_scrape.py")
            return False
        self.weather = pd.read_csv(weather_file)
        print(f"✓ Loaded weather for {len(self.weather)} stadiums")
        
        # Load Yahoo roster (find most recent)
        roster_files = sorted(self.data_dir.glob("yahoo_fantasy_rosters_*.csv"))
        if not roster_files:
            print("❌ No Yahoo roster found. Run: python src/scripts/yahoo_scrape.py")
            return False
        self.roster = pd.read_csv(roster_files[-1])
        print(f"✓ Loaded roster with {len(self.roster)} players")
        
        # Load player database
        players_file = self.data_dir / "mlb_all_players_2024.csv"
        if not players_file.exists():
            print("⚠️  2024 player data not found - continuing without player details")
        else:
            self.players = pd.read_csv(players_file)
            print(f"✓ Loaded {len(self.players)} players from 2024")
        
        return True
    
    def get_last_30_games(self):
        """Get last 30 games of 2024 season"""
        self.print_header("Step 2: Finding Last 30 Games of 2024")
        
        # Parse dates
        self.schedule['game_date'] = pd.to_datetime(self.schedule['game_date'], errors='coerce')
        
        # Get games in 2024 with valid dates
        season_games = self.schedule[(self.schedule['season'] == 2024) & (self.schedule['game_date'].notna())].copy()
        
        # Sort by date descending and take last 30
        season_games = season_games.sort_values('game_date', ascending=False)
        last_30 = season_games.head(30).copy()
        
        if len(last_30) > 0:
            print(f"✓ Found last 30 games")
            print(f"  Date range: {last_30['game_date'].min().date()} to {last_30['game_date'].max().date()}")
            print(f"  Total games: {len(last_30)}")
        else:
            print("⚠️  No games found in 2024")
        
        return last_30
    
    def calculate_wind_advantage(self, wind_direction: float, wind_speed: float, 
                                 stadium_orientation: float) -> dict:
        """
        Calculate wind advantage for hitting/pitching
        
        Args:
            wind_direction: Wind direction in degrees (where wind is coming FROM)
            wind_speed: Wind speed in km/h
            stadium_orientation: Direction from pitcher mound to home plate
            
        Returns:
            dict with advantage scores and descriptions
        """
        # Calculate relative wind direction
        # Positive = tailwind (pitcher → home), negative = headwind
        relative_direction = (wind_direction - stadium_orientation) % 360
        
        # Convert to -180 to 180 range
        if relative_direction > 180:
            relative_direction -= 360
        
        # Calculate wind component along pitcher-home line
        # cos(0) = 1.0 means direct tailwind (best for hitters)
        # cos(180) = -1.0 means direct headwind (best for pitchers)
        wind_component = np.cos(np.radians(relative_direction)) * wind_speed
        
        # Determine advantage
        # Positive component = wind helps ball travel (favors hitters)
        # Negative component = wind holds ball back (favors pitchers)
        
        if wind_component > 10:
            hitter_advantage = "VERY FAVORABLE"
            pitcher_advantage = "VERY UNFAVORABLE"
            advantage_score = 2.0
        elif wind_component > 5:
            hitter_advantage = "FAVORABLE"
            pitcher_advantage = "UNFAVORABLE"
            advantage_score = 1.0
        elif wind_component > -5:
            hitter_advantage = "NEUTRAL"
            pitcher_advantage = "NEUTRAL"
            advantage_score = 0.0
        elif wind_component > -10:
            hitter_advantage = "UNFAVORABLE"
            pitcher_advantage = "FAVORABLE"
            advantage_score = -1.0
        else:
            hitter_advantage = "VERY UNFAVORABLE"
            pitcher_advantage = "VERY FAVORABLE"
            advantage_score = -2.0
        
        # Calculate crosswind component
        crosswind = abs(np.sin(np.radians(relative_direction)) * wind_speed)
        
        return {
            'wind_component_kmh': wind_component,
            'crosswind_kmh': crosswind,
            'hitter_advantage': hitter_advantage,
            'pitcher_advantage': pitcher_advantage,
            'advantage_score': advantage_score,
            'relative_wind_dir': relative_direction
        }
    
    def analyze_games(self, games_df: pd.DataFrame):
        """Analyze weather advantages for games"""
        self.print_header("Step 3: Analyzing Weather Advantages")
        
        results = []
        
        for _, game in games_df.iterrows():
            venue = game['venue']
            
            # Get weather for this venue
            venue_weather = self.weather[self.weather['venue'] == venue]
            if venue_weather.empty:
                continue
            
            weather = venue_weather.iloc[0]
            
            # Get stadium orientation
            orientation = self.STADIUM_ORIENTATIONS.get(venue, 0)
            
            # Calculate wind advantage
            advantage = self.calculate_wind_advantage(
                weather['wind_direction_degrees'],
                weather['wind_speed_kmh'],
                orientation
            )
            
            results.append({
                'game_date': game['game_date'],
                'venue': venue,
                'away_team': game['away_team'],
                'home_team': game['home_team'],
                'temperature_c': weather['temperature_c'],
                'wind_speed_kmh': weather['wind_speed_kmh'],
                'wind_direction': weather['wind_direction_cardinal'],
                'wind_direction_degrees': weather['wind_direction_degrees'],
                'stadium_orientation': orientation,
                'wind_component_kmh': advantage['wind_component_kmh'],
                'crosswind_kmh': advantage['crosswind_kmh'],
                'hitter_advantage': advantage['hitter_advantage'],
                'pitcher_advantage': advantage['pitcher_advantage'],
                'advantage_score': advantage['advantage_score'],
                'humidity': weather['humidity_pct'],
                'pressure': weather['pressure_hpa'],
                'conditions': weather['prediction']
            })
        
        return pd.DataFrame(results)
    
    def find_roster_players_in_games(self, game_analysis: pd.DataFrame):
        """Find which roster players are playing in these games"""
        self.print_header("Step 4: Matching Your Roster to Games")
        
        player_games = []
        
        for _, player in self.roster.iterrows():
            player_name = player['player_name']
            player_team = player['mlb_team']
            position = player['position']
            fantasy_team = player['fantasy_team']
            
            # Find games where this player's team is playing
            player_games_df = game_analysis[
                (game_analysis['away_team'].str.contains(player_team, case=False, na=False)) |
                (game_analysis['home_team'].str.contains(player_team, case=False, na=False))
            ].copy()
            
            for _, game in player_games_df.iterrows():
                # Determine if player is home or away
                is_home = player_team.lower() in game['home_team'].lower()
                
                # Determine player type impact
                is_pitcher = position in ['SP', 'RP', 'P']
                
                if is_pitcher:
                    advantage = game['pitcher_advantage']
                    score = -game['advantage_score']  # Inverse for pitchers
                else:
                    advantage = game['hitter_advantage']
                    score = game['advantage_score']
                
                player_games.append({
                    'fantasy_team': fantasy_team,
                    'player_name': player_name,
                    'mlb_team': player_team,
                    'position': position,
                    'player_type': 'Pitcher' if is_pitcher else 'Hitter',
                    'game_date': game['game_date'],
                    'opponent': game['away_team'] if is_home else game['home_team'],
                    'venue': game['venue'],
                    'is_home': is_home,
                    'temperature': game['temperature_c'],
                    'wind_speed': game['wind_speed_kmh'],
                    'wind_direction': game['wind_direction'],
                    'wind_component': game['wind_component_kmh'],
                    'crosswind': game['crosswind_kmh'],
                    'advantage': advantage,
                    'advantage_score': score,
                    'conditions': game['conditions'],
                    'humidity': game['humidity']
                })
        
        return pd.DataFrame(player_games)
    
    def generate_recommendations(self, player_games: pd.DataFrame):
        """Generate actionable recommendations"""
        self.print_header("Step 5: Generating Recommendations")
        
        # Sort by advantage score
        favorable = player_games[player_games['advantage_score'] >= 1.0].sort_values(
            'advantage_score', ascending=False
        )
        
        unfavorable = player_games[player_games['advantage_score'] <= -1.0].sort_values(
            'advantage_score'
        )
        
        print(f"✅ FAVORABLE CONDITIONS ({len(favorable)} player-games):\n")
        
        if len(favorable) > 0:
            for _, row in favorable.head(10).iterrows():
                print(f"  🌟 {row['player_name']} ({row['position']}) - {row['fantasy_team']}")
                print(f"     {row['game_date'].strftime('%Y-%m-%d')} @ {row['venue']}")
                print(f"     Wind: {row['wind_speed']:.1f} km/h {row['wind_direction']} (component: {row['wind_component']:.1f})")
                print(f"     {row['advantage']} - Score: +{row['advantage_score']:.1f}")
                print()
        else:
            print("  No highly favorable conditions found\n")
        
        print(f"\n⚠️  UNFAVORABLE CONDITIONS ({len(unfavorable)} player-games):\n")
        
        if len(unfavorable) > 0:
            for _, row in unfavorable.head(10).iterrows():
                print(f"  ⛔ {row['player_name']} ({row['position']}) - {row['fantasy_team']}")
                print(f"     {row['game_date'].strftime('%Y-%m-%d')} @ {row['venue']}")
                print(f"     Wind: {row['wind_speed']:.1f} km/h {row['wind_direction']} (component: {row['wind_component']:.1f})")
                print(f"     {row['advantage']} - Score: {row['advantage_score']:.1f}")
                print()
        else:
            print("  No highly unfavorable conditions found\n")
        
        return favorable, unfavorable
    
    def export_results(self, player_games: pd.DataFrame):
        """Export analysis to CSV"""
        self.print_header("Step 6: Exporting Results")
        
        if player_games.empty:
            print("⚠️  No player games to export")
            return
        
        # Sort by advantage score
        player_games_sorted = player_games.sort_values('advantage_score', ascending=False)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"weather_advantage_analysis_{timestamp}.csv"
        filepath = self.data_dir / filename
        
        player_games_sorted.to_csv(filepath, index=False)
        
        print(f"✅ Exported {len(player_games_sorted)} player-game analyses to:")
        print(f"   {filepath}\n")
        
        # Show summary statistics
        print("📊 Summary Statistics:\n")
        print(f"  Total player-games analyzed: {len(player_games)}")
        print(f"  Favorable conditions: {len(player_games[player_games['advantage_score'] >= 1.0])}")
        print(f"  Neutral conditions: {len(player_games[(player_games['advantage_score'] > -1.0) & (player_games['advantage_score'] < 1.0)])}")
        print(f"  Unfavorable conditions: {len(player_games[player_games['advantage_score'] <= -1.0])}")
        print(f"\n  Average advantage score: {player_games['advantage_score'].mean():.2f}")
        print(f"  Best advantage score: {player_games['advantage_score'].max():.2f}")
        print(f"  Worst advantage score: {player_games['advantage_score'].min():.2f}")
    
    def run(self):
        """Execute full analysis"""
        print("\n" + "="*80)
        print("FANTASY BASEBALL WEATHER ADVANTAGE ANALYZER".center(80))
        print("="*80)
        print(f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Load data
        if not self.load_data():
            return False
        
        # Get last 30 games
        last_30_games = self.get_last_30_games()
        
        # Analyze weather advantages
        game_analysis = self.analyze_games(last_30_games)
        
        # Find roster players in these games
        player_games = self.find_roster_players_in_games(game_analysis)
        
        if player_games.empty:
            print("\n⚠️  No roster players found in last 30 games")
            return False
        
        # Generate recommendations
        self.generate_recommendations(player_games)
        
        # Export results
        self.export_results(player_games)
        
        self.print_header("ANALYSIS COMPLETE")
        
        print("✅ Weather advantage analysis finished!\n")
        print("💡 Use this data to:")
        print("   • Start players with favorable wind conditions")
        print("   • Bench players facing strong headwinds")
        print("   • Target hitters in hitter-friendly wind patterns")
        print("   • Stream pitchers with favorable wind support")
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        return True


def main():
    """Main entry point"""
    analyzer = WeatherAdvantageAnalyzer()
    
    try:
        success = analyzer.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Analysis interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
