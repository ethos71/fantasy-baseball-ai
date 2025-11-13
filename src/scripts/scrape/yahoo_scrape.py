#!/usr/bin/env python3
"""
Yahoo Fantasy Baseball API Client

Uses Yahoo's official Fantasy Sports API (OAuth) with browser authentication.

Requirements:
    pip install yahoo-oauth requests

Setup:
    1. Go to https://developer.yahoo.com/apps/create/
    2. Create app with Fantasy Sports permissions
    3. Set Redirect URI to: https://localhost:8080
    4. Credentials are already configured in oauth2.json
    5. Run script - browser opens automatically for OAuth
    6. Authorize in browser
    7. Script fetches roster data automatically

Teams: "I like big bunts", "Pure uncut adam west"
"""

import sys
from datetime import datetime
from pathlib import Path
import pandas as pd

try:
    from yahoo_oauth import OAuth2
except ImportError:
    print("❌ Install required packages: pip install yahoo-oauth")
    sys.exit(1)


class YahooFantasyAPI:
    """Yahoo Fantasy Sports API client"""
    
    BASE_URL = "https://fantasysports.yahooapis.com/fantasy/v2"
    TARGET_TEAMS = ["I Like BIG Bunts", "Pure Uncut Adam West"]
    
    def __init__(self):
        self.oauth = None
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.oauth_file = self.project_root / "oauth2.json"
        
    def print_header(self, text):
        print(f"\n{'='*80}\n{text.center(80)}\n{'='*80}\n")
    
    def setup_oauth(self):
        """Setup OAuth2 - will open browser automatically"""
        self.print_header("OAuth Authentication")
        
        if not self.oauth_file.exists():
            print("❌ oauth2.json not found!")
            print("\nCredentials are already configured in oauth2.json")
            print("Make sure the file exists with your Yahoo API keys.")
            return False
        
        print("🌐 Opening browser for Yahoo authentication...")
        print("   Please authorize the app in your browser")
        print("   You may need to copy/paste the verification code\n")
        
        try:
            self.oauth = OAuth2(None, None, from_file=str(self.oauth_file))
            
            if not self.oauth.token_is_valid():
                print("🔄 Token expired or missing, refreshing...")
                # This will automatically open browser if needed
                
            print("✓ OAuth authentication successful!")
            return True
        except Exception as e:
            print(f"❌ OAuth failed: {e}")
            print("\nTroubleshooting:")
            print("1. Make sure oauth2.json has correct credentials")
            print("2. Browser should open automatically for authorization")
            print("3. If browser doesn't open, check the URL printed above")
            return False
    
    def request(self, endpoint):
        """Make API request"""
        url = f"{self.BASE_URL}/{endpoint}"
        return self.oauth.session.get(url, params={'format': 'json'}).json()
    
    def get_teams(self):
        """Get user's teams for the current/most recent MLB season"""
        self.print_header("Finding Your Teams")
        
        # Get all leagues
        try:
            data = self.request("users;use_login=1/games;game_codes=mlb/leagues")
        except Exception as e:
            print(f"⚠️  Error fetching teams: {e}")
            return []
        
        teams = []
        games = data['fantasy_content']['users']['0']['user'][1]['games']
        
        # Look for the most recent season (highest game key)
        game_keys = [k for k in games.keys() if k != 'count']
        
        # Process games in reverse order (most recent first)
        for key in sorted(game_keys, reverse=True):
            game_data = games[key]['game']
            if not isinstance(game_data, list):
                continue
                
            # Get game info
            game_info = game_data[0]
            season = game_info.get('season', '')
            _ = game_info.get('game_key', '')
            
            print(f"\n  Checking {season} season...")
            
            # Look for leagues in this game
            for item in game_data:
                if isinstance(item, dict) and 'leagues' in item:
                    league_count = int(item['leagues'].get('count', 0))
                    
                    for i in range(league_count):
                        if str(i) not in item['leagues']:
                            continue
                            
                        league_list = item['leagues'][str(i)]['league']
                        
                        # League data is a list with a single dict containing all fields
                        if not league_list or not isinstance(league_list, list):
                            continue
                        
                        league_data = league_list[0]  # First item has all the data
                        
                        # Extract league info directly from the dict
                        league_key = league_data.get('league_key')
                        league_name = league_data.get('name')
                        
                        if league_key:
                            # Get user's team in this league
                            team_info = self._get_user_team_in_league(league_key, league_name, season)
                            if team_info:
                                teams.append(team_info)
            
            # If we found teams, stop (use most recent season)
            if teams:
                break
        
        return teams
    
    def _get_user_guid(self):
        """Get the current user's GUID"""
        if not hasattr(self, 'user_guid'):
            try:
                data = self.request("users;use_login=1")
                self.user_guid = data['fantasy_content']['users']['0']['user'][0]['guid']
            except Exception as e:
                print(f"⚠️  Error getting user GUID: {e}")
                self.user_guid = None
        return self.user_guid
    
    def _get_user_team_in_league(self, league_key, league_name, season):
        """Get the user's team within a specific league"""
        try:
            user_guid = self._get_user_guid()
            if not user_guid:
                return None
                
            data = self.request(f"league/{league_key}/teams")
            teams_data = data['fantasy_content']['league'][1]['teams']
            
            # Find the team owned by the user (check manager GUID)
            team_count = int(teams_data.get('count', 0))
            
            for i in range(team_count):
                if str(i) not in teams_data:
                    continue
                    
                team = teams_data[str(i)]['team'][0]
                
                # Extract team info
                team_key = None
                team_name = None
                is_owned = False
                
                for t_item in team:
                    if isinstance(t_item, dict):
                        if 'team_key' in t_item:
                            team_key = t_item['team_key']
                        if 'name' in t_item:
                            team_name = t_item['name']
                        if 'managers' in t_item:
                            # Check if any manager has the user's GUID
                            for manager_item in t_item['managers']:
                                if isinstance(manager_item, dict) and 'manager' in manager_item:
                                    manager_guid = manager_item['manager'].get('guid', '')
                                    if manager_guid == user_guid:
                                        is_owned = True
                                        break
                
                if is_owned and team_key and team_name:
                    print(f"    ✓ {team_name} (in {league_name})")
                    return {
                        'key': team_key,
                        'name': team_name,
                        'league': league_name,
                        'season': season
                    }
            
        except Exception as e:
            print(f"    ⚠️  Error fetching team from {league_name}: {e}")
            import traceback
            traceback.print_exc()
        
        return None
    
    def get_roster(self, team_key, team_name):
        """Get team roster"""
        print(f"\n📊 Fetching '{team_name}'...")
        data = self.request(f"team/{team_key}/roster")
        
        roster = data['fantasy_content']['team'][1]['roster']['0']['players']
        players = []
        
        for i in range(int(roster['count'])):
            p_data = roster[str(i)]['player'][0]
            player = {}
            
            for item in p_data:
                if isinstance(item, dict):
                    if 'name' in item:
                        player['name'] = item['name']['full']
                    elif 'eligible_positions' in item:
                        pos = item['eligible_positions']
                        player['positions'] = ', '.join([pos[str(j)]['position'] 
                                                        for j in range(len(pos)) if str(j) in pos])
                    elif 'selected_position' in item:
                        player['position'] = item['selected_position'][1]['position']
                    elif 'editorial_team_abbr' in item:
                        player['mlb_team'] = item['editorial_team_abbr']
            
            players.append({
                'fantasy_team': team_name,
                'player_name': player.get('name', ''),
                'mlb_team': player.get('mlb_team', ''),
                'position': player.get('position', ''),
                'eligible_positions': player.get('positions', ''),
                'scraped_at': datetime.now().isoformat()
            })
            print(f"  ✓ {player.get('name')} - {player.get('mlb_team')} ({player.get('position')})")
        
        return players
    
    def run(self):
        """Execute workflow"""
        print("\n" + "="*80)
        print("YAHOO FANTASY BASEBALL API CLIENT".center(80))
        print("="*80)
        
        if not self.setup_oauth():
            return False
        
        # Get all user's teams
        all_teams = self.get_teams()
        
        if not all_teams:
            print("\n⚠️  No teams found!")
            return False
        
        # Fetch rosters from all teams
        self.print_header(f"Fetching Rosters from {len(all_teams)} Team(s)")
        all_rosters = []
        
        for team in all_teams:
            roster = self.get_roster(team['key'], team['name'])
            all_rosters.extend(roster)
        
        # Export
        if all_rosters:
            df = pd.DataFrame(all_rosters)
            self.data_dir.mkdir(exist_ok=True)
            filename = f"yahoo_fantasy_rosters_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = self.data_dir / filename
            df.to_csv(filepath, index=False)
            
            print(f"\n✅ Exported {len(all_rosters)} players to:")
            print(f"   {filepath}")
            
            # Show count by team
            for team_name in df['fantasy_team'].unique():
                count = len(df[df['fantasy_team'] == team_name])
                print(f"   {team_name}: {count} players")
        
        return True


def main():
    print("\n✨ Yahoo Fantasy API - Official OAuth")
    print("Setup: https://developer.yahoo.com/apps/create/\n")
    
    api = YahooFantasyAPI()
    try:
        api.run()
    except KeyboardInterrupt:
        print("\n❌ Cancelled")
        sys.exit(1)


if __name__ == "__main__":
    main()
