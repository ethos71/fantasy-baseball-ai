#!/usr/bin/env python3
"""
Backtesting and Weight Tuning System

This script analyzes historical game performance from 2022 onwards using all factor analyses
to determine optimal weights for sit/start recommendations. It compares predictions against
actual game results to tune weights for individual players on your roster.

Usage:
    python src/scripts/backtest_weights.py                    # Run for entire roster
    python src/scripts/backtest_weights.py --player "Ohtani"  # Run for specific player
    python src/scripts/backtest_weights.py --save             # Save tuned weights
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple
import argparse
from scipy.optimize import differential_evolution

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import all factor analysis modules
from scripts.fa import wind_analysis
from scripts.fa import matchup_fa
from scripts.fa import home_away_fa
from scripts.fa import platoon_fa
from scripts.fa import park_factors_fa
from scripts.fa import rest_day_fa
from scripts.fa import injury_fa
from scripts.fa import umpire_fa
from scripts.fa import temperature_fa
from scripts.fa import pitch_mix_fa
from scripts.fa import lineup_position_fa
from scripts.fa import time_of_day_fa
from scripts.fa import defensive_positions_fa


class WeightTuner:
    """Tunes factor analysis weights based on historical performance"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.data_dir = project_root / "data"
        self.config_dir = project_root / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Default weights for all factors
        self.default_weights = {
            'wind': 0.10,
            'matchup': 0.15,
            'home_away': 0.12,
            'platoon': 0.10,
            'park_factors': 0.08,
            'rest_day': 0.08,
            'injury': 0.12,
            'umpire': 0.05,
            'temperature': 0.05,
            'pitch_mix': 0.05,
            'lineup_position': 0.05,
            'time_of_day': 0.03,
            'defensive_positions': 0.02
        }
        
        # Load existing weights if available
        self.weights_file = self.config_dir / "factor_weights.json"
        self.player_weights_file = self.config_dir / "player_weights.json"
        
        self.global_weights = self.load_weights(self.weights_file, self.default_weights)
        self.player_weights = self.load_player_weights()
        
    def load_weights(self, file_path: Path, default: Dict) -> Dict:
        """Load weights from JSON file or return default"""
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading weights from {file_path}: {e}")
                return default.copy()
        return default.copy()
    
    def load_player_weights(self) -> Dict:
        """Load player-specific weights"""
        if self.player_weights_file.exists():
            try:
                with open(self.player_weights_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Error loading player weights: {e}")
                return {}
        return {}
    
    def save_weights(self, weights: Dict, file_path: Path):
        """Save weights to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(weights, f, indent=2)
            print(f"✓ Saved weights to {file_path}")
        except Exception as e:
            print(f"✗ Error saving weights to {file_path}: {e}")
    
    def load_roster(self) -> pd.DataFrame:
        """Load current Yahoo roster"""
        roster_file = self.data_dir / "yahoo_roster.csv"
        if not roster_file.exists():
            print("⚠️  No roster file found. Run yahoo_scrape.py first.")
            return pd.DataFrame()
        
        return pd.read_csv(roster_file)
    
    def load_historical_games(self, start_year: int = 2022) -> pd.DataFrame:
        """Load historical game data from start_year to present"""
        all_games = []
        
        current_year = datetime.now().year
        for year in range(start_year, current_year + 1):
            schedule_file = self.data_dir / f"mlb_{year}_schedule.csv"
            if schedule_file.exists():
                df = pd.read_csv(schedule_file)
                df['year'] = year
                all_games.append(df)
                print(f"  Loaded {len(df)} games from {year}")
        
        if not all_games:
            print("⚠️  No historical game data found")
            return pd.DataFrame()
        
        games_df = pd.concat(all_games, ignore_index=True)
        
        # Convert date column
        if 'game_date' in games_df.columns:
            games_df['game_date'] = pd.to_datetime(games_df['game_date'])
        
        # Filter to only completed games
        games_df = games_df[games_df['status'] == 'Final'].copy()
        
        print(f"\n✓ Loaded {len(games_df)} completed games from {start_year}-{current_year}")
        return games_df
    
    def load_player_stats(self) -> pd.DataFrame:
        """Load historical player statistics"""
        stats_file = self.data_dir / "mlb_all_players_complete.csv"
        if not stats_file.exists():
            print("⚠️  No player stats file found")
            return pd.DataFrame()
        
        return pd.read_csv(stats_file)
    
    def calculate_factor_scores(self, player: str, game_data: Dict, weights: Dict) -> Dict:
        """Calculate all factor analysis scores for a player/game"""
        scores = {}
        
        # Each factor returns a score between -1 and 1
        # Positive = favorable, Negative = unfavorable
        
        try:
            # Wind analysis
            wind_score = self.analyze_wind(game_data)
            scores['wind'] = wind_score * weights.get('wind', 0.10)
            
            # Matchup analysis (pitcher vs hitter history)
            matchup_score = self.analyze_matchup(player, game_data)
            scores['matchup'] = matchup_score * weights.get('matchup', 0.15)
            
            # Home/Away performance
            home_away_score = self.analyze_home_away(player, game_data)
            scores['home_away'] = home_away_score * weights.get('home_away', 0.12)
            
            # Platoon advantage
            platoon_score = self.analyze_platoon(player, game_data)
            scores['platoon'] = platoon_score * weights.get('platoon', 0.10)
            
            # Park factors
            park_score = self.analyze_park_factors(player, game_data)
            scores['park_factors'] = park_score * weights.get('park_factors', 0.08)
            
            # Rest days
            rest_score = self.analyze_rest_days(player, game_data)
            scores['rest_day'] = rest_score * weights.get('rest_day', 0.08)
            
            # Injury/recovery
            injury_score = self.analyze_injury(player, game_data)
            scores['injury'] = injury_score * weights.get('injury', 0.12)
            
            # Umpire
            umpire_score = self.analyze_umpire(game_data)
            scores['umpire'] = umpire_score * weights.get('umpire', 0.05)
            
            # Temperature
            temp_score = self.analyze_temperature(game_data)
            scores['temperature'] = temp_score * weights.get('temperature', 0.05)
            
            # Pitch mix
            pitch_mix_score = self.analyze_pitch_mix(player, game_data)
            scores['pitch_mix'] = pitch_mix_score * weights.get('pitch_mix', 0.05)
            
            # Lineup position
            lineup_score = self.analyze_lineup_position(player, game_data)
            scores['lineup_position'] = lineup_score * weights.get('lineup_position', 0.05)
            
            # Time of day
            time_score = self.analyze_time_of_day(player, game_data)
            scores['time_of_day'] = time_score * weights.get('time_of_day', 0.03)
            
            # Defensive positions
            defense_score = self.analyze_defensive_positions(game_data)
            scores['defensive_positions'] = defense_score * weights.get('defensive_positions', 0.02)
            
        except Exception as e:
            print(f"⚠️  Error calculating factor scores: {e}")
        
        return scores
    
    # Placeholder analysis functions (simplified for backtesting)
    def analyze_wind(self, game_data: Dict) -> float:
        """Analyze wind conditions"""
        wind_speed = game_data.get('wind_speed', 0)
        wind_direction = game_data.get('wind_direction', '')
        
        # Favorable: wind blowing out (to outfield)
        if 'out' in wind_direction.lower() or 'center' in wind_direction.lower():
            return min(wind_speed / 20.0, 1.0)  # 0 to 1
        # Unfavorable: wind blowing in
        elif 'in' in wind_direction.lower():
            return -min(wind_speed / 20.0, 1.0)  # 0 to -1
        return 0.0
    
    def analyze_matchup(self, player: str, game_data: Dict) -> float:
        """Analyze historical matchup performance"""
        # Simplified: check if pitcher/hitter has faced each other
        # In real implementation, use actual historical stats
        return np.random.uniform(-0.3, 0.3)  # Placeholder
    
    def analyze_home_away(self, player: str, game_data: Dict) -> float:
        """Analyze home vs away performance"""
        is_home = game_data.get('is_home', False)
        # Most players perform better at home
        return 0.2 if is_home else -0.1
    
    def analyze_platoon(self, player: str, game_data: Dict) -> float:
        """Analyze platoon advantage"""
        batter_hand = game_data.get('batter_hand', 'R')
        pitcher_hand = game_data.get('pitcher_hand', 'R')
        
        # Favorable: opposite handed matchup
        if batter_hand != pitcher_hand:
            return 0.3
        return -0.2
    
    def analyze_park_factors(self, player: str, game_data: Dict) -> float:
        """Analyze park hitting factors"""
        park = game_data.get('park', '')
        # Simplified park factors
        hitter_friendly = ['Coors Field', 'Great American Ball Park', 'Fenway Park']
        pitcher_friendly = ['Oracle Park', 'Marlins Park', 'Petco Park']
        
        if park in hitter_friendly:
            return 0.25
        elif park in pitcher_friendly:
            return -0.25
        return 0.0
    
    def analyze_rest_days(self, player: str, game_data: Dict) -> float:
        """Analyze rest day impact"""
        days_rest = game_data.get('days_rest', 0)
        
        # 1 day rest is optimal, 0 or 2+ less optimal
        if days_rest == 1:
            return 0.15
        elif days_rest == 0:
            return -0.1
        elif days_rest >= 3:
            return -0.15
        return 0.0
    
    def analyze_injury(self, player: str, game_data: Dict) -> float:
        """Analyze injury status"""
        injury_status = game_data.get('injury_status', 'Healthy')
        
        if injury_status == 'Healthy':
            return 0.0
        elif injury_status == 'Day-to-Day':
            return -0.3
        elif injury_status == 'Questionable':
            return -0.5
        return -0.8
    
    def analyze_umpire(self, game_data: Dict) -> float:
        """Analyze umpire tendencies"""
        # Simplified: some umpires favor pitchers/hitters
        return np.random.uniform(-0.1, 0.1)  # Placeholder
    
    def analyze_temperature(self, game_data: Dict) -> float:
        """Analyze temperature impact"""
        temp = game_data.get('temperature', 70)
        
        # Warm weather favors offense
        if temp >= 80:
            return 0.2
        elif temp <= 50:
            return -0.2
        return 0.0
    
    def analyze_pitch_mix(self, player: str, game_data: Dict) -> float:
        """Analyze pitcher's pitch mix vs player strength"""
        return np.random.uniform(-0.2, 0.2)  # Placeholder
    
    def analyze_lineup_position(self, player: str, game_data: Dict) -> float:
        """Analyze batting order position"""
        position = game_data.get('batting_order', 5)
        
        # Top of order gets more at-bats
        if position <= 3:
            return 0.15
        elif position >= 7:
            return -0.15
        return 0.0
    
    def analyze_time_of_day(self, player: str, game_data: Dict) -> float:
        """Analyze day vs night game performance"""
        game_time = game_data.get('game_time', '19:00')
        hour = int(game_time.split(':')[0]) if ':' in game_time else 19
        
        # Day games (before 5pm) can be harder to see
        if hour < 17:
            return -0.1
        return 0.05
    
    def analyze_defensive_positions(self, game_data: Dict) -> float:
        """Analyze defensive matchup"""
        return np.random.uniform(-0.1, 0.1)  # Placeholder
    
    def calculate_composite_score(self, scores: Dict) -> float:
        """Calculate composite score from all factors"""
        return sum(scores.values())
    
    def get_actual_performance(self, player: str, game_data: Dict) -> float:
        """Get actual game performance (fantasy points)"""
        # This should load actual stats from game results
        # For now, return placeholder based on game data
        
        # Fantasy scoring (example):
        # Singles: 3pts, Doubles: 5pts, Triples: 8pts, HR: 10pts
        # RBI: 2pts, Runs: 2pts, SB: 5pts, BB: 2pts
        
        stats = game_data.get('stats', {})
        
        fantasy_points = (
            stats.get('singles', 0) * 3 +
            stats.get('doubles', 0) * 5 +
            stats.get('triples', 0) * 8 +
            stats.get('home_runs', 0) * 10 +
            stats.get('rbi', 0) * 2 +
            stats.get('runs', 0) * 2 +
            stats.get('stolen_bases', 0) * 5 +
            stats.get('walks', 0) * 2 +
            stats.get('strikeouts', 0) * -1
        )
        
        return fantasy_points
    
    def backtest_player(self, player: str, games_df: pd.DataFrame, 
                       weights: Dict) -> Dict:
        """Backtest predictions for a single player"""
        
        print(f"\n{'='*60}")
        print(f"Backtesting: {player}")
        print(f"{'='*60}")
        
        results = {
            'player': player,
            'games_analyzed': 0,
            'predictions': [],
            'actuals': [],
            'scores': [],
            'accuracy': 0.0,
            'mae': 0.0,
            'rmse': 0.0
        }
        
        # Filter games for this player
        player_games = games_df[
            (games_df['home_team'].str.contains(player, case=False, na=False)) |
            (games_df['away_team'].str.contains(player, case=False, na=False))
        ].copy()
        
        if len(player_games) == 0:
            print(f"⚠️  No games found for {player}")
            return results
        
        print(f"Found {len(player_games)} games for {player}")
        
        for idx, game in player_games.iterrows():
            try:
                # Create game data dict
                game_data = game.to_dict()
                
                # Calculate factor scores
                factor_scores = self.calculate_factor_scores(player, game_data, weights)
                
                # Calculate composite score
                composite_score = self.calculate_composite_score(factor_scores)
                
                # Get actual performance
                actual_performance = self.get_actual_performance(player, game_data)
                
                # Store results
                results['predictions'].append(composite_score)
                results['actuals'].append(actual_performance)
                results['scores'].append(factor_scores)
                results['games_analyzed'] += 1
                
            except Exception as e:
                print(f"⚠️  Error processing game {idx}: {e}")
                continue
        
        # Calculate metrics
        if results['games_analyzed'] > 0:
            predictions = np.array(results['predictions'])
            actuals = np.array(results['actuals'])
            
            # Normalize actual performance to -1 to 1 scale for comparison
            if actuals.std() > 0:
                actuals_normalized = (actuals - actuals.mean()) / actuals.std()
            else:
                actuals_normalized = actuals
            
            # Calculate correlation (accuracy)
            if len(predictions) > 1:
                results['accuracy'] = np.corrcoef(predictions, actuals_normalized)[0, 1]
            
            # Calculate error metrics
            results['mae'] = np.mean(np.abs(predictions - actuals_normalized))
            results['rmse'] = np.sqrt(np.mean((predictions - actuals_normalized) ** 2))
        
        print(f"\n✓ Analyzed {results['games_analyzed']} games")
        print(f"  Accuracy (correlation): {results['accuracy']:.3f}")
        print(f"  MAE: {results['mae']:.3f}")
        print(f"  RMSE: {results['rmse']:.3f}")
        
        return results
    
    def optimize_weights(self, player: str, games_df: pd.DataFrame) -> Dict:
        """Optimize weights for a specific player using differential evolution"""
        
        print(f"\n{'='*60}")
        print(f"Optimizing weights for: {player}")
        print(f"{'='*60}")
        
        def objective_function(weight_values):
            """Objective function to minimize (negative correlation)"""
            weights = dict(zip(self.default_weights.keys(), weight_values))
            results = self.backtest_player(player, games_df, weights)
            # Return negative accuracy (we want to maximize correlation)
            return -results['accuracy']
        
        # Define bounds for each weight (0.0 to 0.3)
        bounds = [(0.0, 0.3) for _ in range(len(self.default_weights))]
        
        # Constraint: weights should sum to approximately 1.0
        # We'll handle this by normalizing after optimization
        
        print("\n🔧 Running optimization (this may take a few minutes)...")
        
        result = differential_evolution(
            objective_function,
            bounds,
            maxiter=20,  # Reduced for faster testing
            popsize=10,
            tol=0.01,
            workers=1,
            updating='deferred',
            seed=42
        )
        
        # Extract and normalize optimized weights
        optimized_values = result.x
        weight_sum = np.sum(optimized_values)
        if weight_sum > 0:
            optimized_values = optimized_values / weight_sum
        
        optimized_weights = dict(zip(self.default_weights.keys(), optimized_values))
        
        print("\n✓ Optimization complete!")
        print(f"  Best accuracy: {-result.fun:.3f}")
        
        return optimized_weights
    
    def run_backtest_suite(self, players: List[str], optimize: bool = False, 
                          save: bool = False):
        """Run backtesting for multiple players"""
        
        print("\n" + "="*80)
        print("FANTASY BASEBALL AI - WEIGHT BACKTESTING & TUNING".center(80))
        print("="*80)
        
        # Load data
        print("\n📊 Loading historical data...")
        roster_df = self.load_roster()
        games_df = self.load_historical_games(start_year=2022)
        stats_df = self.load_player_stats()
        
        if games_df.empty:
            print("❌ No historical data available. Run data refresh first.")
            return
        
        # If no players specified, use entire roster
        if not players:
            if not roster_df.empty:
                players = roster_df['Player'].unique().tolist()
                print(f"\n👥 Analyzing entire roster ({len(players)} players)")
            else:
                print("❌ No roster data available. Specify players manually.")
                return
        
        all_results = {}
        optimized_weights = {}
        
        for player in players:
            try:
                if optimize:
                    # Optimize weights for this player
                    player_weights = self.optimize_weights(player, games_df)
                    optimized_weights[player] = player_weights
                    
                    # Run backtest with optimized weights
                    results = self.backtest_player(player, games_df, player_weights)
                else:
                    # Use existing weights
                    weights = self.player_weights.get(player, self.global_weights)
                    results = self.backtest_player(player, games_df, weights)
                
                all_results[player] = results
                
            except Exception as e:
                print(f"❌ Error processing {player}: {e}")
                continue
        
        # Display summary
        self.display_summary(all_results, optimized_weights)
        
        # Save weights if requested
        if save and optimized_weights:
            self.save_optimized_weights(optimized_weights)
    
    def display_summary(self, results: Dict, optimized_weights: Dict):
        """Display summary of backtest results"""
        
        print("\n" + "="*80)
        print("BACKTEST RESULTS SUMMARY".center(80))
        print("="*80)
        
        if not results:
            print("\n❌ No results to display")
            return
        
        # Create summary table
        summary_data = []
        for player, result in results.items():
            summary_data.append({
                'Player': player,
                'Games': result['games_analyzed'],
                'Accuracy': f"{result['accuracy']:.3f}",
                'MAE': f"{result['mae']:.3f}",
                'RMSE': f"{result['rmse']:.3f}"
            })
        
        summary_df = pd.DataFrame(summary_data)
        print("\n" + summary_df.to_string(index=False))
        
        # Display optimized weights if available
        if optimized_weights:
            print("\n" + "="*80)
            print("OPTIMIZED WEIGHTS".center(80))
            print("="*80)
            
            for player, weights in optimized_weights.items():
                print(f"\n{player}:")
                for factor, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True):
                    print(f"  {factor:25s}: {weight:.4f}")
    
    def save_optimized_weights(self, optimized_weights: Dict):
        """Save optimized player weights"""
        
        # Merge with existing player weights
        self.player_weights.update(optimized_weights)
        
        # Save to file
        self.save_weights(self.player_weights, self.player_weights_file)
        
        print(f"\n✓ Saved optimized weights for {len(optimized_weights)} players")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Backtest and tune factor analysis weights',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/scripts/backtest_weights.py                    # Backtest entire roster
  python src/scripts/backtest_weights.py --player "Ohtani"  # Backtest one player
  python src/scripts/backtest_weights.py --optimize         # Optimize weights
  python src/scripts/backtest_weights.py --optimize --save  # Optimize and save
        """
    )
    
    parser.add_argument(
        '--player',
        type=str,
        help='Specific player to analyze (default: all roster players)'
    )
    
    parser.add_argument(
        '--optimize',
        action='store_true',
        help='Optimize weights using differential evolution'
    )
    
    parser.add_argument(
        '--save',
        action='store_true',
        help='Save optimized weights to config file'
    )
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    # Create tuner
    tuner = WeightTuner(project_root)
    
    # Determine players to analyze
    players = [args.player] if args.player else []
    
    # Run backtest suite
    try:
        tuner.run_backtest_suite(
            players=players,
            optimize=args.optimize,
            save=args.save
        )
        
        print("\n✅ Backtesting complete!")
        
        if not args.save and args.optimize:
            print("\n💡 Tip: Add --save flag to persist optimized weights")
        
    except KeyboardInterrupt:
        print("\n\n❌ Operation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
