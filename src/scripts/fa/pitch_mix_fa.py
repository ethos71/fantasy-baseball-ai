#!/usr/bin/env python3
"""
Pitch Mix Analysis Factor

Analyzes pitcher's pitch mix (types, frequencies, velocities) and batter's historical
performance against different pitch types to predict favorable/unfavorable matchups.

Key Concepts:
- Pitch Types: Fastball (4-seam, 2-seam, Cutter), Breaking (Slider, Curve), Offspeed (Change, Split)
- Usage Rates: Frequency each pitch type is thrown
- Pitcher Tendencies: Primary vs secondary pitches, situational usage
- Batter Performance: Success rates against different pitch types
- Matchup Analysis: Pitcher strengths vs batter weaknesses

Output:
- Pitch mix breakdown for pitchers
- Batter performance vs pitch types
- Matchup advantage score based on pitch mix vs batter tendencies
- Specific pitch type advantages/disadvantages
"""

import pandas as pd
from pathlib import Path


class PitchMixAnalyzer:
    """Analyze pitch mix and its impact on matchups"""
    
    # Pitch type categories
    FASTBALLS = ['4-Seam Fastball', 'FF', '4-seam', 'Fastball', 'Sinker', 'SI', '2-seam', 'Cutter', 'FC']
    BREAKING = ['Slider', 'SL', 'Curveball', 'CU', 'Curve', 'Slurve']
    OFFSPEED = ['Changeup', 'CH', 'Splitter', 'FS', 'Split-Finger']
    
    # Performance thresholds
    GOOD_BATTING_AVG = 0.300
    POOR_BATTING_AVG = 0.200
    HIGH_USAGE = 0.30  # 30%+
    LOW_USAGE = 0.10   # 10%-
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def categorize_pitch(self, pitch_type):
        """Categorize pitch into broader groups"""
        if any(p in str(pitch_type) for p in self.FASTBALLS):
            return 'Fastball'
        elif any(p in str(pitch_type) for p in self.BREAKING):
            return 'Breaking'
        elif any(p in str(pitch_type) for p in self.OFFSPEED):
            return 'Offspeed'
        else:
            return 'Other'
    
    def calculate_pitcher_mix(self, pitcher_stats):
        """Calculate pitch mix profile for a pitcher"""
        # Simulated pitch mix - in reality would come from MLB Statcast data
        # Default distribution if no data available
        mix = {
            'Fastball': 0.55,
            'Breaking': 0.25,
            'Offspeed': 0.20
        }
        
        # Would analyze actual pitch-by-pitch data here
        return mix
    
    def calculate_batter_vs_pitch_type(self, batter_stats):
        """Calculate batter's performance vs different pitch types"""
        # Simulated stats - in reality would come from MLB data
        # Default performance if no data available
        performance = {
            'Fastball': {'avg': 0.250, 'slg': 0.400, 'ops': 0.750},
            'Breaking': {'avg': 0.220, 'slg': 0.350, 'ops': 0.650},
            'Offspeed': {'avg': 0.240, 'slg': 0.380, 'ops': 0.700}
        }
        
        # Would analyze actual performance splits here
        return performance
    
    def calculate_matchup_advantage(self, pitcher_mix, batter_performance):
        """Calculate advantage score based on pitch mix vs batter performance"""
        total_score = 0.0
        details = []
        
        for pitch_type, usage_rate in pitcher_mix.items():
            if pitch_type not in batter_performance:
                continue
            
            batter_stats = batter_performance[pitch_type]
            avg = batter_stats['avg']
            
            # Calculate how effective this pitch type is
            if avg > self.GOOD_BATTING_AVG:
                # Batter hits this well, bad for pitcher
                pitch_score = -1.0 * usage_rate
                strength = "Batter strength"
            elif avg < self.POOR_BATTING_AVG:
                # Batter struggles, good for pitcher
                pitch_score = 1.0 * usage_rate
                strength = "Batter weakness"
            else:
                # Neutral
                pitch_score = 0.0
                strength = "Neutral"
            
            # Weight by usage rate
            weighted_score = pitch_score * 3.0  # Scale factor
            total_score += weighted_score
            
            if usage_rate >= self.HIGH_USAGE:
                usage_desc = "high usage"
            elif usage_rate <= self.LOW_USAGE:
                usage_desc = "low usage"
            else:
                usage_desc = "moderate usage"
            
            details.append({
                'pitch_type': pitch_type,
                'usage_rate': usage_rate,
                'usage_desc': usage_desc,
                'batter_avg': avg,
                'strength': strength,
                'weighted_score': weighted_score
            })
        
        return total_score, details
    
    def analyze(self, games_df, mlb_df, roster_df):
        """Analyze pitch mix advantages for matchups"""
        results = []
        
        for _, game in games_df.iterrows():
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            
            # Find pitchers and batters in this game
            for _, player in roster_df.iterrows():
                player_name = player['player_name']
                player_team = player.get('mlb_team', '')
                position = player.get('position', '')
                
                if not player_team:
                    continue
                
                # Find opposing pitcher or batters
                is_pitcher = position in ['SP', 'RP', 'P']
                
                if is_pitcher:
                    # Pitcher vs opposing team's batters
                    opposing_team = away_team if player_team == home_team else home_team
                    pitcher_mix = self.calculate_pitcher_mix(None)
                    
                    # Average opposing team performance (simplified)
                    avg_batter_performance = self.calculate_batter_vs_pitch_type(None)
                    
                    matchup_score, details = self.calculate_matchup_advantage(
                        pitcher_mix, avg_batter_performance
                    )
                    
                    # For pitcher, positive score is good
                    primary_pitch = max(pitcher_mix.items(), key=lambda x: x[1])
                    
                    results.append({
                        'player_name': player_name,
                        'position': position,
                        'game_date': game['game_date'],
                        'opponent': opposing_team,
                        'role': 'Pitcher',
                        'primary_pitch': f"{primary_pitch[0]} ({primary_pitch[1]*100:.0f}%)",
                        'pitch_mix_score': round(matchup_score, 2),
                        'impact': self._get_pitcher_impact(matchup_score, primary_pitch[0])
                    })
                    
                else:
                    # Batter vs opposing pitcher
                    # Need to find opposing pitcher's likely starter
                    opposing_team = away_team if player_team == home_team else home_team
                    
                    # Simulate opposing pitcher's pitch mix
                    opposing_pitcher_mix = self.calculate_pitcher_mix(None)
                    batter_performance = self.calculate_batter_vs_pitch_type(None)
                    
                    matchup_score, details = self.calculate_matchup_advantage(
                        opposing_pitcher_mix, batter_performance
                    )
                    
                    # For batter, negative score is good (pitcher struggling = batter success)
                    matchup_score = -matchup_score
                    
                    # Find batter's best pitch type
                    best_pitch = max(batter_performance.items(), key=lambda x: x[1]['avg'])
                    worst_pitch = min(batter_performance.items(), key=lambda x: x[1]['avg'])
                    
                    results.append({
                        'player_name': player_name,
                        'position': position,
                        'game_date': game['game_date'],
                        'opponent': opposing_team,
                        'role': 'Batter',
                        'best_vs_pitch': f"{best_pitch[0]} (.{int(best_pitch[1]['avg']*1000):03d})",
                        'worst_vs_pitch': f"{worst_pitch[0]} (.{int(worst_pitch[1]['avg']*1000):03d})",
                        'pitch_mix_score': round(matchup_score, 2),
                        'impact': self._get_batter_impact(matchup_score, best_pitch[0])
                    })
        
        return pd.DataFrame(results)
    
    def _get_pitcher_impact(self, score, primary_pitch):
        """Generate impact description for pitcher"""
        if score > 1.0:
            return f"Strong advantage - {primary_pitch} effective vs opponent"
        elif score > 0.5:
            return f"Moderate advantage - {primary_pitch} should work well"
        elif score > -0.5:
            return "Neutral matchup - balanced pitch mix"
        elif score > -1.0:
            return f"Slight disadvantage - opponent hits {primary_pitch} well"
        else:
            return f"Significant disadvantage - {primary_pitch} may struggle"
    
    def _get_batter_impact(self, score, best_pitch):
        """Generate impact description for batter"""
        if score > 1.0:
            return f"Favorable matchup - pitcher throws {best_pitch} frequently"
        elif score > 0.5:
            return "Good opportunity - should see favorable pitch types"
        elif score > -0.5:
            return "Average matchup - typical pitch mix expected"
        elif score > -1.0:
            return f"Challenging matchup - limited exposure to {best_pitch}"
        else:
            return "Difficult matchup - facing mostly troublesome pitch types"


    def analyze_roster(self, roster_df, schedule_df, players_df=None):
        """Wrapper for analyze to match interface"""
        return self.analyze(schedule_df, players_df, roster_df)
    
    def _load_gamelogs(self):
        """Helper to load game logs if needed"""
        game_logs_file = self.data_dir / "mlb_game_logs_2024.csv"
        if game_logs_file.exists():
            import pandas as pd
            return pd.read_csv(game_logs_file)
        return pd.DataFrame()
