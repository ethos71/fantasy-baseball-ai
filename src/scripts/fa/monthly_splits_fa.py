#!/usr/bin/env python3
"""
Monthly/Seasonal Splits Factor Analysis

Analyzes player performance by month and season to identify trends.
Some players are "April players" (hot early), others peak in summer or September.

Key Concepts:
- Monthly Patterns: Performance varies by month (weather, routine, sample size)
- Career Splits: 4 years of data reveals consistent monthly tendencies
- Day/Night Splits by Month: Some players hit better in night games in summer
- Weather Correlation: April = cold, August = hot, affects certain players

Research Basis:
- ~20% of players show significant monthly performance variance (>50 OPS points)
- "Slow starters" hit .230 in April, .280+ May-Sept
- "September surges" common for players fighting for contracts/playoffs
- Sample size matters: Need 3+ seasons to trust monthly splits

Output: Monthly performance profiles and current month adjustment scores
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import calendar


class MonthlySplitsAnalyzer:
    """Analyze player monthly and seasonal performance splits"""
    
    MONTHS = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def calculate_monthly_stats(self, player_games, month):
        """Calculate stats for a specific month"""
        month_games = player_games[player_games['game_date'].dt.month == month]
        
        if len(month_games) == 0:
            return {
                'games': 0,
                'avg': 0.0,
                'obp': 0.0,
                'slg': 0.0,
                'ops': 0.0,
                'hr': 0,
                'rbi': 0
            }
        
        # Calculate stats
        total_ab = month_games['AB'].sum()
        total_h = month_games['H'].sum()
        total_bb = month_games['BB'].sum() if 'BB' in month_games.columns else 0
        total_hr = month_games['HR'].sum() if 'HR' in month_games.columns else 0
        total_rbi = month_games['RBI'].sum() if 'RBI' in month_games.columns else 0
        
        avg = total_h / total_ab if total_ab > 0 else 0.0
        
        # Simplified OBP/SLG (would need more detailed stats)
        obp = (total_h + total_bb) / (total_ab + total_bb) if (total_ab + total_bb) > 0 else 0.0
        
        # Rough SLG estimate
        singles = total_h - (month_games['2B'].sum() if '2B' in month_games.columns else 0) - \
                  (month_games['3B'].sum() if '3B' in month_games.columns else 0) - total_hr
        total_bases = singles + (month_games['2B'].sum() if '2B' in month_games.columns else 0) * 2 + \
                     (month_games['3B'].sum() if '3B' in month_games.columns else 0) * 3 + total_hr * 4
        slg = total_bases / total_ab if total_ab > 0 else 0.0
        
        return {
            'games': len(month_games) if len(month_games) > 0 else 0,
            'avg': round(avg, 3) if len(month_games) > 0 else 0.0,
            'obp': round(obp, 3) if len(month_games) > 0 else 0.0,
            'slg': round(slg, 3) if len(month_games) > 0 else 0.0,
            'ops': round(obp + slg, 3) if len(month_games) > 0 else 0.0,
            'hr': int(total_hr) if len(month_games) > 0 else 0,
            'rbi': int(total_rbi) if len(month_games) > 0 else 0
        }
    
    def analyze_player_monthly_profile(self, player_name, player_games):
        """Analyze player's career monthly performance"""
        if len(player_games) == 0:
            return None
        
        # Ensure datetime
        player_games['game_date'] = pd.to_datetime(player_games['game_date'])
        
        # Calculate stats for each month
        monthly_stats = {}
        season_stats = self.calculate_monthly_stats(
            player_games, 
            month=None  # Will use all months
        )
        
        # Baseball season: April (4) through September (9), sometimes Oct (10)
        baseball_months = [4, 5, 6, 7, 8, 9, 10]
        
        for month in baseball_months:
            monthly_stats[month] = self.calculate_monthly_stats(player_games, month)
        
        # Find best and worst months (min 10 games)
        valid_months = {m: s for m, s in monthly_stats.items() if s['games'] >= 10}
        
        if valid_months:
            best_month = max(valid_months.items(), key=lambda x: x[1]['ops'])
            worst_month = min(valid_months.items(), key=lambda x: x[1]['ops'])
        else:
            best_month = (0, {'ops': 0})
            worst_month = (0, {'ops': 0})
        
        # Calculate current month advantage
        current_month = datetime.now().month
        current_stats = monthly_stats.get(current_month, {
            'games': 0, 'avg': 0.0, 'obp': 0.0, 'slg': 0.0, 'ops': 0.700, 'hr': 0, 'rbi': 0
        })
        
        if current_stats['games'] >= 10:
            # Compare to season average
            season_ops = season_stats['ops'] if season_stats['ops'] > 0 else 0.700
            ops_diff = current_stats['ops'] - season_ops
            
            # Scale to -1.0 to +1.0
            month_score = np.clip(ops_diff / 0.150, -1.0, 1.0)  # ±150 OPS points = ±1.0
        else:
            month_score = 0.0  # Insufficient data
        
        return {
            'player_name': player_name,
            'season_avg': season_stats.get('avg', 0.0),
            'season_ops': season_stats.get('ops', 0.0),
            'best_month': self.MONTHS.get(best_month[0], 'Unknown'),
            'best_month_ops': best_month[1].get('ops', 0.0),
            'worst_month': self.MONTHS.get(worst_month[0], 'Unknown'),
            'worst_month_ops': worst_month[1].get('ops', 0.0),
            'current_month': self.MONTHS.get(current_month, 'Unknown'),
            'current_month_avg': current_stats.get('avg', 0.0),
            'current_month_ops': current_stats.get('ops', 0.0),
            'current_month_games': current_stats.get('games', 0),
            'month_score': round(month_score, 2),
            'monthly_pattern': self.classify_monthly_pattern(monthly_stats)
        }
    
    def classify_monthly_pattern(self, monthly_stats):
        """Classify player's monthly performance pattern"""
        # Extract OPS by month (where games >= 10)
        valid = {m: s['ops'] for m, s in monthly_stats.items() if s['games'] >= 10}
        
        if len(valid) < 3:
            return 'Insufficient Data'
        
        # Check for patterns
        early_season = np.mean([valid.get(m, 0) for m in [4, 5] if m in valid]) if any(m in valid for m in [4, 5]) else 0
        mid_season = np.mean([valid.get(m, 0) for m in [6, 7] if m in valid]) if any(m in valid for m in [6, 7]) else 0
        late_season = np.mean([valid.get(m, 0) for m in [8, 9] if m in valid]) if any(m in valid for m in [8, 9]) else 0
        
        if early_season > mid_season and early_season > late_season and early_season > 0:
            return 'Hot Starter'
        elif late_season > early_season and late_season > mid_season and late_season > 0:
            return 'September Surge'
        elif mid_season > early_season and mid_season > late_season and mid_season > 0:
            return 'Summer Peak'
        else:
            return 'Consistent'
    
    def analyze_roster(self, roster_df, schedule_df, players_df, as_of_date=None):
        """Analyze monthly splits for all roster players"""
        if as_of_date is None:
            as_of_date = datetime.now()
        elif isinstance(as_of_date, str):
            as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d')
        
        # Load game logs
        game_log_file = self.data_dir / "mlb_game_logs_2024.csv"
        
        if not game_log_file.exists():
            print(f"⚠️  Game log file not found: {game_log_file.name}")
            print("   Need player game logs for monthly split analysis")
            print("   Run: python src/scripts/scrape/gamelog_scrape.py\n")
            
            # Return placeholder
            results = []
            for _, player in roster_df.iterrows():
                results.append({
                    'player_name': player['player_name'],
                    'season_ops': 0.0,
                    'current_month': self.MONTHS[datetime.now().month],
                    'current_month_ops': 0.0,
                    'month_score': 0.0,
                    'monthly_pattern': 'No Data',
                    'note': 'Need game log data'
                })
            return pd.DataFrame(results)
        
        # Load game logs
        print(f"Loading game logs from {game_log_file.name}...")
        game_logs_df = pd.read_csv(game_log_file)
        game_logs_df['game_date'] = pd.to_datetime(game_logs_df['game_date'])
        
        results = []
        
        for _, player in roster_df.iterrows():
            player_name = player['player_name']
            
            # Get player's games
            player_games = game_logs_df[game_logs_df['player_name'] == player_name].copy()
            
            if len(player_games) == 0:
                print(f"  {player_name}: No game log data")
                results.append({
                    'player_name': player_name,
                    'season_ops': 0.0,
                    'current_month': self.MONTHS[datetime.now().month],
                    'month_score': 0.0,
                    'monthly_pattern': 'No Data'
                })
                continue
            
            # Analyze monthly profile
            profile = self.analyze_player_monthly_profile(player_name, player_games)
            
            if profile:
                results.append(profile)
                print(f"  {player_name}: {profile['monthly_pattern']}, "
                      f"Best={profile['best_month']} ({profile['best_month_ops']:.3f})")
        
        return pd.DataFrame(results)


def main():
    """Main execution"""
    project_root = Path(__file__).parent.parent.parent.parent
    data_dir = project_root / "data"
    
    print("="*80)
    print("Monthly/Seasonal Splits Analysis".center(80))
    print("="*80 + "\n")
    
    analyzer = MonthlySplitsAnalyzer(data_dir)
    
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
        
        print("Analyzing monthly performance splits...\n")
        
        # Analyze
        splits_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
        
        # Save
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = data_dir / f"monthly_splits_analysis_{timestamp}.csv"
        splits_df.to_csv(output_file, index=False)
        
        print(f"\n✓ Analysis complete: {len(splits_df)} players analyzed")
        print(f"📁 Saved to: {output_file.name}\n")
        
        # Summary
        if len(splits_df) > 0 and 'monthly_pattern' in splits_df.columns:
            print("Monthly Pattern Summary:")
            patterns = splits_df['monthly_pattern'].value_counts()
            for pattern, count in patterns.items():
                print(f"  {pattern}: {count} players")
        
    except FileNotFoundError as e:
        print(f"❌ Required data file not found: {e}")
        return
    
    print("\n" + "="*80)
    print("Analysis complete!")
    print("="*80)


if __name__ == "__main__":
    main()
