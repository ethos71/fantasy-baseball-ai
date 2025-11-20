#!/usr/bin/env python3
"""
Resume Waiver Wire Batch Analysis

Resumes the all-players analysis from where it left off.
Uses the existing timestamp: 20251117_152307
Skips already completed analyses.
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scripts.fa import (
    injury_fa,
    platoon_fa,
    temperature_fa,
    pitch_mix_fa,
    park_factors_fa,
    lineup_position_fa,
    time_of_day_fa,
    defensive_positions_fa,
    recent_form_fa,
    bullpen_fatigue_fa,
    humidity_elevation_fa,
    monthly_splits_fa,
    team_momentum_fa,
    statcast_metrics_fa,
    vegas_odds_fa
)

# Use the existing timestamp to keep files together
RESUME_TIMESTAMP = "20251117_152307"
ANALYSIS_DATE = "2025-09-28"

data_dir = Path(__file__).parent / 'data'

# Completed analyses (skip these)
COMPLETED = ['wind', 'matchup', 'home_away', 'rest_day', 'umpire']

print("="*80)
print("Resuming Waiver Wire Batch Analysis".center(80))
print("="*80)
print(f"\nTimestamp: {RESUME_TIMESTAMP}")
print(f"Analysis Date: {ANALYSIS_DATE}")
print(f"Skipping completed: {', '.join(COMPLETED)}\n")

# Load data
print("Loading data files...")
as_of_date = datetime.strptime(ANALYSIS_DATE, "%Y-%m-%d")

roster_df = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
current_season = as_of_date.year
if 'season' in roster_df.columns:
    roster_df = roster_df[roster_df['season'] == current_season]

# Normalize columns
if 'team_name' in roster_df.columns:
    roster_df['team'] = roster_df['team_name']
    roster_df['mlb_team'] = roster_df['team_name']

schedule_2025 = pd.read_csv(data_dir / "mlb_2025_schedule.csv")
weather = pd.read_csv(data_dir / "mlb_stadium_weather.csv")
players_complete = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
teams = pd.read_csv(data_dir / "mlb_all_teams.csv")

print(f"✓ Loaded {len(roster_df)} active MLB players")
print(f"✓ Loaded {len(schedule_2025)} games from 2025 schedule")
print(f"✓ Loaded weather for {len(weather)} stadiums")

# Batch processing
batch_size = 100
num_batches = (len(roster_df) + batch_size - 1) // batch_size

print(f"\n📦 Processing {len(roster_df)} players in {num_batches} batches of {batch_size}")
print(f"   Estimated time: {(num_batches * 15) // 60} hours\n")

def process_in_batches(analyzer_func, *args, **kwargs):
    """Process roster in batches and combine results"""
    if num_batches == 1:
        return analyzer_func(*args, **kwargs)
    
    all_results = []
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, len(roster_df))
        batch_roster = roster_df.iloc[start_idx:end_idx].copy()
        
        # Replace first positional argument (roster_df) with batch
        new_args = list(args)
        new_args[0] = batch_roster
        
        batch_result = analyzer_func(*new_args, **kwargs)
        all_results.append(batch_result)
        
        if batch_num % 5 == 4:
            print(f"    [{batch_num + 1}/{num_batches} batches]", end='\r')
    
    if num_batches > 1:
        print(f"    [{num_batches}/{num_batches} batches] ✓")
    
    return pd.concat(all_results, ignore_index=True)

results = {}

# Resume from #6 (Injury was #5 but failed, so retry it)
print("5/20 Injury/Recovery Analysis (RETRY - FIXED)...")
try:
    analyzer = injury_fa.InjuryFactorAnalyzer(data_dir)
    injury_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
    output_file = data_dir / f"injury_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    injury_df.to_csv(output_file, index=False)
    results['injury'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    print("  Skipping and continuing...")

# 7. Platoon Analysis
print("7/20 Platoon Advantage Analysis (FIXED)...")
try:
    analyzer = platoon_fa.PlatoonFactorAnalyzer(data_dir)
    platoon_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
    output_file = data_dir / f"platoon_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    platoon_df.to_csv(output_file, index=False)
    results['platoon'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 8. Temperature Analysis
print("8/20 Temperature Analysis...")
try:
    analyzer = temperature_fa.TemperatureAnalyzer(data_dir)
    temp_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, weather)
    output_file = data_dir / f"temperature_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    temp_df.to_csv(output_file, index=False)
    results['temperature'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 9. Pitch Mix Analysis
print("9/20 Pitch Mix Analysis...")
try:
    analyzer = pitch_mix_fa.PitchMixAnalyzer(data_dir)
    pitch_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
    output_file = data_dir / f"pitch_mix_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    pitch_df.to_csv(output_file, index=False)
    results['pitch_mix'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 10. Park Factors Analysis
print("10/20 Park Factors Analysis...")
try:
    analyzer = park_factors_fa.ParkFactorsAnalyzer(data_dir)
    park_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, teams)
    output_file = data_dir / f"park_factors_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    park_df.to_csv(output_file, index=False)
    results['park'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 11. Lineup Position Analysis
print("11/20 Lineup Position Analysis...")
try:
    analyzer = lineup_position_fa.LineupPositionAnalyzer(data_dir)
    lineup_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025)
    output_file = data_dir / f"lineup_position_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    lineup_df.to_csv(output_file, index=False)
    results['lineup'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 12. Time of Day Analysis
print("12/20 Time of Day Analysis...")
try:
    analyzer = time_of_day_fa.TimeOfDayAnalyzer(data_dir)
    time_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
    output_file = data_dir / f"time_of_day_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    time_df.to_csv(output_file, index=False)
    results['time'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 13. Defensive Positions Analysis
print("13/20 Defensive Positions Analysis...")
try:
    analyzer = defensive_positions_fa.DefensivePositionsFactorAnalyzer(data_dir)
    defense_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, teams)
    output_file = data_dir / f"defensive_positions_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    defense_df.to_csv(output_file, index=False)
    results['defense'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 14. Recent Form / Streaks Analysis
print("14/20 Recent Form / Streaks Analysis...")
try:
    analyzer = recent_form_fa.RecentFormAnalyzer(data_dir)
    form_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete, target_date=as_of_date)
    output_file = data_dir / f"recent_form_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    form_df.to_csv(output_file, index=False)
    results['recent_form'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 15. Bullpen Fatigue Analysis
print("15/20 Bullpen Fatigue Detection...")
try:
    analyzer = bullpen_fatigue_fa.BullpenFatigueAnalyzer(data_dir)
    bullpen_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
    output_file = data_dir / f"bullpen_fatigue_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    bullpen_df.to_csv(output_file, index=False)
    results['bullpen'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 16. Humidity & Elevation Analysis
print("16/20 Humidity & Elevation Analysis...")
try:
    analyzer = humidity_elevation_fa.HumidityElevationAnalyzer(data_dir)
    humidity_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, weather)
    output_file = data_dir / f"humidity_elevation_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    humidity_df.to_csv(output_file, index=False)
    results['humidity'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 17. Monthly Splits Analysis
print("17/20 Monthly Splits Analysis...")
try:
    analyzer = monthly_splits_fa.MonthlySplitsAnalyzer(data_dir)
    monthly_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
    output_file = data_dir / f"monthly_splits_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    monthly_df.to_csv(output_file, index=False)
    results['monthly'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 18. Team Momentum Analysis
print("18/20 Team Momentum Analysis...")
try:
    analyzer = team_momentum_fa.TeamOffensiveMomentumAnalyzer(data_dir)
    momentum_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, teams)
    output_file = data_dir / f"team_momentum_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    momentum_df.to_csv(output_file, index=False)
    results['momentum'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 19. Statcast Metrics Analysis
print("19/20 Statcast Metrics Analysis...")
try:
    analyzer = statcast_metrics_fa.StatcastMetricsAnalyzer(data_dir)
    statcast_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete, as_of_date=as_of_date)
    output_file = data_dir / f"statcast_metrics_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    statcast_df.to_csv(output_file, index=False)
    results['statcast'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

# 20. Vegas Odds Analysis
print("20/20 Vegas Odds Analysis...")
try:
    analyzer = vegas_odds_fa.VegasOddsAnalyzer(data_dir)
    vegas_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete, as_of_date=as_of_date)
    output_file = data_dir / f"vegas_odds_analysis_all_players_{RESUME_TIMESTAMP}.csv"
    vegas_df.to_csv(output_file, index=False)
    results['vegas'] = output_file
    print(f"  ✓ Saved to {output_file.name}")
except Exception as e:
    print(f"  ✗ Error: {e}")

print(f"\n✓ Resume completed: {len(results)}/15 additional analyses")
print(f"✓ Total analyses with timestamp {RESUME_TIMESTAMP}: {5 + len(results)}/20")
