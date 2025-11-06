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

import os
import sys
import json
import webbrowser
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
        self.project_root = Path(__file__).parent.parent.parent
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
        """Get user's teams"""
        self.print_header("Finding Your Teams")
        data = self.request("users;use_login=1/games;game_keys=mlb/teams")
        
        teams = []
        games = data['fantasy_content']['users']['0']['user'][1]['games']
        
        for key in games:
            if key == 'count': continue
            for item in games[key]['game']:
                if isinstance(item, dict) and 'teams' in item:
                    for i in range(int(item['teams']['count'])):
                        team = item['teams'][str(i)]['team'][0]
                        info = {
                            'key': team[0]['team_key'],
                            'name': team[2]['name']
                        }
                        teams.append(info)
                        print(f"  ✓ {info['name']}")
        
        return teams
    
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
        
        # Get all teams
        all_teams = self.get_teams()
        
        # Fetch target teams
        self.print_header("Fetching Target Teams")
        all_rosters = []
        
        for team in all_teams:
            if team['name'] in self.TARGET_TEAMS:
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
            for team in self.TARGET_TEAMS:
                count = len(df[df['fantasy_team'] == team])
                if count > 0:
                    print(f"   {team}: {count} players")
        
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
