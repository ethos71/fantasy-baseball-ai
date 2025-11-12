#!/usr/bin/env python3
"""
Run All Factor Analyses

Executes all 13 factor analyses and saves results to CSV files.
This is a wrapper that runs each FA module and saves outputs.

Usage:
    python src/scripts/run_all_fa.py
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

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
    defensive_positions_fa
)


def run_all_factor_analyses(data_dir: Path):
    """Run all 13 factor analyses and save outputs"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Load required data
    print("Loading data files...")
    
    # Get latest roster
    roster_files = sorted(data_dir.glob("yahoo_fantasy_rosters_*.csv"), 
                         key=lambda x: x.stat().st_mtime, reverse=True)
    if not roster_files:
        print("❌ No roster file found!")
        return False
    
    roster_df = pd.read_csv(roster_files[0])
    print(f"✓ Loaded roster: {roster_files[0].name} ({len(roster_df)} players)")
    
    # Load other data files
    try:
        schedule_2025 = pd.read_csv(data_dir / "mlb_2025_schedule.csv")
        weather = pd.read_csv(data_dir / "mlb_stadium_weather.csv")
        players_complete = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
        teams = pd.read_csv(data_dir / "mlb_all_teams.csv")
        
        print(f"✓ Loaded {len(schedule_2025)} games from 2025 schedule")
        print(f"✓ Loaded weather for {len(weather)} stadiums")
        print(f"✓ Loaded {len(players_complete)} player records")
        
    except Exception as e:
        print(f"❌ Error loading data files: {e}")
        return False
    
    print("\nRunning factor analyses...\n")
    
    # Track results
    results = {}
    
    # 1. Wind Analysis
    print("1/13 Wind Analysis...")
    try:
        analyzer = wind_analysis.WindAnalyzer()
        wind_df = analyzer.analyze_roster(roster_df, schedule_2025, weather)
        output_file = data_dir / f"wind_analysis_{timestamp}.csv"
        wind_df.to_csv(output_file, index=False)
        results['wind'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 2. Matchup Analysis  
    print("2/13 Historical Matchup Analysis...")
    try:
        analyzer = matchup_fa.MatchupAnalyzer()
        matchup_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
        output_file = data_dir / f"matchup_analysis_{timestamp}.csv"
        matchup_df.to_csv(output_file, index=False)
        results['matchup'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 3. Home/Away Analysis
    print("3/13 Home/Away Venue Analysis...")
    try:
        analyzer = home_away_fa.HomeAwayAnalyzer()
        venue_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
        output_file = data_dir / f"home_away_analysis_{timestamp}.csv"
        venue_df.to_csv(output_file, index=False)
        results['home_away'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 4. Rest Day Analysis
    print("4/13 Rest Day Impact Analysis...")
    try:
        analyzer = rest_day_fa.RestDayAnalyzer()
        rest_df = analyzer.analyze_roster(roster_df, schedule_2025)
        output_file = data_dir / f"rest_day_analysis_{timestamp}.csv"
        rest_df.to_csv(output_file, index=False)
        results['rest'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 5. Injury/Recovery Analysis
    print("5/13 Injury/Recovery Analysis...")
    try:
        analyzer = injury_fa.InjuryAnalyzer()
        injury_df = analyzer.analyze_roster(roster_df, players_complete)
        output_file = data_dir / f"injury_analysis_{timestamp}.csv"
        injury_df.to_csv(output_file, index=False)
        results['injury'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 6. Umpire Analysis
    print("6/13 Umpire Strike Zone Analysis...")
    try:
        analyzer = umpire_fa.UmpireAnalyzer()
        umpire_df = analyzer.analyze_roster(roster_df, schedule_2025)
        output_file = data_dir / f"umpire_analysis_{timestamp}.csv"
        umpire_df.to_csv(output_file, index=False)
        results['umpire'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 7. Platoon Analysis
    print("7/13 Platoon Advantage Analysis...")
    try:
        analyzer = platoon_fa.PlatoonAnalyzer()
        platoon_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
        output_file = data_dir / f"platoon_analysis_{timestamp}.csv"
        platoon_df.to_csv(output_file, index=False)
        results['platoon'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 8. Temperature Analysis
    print("8/13 Temperature Analysis...")
    try:
        analyzer = temperature_fa.TemperatureAnalyzer()
        temp_df = analyzer.analyze_roster(roster_df, schedule_2025, weather)
        output_file = data_dir / f"temperature_analysis_{timestamp}.csv"
        temp_df.to_csv(output_file, index=False)
        results['temperature'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 9. Pitch Mix Analysis
    print("9/13 Pitch Mix Analysis...")
    try:
        analyzer = pitch_mix_fa.PitchMixAnalyzer()
        pitch_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
        output_file = data_dir / f"pitch_mix_analysis_{timestamp}.csv"
        pitch_df.to_csv(output_file, index=False)
        results['pitch_mix'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 10. Park Factors Analysis
    print("10/13 Park Factors Analysis...")
    try:
        analyzer = park_factors_fa.ParkFactorsAnalyzer()
        park_df = analyzer.analyze_roster(roster_df, schedule_2025, teams)
        output_file = data_dir / f"park_factors_analysis_{timestamp}.csv"
        park_df.to_csv(output_file, index=False)
        results['park'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 11. Lineup Position Analysis
    print("11/13 Lineup Position Analysis...")
    try:
        analyzer = lineup_position_fa.LineupPositionAnalyzer()
        lineup_df = analyzer.analyze_roster(roster_df, schedule_2025)
        output_file = data_dir / f"lineup_position_analysis_{timestamp}.csv"
        lineup_df.to_csv(output_file, index=False)
        results['lineup'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 12. Time of Day Analysis
    print("12/13 Time of Day Analysis...")
    try:
        analyzer = time_of_day_fa.TimeOfDayAnalyzer()
        time_df = analyzer.analyze_roster(roster_df, schedule_2025, players_complete)
        output_file = data_dir / f"time_of_day_analysis_{timestamp}.csv"
        time_df.to_csv(output_file, index=False)
        results['time'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 13. Defensive Positions Analysis
    print("13/13 Defensive Positions Analysis...")
    try:
        analyzer = defensive_positions_fa.DefensivePositionsAnalyzer()
        defense_df = analyzer.analyze_roster(roster_df, schedule_2025, teams)
        output_file = data_dir / f"defensive_positions_analysis_{timestamp}.csv"
        defense_df.to_csv(output_file, index=False)
        results['defense'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print(f"\n✓ Completed {len(results)}/13 factor analyses")
    
    return len(results) >= 10  # Success if at least 10 completed


def main():
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    print("="*80)
    print("Running All Factor Analyses".center(80))
    print("="*80 + "\n")
    
    try:
        success = run_all_factor_analyses(data_dir)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
