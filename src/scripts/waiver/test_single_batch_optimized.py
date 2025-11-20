#!/usr/bin/env python3
"""
Test Single Batch - Optimized version with 100 players
Tests all 20 factor analyses on a single batch to verify they work
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.fa import (
    wind_analysis,
    matchup_fa,
    home_away_fa,
    rest_day_fa,
    injury_fa,
    umpire_fa,
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
data_dir = Path(__file__).parent.parent.parent.parent / 'data'

print("="*80)
print("Single Batch Test - 100 Players (Optimized)".center(80))
print("="*80)
print(f"\nAnalysis Date: {ANALYSIS_DATE}\n")

# Load data
print("Loading data files...")
as_of_date = datetime.strptime(ANALYSIS_DATE, "%Y-%m-%d")

roster_df = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
current_season = as_of_date.year
if 'season' in roster_df.columns:
    roster_df = roster_df[roster_df['season'] == current_season]

# Take first 100 players only
roster_df = roster_df.head(100)

# Normalize columns
if 'team_name' in roster_df.columns:
    roster_df['team'] = roster_df['team_name']
    roster_df['mlb_team'] = roster_df['team_name']

schedule_2025 = pd.read_csv(data_dir / "mlb_2025_schedule.csv")

# For waiver wire analysis, we only need upcoming games (next 7-14 days)
# Filter to a manageable date range around the analysis date
schedule_temp = schedule_2025.copy()
schedule_temp['game_date'] = pd.to_datetime(schedule_temp['game_date'])
analysis_start = as_of_date
analysis_end = as_of_date + pd.Timedelta(days=14)
schedule_2025 = schedule_temp[
    (schedule_temp['game_date'] >= analysis_start) &
    (schedule_temp['game_date'] <= analysis_end)
].copy()
# Convert back to string format for the analyses
schedule_2025['game_date'] = schedule_2025['game_date'].dt.strftime('%Y-%m-%d')

weather = pd.read_csv(data_dir / "mlb_stadium_weather.csv")
players_complete = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
teams = pd.read_csv(data_dir / "mlb_all_teams.csv")

print(f"✓ Testing with {len(roster_df)} players")
print(f"✓ Loaded {len(schedule_2025)} games from analysis window ({analysis_start.date()} to {analysis_end.date()})")
print(f"✓ Loaded weather for {len(weather)} stadiums\n")

results = {}
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

analyses = [
    ("Wind", wind_analysis.WindAnalyzer, [roster_df, schedule_2025, weather]),
    ("Matchup", matchup_fa.MatchupFactorAnalyzer, [roster_df, schedule_2025, players_complete]),
    ("Home/Away", home_away_fa.HomeAwayFactorAnalyzer, [roster_df, schedule_2025, players_complete]),
    ("Rest Day", rest_day_fa.RestDayFactorAnalyzer, [roster_df, schedule_2025]),
    ("Injury", injury_fa.InjuryFactorAnalyzer, [roster_df, schedule_2025, players_complete]),
    ("Umpire", umpire_fa.UmpireFactorAnalyzer, [roster_df, schedule_2025]),
    ("Platoon", platoon_fa.PlatoonFactorAnalyzer, [roster_df, schedule_2025, players_complete]),
    ("Temperature", temperature_fa.TemperatureAnalyzer, [roster_df, schedule_2025, weather]),
    ("Pitch Mix", pitch_mix_fa.PitchMixAnalyzer, [roster_df, schedule_2025, players_complete]),
    ("Park Factors", park_factors_fa.ParkFactorsAnalyzer, [roster_df, schedule_2025, teams]),
    ("Lineup Position", lineup_position_fa.LineupPositionAnalyzer, [roster_df, schedule_2025]),
    ("Time of Day", time_of_day_fa.TimeOfDayAnalyzer, [roster_df, schedule_2025, players_complete]),
    ("Defensive Positions", defensive_positions_fa.DefensivePositionsFactorAnalyzer, [roster_df, schedule_2025, teams]),
    ("Recent Form", recent_form_fa.RecentFormAnalyzer, [roster_df, schedule_2025, players_complete], {"target_date": as_of_date}),
    ("Bullpen Fatigue", bullpen_fatigue_fa.BullpenFatigueAnalyzer, [roster_df, schedule_2025, players_complete]),
    ("Humidity & Elevation", humidity_elevation_fa.HumidityElevationAnalyzer, [roster_df, schedule_2025, weather]),
    ("Monthly Splits", monthly_splits_fa.MonthlySplitsAnalyzer, [roster_df, schedule_2025, players_complete]),
    ("Team Momentum", team_momentum_fa.TeamOffensiveMomentumAnalyzer, [roster_df, schedule_2025, teams]),
    ("Statcast Metrics", statcast_metrics_fa.StatcastMetricsAnalyzer, [roster_df, schedule_2025, players_complete], {"as_of_date": as_of_date}),
    ("Vegas Odds", vegas_odds_fa.VegasOddsAnalyzer, [roster_df, schedule_2025, players_complete], {"as_of_date": as_of_date}),
]

print("Running factor analyses...\n")
start_time = datetime.now()

import sys

for i, analysis_info in enumerate(analyses, 1):
    name = analysis_info[0]
    analyzer_class = analysis_info[1]
    args = analysis_info[2]
    kwargs = analysis_info[3] if len(analysis_info) > 3 else {}
    
    print(f"{i}/20 {name} Analysis...", flush=True)
    sys.stdout.flush()
    try:
        analyzer = analyzer_class(data_dir)
        result_df = analyzer.analyze_roster(*args, **kwargs)
        print(f"  ✓ Analyzed {len(result_df):,} records", flush=True)
        results[name.lower().replace(' ', '_').replace('&', 'and')] = result_df
    except Exception as e:
        print(f"  ✗ Error: {e}", flush=True)
        import traceback
        traceback.print_exc()

elapsed = (datetime.now() - start_time).total_seconds()

print(f"\n{'='*80}")
print(f"SUMMARY: Completed {len(results)}/20 analyses in {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
print(f"{'='*80}\n")

if results:
    # Save all results
    for name, df in results.items():
        output_file = data_dir / f"test_single_batch_{name}_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        print(f"✓ Saved {name}: {output_file.name} ({len(df):,} rows)")
    
    print(f"\n{'='*80}")
    print("SAMPLE: First analysis results (first 5 records)")
    print(f"{'='*80}")
    first_key = list(results.keys())[0]
    print(results[first_key].head(5).to_string(index=False))

print(f"\n✅ Single batch test complete!")
print(f"   If all 20 analyses completed, the batch process is ready to run.")
