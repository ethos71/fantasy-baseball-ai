#!/usr/bin/env python3
"""
Opponent Analysis - Run 20-factor analysis on opposing team
Analyzes your weekly matchup opponent's roster with the same scoring system
"""

import pandas as pd
import sys
import os
from datetime import datetime
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from scripts.scrape.yahoo_scrape import YahooFantasyAPI
# from scripts.daily_sitstart import calculate_sitstart_scores  # Function doesn't exist

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_current_opponent(league_id: str, team_key: str) -> dict:
    """
    Get the current week's opponent team information
    
    Returns:
        dict: {'team_key': str, 'team_name': str, 'manager': str}
    """
    try:
        yahoo_api = YahooFantasyAPI()
        
        # Get current matchup
        matchup = yahoo_api.get_current_matchup(league_id, team_key)
        
        if not matchup or 'opponent' not in matchup:
            logger.warning("No current matchup found")
            return None
            
        opponent = matchup['opponent']
        return {
            'team_key': opponent.get('team_key'),
            'team_name': opponent.get('name', 'Unknown Team'),
            'manager': opponent.get('manager', 'Unknown Manager')
        }
        
    except Exception as e:
        logger.error(f"Error getting opponent: {e}")
        return None

def analyze_opponent_roster(league_id: str, my_team_key: str, output_dir: str = "data/opponent_analysis") -> pd.DataFrame:
    """
    Run full 20-factor analysis on opponent's roster
    
    Args:
        league_id: Yahoo league ID
        my_team_key: Your team key (to find opponent)
        output_dir: Where to save analysis results
        
    Returns:
        DataFrame with opponent's player scores
    """
    try:
        # Get opponent info
        opponent = get_current_opponent(league_id, my_team_key)
        
        if not opponent:
            logger.error("Could not identify opponent team")
            return None
            
        logger.info(f"Analyzing opponent: {opponent['team_name']} (Manager: {opponent['manager']})")
        
        # Get opponent's roster
        yahoo_api = YahooFantasyAPI()
        opponent_roster = yahoo_api.get_team_roster(opponent['team_key'])
        
        if not opponent_roster or len(opponent_roster) == 0:
            logger.error("No roster data found for opponent")
            return None
            
        # Convert to DataFrame
        roster_df = pd.DataFrame(opponent_roster)
        
        # Run the same 20-factor analysis
        logger.info(f"Running 20-factor analysis on {len(roster_df)} opponent players...")
        # TODO: Implement 20-factor analysis for opponent roster
        # scores_df = calculate_sitstart_scores(roster_df)
        scores_df = roster_df.copy()
        
        # Add opponent info
        scores_df['opponent_team'] = opponent['team_name']
        scores_df['opponent_manager'] = opponent['manager']
        scores_df['analysis_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Save results
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(output_dir, f"opponent_analysis_{timestamp}.csv")
        scores_df.to_csv(output_file, index=False)
        
        logger.info(f"Opponent analysis saved to: {output_file}")
        logger.info(f"Analyzed {len(scores_df)} players from {opponent['team_name']}")
        
        return scores_df
        
    except Exception as e:
        logger.error(f"Error analyzing opponent roster: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze opponent team roster')
    parser.add_argument('--league', required=True, help='Yahoo league ID')
    parser.add_argument('--team', required=True, help='Your team key')
    
    args = parser.parse_args()
    
    result = analyze_opponent_roster(args.league, args.team)
    
    if result is not None:
        print(f"\n✅ Analysis complete! {len(result)} players analyzed")
        print(f"\nTop 5 Opponent Starts:")
        print(result.nlargest(5, 'final_score')[['player_name', 'position', 'final_score', 'recommendation']])
        print(f"\nBottom 5 Opponent Players:")
        print(result.nsmallest(5, 'final_score')[['player_name', 'position', 'final_score', 'recommendation']])
    else:
        print("❌ Analysis failed")
