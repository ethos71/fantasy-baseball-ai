#!/usr/bin/env python3
"""
Fantasy Baseball AI - Main Utility Script

Usage:
    python src/fb_ai.py                    # Show data statistics and available commands
    python src/fb_ai.py --refresh          # Clear and re-scrape all data
    python src/fb_ai.py --help             # Show help message

This script:
- Without arguments: Shows current data status and available options
- With --refresh: Clears all data and re-scrapes MLB statistics and weather
"""

import os
import sys
import glob
import subprocess
import argparse
from datetime import datetime
from pathlib import Path


class DataRefreshManager:
    """Manages complete data refresh for Fantasy Baseball AI"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.scripts_dir = self.project_root / "src" / "scripts"
        
    def print_header(self, text: str):
        """Print formatted section header"""
        print(f"\n{'='*80}")
        print(f"{text.center(80)}")
        print(f"{'='*80}\n")
    
    def confirm_refresh(self) -> bool:
        """Ask user to confirm data refresh"""
        self.print_header("MLB DATA REFRESH - CONFIRMATION")
        
        print("⚠️  WARNING: This will DELETE all existing data files!")
        print(f"\nData directory: {self.data_dir}")
        
        # Count existing CSV files
        csv_files = list(self.data_dir.glob("*.csv")) if self.data_dir.exists() else []
        print(f"Files to be deleted: {len(csv_files)} CSV files")
        
        if csv_files:
            print("\nExisting files:")
            for f in sorted(csv_files)[:10]:
                print(f"  - {f.name}")
            if len(csv_files) > 10:
                print(f"  ... and {len(csv_files) - 10} more")
        
        print(f"\n📊 New data will be fetched:")
        print(f"  • MLB Teams (30 teams)")
        print(f"  • Game Schedules (4 years)")
        print(f"  • Player Rosters (all teams, 4 years)")
        print(f"  • Stadium Weather (30 stadiums)")
        
        print(f"\n⏱️  Estimated time: 5-10 minutes")
        
        response = input("\nProceed with data refresh? (yes/no): ").strip().lower()
        return response in ['yes', 'y']
    
    def clear_data_directory(self):
        """Remove all CSV files from data directory"""
        self.print_header("STEP 1: Clearing Existing Data")
        
        if not self.data_dir.exists():
            print(f"Creating data directory: {self.data_dir}")
            self.data_dir.mkdir(parents=True, exist_ok=True)
            print("✓ Data directory created")
            return
        
        csv_files = list(self.data_dir.glob("*.csv"))
        
        if not csv_files:
            print("No CSV files to remove")
            return
        
        print(f"Removing {len(csv_files)} CSV files...")
        
        removed = 0
        for csv_file in csv_files:
            try:
                csv_file.unlink()
                print(f"  ✓ Removed: {csv_file.name}")
                removed += 1
            except Exception as e:
                print(f"  ✗ Failed to remove {csv_file.name}: {e}")
        
        print(f"\n✓ Removed {removed}/{len(csv_files)} files")
    
    def run_script(self, script_name: str, description: str):
        """Run a Python script and capture output"""
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            print(f"✗ Script not found: {script_path}")
            return False
        
        self.print_header(description)
        
        print(f"Running: {script_path.name}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        try:
            # Run the script and stream output in real-time
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(self.project_root),
                check=True,
                text=True
            )
            
            print(f"\n✓ {script_name} completed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"\n✗ {script_name} failed with exit code {e.returncode}")
            return False
        except Exception as e:
            print(f"\n✗ Error running {script_name}: {e}")
            return False
    
    def verify_data(self):
        """Verify data was created successfully"""
        self.print_header("STEP 4: Verification")
        
        csv_files = list(self.data_dir.glob("*.csv"))
        
        if not csv_files:
            print("✗ No CSV files found!")
            return False
        
        print(f"✓ Generated {len(csv_files)} CSV files:\n")
        
        total_size = 0
        expected_files = {
            'mlb_all_teams.csv': 'Teams data',
            'mlb_stadium_weather.csv': 'Weather data',
            'mlb_all_players_complete.csv': 'Complete player database',
        }
        
        # Check expected files
        for filename, description in expected_files.items():
            file_path = self.data_dir / filename
            if file_path.exists():
                size = file_path.stat().st_size
                total_size += size
                print(f"  ✓ {filename:35s} {size:>10,d} bytes - {description}")
            else:
                print(f"  ✗ {filename:35s} MISSING!")
        
        # Check schedule files
        schedule_files = sorted(self.data_dir.glob("mlb_*_schedule.csv"))
        if schedule_files:
            print(f"\n  Schedule files ({len(schedule_files)}):")
            for f in schedule_files:
                size = f.stat().st_size
                total_size += size
                print(f"    • {f.name:33s} {size:>10,d} bytes")
        
        # Check player files
        player_files = sorted(self.data_dir.glob("mlb_all_players_*.csv"))
        player_files = [f for f in player_files if f.name != 'mlb_all_players_complete.csv']
        if player_files:
            print(f"\n  Player files by year ({len(player_files)}):")
            for f in player_files:
                size = f.stat().st_size
                total_size += size
                print(f"    • {f.name:33s} {size:>10,d} bytes")
        
        print(f"\n📊 Total data size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
        
        return True
    
    def show_status(self):
        """Display current data status without modifying anything"""
        print("\n" + "="*80)
        print("FANTASY BASEBALL AI - DATA STATUS".center(80))
        print("="*80)
        print(f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        self.print_header("Current Data Files")
        
        if not self.data_dir.exists():
            print("⚠️  Data directory does not exist!")
            print(f"📁 Expected location: {self.data_dir}")
            print("\n💡 Run with --refresh to create data directory and fetch all data")
            return
        
        csv_files = list(self.data_dir.glob("*.csv"))
        
        if not csv_files:
            print("⚠️  No data files found!")
            print(f"📁 Data directory: {self.data_dir}")
            print("\n💡 Run with --refresh to fetch all MLB data")
            return
        
        print(f"✓ Found {len(csv_files)} CSV files\n")
        
        # Categorize files
        teams_weather = []
        schedules = []
        players = []
        
        for f in csv_files:
            if 'schedule' in f.name:
                schedules.append(f)
            elif 'players' in f.name:
                players.append(f)
            else:
                teams_weather.append(f)
        
        total_size = 0
        
        # Display teams/weather
        if teams_weather:
            print("📊 Teams & Weather:")
            for f in sorted(teams_weather):
                size = f.stat().st_size
                total_size += size
                modified = datetime.fromtimestamp(f.stat().st_mtime)
                age = datetime.now() - modified
                age_str = f"{age.days} days ago" if age.days > 0 else "today"
                print(f"  • {f.name:35s} {size:>10,d} bytes (updated {age_str})")
        
        # Display schedules
        if schedules:
            print(f"\n📅 Game Schedules ({len(schedules)}):")
            for f in sorted(schedules):
                size = f.stat().st_size
                total_size += size
                print(f"  • {f.name:35s} {size:>10,d} bytes")
        
        # Display player files
        if players:
            print(f"\n👥 Player Data ({len(players)}):")
            for f in sorted(players):
                size = f.stat().st_size
                total_size += size
                print(f"  • {f.name:35s} {size:>10,d} bytes")
        
        print(f"\n📊 Total data size: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")
        
        # Check data freshness
        if csv_files:
            oldest = min(csv_files, key=lambda f: f.stat().st_mtime)
            oldest_time = datetime.fromtimestamp(oldest.stat().st_mtime)
            age = datetime.now() - oldest_time
            
            if age.days > 7:
                print(f"\n⚠️  Data is {age.days} days old - consider refreshing")
            elif age.days > 0:
                print(f"\n✓ Data is {age.days} days old")
            else:
                print(f"\n✓ Data is fresh (updated today)")
        
        self.print_header("Available Commands")
        
        print("🔄 Full refresh (clears and re-scrapes all):")
        print("   python src/fb_ai.py --refresh")
        
        print("\n⚡ Quick update (incremental changes only):")
        print("   python src/scripts/mlb_delta_scrape.py")
        print("   python src/scripts/weather_delta_scrape.py")
        
        print("\n📊 Individual full scripts:")
        print("   python src/scripts/mlb_scrape.py")
        print("   python src/scripts/weather_scrape.py")
        print("   python src/scripts/xgboost_ml.py")
        
        print("\n💡 Tips:")
        print("   • Use delta scrapers for daily updates (~30 seconds)")
        print("   • Full refresh weekly for complete data (~5 minutes)")
        print("   • Weather delta updates are fast and recommended daily")
        
        print("\n" + "="*80 + "\n")
    
    def run_refresh(self):
        """Execute complete data refresh process"""
        print("\n" + "="*80)
        print("MLB FANTASY BASEBALL AI - DATA REFRESH".center(80))
        print("="*80)
        print(f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 0: Confirm
        if not self.confirm_refresh():
            print("\n❌ Data refresh cancelled by user")
            return False
        
        # Step 1: Clear data
        self.clear_data_directory()
        
        # Step 2: Run MLB scraper
        if not self.run_script("mlb_scrape.py", "STEP 2: Fetching MLB Data"):
            print("\n❌ MLB data scraping failed")
            return False
        
        # Step 3: Run weather scraper
        if not self.run_script("weather_scrape.py", "STEP 3: Fetching Weather Data"):
            print("\n❌ Weather data scraping failed")
            return False
        
        # Step 4: Verify
        if not self.verify_data():
            print("\n⚠️  Data verification found issues")
            return False
        
        # Step 5: Run delta updates to ensure we have latest data
        print("\n" + "="*80)
        print("STEP 5: Running Delta Updates".center(80))
        print("="*80 + "\n")
        print("Fetching any new games and roster changes since scrape completed...")
        
        if not self.run_script("mlb_delta_scrape.py", "STEP 5a: MLB Delta Update"):
            print("⚠️  Delta update had issues (not critical)")
        
        if not self.run_script("weather_delta_scrape.py", "STEP 5b: Weather Delta Update"):
            print("⚠️  Weather delta update had issues (not critical)")
        
        # Step 6: Fetch Yahoo roster and run weather advantage analysis
        print("\n" + "="*80)
        print("STEP 6: Fetching Yahoo Roster & Weather Analysis".center(80))
        print("="*80 + "\n")
        
        if not self.run_script("yahoo_scrape.py", "STEP 6a: Yahoo Fantasy Roster"):
            print("⚠️  Yahoo roster fetch had issues (continuing anyway)")
        
        print("\nRunning weather advantage analysis...")
        if not self.run_script("weather_advantage.py", "STEP 6b: Weather Advantage Analysis"):
            print("⚠️  Weather advantage analysis had issues")
        
        print("\nRunning pitcher-hitter matchup analysis...")
        if not self.run_script("matchup_analysis.py", "STEP 6c: Matchup Analysis"):
            print("⚠️  Matchup analysis had issues")
        
        # Success!
        self.print_header("DATA REFRESH COMPLETE!")
        
        print("✅ All data successfully refreshed!\n")
        print("📁 Data location:", self.data_dir)
        print("📊 You can now use the data for analysis and predictions")
        
        print(f"\n⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Fantasy Baseball AI - Main Utility',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/fb_ai.py              Show current data status
  python src/fb_ai.py --refresh    Clear and re-scrape all data
  python src/fb_ai.py --help       Show this help message

Data includes:
  • 30 MLB teams with complete rosters
  • Game schedules for 4 years (2022-2025)
  • 5,969 player-season records
  • Real-time weather for all 30 stadiums
        """
    )
    
    parser.add_argument(
        '--refresh',
        action='store_true',
        help='Clear all data and re-scrape from MLB API'
    )
    
    args = parser.parse_args()
    manager = DataRefreshManager()
    
    try:
        if args.refresh:
            # Run data refresh
            success = manager.run_refresh()
            sys.exit(0 if success else 1)
        else:
            # Show status
            manager.show_status()
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n❌ Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
