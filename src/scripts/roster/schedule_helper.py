#!/usr/bin/env python3
"""
Game Time Scheduler Helper

This script helps you schedule the daily sit/start script to run 30 minutes
before your players' games start.

Usage:
    python src/scripts/schedule_helper.py                  # Show today's game times
    python src/scripts/schedule_helper.py --date 2025-09-29 # Show specific date
    python src/scripts/schedule_helper.py --cron           # Generate cron commands
"""

import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import argparse
import sys


def load_schedule(data_dir: Path, year: int = 2025) -> pd.DataFrame:
    """Load MLB schedule for given year"""
    schedule_file = data_dir / f"mlb_{year}_schedule.csv"
    
    if not schedule_file.exists():
        print(f"❌ Schedule file not found: {schedule_file}")
        return pd.DataFrame()
    
    df = pd.read_csv(schedule_file)
    return df


def load_roster(data_dir: Path) -> pd.DataFrame:
    """Load latest Yahoo roster"""
    roster_files = sorted(data_dir.glob("yahoo_fantasy_rosters_*.csv"),
                         key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not roster_files:
        print("❌ No roster file found!")
        return pd.DataFrame()
    
    df = pd.read_csv(roster_files[0])
    print(f"Using roster: {roster_files[0].name}")
    return df


def find_games_for_date(schedule_df: pd.DataFrame, roster_df: pd.DataFrame, 
                        target_date: str) -> pd.DataFrame:
    """Find games for roster players on target date"""
    
    # Filter schedule to target date
    games_today = schedule_df[schedule_df['game_date'] == target_date].copy()
    
    if games_today.empty:
        return pd.DataFrame()
    
    # Get roster teams
    roster_teams = set(roster_df['mlb_team'].unique()) if 'mlb_team' in roster_df.columns else set()
    
    # Find games involving roster teams
    roster_games = games_today[
        games_today['away_team'].isin(roster_teams) | 
        games_today['home_team'].isin(roster_teams)
    ].copy()
    
    return roster_games


def show_game_schedule(data_dir: Path, target_date: str):
    """Show game times for target date"""
    
    year = int(target_date[:4])
    schedule_df = load_schedule(data_dir, year)
    roster_df = load_roster(data_dir)
    
    if schedule_df.empty or roster_df.empty:
        return
    
    games = find_games_for_date(schedule_df, roster_df, target_date)
    
    print("\n" + "="*80)
    print(f"GAMES FOR YOUR ROSTER PLAYERS - {target_date}".center(80))
    print("="*80 + "\n")
    
    if games.empty:
        print(f"No games found for {target_date}")
        print("\nThis could mean:")
        print("  • It's an off day")
        print("  • Schedule data needs updating")
        print("  • No roster players have games today")
        return
    
    # Parse and sort by game time
    games['game_time'] = pd.to_datetime(games['game_datetime'])
    games = games.sort_values('game_time')
    
    # Find earliest game
    earliest = games.iloc[0]
    earliest_time = earliest['game_time']
    
    # Calculate when to run script (30 mins before)
    run_time = earliest_time - timedelta(minutes=30)
    
    print(f"{'Time':10} {'Matchup':40} {'Venue':25}")
    print("-" * 80)
    
    for _, game in games.iterrows():
        time_str = game['game_time'].strftime('%I:%M %p')
        matchup = f"{game['away_team']} @ {game['home_team']}"
        venue = game.get('venue_name', 'TBD')
        print(f"{time_str:10} {matchup:40} {venue:25}")
    
    print("\n" + "="*80)
    print(f"⏰ EARLIEST GAME: {earliest_time.strftime('%I:%M %p')}")
    print(f"🎯 RUN SCRIPT AT: {run_time.strftime('%I:%M %p')} ({run_time.strftime('%H:%M')} in 24h)")
    print("="*80 + "\n")
    
    print("Command to run:")
    print(f"  python src/scripts/daily_sitstart.py --date {target_date}\n")
    
    print("Or with skip-tune for faster results:")
    print(f"  python src/scripts/daily_sitstart.py --date {target_date} --skip-tune\n")
    
    return run_time


def generate_cron_example(run_time: datetime, target_date: str, project_root: Path):
    """Generate example cron command"""
    
    hour = run_time.hour
    minute = run_time.minute
    day = run_time.day
    month = run_time.month
    
    print("\n" + "="*80)
    print("CRON SCHEDULING EXAMPLE".center(80))
    print("="*80 + "\n")
    
    print("To schedule this command with cron:")
    print("1. Open crontab: crontab -e")
    print("2. Add this line:\n")
    
    cron_line = f"{minute} {hour} {day} {month} * cd {project_root} && python src/scripts/daily_sitstart.py --date {target_date}"
    print(f"   {cron_line}\n")
    
    print("This will run ONCE on the specified date.")
    print("\nFor daily automatic runs at the same time:")
    daily_cron = f"{minute} {hour} * * * cd {project_root} && python src/scripts/daily_sitstart.py"
    print(f"   {daily_cron}\n")
    
    print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Game Time Scheduler Helper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/scripts/schedule_helper.py                    # Today's games
  python src/scripts/schedule_helper.py --date 2025-09-29  # Specific date
  python src/scripts/schedule_helper.py --cron             # Show cron examples

This tool helps you determine when to run the daily sit/start script
(30 minutes before your first game).
        """
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Target date (YYYY-MM-DD format, defaults to today)'
    )
    
    parser.add_argument(
        '--cron',
        action='store_true',
        help='Generate cron scheduling examples'
    )
    
    args = parser.parse_args()
    
    # Determine target date
    if args.date:
        target_date = args.date
    else:
        target_date = datetime.now().strftime('%Y-%m-%d')
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    try:
        run_time = show_game_schedule(data_dir, target_date)
        
        if args.cron and run_time:
            generate_cron_example(run_time, target_date, project_root)
        
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
