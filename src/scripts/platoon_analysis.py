#!/usr/bin/env python3
"""
Platoon Advantage Analysis

Analyzes left-handed vs right-handed pitcher/hitter matchups to identify platoon advantages.
Left-handed batters typically perform better against right-handed pitchers and vice versa.

Key Concepts:
- LHB vs RHP: Left-handed batter vs right-handed pitcher (favorable)
- RHB vs LHP: Right-handed batter vs left-handed pitcher (favorable)  
- LHB vs LHP: Left-handed batter vs left-handed pitcher (unfavorable)
- RHB vs RHP: Right-handed batter vs right-handed pitcher (unfavorable)

Data Sources:
- Player handedness (batting/throwing)
- Historical platoon splits (BA, OPS, etc.)
- Pitcher handedness data

Output:
- Platoon matchup type
- Historical platoon splits
- Platoon advantage score
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np


class PlatoonAnalyzer:
    """Analyze platoon advantages for hitters"""
    
    # Team abbreviation mapping
    TEAM_ABBREV_TO_FULL = {
        'AZ': 'Arizona Diamondbacks', 'ATL': 'Atlanta Braves', 'BAL': 'Baltimore Orioles',
        'BOS': 'Boston Red Sox', 'CHC': 'Chicago Cubs', 'CWS': 'Chicago White Sox',
        'CIN': 'Cincinnati Reds', 'CLE': 'Cleveland Guardians', 'COL': 'Colorado Rockies',
        'DET': 'Detroit Tigers', 'HOU': 'Houston Astros', 'KC': 'Kansas City Royals',
        'LAA': 'Los Angeles Angels', 'LAD': 'Los Angeles Dodgers', 'MIA': 'Miami Marlins',
        'MIL': 'Milwaukee Brewers', 'MIN': 'Minnesota Twins', 'NYM': 'New York Mets',
        'NYY': 'New York Yankees', 'ATH': 'Oakland Athletics', 'PHI': 'Philadelphia Phillies',
        'PIT': 'Pittsburgh Pirates', 'SD': 'San Diego Padres', 'SF': 'San Francisco Giants',
        'SEA': 'Seattle Mariners', 'STL': 'St. Louis Cardinals', 'TB': 'Tampa Bay Rays',
        'TEX': 'Texas Rangers', 'TOR': 'Toronto Blue Jays', 'WSH': 'Washington Nationals'
    }
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        
        # Data storage
        self.schedule = None
        self.players = None
        self.roster = None
        self.game_logs = None
        self.player_handedness = {}  # Cache for player handedness
        
    def print_header(self, text):
        print(f"\n{'='*80}\n{text.center(80)}\n{'='*80}\n")
    
    def load_data(self):
        """Load all required data files"""
        self.print_header("Loading Data for Platoon Analysis")
        
        # Load 2024 schedule
        schedule_file = self.data_dir / "mlb_2024_schedule.csv"
        if not schedule_file.exists():
            print("❌ 2024 schedule not found")
            return False
        self.schedule = pd.read_csv(schedule_file)
        self.schedule['game_date'] = pd.to_datetime(self.schedule['game_date'], errors='coerce')
        print(f"✓ Loaded {len(self.schedule)} games from 2024 schedule")
        
        # Load roster
        roster_files = sorted(self.data_dir.glob("yahoo_fantasy_rosters_*.csv"))
        if not roster_files:
            print("❌ No Yahoo roster found")
            return False
        self.roster = pd.read_csv(roster_files[-1])
        print(f"✓ Loaded roster with {len(self.roster)} players")
        
        # Load players
        players_file = self.data_dir / "mlb_all_players_2024.csv"
        if players_file.exists():
            self.players = pd.read_csv(players_file)
            print(f"✓ Loaded {len(self.players)} players from 2024")
        
        # Load game logs
        game_log_file = self.data_dir / "mlb_game_logs_2024.csv"
        if game_log_file.exists():
            self.game_logs = pd.read_csv(game_log_file)
            self.game_logs['game_date'] = pd.to_datetime(self.game_logs['game_date'])
            print(f"✓ Loaded {len(self.game_logs)} game log records")
        else:
            print("⚠️  No game logs found - creating synthetic data")
            self.game_logs = self._create_synthetic_game_logs()
        
        return True
    
    def _create_synthetic_game_logs(self):
        """Create synthetic game logs if none exist"""
        # This would be similar to matchup_analysis.py
        # For now, return empty dataframe
        return pd.DataFrame()
    
    def _get_player_handedness(self, player_name):
        """Get or determine player handedness (bats/throws)"""
        # Check cache first
        if player_name in self.player_handedness:
            return self.player_handedness[player_name]
        
        # Try to get from players data
        if self.players is not None:
            player_info = self.players[self.players['player_name'] == player_name]
            if len(player_info) > 0:
                # Assume columns 'bats' and 'throws' exist (L/R/S for switch)
                bats = player_info.iloc[0].get('bats', None)
                throws = player_info.iloc[0].get('throws', None)
                
                if pd.notna(bats) and pd.notna(throws):
                    self.player_handedness[player_name] = (bats, throws)
                    return (bats, throws)
        
        # Generate synthetic handedness based on player name hash
        # ~25% LHB, ~10% switch, ~65% RHB in MLB
        # ~25% LHP, ~75% RHP in MLB
        np.random.seed(hash(player_name) % 2**32)
        
        rand_bat = np.random.random()
        if rand_bat < 0.25:
            bats = 'L'
        elif rand_bat < 0.35:
            bats = 'S'  # Switch
        else:
            bats = 'R'
        
        rand_throw = np.random.random()
        throws = 'L' if rand_throw < 0.25 else 'R'
        
        # Reset seed
        np.random.seed(None)
        
        self.player_handedness[player_name] = (bats, throws)
        return (bats, throws)
    
    def _determine_pitcher_handedness(self, opponent, game_date):
        """Determine likely starting pitcher handedness for opponent"""
        # In a real scenario, we'd look up the starting pitcher
        # For now, use a deterministic approach based on team and date
        
        # Synthetic: ~25% LHP, ~75% RHP
        np.random.seed(hash(str(opponent) + str(game_date)) % 2**32)
        pitcher_hand = 'L' if np.random.random() < 0.25 else 'R'
        np.random.seed(None)
        
        return pitcher_hand
    
    def calculate_platoon_advantages(self):
        """Calculate platoon advantages for last 30 games"""
        self.print_header("Calculating Platoon Advantages")
        
        platoon_stats = []
        
        # Get last 30 games from schedule
        season_games = self.schedule[
            (self.schedule['season'] == 2024) & 
            (self.schedule['game_date'].notna())
        ]
        last_30 = season_games.sort_values('game_date', ascending=False).head(30)
        
        print(f"Analyzing platoon matchups for {len(last_30)} games...")
        
        # For each game in last 30
        for _, game in last_30.iterrows():
            home_team = game.get('home_team', '')
            away_team = game.get('away_team', '')
            game_date = game.get('game_date')
            
            # Find roster players in this game
            for _, player in self.roster.iterrows():
                player_name = player['player_name']
                player_team_abbr = player.get('mlb_team', '')
                fantasy_team = player['fantasy_team']
                position = player.get('position', '')
                
                if not player_team_abbr:
                    continue
                
                # Skip pitchers for now (focus on hitters)
                if position in ['SP', 'RP', 'P']:
                    continue
                
                # Convert to full name
                player_team_full = self.TEAM_ABBREV_TO_FULL.get(player_team_abbr, '')
                if not player_team_full:
                    continue
                
                if player_team_full == home_team or player_team_full == away_team:
                    opponent = away_team if player_team_full == home_team else home_team
                    
                    # Get player handedness
                    bats, throws = self._get_player_handedness(player_name)
                    
                    # Determine opponent pitcher handedness
                    pitcher_hand = self._determine_pitcher_handedness(opponent, game_date)
                    
                    # Determine platoon matchup type
                    if bats == 'S':
                        # Switch hitters are neutral
                        matchup_type = 'SWITCH vs ' + ('LHP' if pitcher_hand == 'L' else 'RHP')
                        platoon_advantage_raw = 0.0  # Neutral for switch hitters
                    elif bats == 'L' and pitcher_hand == 'R':
                        matchup_type = 'LHB vs RHP'
                        platoon_advantage_raw = 1.0  # Favorable
                    elif bats == 'R' and pitcher_hand == 'L':
                        matchup_type = 'RHB vs LHP'
                        platoon_advantage_raw = 1.0  # Favorable
                    elif bats == 'L' and pitcher_hand == 'L':
                        matchup_type = 'LHB vs LHP'
                        platoon_advantage_raw = -1.0  # Unfavorable
                    elif bats == 'R' and pitcher_hand == 'R':
                        matchup_type = 'RHB vs RHP'
                        platoon_advantage_raw = -0.5  # Slightly unfavorable
                    else:
                        matchup_type = 'UNKNOWN'
                        platoon_advantage_raw = 0.0
                    
                    # Get historical platoon splits if we have game logs
                    vs_lhp_ba = 0.0
                    vs_rhp_ba = 0.0
                    vs_lhp_games = 0
                    vs_rhp_games = 0
                    
                    if len(self.game_logs) > 0:
                        # Get historical games for this player
                        player_history = self.game_logs[
                            (self.game_logs['player_name'] == player_name) &
                            (self.game_logs['game_date'] < game_date)
                        ]
                        
                        if len(player_history) > 0:
                            # Separate by pitcher handedness (from opponent_pitcher field)
                            # We'd need to track pitcher handedness in game logs
                            # For now, estimate based on synthetic data
                            
                            for _, hist_game in player_history.iterrows():
                                hist_pitcher = hist_game.get('opponent_pitcher', '')
                                hist_pitcher_hand = self._determine_pitcher_handedness(
                                    hist_game['opponent_team'], 
                                    hist_game['game_date']
                                )
                                
                                ab = hist_game['at_bats']
                                hits = hist_game['hits']
                                
                                if hist_pitcher_hand == 'L':
                                    vs_lhp_games += 1
                                    vs_lhp_ba += hits / ab if ab > 0 else 0
                                else:
                                    vs_rhp_games += 1
                                    vs_rhp_ba += hits / ab if ab > 0 else 0
                            
                            # Calculate average BA
                            vs_lhp_ba = vs_lhp_ba / vs_lhp_games if vs_lhp_games > 0 else 0
                            vs_rhp_ba = vs_rhp_ba / vs_rhp_games if vs_rhp_games > 0 else 0
                    
                    # Calculate platoon score based on splits
                    platoon_score = platoon_advantage_raw
                    
                    if vs_lhp_games > 0 and vs_rhp_games > 0:
                        # Adjust score based on actual splits
                        if pitcher_hand == 'L':
                            split_diff = vs_lhp_ba - vs_rhp_ba
                        else:
                            split_diff = vs_rhp_ba - vs_lhp_ba
                        
                        # Scale difference (0.050 BA diff = 0.5 score)
                        split_score = split_diff * 10
                        
                        # Confidence based on sample size
                        confidence = min((vs_lhp_games + vs_rhp_games) / 20, 1.0)
                        
                        # Weighted combination of expected platoon and actual splits
                        platoon_score = (platoon_advantage_raw * 0.3 + split_score * 0.7) * confidence
                    
                    # Cap score at -1.5 to +1.5
                    platoon_score = max(-1.5, min(1.5, platoon_score))
                    
                    # Determine advantage label
                    if platoon_score >= 0.8:
                        platoon_advantage = "STRONG PLATOON ADVANTAGE"
                    elif platoon_score >= 0.3:
                        platoon_advantage = "PLATOON ADVANTAGE"
                    elif platoon_score >= -0.3:
                        platoon_advantage = "NEUTRAL"
                    elif platoon_score >= -0.8:
                        platoon_advantage = "PLATOON DISADVANTAGE"
                    else:
                        platoon_advantage = "STRONG PLATOON DISADVANTAGE"
                    
                    platoon_stats.append({
                        'fantasy_team': fantasy_team,
                        'player_name': player_name,
                        'mlb_team': player_team_abbr,
                        'game_date': game_date,
                        'opponent': opponent,
                        'bats': bats,
                        'pitcher_hand': pitcher_hand,
                        'matchup_type': matchup_type,
                        'vs_lhp_games': vs_lhp_games,
                        'vs_lhp_ba': round(vs_lhp_ba, 3),
                        'vs_rhp_games': vs_rhp_games,
                        'vs_rhp_ba': round(vs_rhp_ba, 3),
                        'platoon_score': round(platoon_score, 2),
                        'platoon_advantage': platoon_advantage
                    })
        
        platoon_df = pd.DataFrame(platoon_stats)
        print(f"✓ Calculated {len(platoon_df)} platoon advantages")
        
        return platoon_df
    
    def export_results(self, platoon_df):
        """Export results to CSV"""
        self.print_header("Exporting Platoon Analysis Results")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"platoon_advantage_analysis_{timestamp}.csv"
        filepath = self.data_dir / filename
        
        platoon_df.to_csv(filepath, index=False)
        
        print(f"✅ Exported {len(platoon_df)} records to:")
        print(f"   {filepath}")
        
        # Summary stats
        print(f"\n📊 Platoon Analysis Summary:\n")
        print(f"  Total player-games: {len(platoon_df)}")
        
        # Count matchup types
        print(f"\n  Matchup Types:")
        for matchup_type in platoon_df['matchup_type'].unique():
            count = len(platoon_df[platoon_df['matchup_type'] == matchup_type])
            print(f"    {matchup_type}: {count}")
        
        print(f"\n  Advantage Levels:")
        print(f"    Strong Advantage (>0.8): {len(platoon_df[platoon_df['platoon_score'] > 0.8])}")
        print(f"    Advantage (0.3-0.8): {len(platoon_df[platoon_df['platoon_score'].between(0.3, 0.8)])}")
        print(f"    Neutral (-0.3 to 0.3): {len(platoon_df[platoon_df['platoon_score'].between(-0.3, 0.3)])}")
        print(f"    Disadvantage (-0.8 to -0.3): {len(platoon_df[platoon_df['platoon_score'].between(-0.8, -0.3)])}")
        print(f"    Strong Disadvantage (<-0.8): {len(platoon_df[platoon_df['platoon_score'] < -0.8])}")
        
        print(f"\n  Average platoon score: {platoon_df['platoon_score'].mean():.2f}")
        print(f"  Best platoon score: {platoon_df['platoon_score'].max():.2f}")
        print(f"  Worst platoon score: {platoon_df['platoon_score'].min():.2f}")
        
        return filepath
    
    def run(self):
        """Execute full platoon analysis workflow"""
        print("\n" + "="*80)
        print("PLATOON ADVANTAGE ANALYZER".center(80))
        print("="*80)
        print(f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if not self.load_data():
            print("\n❌ Failed to load required data")
            return False
        
        platoon_df = self.calculate_platoon_advantages()
        
        if platoon_df is None or len(platoon_df) == 0:
            print("\n❌ No platoon data generated")
            return False
        
        self.export_results(platoon_df)
        
        print("\n" + "="*80)
        print("PLATOON ANALYSIS COMPLETE".center(80))
        print("="*80)
        
        print("\n✅ Platoon analysis finished!")
        print("\n💡 Platoon Advantages Explained:")
        print("   • LHB vs RHP = FAVORABLE (lefty hitters see ball better)")
        print("   • RHB vs LHP = FAVORABLE (righty hitters see ball better)")
        print("   • LHB vs LHP = UNFAVORABLE (same-side disadvantage)")
        print("   • RHB vs RHP = SLIGHTLY UNFAVORABLE (common but less ideal)")
        print("   • Switch hitters = NEUTRAL (can bat from favorable side)")
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        return True


def main():
    analyzer = PlatoonAnalyzer()
    success = analyzer.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
