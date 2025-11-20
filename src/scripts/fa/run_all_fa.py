#!/usr/bin/env python3
"""
Run All Factor Analyses

Executes all 20 factor analyses and saves results to CSV files.
This is a wrapper that runs each FA module and saves outputs.

Usage:
    python src/scripts/run_all_fa.py
    python src/scripts/run_all_fa.py --date 2025-09-28
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime
import argparse

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
    defensive_positions_fa,
    recent_form_fa,
    bullpen_fatigue_fa,
    humidity_elevation_fa,
    monthly_splits_fa,
    team_momentum_fa,
    statcast_metrics_fa,
    vegas_odds_fa
)


def run_all_factor_analyses(data_dir: Path, as_of_date=None, all_players=False):
    """Run all 17 factor analyses and save outputs
    
    Args:
        data_dir: Path to data directory
        as_of_date: Target date for analysis (datetime or str). Defaults to today.
        all_players: If True, analyze all MLB players. If False, analyze only rostered players.
    """
    
    # Parse as_of_date
    if as_of_date is None:
        as_of_date = datetime.now()
    elif isinstance(as_of_date, str):
        as_of_date = datetime.strptime(as_of_date, "%Y-%m-%d")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Load required data
    print(f"Loading data files for analysis date: {as_of_date.strftime('%Y-%m-%d')}...")
    
    # Determine which players to analyze
    if all_players:
        print("Mode: Analyzing ALL MLB players (for waiver wire)")
        try:
            roster_df = pd.read_csv(data_dir / "mlb_all_players_complete.csv")
            # Filter to only current season players
            current_season = as_of_date.year
            if 'season' in roster_df.columns:
                roster_df = roster_df[roster_df['season'] == current_season]
            print(f"✓ Loaded {len(roster_df)} active MLB players")
        except Exception as e:
            print(f"❌ Error loading all players file: {e}")
            return False
    else:
        print("Mode: Analyzing ROSTERED players only")
        # Get latest roster
        roster_files = sorted(data_dir.glob("yahoo_fantasy_rosters_*.csv"), 
                             key=lambda x: x.stat().st_mtime, reverse=True)
        if not roster_files:
            print("❌ No roster file found!")
            return False
        
        roster_df = pd.read_csv(roster_files[0])
        print(f"✓ Loaded roster: {roster_files[0].name} ({len(roster_df)} players)")
    
    # Team abbreviation to full name mapping
    TEAM_MAP = {
        'AZ': 'Arizona Diamondbacks', 'ATL': 'Atlanta Braves',
        'ATH': 'Oakland Athletics', 'BAL': 'Baltimore Orioles',
        'BOS': 'Boston Red Sox', 'CHC': 'Chicago Cubs',
        'CHW': 'Chicago White Sox', 'CIN': 'Cincinnati Reds',
        'CLE': 'Cleveland Guardians', 'COL': 'Colorado Rockies',
        'CWS': 'Chicago White Sox', 'DET': 'Detroit Tigers',
        'HOU': 'Houston Astros', 'KC': 'Kansas City Royals',
        'LAA': 'Los Angeles Angels', 'LAD': 'Los Angeles Dodgers',
        'MIA': 'Miami Marlins', 'MIL': 'Milwaukee Brewers',
        'MIN': 'Minnesota Twins', 'NYM': 'New York Mets',
        'NYY': 'New York Yankees', 'OAK': 'Oakland Athletics',
        'PHI': 'Philadelphia Phillies', 'PIT': 'Pittsburgh Pirates',
        'SD': 'San Diego Padres', 'SEA': 'Seattle Mariners',
        'SF': 'San Francisco Giants', 'STL': 'St. Louis Cardinals',
        'TB': 'Tampa Bay Rays', 'TEX': 'Texas Rangers',
        'TOR': 'Toronto Blue Jays', 'WSH': 'Washington Nationals',
    }
    
    # Normalize roster columns based on source
    if all_players:
        # All players file has: player_id, player_name, team_id, team_name
        if 'team_name' in roster_df.columns:
            roster_df['team'] = roster_df['team_name']
            roster_df['mlb_team'] = roster_df['team_name']  # Add mlb_team for analyzer compatibility
    else:
        # Roster file has: mlb_team, name
        if 'mlb_team' in roster_df.columns and 'team' not in roster_df.columns:
            roster_df['team'] = roster_df['mlb_team'].map(TEAM_MAP)
            roster_df['team'].fillna(roster_df['mlb_team'], inplace=True)
        if 'name' in roster_df.columns and 'player_name' not in roster_df.columns:
            roster_df['player_name'] = roster_df['name']
    
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
    
    # Batch processing for large datasets
    batch_size = 100 if all_players else len(roster_df)
    num_batches = (len(roster_df) + batch_size - 1) // batch_size
    
    if all_players and num_batches > 1:
        print(f"📦 Processing {len(roster_df)} players in {num_batches} batches of {batch_size}")
        print(f"   This will take approximately {num_batches * 2} minutes\n")
    
    # Track results
    results = {}
    
    # Determine output file suffix
    file_suffix = "all_players" if all_players else "roster"
    
    # Helper function to process in batches
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
            
            if batch_num % 5 == 4:  # Progress every 5 batches
                print(f"    [{batch_num + 1}/{num_batches} batches]", end='\r')
        
        if num_batches > 1:
            print(f"    [{num_batches}/{num_batches} batches] ✓")
        
        return pd.concat(all_results, ignore_index=True)
    
    # 1. Wind Analysis
    print("1/20 Wind Analysis...")
    try:
        analyzer = wind_analysis.WindAnalyzer(data_dir)
        wind_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, weather)
        output_file = data_dir / f"wind_analysis_{file_suffix}_{timestamp}.csv"
        wind_df.to_csv(output_file, index=False)
        results['wind'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 2. Matchup Analysis  
    print("2/20 Historical Matchup Analysis...")
    try:
        analyzer = matchup_fa.MatchupFactorAnalyzer(data_dir)
        matchup_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
        output_file = data_dir / f"matchup_analysis_{file_suffix}_{timestamp}.csv"
        matchup_df.to_csv(output_file, index=False)
        results['matchup'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 3. Home/Away Analysis
    print("3/20 Home/Away Venue Analysis...")
    try:
        analyzer = home_away_fa.HomeAwayFactorAnalyzer(data_dir)
        venue_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
        output_file = data_dir / f"home_away_analysis_{file_suffix}_{timestamp}.csv"
        venue_df.to_csv(output_file, index=False)
        results['home_away'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 4. Rest Day Analysis
    print("4/20 Rest Day Impact Analysis...")
    try:
        analyzer = rest_day_fa.RestDayFactorAnalyzer(data_dir)
        rest_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025)
        output_file = data_dir / f"rest_day_analysis_{file_suffix}_{timestamp}.csv"
        rest_df.to_csv(output_file, index=False)
        results['rest'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 5. Injury/Recovery Analysis
    print("5/20 Injury/Recovery Analysis...")
    try:
        analyzer = injury_fa.InjuryFactorAnalyzer(data_dir)
        injury_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
        output_file = data_dir / f"injury_analysis_{file_suffix}_{timestamp}.csv"
        injury_df.to_csv(output_file, index=False)
        results['injury'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 6. Umpire Analysis
    print("6/20 Umpire Strike Zone Analysis...")
    try:
        analyzer = umpire_fa.UmpireFactorAnalyzer(data_dir)
        umpire_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025)
        output_file = data_dir / f"umpire_analysis_{file_suffix}_{timestamp}.csv"
        umpire_df.to_csv(output_file, index=False)
        results['umpire'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 7. Platoon Analysis
    print("7/20 Platoon Advantage Analysis...")
    try:
        analyzer = platoon_fa.PlatoonFactorAnalyzer(data_dir)
        platoon_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, players_complete)
        output_file = data_dir / f"platoon_analysis_{file_suffix}_{timestamp}.csv"
        platoon_df.to_csv(output_file, index=False)
        results['platoon'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    # 8. Temperature Analysis
    print("8/20 Temperature Analysis...")
    try:
        analyzer = temperature_fa.TemperatureAnalyzer(data_dir)
        temp_df = process_in_batches(analyzer.analyze_roster, roster_df, schedule_2025, weather)
        output_file = data_dir / f"temperature_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"pitch_mix_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"park_factors_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"lineup_position_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"time_of_day_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"defensive_positions_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"recent_form_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"bullpen_fatigue_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"humidity_elevation_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"monthly_splits_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"team_momentum_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"statcast_metrics_analysis_{file_suffix}_{timestamp}.csv"
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
        output_file = data_dir / f"vegas_odds_analysis_{file_suffix}_{timestamp}.csv"
        vegas_df.to_csv(output_file, index=False)
        results['vegas'] = output_file
        print(f"  ✓ Saved to {output_file.name}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    
    print(f"\n✓ Completed {len(results)}/20 factor analyses")
    
    return len(results) >= 17  # Success if at least 17 completed


def main():
    parser = argparse.ArgumentParser(description='Run all 20 factor analyses')
    parser.add_argument('--date', type=str, help='Target date for analysis (YYYY-MM-DD)')
    parser.add_argument('--all-players', action='store_true', 
                       help='Analyze all MLB players instead of just rostered players (for waiver wire)')
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    print("="*80)
    print("Running All Factor Analyses".center(80))
    print("="*80 + "\n")
    
    try:
        success = run_all_factor_analyses(data_dir, as_of_date=args.date, all_players=args.all_players)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
