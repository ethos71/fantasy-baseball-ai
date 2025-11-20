#!/usr/bin/env python3
"""
Daily Sit/Start Decision Maker

This script provides a repeatable process to be run 30 minutes before game time:
1. Get data deltas (recent games, weather updates)
2. Run all 20 Factor Analyses
3. Tune weights for each player on your current roster
4. Provide sit/start recommendations
5. Suggest waiver wire pickups for weak performers

Usage:
    python src/scripts/daily_sitstart.py                    # Run for today's games
    python src/scripts/daily_sitstart.py --date 2025-09-29  # Run for specific date
    python src/scripts/daily_sitstart.py --skip-tune        # Skip weight tuning (faster)
    python src/scripts/daily_sitstart.py --tune-only        # Only tune weights, no recommendations
    python src/scripts/daily_sitstart.py --skip-waiver      # Skip waiver wire suggestions
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import argparse
from typing import Dict, Optional
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import waiver wire analyzer
from scripts.waiver_wire import WaiverWireAnalyzer


class DailySitStartManager:
    """Manages daily sit/start decision process"""
    
    def __init__(self, project_root: Path, target_date: Optional[str] = None, week_mode: bool = False):
        self.project_root = project_root
        self.data_dir = project_root / "data"
        self.scripts_dir = project_root / "src" / "scripts"
        self.config_dir = project_root / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Parse target date or use today
        if target_date:
            self.target_date = datetime.strptime(target_date, "%Y-%m-%d")
        else:
            self.target_date = datetime.now()
        
        self.week_mode = week_mode
        if week_mode:
            # Analyze 7 days starting from target_date
            self.start_date = self.target_date
            self.end_date = self.target_date + timedelta(days=6)
            print(f"\n🎯 Target Week: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        else:
            print(f"\n🎯 Target Date: {self.target_date.strftime('%Y-%m-%d')}")
    
    def print_header(self, text: str):
        """Print formatted section header"""
        print(f"\n{'='*80}")
        print(f"{text.center(80)}")
        print(f"{'='*80}\n")
    
    def run_script(self, script_path: str, description: str, check_success: bool = True) -> bool:
        """Run a Python script"""
        full_path = self.project_root / script_path
        
        if not full_path.exists():
            print(f"⚠️  Script not found: {script_path}")
            return False
        
        print(f"\n▶ {description}...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(full_path)],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print(f"  ✓ {description} completed")
                return True
            else:
                print(f"  ⚠️  {description} had issues (continuing)")
                if check_success:
                    print(f"     Error: {result.stderr[:200]}")
                return False
                
        except Exception as e:
            print(f"  ✗ Error running {description}: {e}")
            return False
    
    def step1_update_data(self) -> bool:
        """Step 1: Run delta updates to get latest data"""
        self.print_header("STEP 1: Update Data (Deltas)")
        
        print("Fetching latest MLB data and weather updates...")
        
        # Run MLB delta scraper
        mlb_success = self.run_script(
            "src/scripts/scrape/mlb_delta_scrape.py",
            "MLB Delta Update",
            check_success=False
        )
        
        # Run weather delta scraper
        weather_success = self.run_script(
            "src/scripts/scrape/weather_delta_scrape.py",
            "Weather Delta Update",
            check_success=False
        )
        
        # Fetch Yahoo roster
        _ = self.run_script(
            "src/scripts/scrape/yahoo_scrape.py",
            "Yahoo Roster Fetch",
            check_success=False
        )
        
        if mlb_success and weather_success:
            print("\n✓ Data updates completed successfully")
            return True
        else:
            print("\n⚠️  Some data updates had issues, but continuing...")
            return True
    
    def step2_run_all_factor_analyses(self) -> bool:
        """Step 2: Run all 20 factor analyses (for both all players and roster)"""
        self.print_header("STEP 2: Run All Factor Analyses (20 Factors)")
        
        # Run the consolidated FA runner script with target date
        script_path = self.project_root / "src" / "scripts" / "run_all_fa.py"
        target_date_str = self.target_date.strftime("%Y-%m-%d")
        
        # First run: All players (for waiver wire)
        print(f"\n▶ Running analyses for ALL MLB players (for waiver wire)...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path), "--date", target_date_str, "--all-players"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print(f"  ✓ All-players analysis completed")
                all_players_success = True
            else:
                print(f"  ⚠️  All-players analysis had issues (continuing)")
                print(f"     Error: {result.stderr[:200]}")
                all_players_success = False
                
        except Exception as e:
            print(f"  ✗ Error running all-players analysis: {e}")
            all_players_success = False
        
        # Second run: Rostered players only (for sit/start)
        print(f"\n▶ Running analyses for ROSTERED players (for sit/start)...")
        
        try:
            result = subprocess.run(
                [sys.executable, str(script_path), "--date", target_date_str],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                print(f"  ✓ Roster analysis completed")
                roster_success = True
            else:
                print(f"  ⚠️  Roster analysis had issues (continuing)")
                print(f"     Error: {result.stderr[:200]}")
                roster_success = False
                
        except Exception as e:
            print(f"  ✗ Error running roster analysis: {e}")
            roster_success = False
        
        # Success if at least roster analysis completed
        return roster_success
    
    def step3_tune_weights(self) -> bool:
        """Step 3: Tune weights for roster players"""
        self.print_header("STEP 3: Tune Weights for Roster Players")
        
        print("Running weight optimization based on historical performance...")
        print("This may take several minutes depending on roster size...\n")
        
        # Check if backtest script exists
        backtest_script = self.scripts_dir / "backtest_weights.py"
        if not backtest_script.exists():
            print("⚠️  Backtest script not found - skipping weight tuning")
            print("    Using default weights for recommendations")
            return True
        
        # Run backtest with optimize and save flags
        try:
            result = subprocess.run(
                [sys.executable, str(backtest_script), "--optimize", "--save"],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                check=False
            )
            
            if result.returncode == 0:
                print("✓ Weight tuning completed successfully")
                # Show key output lines
                output_lines = result.stdout.split('\n')
                for line in output_lines[-20:]:  # Last 20 lines
                    if 'Correlation' in line or 'saved' in line or 'optimized' in line.lower():
                        print(f"  {line}")
                return True
            else:
                print("⚠️  Weight tuning encountered issues")
                print("    Using default/existing weights")
                return True
                
        except subprocess.TimeoutExpired:
            print("⚠️  Weight tuning timed out - using default weights")
            return True
        except Exception as e:
            print(f"⚠️  Weight tuning error: {e}")
            print("    Using default/existing weights")
            return True
    
    def step4_generate_recommendations(self) -> Dict:
        """Step 4: Generate sit/start recommendations"""
        self.print_header("STEP 4: Generate Sit/Start Recommendations")
        
        # Load latest roster - try both file patterns
        roster_file = self._get_latest_file("yahoo_fantasy_rosters_*.csv")
        if not roster_file:
            roster_file = self._get_latest_file("yahoo_roster_*.csv")
        
        if not roster_file:
            print("❌ No roster file found!")
            print("   Make sure Yahoo roster fetch completed successfully")
            return {}
        
        print(f"Loading roster: {roster_file.name}")
        roster_df = pd.read_csv(roster_file)
        
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
        
        # Normalize column names (handle different roster formats)
        if 'mlb_team' in roster_df.columns and 'team' not in roster_df.columns:
            # Map abbreviations to full names
            roster_df['team'] = roster_df['mlb_team'].map(TEAM_MAP)
            # Fill unmapped with original abbrev
            roster_df['team'].fillna(roster_df['mlb_team'], inplace=True)
        if 'name' in roster_df.columns and 'player_name' not in roster_df.columns:
            roster_df['player_name'] = roster_df['name']
        
        print(f"Found {len(roster_df)} players on roster\n")
        
        # Load all factor analysis results
        recommendations = self._combine_factor_analyses(roster_df)
        
        return recommendations
    
    def _get_latest_file(self, pattern: str) -> Optional[Path]:
        """Get the most recent file matching pattern"""
        files = sorted(self.data_dir.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
        return files[0] if files else None
    
    def _combine_factor_analyses(self, roster_df: pd.DataFrame) -> Dict:
        """Combine all factor analysis results for roster players"""
        
        # Find all factor analysis output files
        fa_files = {
            'wind': self._get_latest_file('wind_analysis_*.csv'),
            'matchup': self._get_latest_file('matchup_analysis_*.csv'),
            'home_away': self._get_latest_file('home_away_analysis_*.csv'),
            'rest': self._get_latest_file('rest_day_analysis_*.csv'),
            'injury': self._get_latest_file('injury_analysis_*.csv'),
            'umpire': self._get_latest_file('umpire_analysis_*.csv'),
            'platoon': self._get_latest_file('platoon_analysis_*.csv'),
            'temperature': self._get_latest_file('temperature_analysis_*.csv'),
            'pitch_mix': self._get_latest_file('pitch_mix_analysis_*.csv'),
            'park': self._get_latest_file('park_factors_analysis_*.csv'),
            'lineup': self._get_latest_file('lineup_position_analysis_*.csv'),
            'time': self._get_latest_file('time_of_day_analysis_*.csv'),
            'defense': self._get_latest_file('defensive_positions_analysis_*.csv'),
            'recent_form': self._get_latest_file('recent_form_analysis_*.csv'),
            'bullpen': self._get_latest_file('bullpen_fatigue_analysis_*.csv'),
            'humidity': self._get_latest_file('humidity_elevation_analysis_*.csv'),
            'monthly': self._get_latest_file('monthly_splits_analysis_*.csv'),
            'momentum': self._get_latest_file('team_momentum_analysis_*.csv'),
            'statcast': self._get_latest_file('statcast_metrics_analysis_*.csv'),
            'vegas': self._get_latest_file('vegas_odds_analysis_*.csv'),
        }
        
        # Load player-specific weights if they exist
        weights = self._load_weights()
        
        # Combine scores for each player
        recommendations = {}
        
        for _, player_row in roster_df.iterrows():
            player_name = player_row.get('player_name', player_row.get('name', 'Unknown'))
            player_id = player_row.get('player_id', None)
            
            # Get scores from each factor
            scores = {}
            for factor_name, file_path in fa_files.items():
                if file_path and file_path.exists():
                    score = self._get_player_score(file_path, player_name, player_id)
                    if score is not None:
                        scores[factor_name] = score
            
            if scores:
                # Get player-specific weights or use defaults
                player_weights = weights.get(player_name, self._default_weights())
                
                # Calculate weighted final score
                final_score = self._calculate_final_score(scores, player_weights)
                
                recommendations[player_name] = {
                    'final_score': final_score,
                    'individual_scores': scores,
                    'weights': player_weights,
                    'recommendation': self._get_recommendation(final_score)
                }
        
        return recommendations
    
    def _get_player_score(self, file_path: Path, player_name: str, player_id: Optional[int]) -> Optional[float]:
        """Extract player's score from a factor analysis file"""
        try:
            df = pd.read_csv(file_path)
            
            # Try matching by name
            mask = df['player_name'].str.contains(player_name, case=False, na=False)
            if mask.any():
                row = df[mask].iloc[0]
                # Look for score column (check multiple patterns)
                score_columns = [
                    'score', 'final_score', 'advantage_score', 'impact_score',
                    'platoon_score', 'temp_score', 'pitch_mix_score', 'park_score',
                    'lineup_score', 'time_score', 'defense_score', 'form_score',
                    'bullpen_score', 'humidity_score', 'monthly_score', 'momentum_score',
                    'statcast_score', 'vegas_score', 'wind_score', 'umpire_score'
                ]
                # Also check for any column ending with '_score'
                for col in df.columns:
                    if col.endswith('_score') and col not in score_columns:
                        score_columns.append(col)
                
                for col in score_columns:
                    if col in df.columns:
                        return float(row[col])
            
            # Try matching by ID if available
            if player_id and 'player_id' in df.columns:
                mask = df['player_id'] == player_id
                if mask.any():
                    row = df[mask].iloc[0]
                    score_columns = [
                        'score', 'final_score', 'advantage_score', 'impact_score',
                        'platoon_score', 'temp_score', 'pitch_mix_score', 'park_score',
                        'lineup_score', 'time_score', 'defense_score', 'form_score',
                        'bullpen_score', 'humidity_score', 'monthly_score', 'momentum_score',
                        'statcast_score', 'vegas_score', 'wind_score', 'umpire_score'
                    ]
                    for col in df.columns:
                        if col.endswith('_score') and col not in score_columns:
                            score_columns.append(col)
                    
                    for col in score_columns:
                        if col in df.columns:
                            return float(row[col])
            
            return None
            
        except Exception:
            return None
    
    def _load_weights(self) -> Dict:
        """Load player-specific weights from config"""
        weight_file = self.config_dir / "player_weights.json"
        
        if weight_file.exists():
            try:
                with open(weight_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {}
    
    def _default_weights(self) -> Dict[str, float]:
        """Default factor weights (optimized based on research)"""
        return {
            'vegas': 0.169,       # 16.9% - Elite predictor (15-20% improvement)
            'statcast': 0.115,    # 11.5% - Elite predictor (10-15% improvement)
            'matchup': 0.087,     #  8.7% - High impact (8-12% improvement)
            'bullpen': 0.087,     #  8.7% - High impact (8-12% improvement)
            'platoon': 0.081,     #  8.1% - High impact (8-12% improvement)
            'home_away': 0.058,   #  5.8% - Medium impact (5-8% improvement)
            'injury': 0.057,      #  5.7% - Medium impact (5-8% improvement)
            'park': 0.056,        #  5.6% - Medium impact (5-8% improvement)
            'recent_form': 0.046, #  4.6% - Medium impact (5-8% improvement)
            'wind': 0.045,        #  4.5% - Medium impact (5-8% improvement)
            'rest': 0.034,        #  3.4% - Moderate impact (3-5% improvement)
            'temperature': 0.032, #  3.2% - Moderate impact (3-5% improvement)
            'lineup': 0.026,      #  2.6% - Moderate impact (3-5% improvement)
            'umpire': 0.025,      #  2.5% - Moderate impact (3-5% improvement)
            'pitch_mix': 0.021,   #  2.1% - Moderate impact (3-5% improvement)
            'time': 0.017,        #  1.7% - Supporting (1-3% improvement)
            'humidity': 0.014,    #  1.4% - Supporting (1-3% improvement)
            'defense': 0.013,     #  1.3% - Supporting (1-3% improvement)
            'monthly': 0.009,     #  0.9% - Supporting (1-3% improvement)
            'momentum': 0.008,    #  0.8% - Supporting (1-3% improvement)
        }
    
    def _calculate_final_score(self, scores: Dict[str, float], weights: Dict[str, float]) -> float:
        """Calculate weighted final score"""
        total_score = 0.0
        
        for factor, score in scores.items():
            weight = weights.get(factor, 0.0)
            total_score += score * weight
        
        return total_score
    
    def _get_recommendation(self, score: float) -> str:
        """Convert score to recommendation based on realistic score distribution"""
        # Adjusted thresholds based on actual score distribution (-0.25 to +0.25 typical range)
        # Using percentile-based cutoffs for more meaningful recommendations
        if score >= 0.15:
            return "🌟 STRONG START - Top tier matchup"
        elif score >= 0.05:
            return "✅ FAVORABLE - Good matchup"
        elif score >= -0.05:
            return "⚖️  NEUTRAL - Average matchup"
        elif score >= -0.15:
            return "⚠️  UNFAVORABLE - Poor matchup"
        else:
            return "🚫 BENCH - Very poor matchup"
    
    def display_recommendations(self, recommendations: Dict):
        """Display sit/start recommendations"""
        self.print_header("SIT/START RECOMMENDATIONS")
        
        if not recommendations:
            print("❌ No recommendations available")
            print("   Make sure factor analyses have run successfully")
            return
        
        # Sort by final score (descending)
        sorted_players = sorted(
            recommendations.items(),
            key=lambda x: x[1]['final_score'],
            reverse=True
        )
        
        print(f"{'Player':<25} {'Score':>8} {'Recommendation':<40}")
        print("=" * 80)
        
        for player_name, data in sorted_players:
            score = data['final_score']
            rec = data['recommendation']
            print(f"{player_name:<25} {score:>8.2f} {rec}")
        
        # Show detailed breakdown for top 3 and bottom 3
        print("\n" + "="*80)
        print("DETAILED FACTOR BREAKDOWN (Top 3 Starts)")
        print("="*80)
        
        for i, (player_name, data) in enumerate(sorted_players[:3]):
            print(f"\n{i+1}. {player_name} (Score: {data['final_score']:.2f})")
            print(f"   {data['recommendation']}")
            print("\n   Factor Scores:")
            
            for factor, score in sorted(data['individual_scores'].items(), key=lambda x: x[1], reverse=True):
                weight = data['weights'].get(factor, 0.0)
                print(f"     • {factor:12s}: {score:>6.2f} (weight: {weight:.0%})")
        
        print("\n" + "="*80)
        print("DETAILED FACTOR BREAKDOWN (Top 3 Sits)")
        print("="*80)
        
        for i, (player_name, data) in enumerate(sorted_players[-3:]):
            print(f"\n{i+1}. {player_name} (Score: {data['final_score']:.2f})")
            print(f"   {data['recommendation']}")
            print("\n   Factor Scores:")
            
            for factor, score in sorted(data['individual_scores'].items(), key=lambda x: x[1]):
                weight = data['weights'].get(factor, 0.0)
                print(f"     • {factor:12s}: {score:>6.2f} (weight: {weight:.0%})")
        
        # Save to CSV
        self._save_recommendations(recommendations)
    
    def _save_recommendations(self, recommendations: Dict):
        """Save recommendations to CSV file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.data_dir / f"sitstart_recommendations_{timestamp}.csv"
        
        rows = []
        for player_name, data in recommendations.items():
            row = {
                'player_name': player_name,
                'final_score': data['final_score'],
                'recommendation': data['recommendation'],
            }
            # Add individual factor scores
            for factor, score in data['individual_scores'].items():
                row[f'{factor}_score'] = score
                row[f'{factor}_weight'] = data['weights'].get(factor, 0.0)
            
            rows.append(row)
        
        df = pd.DataFrame(rows)
        df = df.sort_values('final_score', ascending=False)
        df.to_csv(output_file, index=False)
        
        print(f"\n💾 Recommendations saved to: {output_file.name}")
    
    def step5_analyze_waiver_wire(self, recommendations: Dict) -> None:
        """Step 5: Analyze waiver wire opportunities"""
        self.print_header("STEP 5: Waiver Wire Analysis")
        
        print("Analyzing waiver wire opportunities for weak performers...")
        
        try:
            # Load schedule
            schedule_file = self.data_dir / "mlb_2025_schedule.csv"
            if not schedule_file.exists():
                print("  ⚠️  No schedule file found, skipping waiver analysis")
                return
            
            schedule_df = pd.read_csv(schedule_file)
            if 'game_date' in schedule_df.columns:
                schedule_df['game_date'] = pd.to_datetime(schedule_df['game_date'])
            
            # Load roster
            roster_files = sorted(self.data_dir.glob("yahoo_fantasy_rosters_*.csv"),
                                 key=lambda x: x.stat().st_mtime, reverse=True)
            if not roster_files:
                print("  ⚠️  No roster file found, skipping waiver analysis")
                return
            
            roster_df = pd.read_csv(roster_files[0])
            rostered_players = roster_df['player_name'].tolist() if 'player_name' in roster_df.columns else roster_df['name'].tolist() if 'name' in roster_df.columns else []
            
            # Initialize waiver analyzer
            waiver_analyzer = WaiverWireAnalyzer(self.data_dir)
            
            # Load free agents (all players minus rostered)
            print(f"\n  Loading all-player analysis results...")
            fa_scores_df = waiver_analyzer.load_free_agents(rostered_players)
            
            if fa_scores_df.empty:
                print("  ⚠️  No all-player analysis found!")
                print("  💡 Run: python src/scripts/run_all_fa.py --all-players")
                print("\n  Showing drop candidates from current roster only...\n")
            else:
                print(f"  ✓ Loaded {len(fa_scores_df)} free agents")
                
                # Find best waiver pickups
                print("\n" + "=" * 80)
                print("TOP WAIVER WIRE RECOMMENDATIONS")
                print("=" * 80)
                
                top_pickups = waiver_analyzer.find_best_waiver_pickups(
                    roster_df, schedule_df, fa_scores_df, recommendations, top_n=10
                )
                
                if len(top_pickups) > 0:
                    print(f"\n{'Player':<20} {'Team':>5} {'Score':>6} {'Games':>6} {'Coors':>6} {'Reason':<40}")
                    print("-" * 95)
                    
                    for _, row in top_pickups.iterrows():
                        print(f"{row['player_name']:<20} {row['team']:>5} {row['waiver_score']:>6.1f} "
                              f"{row['upcoming_games']:>6} {row['coors_games']:>6} {row['reasons']:<40}")
                else:
                    print("  No strong waiver candidates found")
            
            # Generate drop candidate analysis
            print("\n" + "=" * 80)
            print("ROSTER ANALYSIS - Drop Candidates")
            print("=" * 80)
            
            drop_candidates = waiver_analyzer.suggest_drop_candidates(
                roster_df, recommendations
            )
            
            if len(drop_candidates) > 0:
                weak_performers = drop_candidates[
                    drop_candidates['drop_priority'].str.contains('DROP|CONSIDER')
                ]
                
                if len(weak_performers) > 0:
                    print("\n⚠️  WEAKEST PERFORMERS THIS WEEK:")
                    print("-" * 80)
                    print(f"{'Player':<25} {'Avg Score':>10} {'Priority':<30}")
                    print("-" * 80)
                    
                    for _, row in weak_performers.head(5).iterrows():
                        print(f"{row['player_name']:<25} {row['avg_score']:>10.2f} {row['drop_priority']:<30}")
                    
                    print("\n💡 Consider these players for streaming/replacement")
                else:
                    print("\n✅ No clear drop candidates - all players have acceptable matchups")
            
            print("\n" + "=" * 80)
            print("WAIVER WIRE STRATEGY TIPS:")
            print("=" * 80)
            print("""
🏔️  COORS FIELD PLAYS:
   • Look for players with upcoming series at Colorado
   • Even weak hitters perform well at Coors
   • Stream for those series, then drop

📅 HIGH VOLUME WEEKS:
   • Target players with 7+ games this week
   • More at-bats = more counting stats
   
⚖️  PLATOON ADVANTAGES:
   • Check upcoming pitcher handedness
   • Stream platoon players for favorable matchups

🏟️  HITTER-FRIENDLY PARKS:
   • CIN (Great American Ball Park)
   • TEX (Globe Life Field)  
   • CHC (Wrigley Field on windy days)
   • BAL (Camden Yards)
   • ARI (Chase Field)
            """)
            
        except Exception as e:
            print(f"  ⚠️  Waiver wire analysis error: {e}")
            import traceback
            traceback.print_exc()
    
    def run_full_process(self, skip_tune: bool = False, tune_only: bool = False, 
                        skip_waiver: bool = False):
        """Run the complete daily sit/start process"""
        self.print_header(f"DAILY SIT/START PROCESS - {self.target_date.strftime('%Y-%m-%d')}")
        
        start_time = datetime.now()
        print(f"Started at: {start_time.strftime('%H:%M:%S')}")
        print("\nThis process should be run 30 minutes before first game time.")
        
        if not tune_only:
            # Step 1: Update data
            if not self.step1_update_data():
                print("\n⚠️  Data update had issues, continuing anyway...")
            
            # Step 2: Run factor analyses
            if not self.step2_run_all_factor_analyses():
                print("\n⚠️  Some factor analyses failed, results may be incomplete")
        
        # Step 3: Tune weights (unless skipped)
        if not skip_tune:
            if not self.step3_tune_weights():
                print("\n⚠️  Weight tuning had issues, using default weights")
        else:
            print("\n⏭️  Skipping weight tuning (--skip-tune flag)")
        
        if tune_only:
            print("\n✓ Weight tuning complete")
            return
        
        # Step 4: Generate and display recommendations
        recommendations = self.step4_generate_recommendations()
        self.display_recommendations(recommendations)
        
        # Step 5: Waiver wire analysis (unless skipped)
        if not skip_waiver:
            self.step5_analyze_waiver_wire(recommendations)
        else:
            print("\n⏭️  Skipping waiver wire analysis (--skip-waiver flag)")
        
        # Summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self.print_header("PROCESS COMPLETE")
        print(f"Started:  {start_time.strftime('%H:%M:%S')}")
        print(f"Finished: {end_time.strftime('%H:%M:%S')}")
        print(f"Duration: {duration:.1f} seconds ({duration/60:.1f} minutes)")
        print(f"\n✅ Sit/Start recommendations ready for {self.target_date.strftime('%Y-%m-%d')}")
        if not skip_waiver:
            print("✅ Waiver wire analysis complete")
        print("\n💡 Run this script 30 minutes before game time for best results")
        print("="*80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description='Daily Sit/Start Decision Maker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/scripts/daily_sitstart.py                      # Run for today
  python src/scripts/daily_sitstart.py --date 2025-09-29    # Run for specific date
  python src/scripts/daily_sitstart.py --skip-tune          # Skip weight tuning (faster)
  python src/scripts/daily_sitstart.py --tune-only          # Only tune weights

Workflow:
  1. Updates data (MLB delta, weather delta, Yahoo roster)
  2. Runs all 20 factor analyses
  3. Tunes weights for roster players (optional)
  4. Generates sit/start recommendations

Run 30 minutes before game time for optimal decisions.
        """
    )
    
    parser.add_argument(
        '--date',
        type=str,
        help='Target date (YYYY-MM-DD format, defaults to today)'
    )
    
    parser.add_argument(
        '--skip-tune',
        action='store_true',
        help='Skip weight tuning (faster, uses existing/default weights)'
    )
    
    parser.add_argument(
        '--tune-only',
        action='store_true',
        help='Only run weight tuning, skip recommendations'
    )
    
    parser.add_argument(
        '--skip-waiver',
        action='store_true',
        help='Skip waiver wire pickup analysis'
    )
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    # Create manager
    manager = DailySitStartManager(project_root, args.date)
    
    try:
        manager.run_full_process(
            skip_tune=args.skip_tune, 
            tune_only=args.tune_only,
            skip_waiver=args.skip_waiver
        )
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n❌ Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
