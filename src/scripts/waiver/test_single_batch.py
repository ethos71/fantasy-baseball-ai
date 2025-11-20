#!/usr/bin/env python3
"""
Test Single Batch - Run one batch of 100 players through all analyses
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

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
data_dir = Path(__file__).parent / 'data'

print("="*80)
print("Single Batch Test - 100 Players".center(80))
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
weather = pd.read_csv(data_dir / "mlb_stadium_weather.csv")
players_complete = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
teams = pd.read_csv(data_dir / "mlb_all_teams.csv")

print(f"✓ Testing with {len(roster_df)} players")
print(f"✓ Loaded {len(schedule_2025)} games from 2025 schedule")
print(f"✓ Loaded weather for {len(weather)} stadiums\n")

results = {}
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Run each analysis
print("Running factor analyses...\n")

# 1. Wind Analysis
print("1/20 Wind Analysis...")
try:
    analyzer = wind_analysis.WindAnalyzer(data_dir)
    wind_df = analyzer.analyze_roster(roster_df, schedule_2025, weather)
    print(f"  ✓ Analyzed {len(wind_df)} records")
    results['wind'] = wind_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 2. Matchup Analysis
print("2/20 Historical Matchup Analysis...")
try:
    analyzer = matchup_fa.MatchupFactorAnalyzer(data_dir)
    matchup_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
    print(f"  ✓ Analyzed {len(matchup_df)} records")
    results['matchup'] = matchup_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 3. Home/Away Analysis
print("3/20 Home/Away Venue Analysis...")
try:
    analyzer = home_away_fa.HomeAwayFactorAnalyzer(data_dir)
    venue_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
    print(f"  ✓ Analyzed {len(venue_df)} records")
    results['home_away'] = venue_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 4. Rest Day Analysis
print("4/20 Rest Day Impact Analysis...")
try:
    analyzer = rest_day_fa.RestDayFactorAnalyzer(data_dir)
    rest_df = analyzer.analyze_roster(roster_df, schedule_2025)
    print(f"  ✓ Analyzed {len(rest_df)} records")
    results['rest'] = rest_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 5. Injury/Recovery Analysis
print("5/20 Injury/Recovery Analysis...")
try:
    analyzer = injury_fa.InjuryFactorAnalyzer(data_dir)
    injury_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
    print(f"  ✓ Analyzed {len(injury_df)} records")
    results['injury'] = injury_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 6. Umpire Analysis
print("6/20 Umpire Strike Zone Analysis...")
try:
    analyzer = umpire_fa.UmpireFactorAnalyzer(data_dir)
    umpire_df = analyzer.analyze_roster(roster_df, schedule_2025)
    print(f"  ✓ Analyzed {len(umpire_df)} records")
    results['umpire'] = umpire_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 7. Platoon Analysis
print("7/20 Platoon Advantage Analysis...")
try:
    analyzer = platoon_fa.PlatoonFactorAnalyzer(data_dir)
    platoon_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
    print(f"  ✓ Analyzed {len(platoon_df)} records")
    results['platoon'] = platoon_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 8. Temperature Analysis
print("8/20 Temperature Analysis...")
try:
    analyzer = temperature_fa.TemperatureAnalyzer(data_dir)
    temp_df = analyzer.analyze_roster(roster_df, schedule_2025, weather)
    print(f"  ✓ Analyzed {len(temp_df)} records")
    results['temperature'] = temp_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 9. Pitch Mix Analysis
print("9/20 Pitch Mix Analysis...")
try:
    analyzer = pitch_mix_fa.PitchMixAnalyzer(data_dir)
    pitch_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
    print(f"  ✓ Analyzed {len(pitch_df)} records")
    results['pitch_mix'] = pitch_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 10. Park Factors Analysis
print("10/20 Park Factors Analysis...")
try:
    analyzer = park_factors_fa.ParkFactorsAnalyzer(data_dir)
    park_df = analyzer.analyze_roster(roster_df, schedule_2025, teams)
    print(f"  ✓ Analyzed {len(park_df)} records")
    results['park'] = park_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 11. Lineup Position Analysis
print("11/20 Lineup Position Analysis...")
try:
    analyzer = lineup_position_fa.LineupPositionAnalyzer(data_dir)
    lineup_df = analyzer.analyze_roster(roster_df, schedule_2025)
    print(f"  ✓ Analyzed {len(lineup_df)} records")
    results['lineup'] = lineup_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 12. Time of Day Analysis
print("12/20 Time of Day Analysis...")
try:
    analyzer = time_of_day_fa.TimeOfDayAnalyzer(data_dir)
    time_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
    print(f"  ✓ Analyzed {len(time_df)} records")
    results['time'] = time_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 13. Defensive Positions Analysis
print("13/20 Defensive Positions Analysis...")
try:
    analyzer = defensive_positions_fa.DefensivePositionsFactorAnalyzer(data_dir)
    defense_df = analyzer.analyze_roster(roster_df, schedule_2025, teams)
    print(f"  ✓ Analyzed {len(defense_df)} records")
    results['defense'] = defense_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 14. Recent Form Analysis
print("14/20 Recent Form / Streaks Analysis...")
try:
    analyzer = recent_form_fa.RecentFormAnalyzer(data_dir)
    form_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete, target_date=as_of_date)
    print(f"  ✓ Analyzed {len(form_df)} records")
    results['recent_form'] = form_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 15. Bullpen Fatigue Analysis
print("15/20 Bullpen Fatigue Detection...")
try:
    analyzer = bullpen_fatigue_fa.BullpenFatigueAnalyzer(data_dir)
    bullpen_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
    print(f"  ✓ Analyzed {len(bullpen_df)} records")
    results['bullpen'] = bullpen_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 16. Humidity & Elevation Analysis
print("16/20 Humidity & Elevation Analysis...")
try:
    analyzer = humidity_elevation_fa.HumidityElevationAnalyzer(data_dir)
    humidity_df = analyzer.analyze_roster(roster_df, schedule_2025, weather)
    print(f"  ✓ Analyzed {len(humidity_df)} records")
    results['humidity'] = humidity_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 17. Monthly Splits Analysis
print("17/20 Monthly Splits Analysis...")
try:
    analyzer = monthly_splits_fa.MonthlySplitsAnalyzer(data_dir)
    monthly_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
    print(f"  ✓ Analyzed {len(monthly_df)} records")
    results['monthly'] = monthly_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 18. Team Momentum Analysis
print("18/20 Team Momentum Analysis...")
try:
    analyzer = team_momentum_fa.TeamOffensiveMomentumAnalyzer(data_dir)
    momentum_df = analyzer.analyze_roster(roster_df, schedule_2025, teams)
    print(f"  ✓ Analyzed {len(momentum_df)} records")
    results['momentum'] = momentum_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 19. Statcast Metrics Analysis
print("19/20 Statcast Metrics Analysis...")
try:
    analyzer = statcast_metrics_fa.StatcastMetricsAnalyzer(data_dir)
    statcast_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete, as_of_date=as_of_date)
    print(f"  ✓ Analyzed {len(statcast_df)} records")
    results['statcast'] = statcast_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

# 20. Vegas Odds Analysis
print("20/20 Vegas Odds Analysis...")
try:
    analyzer = vegas_odds_fa.VegasOddsAnalyzer(data_dir)
    vegas_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete, as_of_date=as_of_date)
    print(f"  ✓ Analyzed {len(vegas_df)} records")
    results['vegas'] = vegas_df
except Exception as e:
    print(f"  ✗ Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\n{'='*80}")
print(f"SUMMARY: Completed {len(results)}/20 analyses")
print(f"{'='*80}\n")

# Show sample results from first successful analysis
if results:
    first_key = list(results.keys())[0]
    print(f"Sample results from {first_key} analysis:")
    print(results[first_key].head(10).to_string())
    
    # Save to CSV for inspection
    output_file = data_dir / f"test_batch_{first_key}_{timestamp}.csv"
    results[first_key].to_csv(output_file, index=False)
    print(f"\n✓ Saved test output to: {output_file.name}")
