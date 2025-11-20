#!/usr/bin/env python3
"""
Run All Players Batch Analysis - OPTIMIZED
Uses 14-day window instead of full season for waiver wire analysis
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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

ANALYSIS_DATE = "2025-09-28"
TIMESTAMP = "20251117_152307"  # Use same timestamp as previous batch
data_dir = Path(__file__).parent.parent.parent.parent / 'data'

print("="*80)
print("WAIVER WIRE BATCH ANALYSIS - OPTIMIZED (14-day window)".center(80))
print("="*80)
print(f"\nAnalysis Date: {ANALYSIS_DATE}")
print(f"Timestamp: {TIMESTAMP}")
print()

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

# Load schedule and filter to 14-day window
schedule_2025 = pd.read_csv(data_dir / "mlb_2025_schedule.csv")
schedule_temp = schedule_2025.copy()
schedule_temp['game_date'] = pd.to_datetime(schedule_temp['game_date'])
analysis_start = as_of_date
analysis_end = as_of_date + timedelta(days=14)
schedule_2025 = schedule_temp[
    (schedule_temp['game_date'] >= analysis_start) &
    (schedule_temp['game_date'] <= analysis_end)
].copy()
schedule_2025['game_date'] = schedule_2025['game_date'].dt.strftime('%Y-%m-%d')

weather = pd.read_csv(data_dir / "mlb_stadium_weather.csv")
players_complete = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
teams = pd.read_csv(data_dir / "mlb_all_teams.csv")

print(f"✓ Loaded {len(roster_df)} active MLB players")
print(f"✓ Filtered schedule to {len(schedule_2025)} games ({analysis_start.date()} to {analysis_end.date()})")
print(f"✓ Loaded weather for {len(weather)} stadiums")

# Batch processing
batch_size = 100
num_batches = (len(roster_df) + batch_size - 1) // batch_size

print(f"\n📦 Processing {len(roster_df)} players in {num_batches} batches of {batch_size}")
print(f"   Estimated time: ~{num_batches * 0.8:.0f} minutes\n")

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
        
        if batch_num % 2 == 1:
            print(f"    [{batch_num + 1}/{num_batches} batches]", end='\r')
    
    if num_batches > 1:
        print(f"    [{num_batches}/{num_batches} batches] ✓")
    
    return pd.concat(all_results, ignore_index=True)

results = {}
start_time = datetime.now()

# Run remaining 15 analyses (skip the 5 already completed)
analyses = [
    (6, "Injury", injury_fa.InjuryFactorAnalyzer, [roster_df, schedule_2025, players_complete]),
    (7, "Platoon", platoon_fa.PlatoonFactorAnalyzer, [roster_df, schedule_2025, players_complete]),
    (8, "Temperature", temperature_fa.TemperatureAnalyzer, [roster_df, schedule_2025, weather]),
    (9, "Pitch Mix", pitch_mix_fa.PitchMixAnalyzer, [roster_df, schedule_2025, players_complete]),
    (10, "Park Factors", park_factors_fa.ParkFactorsAnalyzer, [roster_df, schedule_2025, teams]),
    (11, "Lineup Position", lineup_position_fa.LineupPositionAnalyzer, [roster_df, schedule_2025]),
    (12, "Time of Day", time_of_day_fa.TimeOfDayAnalyzer, [roster_df, schedule_2025, players_complete]),
    (13, "Defensive Positions", defensive_positions_fa.DefensivePositionsFactorAnalyzer, [roster_df, schedule_2025, teams]),
    (14, "Recent Form", recent_form_fa.RecentFormAnalyzer, [roster_df, schedule_2025, players_complete], {"target_date": as_of_date}),
    (15, "Bullpen Fatigue", bullpen_fatigue_fa.BullpenFatigueAnalyzer, [roster_df, schedule_2025, players_complete]),
    (16, "Humidity & Elevation", humidity_elevation_fa.HumidityElevationAnalyzer, [roster_df, schedule_2025, weather]),
    (17, "Monthly Splits", monthly_splits_fa.MonthlySplitsAnalyzer, [roster_df, schedule_2025, players_complete]),
    (18, "Team Momentum", team_momentum_fa.TeamOffensiveMomentumAnalyzer, [roster_df, schedule_2025, teams]),
    (19, "Statcast Metrics", statcast_metrics_fa.StatcastMetricsAnalyzer, [roster_df, schedule_2025, players_complete], {"as_of_date": as_of_date}),
    (20, "Vegas Odds", vegas_odds_fa.VegasOddsAnalyzer, [roster_df, schedule_2025, players_complete], {"as_of_date": as_of_date}),
]

print("Running remaining factor analyses...\n")

for analysis_info in analyses:
    num = analysis_info[0]
    name = analysis_info[1]
    analyzer_class = analysis_info[2]
    args = analysis_info[3]
    kwargs = analysis_info[4] if len(analysis_info) > 4 else {}
    
    print(f"{num}/20 {name} Analysis...")
    try:
        analyzer = analyzer_class(data_dir)
        result_df = process_in_batches(analyzer.analyze_roster, *args, **kwargs)
        
        # Save with same timestamp as previous batch
        file_key = name.lower().replace(' ', '_').replace('&', 'and')
        output_file = data_dir / f"{file_key}_analysis_all_players_{TIMESTAMP}.csv"
        result_df.to_csv(output_file, index=False)
        
        print(f"  ✓ Saved {len(result_df):,} records to {output_file.name}")
        results[name] = output_file
    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()

elapsed = (datetime.now() - start_time).total_seconds()

print(f"\n{'='*80}")
print(f"BATCH COMPLETE: {len(results)}/15 analyses in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
print(f"{'='*80}")

# Check total completion
all_files = list(data_dir.glob(f'*_all_players_{TIMESTAMP}.csv'))
print(f"\nTotal analyses with timestamp {TIMESTAMP}: {len(all_files)}/20")

if len(all_files) >= 20:
    print("\n🎉 ALL 20 ANALYSES COMPLETE!")
    print("   Waiver wire recommendations ready to generate")
else:
    print(f"\n⏳ {20 - len(all_files)} analyses still needed")
