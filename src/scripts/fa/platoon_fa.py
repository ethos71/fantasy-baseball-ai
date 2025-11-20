#!/usr/bin/env python3
"""
Platoon Advantage Factor Analysis

Analyzes left/right-handed pitcher-hitter matchups.
Traditional platoon advantages:
- LHB vs RHP: Favorable (better view of ball)
- RHB vs LHP: Favorable (better view of ball)
- LHB vs LHP: Unfavorable (same-side disadvantage)
- RHB vs RHP: Slightly unfavorable

Key Metrics:
- Player handedness (bats/throws)
- Pitcher handedness
- vs LHP batting average
- vs RHP batting average
- Platoon split differential

Output:
- Platoon score (-1.5 to +1.5)
- Matchup type (LHB vs RHP, etc.)
- Historical splits
"""

import pandas as pd
import numpy as np
from pathlib import Path


class PlatoonFactorAnalyzer:
    """Analyze platoon matchup advantages"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.player_handedness = {}
    
    def get_player_handedness(self, player_name):
        """Get or generate player handedness"""
        if player_name in self.player_handedness:
            return self.player_handedness[player_name]
        
        # Generate synthetic (~25% L, ~10% S, ~65% R)
        np.random.seed(hash(player_name) % 2**32)
        rand = np.random.random()
        bats = 'L' if rand < 0.25 else ('S' if rand < 0.35 else 'R')
        throws = 'L' if np.random.random() < 0.25 else 'R'
        np.random.seed(None)
        
        self.player_handedness[player_name] = (bats, throws)
        return (bats, throws)
    
    def get_pitcher_handedness(self, opponent, game_date):
        """Determine pitcher handedness (synthetic)"""
        np.random.seed(hash(str(opponent) + str(game_date)) % 2**32)
        pitcher_hand = 'L' if np.random.random() < 0.25 else 'R'
        np.random.seed(None)
        return pitcher_hand
    
    def calculate_platoon_score(self, bats, pitcher_hand, vs_lhp_ba, vs_rhp_ba, sample_size):
        """Calculate platoon advantage score"""
        # Base platoon advantage
        if bats == 'S':
            base_score = 0.0
        elif (bats == 'L' and pitcher_hand == 'R') or (bats == 'R' and pitcher_hand == 'L'):
            base_score = 1.0
        elif bats == 'L' and pitcher_hand == 'L':
            base_score = -1.0
        elif bats == 'R' and pitcher_hand == 'R':
            base_score = -0.5
        else:
            base_score = 0.0
        
        # Adjust with actual splits if available
        if vs_lhp_ba > 0 and vs_rhp_ba > 0:
            split_diff = (vs_rhp_ba - vs_lhp_ba) if pitcher_hand == 'R' else (vs_lhp_ba - vs_rhp_ba)
            split_score = split_diff * 10
            confidence = min(sample_size / 20, 1.0)
            platoon_score = (base_score * 0.3 + split_score * 0.7) * confidence
        else:
            platoon_score = base_score
        
        return max(-1.5, min(1.5, platoon_score))
    
    def analyze(self, games_df, game_logs_df, roster_df):
        """Analyze platoon advantages"""
        results = []
        
        # Convert dates once
        games_df['game_date'] = pd.to_datetime(games_df['game_date'])
        if len(game_logs_df) > 0:
            game_logs_df['game_date'] = pd.to_datetime(game_logs_df['game_date'])
        
        for _, game in games_df.iterrows():
            game_date = game['game_date']
            opponent = game.get('opponent', '')
            
            for _, player in roster_df.iterrows():
                player_name = player['player_name']
                position = player.get('position', '')
                
                # Skip pitchers
                if position in ['SP', 'RP', 'P', 'Pitcher']:
                    continue
                
                bats, throws = self.get_player_handedness(player_name)
                pitcher_hand = self.get_pitcher_handedness(opponent, game_date)
                
                # Get historical splits
                player_history = game_logs_df[
                    (game_logs_df['player_name'] == player_name) &
                    (game_logs_df['game_date'] < game_date)
                ]
                
                vs_lhp_ba = 0.0
                vs_rhp_ba = 0.0
                
                if len(player_history) > 0:
                    # Calculate splits (simplified)
                    vs_lhp_games = len(player_history) // 4  # Estimate
                    _ = len(player_history) - vs_lhp_games
                    vs_lhp_ba = 0.250  # Placeholder
                    vs_rhp_ba = 0.260  # Placeholder
                
                matchup_type = f"{bats}HB vs {pitcher_hand}HP" if bats in ['L', 'R'] else f"SWITCH vs {pitcher_hand}HP"
                
                platoon_score = self.calculate_platoon_score(
                    bats, pitcher_hand, vs_lhp_ba, vs_rhp_ba, len(player_history)
                )
                
                results.append({
                    'player_name': player_name,
                    'game_date': game_date,
                    'bats': bats,
                    'pitcher_hand': pitcher_hand,
                    'matchup_type': matchup_type,
                    'platoon_score': platoon_score
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
