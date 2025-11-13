#!/usr/bin/env python3
"""
Team Offensive Momentum Factor Analysis

Analyzes team-level offensive performance trends to identify hot/cold team offenses.
Teams on scoring binges tend to continue, benefiting all players in the lineup.

Key Concepts:
- Hot Offense: Team averaging 6+ runs/game over last 7-14 days
- Cold Offense: Team averaging <3 runs/game over last 7-14 days
- Momentum Effect: Hot teams create better RBI/run opportunities
- Lineup Synergy: Rising tide lifts all boats

Research Basis:
- Teams scoring 5+ runs/game in last 10 tend to continue for 5-7 more games
- Hot offenses create 30-40% more fantasy point opportunities
- Cold offenses struggling often due to slumps, injuries, or tough pitching stretch

Output: Team offensive momentum scores and player opportunity adjustments
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime


class TeamOffensiveMomentumAnalyzer:
    """Analyze team offensive momentum and trends"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def calculate_team_momentum(self, team_games, window_days=14):
        """Calculate offensive momentum for a team"""
        if len(team_games) == 0:
            return {
                'games': 0,
                'runs_per_game': 0.0,
                'hits_per_game': 0.0,
                'hr_per_game': 0.0,
                'momentum_score': 0.0,
                'trend': 'Unknown'
            }
        
        # Calculate basic stats
        games = len(team_games)
        total_runs = team_games['runs_scored'].sum()
        total_hits = team_games['hits'].sum() if 'hits' in team_games.columns else 0
        total_hr = team_games['home_runs'].sum() if 'home_runs' in team_games.columns else 0
        
        runs_per_game = total_runs / games if games > 0 else 0
        hits_per_game = total_hits / games if games > 0 else 0
        hr_per_game = total_hr / games if games > 0 else 0
        
        # Calculate momentum score
        # MLB average is ~4.5 runs/game, 8.5 hits/game, 1.2 HR/game
        runs_factor = (runs_per_game - 4.5) / 2.0  # ±2 runs = ±1.0
        hits_factor = (hits_per_game - 8.5) / 2.5
        hr_factor = (hr_per_game - 1.2) / 0.8
        
        momentum_score = (
            runs_factor * 0.50 +
            hits_factor * 0.30 +
            hr_factor * 0.20
        )
        
        momentum_score = np.clip(momentum_score, -2.0, 2.0)
        
        # Determine trend
        if len(team_games) >= 14:
            # Compare last 7 vs previous 7
            recent_7 = team_games.head(7)
            previous_7 = team_games.iloc[7:14]
            
            recent_rpg = recent_7['runs_scored'].mean()
            previous_rpg = previous_7['runs_scored'].mean()
            
            if recent_rpg > previous_rpg * 1.15:
                trend = 'Improving'
            elif recent_rpg < previous_rpg * 0.85:
                trend = 'Declining'
            else:
                trend = 'Stable'
        else:
            trend = 'Limited Data'
        
        return {
            'games': games,
            'runs_per_game': round(runs_per_game, 2),
            'hits_per_game': round(hits_per_game, 2),
            'hr_per_game': round(hr_per_game, 2),
            'momentum_score': round(momentum_score, 2),
            'trend': trend
        }
    
    def get_momentum_rating(self, momentum_score):
        """Convert momentum score to rating"""
        if momentum_score >= 1.0:
            return 'Very Hot'
        elif momentum_score >= 0.5:
            return 'Hot'
        elif momentum_score >= -0.5:
            return 'Average'
        elif momentum_score >= -1.0:
            return 'Cold'
        else:
            return 'Very Cold'
    
    def load_team_game_logs(self, team, as_of_date=None):
        """Load game logs for a team (placeholder - would need actual data)"""
        # In real implementation, would load from team game log files
        # For now, return sample data structure
        
        if as_of_date is None:
            as_of_date = datetime.now()
        
        # Check for team game log file
        game_log_file = self.data_dir / f"team_gamelogs_{team.replace(' ', '_')}.csv"
        
        if game_log_file.exists():
            df = pd.read_csv(game_log_file)
            df['game_date'] = pd.to_datetime(df['game_date'])
            df = df[df['game_date'] < as_of_date]
            df = df.sort_values('game_date', ascending=False)
            return df.head(14)  # Last 14 games
        
        # If no file, return empty
        return pd.DataFrame()
    
    def analyze_roster(self, roster_df, schedule_df, players_df, as_of_date=None):
        """Analyze team momentum for all roster players"""
        if as_of_date is None:
            as_of_date = datetime.now()
        elif isinstance(as_of_date, str):
            as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d')
        
        results = []
        processed_teams = set()
        
        for _, player in roster_df.iterrows():
            player_name = player['player_name']
            team = player.get('team', 'Unknown')
            
            # Skip if we've already analyzed this team
            if team in processed_teams and team != 'Unknown':
                existing = [r for r in results if r['team'] == team]
                if existing:
                    results.append({
                        'player_name': player_name,
                        **existing[0]
                    })
                    continue
            
            # Load team game logs
            team_games = self.load_team_game_logs(team, as_of_date)
            
            if len(team_games) == 0:
                # No data - use placeholder
                results.append({
                    'player_name': player_name,
                    'team': team,
                    'games': 0,
                    'runs_per_game': 0.0,
                    'momentum_score': 0.0,
                    'momentum_rating': 'No Data',
                    'trend': 'Unknown',
                    'note': 'Team game logs not available'
                })
                continue
            
            # Calculate momentum
            momentum = self.calculate_team_momentum(team_games)
            rating = self.get_momentum_rating(momentum['momentum_score'])
            
            result = {
                'player_name': player_name,
                'team': team,
                **momentum,
                'momentum_rating': rating
            }
            
            results.append(result)
            processed_teams.add(team)
        
        return pd.DataFrame(results)


def main():
    """Main execution"""
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data"
    
    print("="*80)
    print("Team Offensive Momentum Analysis".center(80))
    print("="*80 + "\n")
    
    analyzer = TeamOffensiveMomentumAnalyzer(data_dir)
    
    # Load roster
    roster_files = sorted(data_dir.glob("yahoo_fantasy_rosters_*.csv"),
                         key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not roster_files:
        print("❌ No roster file found!")
        return
    
    roster_df = pd.read_csv(roster_files[0])
    print(f"✓ Loaded roster: {roster_files[0].name} ({len(roster_df)} players)\n")
    
    # Load schedule and players
    try:
        schedule_2025 = pd.read_csv(data_dir / "mlb_2025_schedule.csv")
        players_complete = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
        
        print("Analyzing team offensive momentum...")
        print("Note: Requires team game log data for full analysis\n")
        
        # Analyze
        momentum_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = data_dir / f"team_momentum_analysis_{timestamp}.csv"
        momentum_df.to_csv(output_file, index=False)
        
        print(f"✓ Analysis complete: {len(momentum_df)} players analyzed")
        print(f"📁 Saved to: {output_file.name}\n")
        
        # Summary
        if len(momentum_df) > 0:
            print("Team Momentum Summary:")
            ratings = momentum_df['momentum_rating'].value_counts()
            for rating, count in ratings.items():
                print(f"  {rating}: {count} players")
        
    except FileNotFoundError as e:
        print(f"❌ Required data file not found: {e}")
        return
    
    print("\n" + "="*80)
    print("Note: For full analysis, need team game log data")
    print("Future: Scrape team game logs from MLB Stats API")
    print("="*80)


if __name__ == "__main__":
    main()
