#!/usr/bin/env python3
"""
MLB Delta Scraper - Incremental Data Updates

This script fetches only NEW data since the last scrape:
- Checks existing data files for latest dates
- Fetches only games/players added since then
- Appends new data to existing CSV files
- Much faster than full refresh (~30 seconds vs 5 minutes)

Usage:
    python src/scripts/mlb_delta_scrape.py
"""

import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
import os


class MLBDeltaScraper:
    """Incremental MLB data scraper - only fetches new data"""
    
    BASE_URL = "https://statsapi.mlb.com/api/v1"
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.current_year = datetime.now().year
        
    def print_header(self, text: str):
        """Print formatted section header"""
        print(f"\n{'='*80}")
        print(f"{text.center(80)}")
        print(f"{'='*80}\n")
    
    def get_last_update_date(self, filename: str) -> datetime:
        """Get the last update date from a CSV file"""
        filepath = self.data_dir / filename
        
        if not filepath.exists():
            return None
        
        try:
            # Check file modification time
            return datetime.fromtimestamp(filepath.stat().st_mtime)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            return None
    
    def get_latest_schedule_date(self, year: int) -> datetime:
        """Get the latest game date in the schedule file"""
        filepath = self.data_dir / f"mlb_{year}_schedule.csv"
        
        if not filepath.exists():
            return None
        
        try:
            df = pd.read_csv(filepath)
            if 'gameDate' in df.columns and len(df) > 0:
                latest = pd.to_datetime(df['gameDate']).max()
                return latest.to_pydatetime() if pd.notna(latest) else None
        except Exception as e:
            print(f"Error reading schedule: {e}")
            return None
    
    def fetch_schedule_delta(self, year: int, since_date: datetime) -> pd.DataFrame:
        """Fetch games scheduled after the given date"""
        print(f"Fetching new games for {year} since {since_date.strftime('%Y-%m-%d')}...")
        
        # API call for schedule
        start_date = since_date.strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.BASE_URL}/schedule"
        params = {
            'sportId': 1,
            'startDate': start_date,
            'endDate': end_date,
            'gameType': 'R,F,D,L,W'
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            games = []
            for date_entry in data.get('dates', []):
                for game in date_entry.get('games', []):
                    games.append({
                        'gamePk': game.get('gamePk'),
                        'gameType': game.get('gameType'),
                        'season': game.get('season'),
                        'gameDate': game.get('gameDate'),
                        'officialDate': game.get('officialDate'),
                        'status': game['status'].get('detailedState'),
                        'away_id': game['teams']['away']['team'].get('id'),
                        'away_name': game['teams']['away']['team'].get('name'),
                        'home_id': game['teams']['home']['team'].get('id'),
                        'home_name': game['teams']['home']['team'].get('name'),
                        'venue_id': game.get('venue', {}).get('id'),
                        'venue_name': game.get('venue', {}).get('name'),
                    })
            
            return pd.DataFrame(games)
            
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            return pd.DataFrame()
    
    def update_schedules(self) -> bool:
        """Update schedule files with new games"""
        self.print_header("Updating Game Schedules")
        
        updated_count = 0
        
        for year in [self.current_year, self.current_year - 1]:
            filepath = self.data_dir / f"mlb_{year}_schedule.csv"
            
            # Get latest game date
            latest_date = self.get_latest_schedule_date(year)
            
            if latest_date is None:
                print(f"⚠️  No existing schedule for {year} - run full scrape first")
                continue
            
            print(f"📅 {year}: Latest game is {latest_date.strftime('%Y-%m-%d')}")
            
            # Fetch new games
            new_games = self.fetch_schedule_delta(year, latest_date)
            
            if len(new_games) == 0:
                print(f"   ✓ No new games since last update")
                continue
            
            # Load existing and append
            existing_df = pd.read_csv(filepath)
            
            # Remove duplicates based on gamePk
            combined = pd.concat([existing_df, new_games], ignore_index=True)
            combined = combined.drop_duplicates(subset=['gamePk'], keep='last')
            combined = combined.sort_values('gameDate')
            
            # Save updated file
            combined.to_csv(filepath, index=False)
            new_count = len(combined) - len(existing_df)
            print(f"   ✓ Added {new_count} new games")
            updated_count += new_count
        
        return updated_count > 0
    
    def update_current_rosters(self) -> bool:
        """Update player rosters for current year only"""
        self.print_header("Updating Player Rosters")
        
        filepath = self.data_dir / f"mlb_all_players_{self.current_year}.csv"
        
        if not filepath.exists():
            print(f"⚠️  No existing roster data - run full scrape first")
            return False
        
        print(f"Fetching current rosters for all 30 teams...")
        
        # Get all teams
        teams_file = self.data_dir / "mlb_all_teams.csv"
        if not teams_file.exists():
            print("⚠️  Teams file not found - run full scrape first")
            return False
        
        teams_df = pd.read_csv(teams_file)
        
        all_players = []
        
        for _, team in teams_df.iterrows():
            team_id = team['team_id']
            team_name = team['team_name']
            
            print(f"  → {team_name}...", end=" ")
            
            url = f"{self.BASE_URL}/teams/{team_id}/roster"
            params = {'rosterType': 'active'}
            
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                for player in data.get('roster', []):
                    person = player.get('person', {})
                    position = player.get('position', {})
                    
                    all_players.append({
                        'player_id': person.get('id'),
                        'fullName': person.get('fullName'),
                        'firstName': person.get('firstName'),
                        'lastName': person.get('lastName'),
                        'primaryNumber': player.get('jerseyNumber'),
                        'position': position.get('name'),
                        'position_abbr': position.get('abbreviation'),
                        'team_id': team_id,
                        'team_name': team_name,
                        'season': self.current_year,
                        'status': player.get('status', {}).get('description', 'Active')
                    })
                
                print(f"{len(data.get('roster', []))} players")
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error: {e}")
        
        if not all_players:
            print("⚠️  No player data fetched")
            return False
        
        new_df = pd.DataFrame(all_players)
        
        # Load existing and merge
        existing_df = pd.read_csv(filepath)
        
        # Combine and remove duplicates (keep new data)
        combined = pd.concat([existing_df, new_df], ignore_index=True)
        combined = combined.drop_duplicates(subset=['player_id', 'team_id', 'season'], keep='last')
        combined = combined.sort_values(['team_name', 'fullName'])
        
        # Save
        combined.to_csv(filepath, index=False)
        
        # Update complete file
        self.update_complete_player_file()
        
        new_count = len(combined) - len(existing_df)
        print(f"\n✓ Updated {len(combined)} total players ({new_count} changes)")
        
        return True
    
    def update_complete_player_file(self):
        """Rebuild the complete player file from all year files"""
        all_years = []
        
        for year in range(self.current_year - 3, self.current_year + 1):
            filepath = self.data_dir / f"mlb_all_players_{year}.csv"
            if filepath.exists():
                df = pd.read_csv(filepath)
                all_years.append(df)
        
        if all_years:
            complete = pd.concat(all_years, ignore_index=True)
            complete = complete.sort_values(['season', 'team_name', 'fullName'])
            complete_path = self.data_dir / "mlb_all_players_complete.csv"
            complete.to_csv(complete_path, index=False)
    
    def run(self):
        """Execute delta scrape"""
        print("\n" + "="*80)
        print("MLB DELTA SCRAPER - INCREMENTAL UPDATE".center(80))
        print("="*80)
        print(f"\nCurrent time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("This will update existing data with new games and roster changes\n")
        
        if not self.data_dir.exists() or not list(self.data_dir.glob("*.csv")):
            print("❌ No existing data found!")
            print("💡 Run full scrape first: python src/scripts/mlb_scrape.py")
            return False
        
        # Update schedules
        schedules_updated = self.update_schedules()
        
        # Update rosters
        rosters_updated = self.update_current_rosters()
        
        # Summary
        self.print_header("Delta Update Complete")
        
        if schedules_updated or rosters_updated:
            print("✅ Data successfully updated!\n")
            if schedules_updated:
                print("   ✓ Schedule files updated with new games")
            if rosters_updated:
                print("   ✓ Player rosters refreshed")
        else:
            print("✓ All data is current - no updates needed\n")
        
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
        
        return True


def main():
    """Main entry point"""
    scraper = MLBDeltaScraper()
    
    try:
        success = scraper.run()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Delta scrape interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
