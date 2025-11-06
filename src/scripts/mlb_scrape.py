"""
MLB Stats API Scraper
Based on: https://github.com/MajorLeagueBaseball/google-cloud-mlb-hackathon

This script provides functionality to scrape MLB statistics using the official MLB Stats API.
It supports fetching schedules, game data, team rosters, player information, and live game feeds.
"""

import requests
import json
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, List, Any
import time


class MLBStatsScraper:
    """Scraper for MLB Stats API (GUMBO data feeds)"""
    
    BASE_URL = "https://statsapi.mlb.com/api"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MLB-Stats-Scraper/1.0'
        })
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to MLB Stats API"""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error making request to {url}: {e}")
            return {}
    
    def get_schedule(self, season: int = 2024, game_type: str = "R", 
                     team_id: Optional[int] = None, 
                     start_date: Optional[str] = None,
                     end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get MLB schedule for a season
        
        Args:
            season: Season year (default: 2024)
            game_type: R=Regular Season, P=Postseason, S=Spring Training
            team_id: Optional team ID to filter by specific team
            start_date: Optional start date (format: MM/DD/YYYY)
            end_date: Optional end date (format: MM/DD/YYYY)
        
        Returns:
            Schedule data as dictionary
        """
        params = {
            'sportId': 1,  # MLB
            'season': season,
            'gameType': game_type
        }
        
        if team_id:
            params['teamId'] = team_id
        if start_date:
            params['startDate'] = start_date
        if end_date:
            params['endDate'] = end_date
        
        print(f"Fetching {season} MLB schedule (game_type={game_type})...")
        return self._make_request('/v1/schedule', params)
    
    def get_game_pks_from_schedule(self, schedule_data: Dict[str, Any]) -> List[int]:
        """Extract game PKs from schedule data"""
        game_pks = []
        for date in schedule_data.get('dates', []):
            for game in date.get('games', []):
                game_pks.append(game['gamePk'])
        return game_pks
    
    def get_live_game_feed(self, game_pk: int, timecode: Optional[str] = None) -> Dict[str, Any]:
        """
        Get GUMBO live game feed for a specific game
        
        Args:
            game_pk: Game ID (can be obtained from schedule)
            timecode: Optional timestamp (format: yyyymmdd_######)
        
        Returns:
            Complete game state data
        """
        endpoint = f"/v1.1/game/{game_pk}/feed/live"
        params = {'timecode': timecode} if timecode else None
        
        print(f"Fetching live game feed for game {game_pk}...")
        return self._make_request(endpoint, params)
    
    def get_game_timestamps(self, game_pk: int) -> List[str]:
        """Get list of available timestamps for a game"""
        endpoint = f"/v1.1/game/{game_pk}/feed/live/timestamps"
        data = self._make_request(endpoint)
        return data.get('timestamps', [])
    
    def get_team_roster(self, team_id: int, season: int = 2024) -> Dict[str, Any]:
        """
        Get team roster for a specific season
        
        Args:
            team_id: MLB team ID (e.g., 119 for LA Dodgers)
            season: Season year
        
        Returns:
            Roster data including player information
        """
        endpoint = f"/v1/teams/{team_id}/roster"
        params = {'season': season}
        
        print(f"Fetching roster for team {team_id}, season {season}...")
        return self._make_request(endpoint, params)
    
    def get_team_info(self, team_id: int, season: Optional[int] = None) -> Dict[str, Any]:
        """Get detailed team information"""
        endpoint = f"/v1/teams/{team_id}"
        params = {'season': season} if season else None
        
        print(f"Fetching team info for team {team_id}...")
        return self._make_request(endpoint, params)
    
    def get_all_teams(self, season: Optional[int] = None) -> Dict[str, Any]:
        """Get all MLB teams"""
        endpoint = "/v1/teams"
        params = {'sportId': 1}
        if season:
            params['season'] = season
        
        print("Fetching all MLB teams...")
        return self._make_request(endpoint, params)
    
    def get_player_info(self, player_id: int, season: Optional[int] = None) -> Dict[str, Any]:
        """
        Get detailed player information
        
        Args:
            player_id: MLB player ID
            season: Optional season year
        
        Returns:
            Player data including stats
        """
        endpoint = f"/v1/people/{player_id}"
        params = {'season': season} if season else None
        
        print(f"Fetching player info for player {player_id}...")
        return self._make_request(endpoint, params)
    
    def get_player_stats(self, player_id: int, season: int = 2024, 
                         stats_group: str = "hitting") -> Dict[str, Any]:
        """Get player stats with hydration"""
        endpoint = f"/v1/people/{player_id}"
        params = {
            'season': season,
            'hydrate': f'stats(group={stats_group},type=season)'
        }
        
        print(f"Fetching {stats_group} stats for player {player_id}...")
        return self._make_request(endpoint, params)
    
    def export_schedule_to_csv(self, schedule_data: Dict[str, Any], filename: str = "mlb_schedule.csv"):
        """Export schedule data to CSV"""
        games = []
        for date in schedule_data.get('dates', []):
            for game in date.get('games', []):
                games.append({
                    'game_pk': game['gamePk'],
                    'game_date': game['officialDate'],
                    'game_type': game['gameType'],
                    'season': game['season'],
                    'away_team': game['teams']['away']['team']['name'],
                    'away_team_id': game['teams']['away']['team']['id'],
                    'home_team': game['teams']['home']['team']['name'],
                    'home_team_id': game['teams']['home']['team']['id'],
                    'venue': game['venue']['name'],
                    'status': game['status']['detailedState']
                })
        
        df = pd.DataFrame(games)
        df.to_csv(filename, index=False)
        print(f"Exported {len(games)} games to {filename}")
        return df
    
    def export_roster_to_csv(self, roster_data: Dict[str, Any], filename: str = "team_roster.csv", 
                            team_id: Optional[int] = None, team_name: Optional[str] = None, 
                            season: Optional[int] = None):
        """Export roster data to CSV"""
        players = []
        for player in roster_data.get('roster', []):
            person = player['person']
            position = player['position']
            players.append({
                'player_id': person['id'],
                'player_name': person['fullName'],
                'team_id': team_id,
                'team_name': team_name,
                'season': season,
                'jersey_number': player.get('jerseyNumber', 'N/A'),
                'position': position['name'],
                'position_type': position['type'],
                'status': player['status']['description']
            })
        
        df = pd.DataFrame(players)
        df.to_csv(filename, index=False)
        print(f"Exported {len(players)} players to {filename}")
        return df
    
    def export_all_teams_to_csv(self, teams_data: Dict[str, Any], filename: str = "mlb_teams.csv"):
        """Export all teams data to CSV"""
        teams_list = []
        for team in teams_data.get('teams', []):
            teams_list.append({
                'team_id': team['id'],
                'team_name': team['name'],
                'team_abbreviation': team.get('abbreviation', 'N/A'),
                'team_code': team.get('teamCode', 'N/A'),
                'file_code': team.get('fileCode', 'N/A'),
                'location_name': team.get('locationName', 'N/A'),
                'team_short_name': team.get('teamName', 'N/A'),
                'league': team.get('league', {}).get('name', 'N/A'),
                'division': team.get('division', {}).get('name', 'N/A'),
                'venue_name': team.get('venue', {}).get('name', 'N/A'),
                'first_year': team.get('firstYearOfPlay', 'N/A'),
                'active': team.get('active', True)
            })
        
        df = pd.DataFrame(teams_list)
        df.to_csv(filename, index=False)
        print(f"Exported {len(teams_list)} teams to {filename}")
        return df


def main():
    """Example usage of MLB Stats Scraper - Fetches data for all teams and players across multiple years"""
    scraper = MLBStatsScraper()
    
    # Calculate years to fetch (current year + last 3 years)
    current_year = datetime.now().year
    years = [current_year - i for i in range(4)]  # [2025, 2024, 2023, 2022]
    
    print("=" * 70)
    print("MLB Stats API Scraper - Complete Multi-Year Data Collection")
    print("=" * 70)
    print(f"Fetching data for years: {', '.join(map(str, years))}")
    print()
    
    # Step 1: Get all MLB teams
    print("=" * 70)
    print("STEP 1: Fetching All MLB Teams")
    print("=" * 70)
    teams_data = scraper.get_all_teams(season=current_year)
    teams = teams_data.get('teams', [])
    print(f"Found {len(teams)} MLB teams")
    
    # Export teams to CSV
    scraper.export_all_teams_to_csv(teams_data, "data/mlb_all_teams.csv")
    print()
    
    # Step 2: Get schedules for all years
    print("=" * 70)
    print("STEP 2: Fetching Schedules for All Years")
    print("=" * 70)
    all_schedules = []
    for year in years:
        print(f"Fetching {year} schedule...")
        schedule = scraper.get_schedule(season=year, game_type='R')
        if schedule:
            total_games = sum(len(date.get('games', [])) for date in schedule.get('dates', []))
            print(f"- {year}: Found {total_games} games")
            
            if schedule.get('dates'):
                scraper.export_schedule_to_csv(schedule, f"data/mlb_{year}_schedule.csv")
                all_schedules.append((year, schedule))
        time.sleep(0.5)  # Rate limiting
    print()
    
    # Step 3: Get rosters for all teams across all years
    print("=" * 70)
    print("STEP 3: Fetching Rosters for All Teams Across All Years")
    print("=" * 70)
    print(f"This will fetch {len(teams)} teams × {len(years)} years = {len(teams) * len(years)} rosters")
    print("This may take several minutes...")
    print()
    
    all_players = []
    team_count = 0
    
    for year in years:
        print(f"\n--- Fetching {year} Rosters ---")
        year_players = []
        
        for team in teams:
            team_id = team['id']
            team_name = team['name']
            team_count += 1
            
            print(f"[{team_count}/{len(teams) * len(years)}] {team_name} ({year})...", end=" ")
            
            roster = scraper.get_team_roster(team_id=team_id, season=year)
            if roster and 'roster' in roster:
                num_players = len(roster['roster'])
                print(f"{num_players} players")
                
                # Extract player data
                for player in roster['roster']:
                    person = player['person']
                    position = player['position']
                    year_players.append({
                        'player_id': person['id'],
                        'player_name': person['fullName'],
                        'team_id': team_id,
                        'team_name': team_name,
                        'season': year,
                        'jersey_number': player.get('jerseyNumber', 'N/A'),
                        'position': position['name'],
                        'position_type': position['type'],
                        'status': player['status']['description']
                    })
            else:
                print("No data")
            
            time.sleep(0.2)  # Rate limiting
        
        # Export year's players to CSV
        if year_players:
            df_year = pd.DataFrame(year_players)
            df_year.to_csv(f"data/mlb_all_players_{year}.csv", index=False)
            print(f"\n✓ Exported {len(year_players)} players for {year}")
            all_players.extend(year_players)
    
    print()
    print("=" * 70)
    
    # Step 4: Create consolidated all-players file
    print("STEP 4: Creating Consolidated Player Database")
    print("=" * 70)
    if all_players:
        df_all = pd.DataFrame(all_players)
        df_all.to_csv("data/mlb_all_players_complete.csv", index=False)
        print(f"✓ Exported complete database: {len(all_players)} total player-season records")
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"- Total player-season records: {len(all_players)}")
        print(f"- Unique players: {df_all['player_id'].nunique()}")
        print(f"- Teams: {len(teams)}")
        print(f"- Years: {len(years)}")
    print()
    
    # Step 5: Sample player stats
    print("=" * 70)
    print("STEP 5: Sample Player Stats (Shohei Ohtani)")
    print("=" * 70)
    player = scraper.get_player_info(player_id=660271)
    if player and 'people' in player:
        person = player['people'][0]
        print(f"Name: {person['fullName']}")
        print(f"Position: {person['primaryPosition']['name']}")
        print(f"Birth Date: {person.get('birthDate', 'N/A')}")
        print(f"Bats/Throws: {person.get('batSide', {}).get('code', 'N/A')}/{person.get('pitchHand', {}).get('code', 'N/A')}")
        
        print("\nStats by Year:")
        for year in years:
            stats = scraper.get_player_stats(player_id=660271, season=year, stats_group='hitting')
            if stats and 'people' in stats:
                person_data = stats['people'][0]
                if 'stats' in person_data and person_data['stats']:
                    for stat_group in person_data['stats']:
                        if 'splits' in stat_group and stat_group['splits']:
                            stat_data = stat_group['splits'][0].get('stat', {})
                            print(f"  {year}: AVG: {stat_data.get('avg', 'N/A')}, HR: {stat_data.get('homeRuns', 'N/A')}, RBI: {stat_data.get('rbi', 'N/A')}")
                            break
            time.sleep(0.2)
    print()
    
    print("=" * 70)
    print("DATA COLLECTION COMPLETE!")
    print("=" * 70)
    print(f"\nGenerated Files:")
    print(f"  - mlb_all_teams.csv")
    print(f"  - mlb_{{year}}_schedule.csv (4 files)")
    print(f"  - mlb_all_players_{{year}}.csv (4 files)")
    print(f"  - mlb_all_players_complete.csv (consolidated)")
    print(f"\nTotal: {len(all_players)} player-season records across {len(years)} years")
    print("=" * 70)


if __name__ == "__main__":
    # Create data directory if it doesn't exist
    import os
    os.makedirs("data", exist_ok=True)
    
    main()
