#!/usr/bin/env python3
"""
Lineup Position Analysis Factor

Analyzes the impact of a player's batting order position on their fantasy production.
Different lineup spots have different responsibilities and opportunities.

Key Concepts:
- Leadoff (1-2): High PA, speed focus, on-base skills, table setters
- Middle (3-4-5): Power positions, RBI opportunities, run production
- Lower (6-7-8-9): Fewer PA, less protection, pitcher spot in NL

Position Impact:
- Plate Appearances: Higher in order = more opportunities
- RBI Opportunities: More runners on base for 3-4-5 spots
- Run Scoring: Leadoff/2-hole get on base for middle order
- Pitcher Matchups: 1-5 see starter more, 6-9 may see reliever

Output:
- Lineup position and its typical performance characteristics
- Expected PA based on position
- RBI/Run opportunity score
- Position-adjusted fantasy impact
"""

import pandas as pd
import numpy as np
from pathlib import Path


class LineupPositionAnalyzer:
    """Analyze batting order position impact on fantasy production"""
    
    # Expected plate appearances per position (9-inning game average)
    EXPECTED_PA = {
        1: 4.6,  # Leadoff
        2: 4.5,
        3: 4.4,  # Cleanup
        4: 4.3,
        5: 4.2,
        6: 4.0,
        7: 3.9,
        8: 3.8,
        9: 3.6   # Last spot
    }
    
    # RBI opportunity multipliers by position
    RBI_OPPORTUNITY = {
        1: 0.6,  # Fewer runners on
        2: 0.7,
        3: 1.3,  # Prime RBI spots
        4: 1.4,
        5: 1.2,
        6: 0.9,
        7: 0.8,
        8: 0.7,
        9: 0.6
    }
    
    # Run scoring opportunity multipliers
    RUN_OPPORTUNITY = {
        1: 1.4,  # Most chances to score
        2: 1.3,
        3: 1.2,
        4: 1.1,
        5: 1.0,
        6: 0.9,
        7: 0.8,
        8: 0.7,
        9: 0.6
    }
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def get_lineup_position(self, player_name, team, game_date, mlb_df):
        """Get player's lineup position for a specific game"""
        # In reality, would scrape from MLB lineup data
        # For now, simulate based on player stats/role
        
        # Check if player stats indicate typical lineup spot
        player_stats = mlb_df[mlb_df['player_name'] == player_name]
        if player_stats.empty:
            return None
        
        # Use stats to estimate lineup position
        # This is simplified - real implementation would use actual lineup data
        position = self._estimate_lineup_spot(player_stats.iloc[0])
        return position
    
    def _estimate_lineup_spot(self, player_stats):
        """Estimate typical lineup position based on player stats"""
        # Get relevant stats (with defaults)
        avg = player_stats.get('avg', 0.250)
        hr = player_stats.get('hr', 0)
        sb = player_stats.get('sb', 0)
        obp = player_stats.get('obp', 0.320)
        
        # Leadoff hitters: High OBP, speed
        if obp > 0.340 and sb > 10:
            return 1
        
        # 2-hole: Good contact, speed
        if obp > 0.330 and avg > 0.270:
            return 2
        
        # 3-hole: Best hitter, balanced
        if avg > 0.280 and hr > 15:
            return 3
        
        # Cleanup: Power hitter
        if hr > 25:
            return 4
        
        # 5-hole: Secondary power
        if hr > 15:
            return 5
        
        # 6-hole: Solid regular
        if avg > 0.250:
            return 6
        
        # 7-9: Lower production
        return np.random.choice([7, 8, 9])
    
    def calculate_position_impact(self, lineup_position):
        """Calculate fantasy impact multipliers for lineup position"""
        if lineup_position is None or lineup_position not in range(1, 10):
            # No lineup data or invalid position
            return {
                'pa_multiplier': 1.0,
                'rbi_multiplier': 1.0,
                'run_multiplier': 1.0,
                'overall_multiplier': 1.0
            }
        
        pa_mult = self.EXPECTED_PA[lineup_position] / self.EXPECTED_PA[5]  # Normalize to 5-hole
        rbi_mult = self.RBI_OPPORTUNITY[lineup_position]
        run_mult = self.RUN_OPPORTUNITY[lineup_position]
        
        # Overall multiplier weighted toward PA (most important)
        overall_mult = (pa_mult * 0.5) + (rbi_mult * 0.25) + (run_mult * 0.25)
        
        return {
            'pa_multiplier': round(pa_mult, 2),
            'rbi_multiplier': round(rbi_mult, 2),
            'run_multiplier': round(run_mult, 2),
            'overall_multiplier': round(overall_mult, 2)
        }
    
    def get_position_description(self, lineup_position):
        """Get description of lineup position characteristics"""
        if lineup_position is None:
            return "Unknown - Position not available"
        
        descriptions = {
            1: "Leadoff - Max PA, table setter, run scoring focus",
            2: "Two-hole - High PA, contact skills, gets RBI from leadoff",
            3: "Three-hole - Premium spot, balanced stats, protection",
            4: "Cleanup - Power spot, best RBI opportunities, run producer",
            5: "Five-hole - Strong spot, good RBI chances, protects cleanup",
            6: "Six-hole - Above average PA, moderate RBI opportunities",
            7: "Seven-hole - Below average PA, limited RBI chances",
            8: "Eight-hole - Low PA, minimal RBI opportunities",
            9: "Nine-hole - Lowest PA, fewest opportunities (often pitcher in NL)"
        }
        
        return descriptions.get(lineup_position, "Unknown position")
    
    def get_lineup_tier(self, lineup_position):
        """Categorize lineup position into tier"""
        if lineup_position is None:
            return "Unknown"
        elif lineup_position in [1, 2]:
            return "Top" 
        elif lineup_position in [3, 4, 5]:
            return "Middle"
        else:
            return "Bottom"
    
    def analyze(self, games_df, mlb_df, roster_df):
        """Analyze lineup position advantages for roster players"""
        results = []
        
        for _, game in games_df.iterrows():
            game_date = game.get('game_date', '')
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            
            for _, player in roster_df.iterrows():
                player_name = player['player_name']
                player_team = player.get('mlb_team', '')
                position = player.get('position', '')
                
                # Only analyze batters
                if position in ['SP', 'RP', 'P']:
                    continue
                
                if not player_team or player_team not in [home_team, away_team]:
                    continue
                
                # Get lineup position
                lineup_position = self.get_lineup_position(
                    player_name, player_team, game_date, mlb_df
                )
                
                # Calculate impact
                impact = self.calculate_position_impact(lineup_position)
                position_desc = self.get_position_description(lineup_position)
                tier = self.get_lineup_tier(lineup_position)
                
                # Calculate score (higher lineup position = better)
                if lineup_position:
                    # Invert so 1st = highest score
                    position_score = (10 - lineup_position) * impact['overall_multiplier']
                else:
                    position_score = 0.0
                
                results.append({
                    'player_name': player_name,
                    'position': position,
                    'game_date': game_date,
                    'opponent': away_team if player_team == home_team else home_team,
                    'lineup_spot': lineup_position if lineup_position else 'N/A',
                    'lineup_tier': tier,
                    'expected_pa': self.EXPECTED_PA.get(lineup_position, 4.0),
                    'pa_multiplier': impact['pa_multiplier'],
                    'rbi_multiplier': impact['rbi_multiplier'],
                    'run_multiplier': impact['run_multiplier'],
                    'lineup_score': round(position_score, 2),
                    'impact': position_desc
                })
        
        return pd.DataFrame(results)
    
    def get_position_quality_rating(self, lineup_position):
        """Get quality rating for lineup position"""
        if lineup_position is None:
            return "Unknown"
        elif lineup_position in [1, 2, 3, 4]:
            return "Excellent"
        elif lineup_position == 5:
            return "Good"
        elif lineup_position in [6, 7]:
            return "Fair"
        else:
            return "Poor"
    
    def analyze_roster(self, roster_df, schedule_df):
        """Wrapper for analyze to match interface"""
        # Load MLB data
        mlb_file = self.data_dir / "mlb_all_players_complete.csv"
        if mlb_file.exists():
            mlb_df = pd.read_csv(mlb_file)
        else:
            mlb_df = pd.DataFrame()
        return self.analyze(schedule_df, mlb_df, roster_df)


def analyze_lineup_position(data_dir='data'):
    """Main function to run lineup position analysis"""
    analyzer = LineupPositionAnalyzer(data_dir)
    
    data_path = Path(data_dir)
    
    # Load data files
    try:
        games_df = pd.read_csv(data_path / 'upcoming_games.csv')
    except FileNotFoundError:
        print("Warning: upcoming_games.csv not found, using empty dataframe")
        games_df = pd.DataFrame()
    
    try:
        mlb_df = pd.read_csv(data_path / 'mlb_stats.csv')
    except FileNotFoundError:
        print("Warning: mlb_stats.csv not found, using empty dataframe")
        mlb_df = pd.DataFrame()
    
    try:
        roster_df = pd.read_csv(data_path / 'roster.csv')
    except FileNotFoundError:
        print("Warning: roster.csv not found, using empty dataframe")
        roster_df = pd.DataFrame()
    
    if games_df.empty or mlb_df.empty or roster_df.empty:
        print("Insufficient data for lineup position analysis")
        return pd.DataFrame()
    
    results_df = analyzer.analyze(games_df, mlb_df, roster_df)
    
    # Save results
    output_file = data_path / 'lineup_position_analysis.csv'
    results_df.to_csv(output_file, index=False)
    print(f"\nLineup Position Analysis saved to {output_file}")
    
    return results_df


if __name__ == "__main__":
    results = analyze_lineup_position()
    if not results.empty:
        print("\n=== LINEUP POSITION ANALYSIS ===")
        print(results.to_string(index=False))
