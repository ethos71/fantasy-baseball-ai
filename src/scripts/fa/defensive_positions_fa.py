#!/usr/bin/env python3
"""
Defensive Positions Factor Analysis

Analyzes expected defensive positions and shifts for fantasy baseball context.
Important: In fantasy baseball, rosters are locked 30 minutes before game time,
so mid-game defensive shifts cannot be exploited. This analyzes starting positions
and team defensive strategies that are set before the game.

Key Metrics:
- Starting defensive position assignment
- Team defensive shift tendencies
- Expected fielding opportunities by position
- Quality of defensive players at each position
- Impact on opposing hitters' production

Defensive Considerations:
- Strong defensive teams reduce opponent stats
- Weak defensive teams allow more hits/runs
- Specific position weaknesses (e.g., weak SS/2B)
- Shift tendencies against LHB/RHB

Output:
- Defensive impact score (-2.0 to +2.0)
- Expected starting position
- Opponent defensive rating
- Position-specific matchup quality
"""

import pandas as pd
import numpy as np
from pathlib import Path


class DefensivePositionsFactorAnalyzer:
    """Analyze defensive position matchups for fantasy baseball"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.team_defensive_ratings = {}
        self.position_defensive_quality = {}
    
    def get_team_defensive_rating(self, team):
        """Get or generate team defensive rating"""
        if team in self.team_defensive_ratings:
            return self.team_defensive_ratings[team]
        
        # Generate synthetic defensive rating (0.5 = average, 0.0-1.0 range)
        np.random.seed(hash(team) % 2**32)
        rating = np.random.normal(0.5, 0.15)
        rating = max(0.0, min(1.0, rating))
        np.random.seed(None)
        
        self.team_defensive_ratings[team] = rating
        return rating
    
    def get_position_defensive_quality(self, team, position):
        """Get defensive quality at specific position"""
        key = f"{team}_{position}"
        if key in self.position_defensive_quality:
            return self.position_defensive_quality[key]
        
        # Generate synthetic position-specific quality
        np.random.seed(hash(key) % 2**32)
        quality = np.random.normal(0.5, 0.2)
        quality = max(0.0, min(1.0, quality))
        np.random.seed(None)
        
        self.position_defensive_quality[key] = quality
        return quality
    
    def get_shift_tendency(self, team, batter_hand):
        """Get team's shift tendency against LHB/RHB"""
        # Generate synthetic shift tendency (0.0-1.0, higher = more shifts)
        np.random.seed(hash(f"{team}_{batter_hand}") % 2**32)
        shift_rate = np.random.beta(2, 3)  # Skewed toward moderate shifting
        np.random.seed(None)
        return shift_rate
    
    def calculate_defensive_impact(self, position, opponent_team, batter_hand, 
                                   team_def_rating, pos_def_quality, shift_tendency):
        """Calculate defensive impact on hitter performance"""
        
        # Base impact from team defense
        team_impact = (team_def_rating - 0.5) * -2.0  # Good defense = negative for hitter
        
        # Position-specific impact (varies by position importance)
        position_weights = {
            'C': 0.3, '1B': 0.5, '2B': 1.2, '3B': 1.0, 'SS': 1.2,
            'LF': 0.7, 'CF': 1.0, 'RF': 0.7, 'OF': 0.8, 'DH': 0.0
        }
        pos_weight = position_weights.get(position, 0.5)
        pos_impact = (pos_def_quality - 0.5) * -1.5 * pos_weight
        
        # Shift impact (shifts generally help defense)
        shift_impact = 0.0
        if position in ['1B', '2B', 'SS', '3B']:  # Infield positions affected by shifts
            if batter_hand == 'L':  # LHB face more shifts
                shift_impact = shift_tendency * -0.8
            elif batter_hand == 'R':
                shift_impact = shift_tendency * -0.3
        
        # Combined impact
        total_impact = team_impact + pos_impact + shift_impact
        
        return max(-2.0, min(2.0, total_impact))
    
    def get_expected_at_bats_by_position(self, position):
        """Estimate impact based on defensive opportunities"""
        # More defensive plays = more impact on opponent stats
        opportunity_multiplier = {
            'SS': 1.3, '2B': 1.3, '3B': 1.1, 'CF': 1.2,
            '1B': 1.1, 'LF': 0.9, 'RF': 0.9, 'C': 0.8, 'DH': 0.0
        }
        return opportunity_multiplier.get(position, 1.0)
    
    def get_batter_handedness(self, player_name):
        """Get batter handedness"""
        np.random.seed(hash(player_name) % 2**32)
        rand = np.random.random()
        bats = 'L' if rand < 0.25 else ('S' if rand < 0.35 else 'R')
        np.random.seed(None)
        return bats
    
    def analyze(self, games_df, game_logs_df, roster_df):
        """Analyze defensive position matchups"""
        results = []
        
        for _, game in games_df.iterrows():
            game_date = game['game_date']
            opponent = game.get('opponent', 'UNK')
            is_home = game.get('is_home', True)
            
            # Get opponent's defensive rating
            team_def_rating = self.get_team_defensive_rating(opponent)
            
            for _, player in roster_df.iterrows():
                player_name = player['player_name']
                position = player.get('position', 'OF')
                
                # Skip pitchers (they're not affected by fielding positions)
                if position in ['SP', 'RP', 'P']:
                    continue
                
                # Get player handedness
                batter_hand = self.get_batter_handedness(player_name)
                
                # Get position-specific defensive quality
                pos_def_quality = self.get_position_defensive_quality(opponent, position)
                
                # Get shift tendency
                shift_tendency = self.get_shift_tendency(opponent, batter_hand)
                
                # Calculate defensive impact
                defensive_impact = self.calculate_defensive_impact(
                    position, opponent, batter_hand,
                    team_def_rating, pos_def_quality, shift_tendency
                )
                
                # Adjust for defensive opportunity
                opportunity_mult = self.get_expected_at_bats_by_position(position)
                final_score = defensive_impact * opportunity_mult
                
                # Determine defensive quality category
                if team_def_rating > 0.65:
                    def_quality = "Strong"
                elif team_def_rating < 0.35:
                    def_quality = "Weak"
                else:
                    def_quality = "Average"
                
                # Position-specific notes
                if pos_def_quality > 0.7:
                    pos_note = "Elite defender"
                elif pos_def_quality < 0.3:
                    pos_note = "Weak defender"
                else:
                    pos_note = "Average defender"
                
                results.append({
                    'player_name': player_name,
                    'game_date': game_date,
                    'position': position,
                    'opponent': opponent,
                    'batter_hand': batter_hand,
                    'team_def_rating': team_def_rating,
                    'pos_def_quality': pos_def_quality,
                    'shift_tendency': shift_tendency,
                    'score': final_score,
                    'def_quality': def_quality,
                    'position_note': pos_note,
                    'opportunity_mult': opportunity_mult
                })
        
        return pd.DataFrame(results)
    
    def analyze_roster(self, roster_df, schedule_df, teams_df):
        """Wrapper for analyze to match interface"""
        # Load game logs
        game_logs_file = self.data_dir / "mlb_game_logs_2024.csv"
        if game_logs_file.exists():
            game_logs_df = pd.read_csv(game_logs_file)
        else:
            game_logs_df = pd.DataFrame()
        return self.analyze(schedule_df, game_logs_df, roster_df)
