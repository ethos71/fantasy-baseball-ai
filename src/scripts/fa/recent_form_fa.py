#!/usr/bin/env python3
"""
Recent Form / Streaks Factor Analysis

Analyzes player recent performance trends (hot/cold streaks) to predict future performance.
Players on hot streaks tend to continue performing well, while cold streaks indicate struggles.

Key Concepts:
- Hot Streak: 5+ consecutive games with a hit, or exceptional recent performance
- Cold Streak: Extended period of poor performance (0-for-10+)
- Rolling Averages: Last 7/14/30 day performance trends
- Form Score: Composite score of recent performance vs. season average

Output:
- Recent performance metrics (7/14/30 day windows)
- Streak detection (hot/cold)
- Form score (-1.0 to +1.0)
- Trend direction (improving/declining)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


class RecentFormAnalyzer:
    """Analyze player recent form and streaks"""
    
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
    
    def calculate_rolling_stats(self, player_stats, window_days):
        """Calculate rolling statistics for a time window"""
        if len(player_stats) == 0:
            return {
                'games': 0,
                'avg': 0.0,
                'obp': 0.0,
                'slg': 0.0,
                'ops': 0.0,
                'hr': 0,
                'rbi': 0,
                'runs': 0,
                'sb': 0
            }
        
        # Calculate basic stats
        total_ab = player_stats['AB'].sum()
        total_h = player_stats['H'].sum()
        total_bb = player_stats['BB'].sum()
        total_hbp = player_stats['HBP'].sum() if 'HBP' in player_stats.columns else 0
        total_sf = player_stats['SF'].sum() if 'SF' in player_stats.columns else 0
        
        # Calculate AVG
        avg = total_h / total_ab if total_ab > 0 else 0.0
        
        # Calculate OBP
        pa = total_ab + total_bb + total_hbp + total_sf
        obp = (total_h + total_bb + total_hbp) / pa if pa > 0 else 0.0
        
        # Calculate SLG (simplified - would need singles, doubles, triples, HR breakdown)
        total_tb = (
            player_stats['1B'].sum() if '1B' in player_stats.columns else 0 +
            player_stats['2B'].sum() * 2 if '2B' in player_stats.columns else 0 +
            player_stats['3B'].sum() * 3 if '3B' in player_stats.columns else 0 +
            player_stats['HR'].sum() * 4
        )
        slg = total_tb / total_ab if total_ab > 0 else 0.0
        
        return {
            'games': len(player_stats),
            'avg': round(avg, 3),
            'obp': round(obp, 3),
            'slg': round(slg, 3),
            'ops': round(obp + slg, 3),
            'hr': int(player_stats['HR'].sum()) if 'HR' in player_stats.columns else 0,
            'rbi': int(player_stats['RBI'].sum()) if 'RBI' in player_stats.columns else 0,
            'runs': int(player_stats['R'].sum()) if 'R' in player_stats.columns else 0,
            'sb': int(player_stats['SB'].sum()) if 'SB' in player_stats.columns else 0
        }
    
    def detect_hot_streak(self, recent_games):
        """Detect if player is on a hot streak"""
        if len(recent_games) < 5:
            return False, 0
        
        # Check last 5-10 games for hitting streak
        last_10 = recent_games.head(10)
        
        # Hot streak criteria:
        # 1. Hit in 5+ consecutive games, OR
        # 2. Batting .350+ over last 7 games with 20+ ABs
        
        consecutive_hits = 0
        max_streak = 0
        
        for _, game in last_10.iterrows():
            if game.get('H', 0) > 0:
                consecutive_hits += 1
                max_streak = max(max_streak, consecutive_hits)
            else:
                consecutive_hits = 0
        
        # Check batting average hot streak
        last_7 = recent_games.head(7)
        total_ab = last_7['AB'].sum() if 'AB' in last_7.columns else 0
        total_h = last_7['H'].sum() if 'H' in last_7.columns else 0
        recent_avg = total_h / total_ab if total_ab >= 20 else 0
        
        is_hot = max_streak >= 5 or (recent_avg >= 0.350 and total_ab >= 20)
        
        return is_hot, max_streak
    
    def detect_cold_streak(self, recent_games):
        """Detect if player is in a slump"""
        if len(recent_games) < 5:
            return False, 0
        
        # Cold streak criteria:
        # 1. 0-for-10 or worse in recent ABs, OR
        # 2. Batting under .150 in last 7 games with 20+ ABs
        
        # Check hitless at-bats
        recent_abs = []
        for _, game in recent_games.head(15).iterrows():
            ab = game.get('AB', 0)
            h = game.get('H', 0)
            if ab > 0:
                recent_abs.extend([1 if i < h else 0 for i in range(ab)])
        
        # Count consecutive hitless ABs
        consecutive_outs = 0
        max_slump = 0
        for ab in recent_abs:
            if ab == 0:
                consecutive_outs += 1
                max_slump = max(max_slump, consecutive_outs)
            else:
                consecutive_outs = 0
        
        # Check batting average slump
        last_7 = recent_games.head(7)
        total_ab = last_7['AB'].sum() if 'AB' in last_7.columns else 0
        total_h = last_7['H'].sum() if 'H' in last_7.columns else 0
        recent_avg = total_h / total_ab if total_ab >= 20 else 0.300  # Assume average if small sample
        
        is_cold = max_slump >= 10 or (recent_avg < 0.150 and total_ab >= 20)
        
        return is_cold, max_slump
    
    def calculate_form_score(self, recent_stats, season_stats):
        """Calculate form score comparing recent performance to season average"""
        # Compare recent OPS to season OPS
        recent_ops = recent_stats.get('ops', 0.700)
        season_ops = season_stats.get('ops', 0.700)
        
        if season_ops == 0:
            return 0.0
        
        # Calculate percentage difference
        ops_diff = (recent_ops - season_ops) / season_ops
        
        # Scale to -1.0 to +1.0 range
        # +50% or more = 1.0 (very hot)
        # -50% or more = -1.0 (very cold)
        form_score = np.clip(ops_diff / 0.5, -1.0, 1.0)
        
        return round(form_score, 2)
    
    def analyze_player_form(self, player_name, player_stats_df, as_of_date=None):
        """Analyze recent form for a single player"""
        if as_of_date is None:
            as_of_date = datetime.now()
        
        # Filter to games before as_of_date
        player_stats_df['game_date'] = pd.to_datetime(player_stats_df['game_date'])
        recent_games = player_stats_df[player_stats_df['game_date'] < as_of_date].copy()
        recent_games = recent_games.sort_values('game_date', ascending=False)
        
        if len(recent_games) == 0:
            return None
        
        # Calculate rolling windows
        cutoff_7 = as_of_date - timedelta(days=7)
        cutoff_14 = as_of_date - timedelta(days=14)
        cutoff_30 = as_of_date - timedelta(days=30)
        
        last_7_days = recent_games[recent_games['game_date'] >= cutoff_7]
        last_14_days = recent_games[recent_games['game_date'] >= cutoff_14]
        last_30_days = recent_games[recent_games['game_date'] >= cutoff_30]
        
        stats_7 = self.calculate_rolling_stats(last_7_days, 7)
        stats_14 = self.calculate_rolling_stats(last_14_days, 14)
        stats_30 = self.calculate_rolling_stats(last_30_days, 30)
        season_stats = self.calculate_rolling_stats(recent_games, 365)
        
        # Detect streaks
        is_hot, hit_streak = self.detect_hot_streak(recent_games)
        is_cold, slump_length = self.detect_cold_streak(recent_games)
        
        # Calculate form score
        form_score = self.calculate_form_score(stats_7, season_stats)
        
        # Determine trend
        if stats_7['ops'] > stats_14['ops'] > stats_30['ops']:
            trend = 'improving'
        elif stats_7['ops'] < stats_14['ops'] < stats_30['ops']:
            trend = 'declining'
        else:
            trend = 'stable'
        
        return {
            'player_name': player_name,
            'as_of_date': as_of_date.strftime('%Y-%m-%d'),
            
            # 7-day stats
            'last_7_games': stats_7['games'],
            'last_7_avg': stats_7['avg'],
            'last_7_ops': stats_7['ops'],
            'last_7_hr': stats_7['hr'],
            
            # 14-day stats
            'last_14_games': stats_14['games'],
            'last_14_avg': stats_14['avg'],
            'last_14_ops': stats_14['ops'],
            
            # 30-day stats
            'last_30_games': stats_30['games'],
            'last_30_avg': stats_30['avg'],
            'last_30_ops': stats_30['ops'],
            
            # Season baseline
            'season_avg': season_stats['avg'],
            'season_ops': season_stats['ops'],
            
            # Streaks
            'is_hot_streak': is_hot,
            'hit_streak_length': hit_streak,
            'is_cold_streak': is_cold,
            'slump_length': slump_length,
            
            # Form analysis
            'form_score': form_score,
            'trend': trend,
            
            # Overall assessment
            'form_rating': self.get_form_rating(form_score, is_hot, is_cold)
        }
    
    def get_form_rating(self, form_score, is_hot, is_cold):
        """Get textual rating of current form"""
        if is_hot or form_score >= 0.5:
            return 'Very Hot'
        elif form_score >= 0.2:
            return 'Hot'
        elif form_score >= -0.2:
            return 'Average'
        elif is_cold or form_score <= -0.5:
            return 'Very Cold'
        else:
            return 'Cold'
    
    def analyze_roster(self, roster_df, schedule_df, players_df, target_date=None):
        """Analyze recent form for all players on roster"""
        if target_date is None:
            target_date = datetime.now()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, '%Y-%m-%d')
        
        # Load game logs
        game_log_file = self.data_dir / "mlb_game_logs_2024.csv"
        
        if not game_log_file.exists():
            print(f"⚠️  Game log file not found: {game_log_file.name}")
            print("   Run: python src/scripts/scrape/gamelog_scrape.py")
            print("   Using placeholder data for now...\n")
            
            # Return placeholder results
            results = []
            for _, player in roster_df.iterrows():
                results.append({
                    'player_name': player['player_name'],
                    'as_of_date': target_date.strftime('%Y-%m-%d'),
                    'last_7_avg': 0.0,
                    'last_14_avg': 0.0,
                    'last_30_avg': 0.0,
                    'form_score': 0.0,
                    'form_rating': 'No Data',
                    'note': 'Run gamelog_scrape.py to get data'
                })
            return pd.DataFrame(results)
        
        # Load game logs
        print(f"Loading game logs from {game_log_file.name}...")
        game_logs_df = pd.read_csv(game_log_file)
        game_logs_df['game_date'] = pd.to_datetime(game_logs_df['game_date'])
        
        results = []
        
        for _, player in roster_df.iterrows():
            player_name = player['player_name']
            
            # Get player's game log
            player_games = game_logs_df[game_logs_df['player_name'] == player_name].copy()
            
            if len(player_games) == 0:
                print(f"  {player_name}: No game log data found")
                results.append({
                    'player_name': player_name,
                    'as_of_date': target_date.strftime('%Y-%m-%d'),
                    'last_7_avg': 0.0,
                    'form_score': 0.0,
                    'form_rating': 'No Data'
                })
                continue
            
            # Analyze player form
            form_data = self.analyze_player_form(player_name, player_games, target_date)
            
            if form_data:
                results.append(form_data)
        
        return pd.DataFrame(results)


def main():
    """Main execution"""
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    print("="*80)
    print("Recent Form / Streaks Analysis".center(80))
    print("="*80 + "\n")
    
    analyzer = RecentFormAnalyzer(data_dir)
    
    # Load roster
    roster_files = sorted(data_dir.glob("yahoo_fantasy_rosters_*.csv"),
                         key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not roster_files:
        print("❌ No roster file found!")
        return
    
    roster_df = pd.read_csv(roster_files[0])
    print(f"✓ Loaded roster: {roster_files[0].name} ({len(roster_df)} players)\n")
    
    # Load schedule and players
    schedule_2025 = pd.read_csv(data_dir / "mlb_2025_schedule.csv")
    players_complete = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
    
    print("Analyzing recent form for roster players...")
    print("Note: Need individual game log data for full analysis\n")
    
    # Analyze roster
    form_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = data_dir / f"recent_form_analysis_{timestamp}.csv"
    form_df.to_csv(output_file, index=False)
    
    print("✓ Analysis complete")
    print(f"📁 Saved to: {output_file.name}\n")
    
    print("="*80)
    print("Note: This is a framework. Need MLB game log data for full implementation.")
    print("Game logs available via MLB Stats API: /api/v1/people/{playerId}/stats")
    print("="*80)


if __name__ == "__main__":
    main()
