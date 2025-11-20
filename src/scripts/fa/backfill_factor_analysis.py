#!/usr/bin/env python3
"""
Backfill Factor Analysis for Historical Data (2022-2024)

This script processes factor analysis for all players across multiple years.
It is designed to be resumable - can pick up where it left off if interrupted.

Features:
- Processes one date at a time to manage memory
- Saves progress after each date
- Skips already processed dates
- Generates comprehensive factor analysis for all 20 factors
- Can be interrupted and resumed without data loss

Usage:
    # Full backfill (2022-2024)
    python src/scripts/backfill_factor_analysis.py
    
    # Specific year
    python src/scripts/backfill_factor_analysis.py --year 2023
    
    # Specific date range
    python src/scripts/backfill_factor_analysis.py --start-date 2023-04-01 --end-date 2023-04-30
    
    # Resume from last checkpoint
    python src/scripts/backfill_factor_analysis.py --resume
"""

import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import time

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

# Constants
CHECKPOINT_FILE = "data/backfill_checkpoint.json"
OUTPUT_DIR = Path("data/historical_factor_analysis")
BATCH_SIZE = 1  # Process one date at a time


class BackfillManager:
    """Manages backfill process with checkpointing and resume capability"""
    
    def __init__(self, start_date, end_date, force_restart=False):
        self.start_date = pd.to_datetime(start_date)
        self.end_date = pd.to_datetime(end_date)
        self.force_restart = force_restart
        self.checkpoint = self._load_checkpoint()
        
        # Create output directory
        OUTPUT_DIR.mkdir(exist_ok=True)
        
    def _load_checkpoint(self):
        """Load checkpoint from file or create new one"""
        if self.force_restart and Path(CHECKPOINT_FILE).exists():
            Path(CHECKPOINT_FILE).unlink()
            
        if Path(CHECKPOINT_FILE).exists():
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        else:
            return {
                'last_completed_date': None,
                'total_dates_processed': 0,
                'failed_dates': [],
                'start_time': datetime.now().isoformat(),
                'last_update': None
            }
    
    def _save_checkpoint(self, current_date, success=True):
        """Save checkpoint to file"""
        self.checkpoint['last_completed_date'] = current_date.strftime('%Y-%m-%d')
        self.checkpoint['total_dates_processed'] += 1
        self.checkpoint['last_update'] = datetime.now().isoformat()
        
        if not success:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str not in self.checkpoint['failed_dates']:
                self.checkpoint['failed_dates'].append(date_str)
        
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)
    
    def get_dates_to_process(self):
        """Get list of dates that need processing"""
        all_dates = pd.date_range(self.start_date, self.end_date, freq='D')
        
        if self.checkpoint['last_completed_date']:
            last_date = pd.to_datetime(self.checkpoint['last_completed_date'])
            # Resume from next date after checkpoint
            remaining_dates = [d for d in all_dates if d > last_date]
            print(f"📍 Resuming from {last_date.strftime('%Y-%m-%d')}")
            print(f"   Already processed: {self.checkpoint['total_dates_processed']} dates")
            return remaining_dates
        else:
            return list(all_dates)
    
    def get_progress_stats(self):
        """Get current progress statistics"""
        total_dates = (self.end_date - self.start_date).days + 1
        processed = self.checkpoint['total_dates_processed']
        remaining = total_dates - processed
        
        if processed > 0:
            start_time = pd.to_datetime(self.checkpoint['start_time'])
            elapsed = datetime.now() - start_time
            avg_time_per_date = elapsed.total_seconds() / processed
            estimated_remaining = timedelta(seconds=avg_time_per_date * remaining)
            
            return {
                'total_dates': total_dates,
                'processed': processed,
                'remaining': remaining,
                'percent_complete': (processed / total_dates) * 100,
                'elapsed_time': str(elapsed).split('.')[0],
                'estimated_remaining': str(estimated_remaining).split('.')[0],
                'failed_dates': len(self.checkpoint['failed_dates'])
            }
        else:
            return {
                'total_dates': total_dates,
                'processed': 0,
                'remaining': total_dates,
                'percent_complete': 0,
                'elapsed_time': '00:00:00',
                'estimated_remaining': 'calculating...',
                'failed_dates': 0
            }


def run_factor_analysis_for_date(target_date, data_dir):
    """Run all 20 factor analyses for a specific date
    
    Args:
        target_date: Date to analyze (pd.Timestamp)
        data_dir: Path to data directory
        
    Returns:
        pd.DataFrame: Combined results or None if failed
    """
    date_str = target_date.strftime('%Y-%m-%d')
    
    # Check if output already exists (skip if so)
    output_file = OUTPUT_DIR / f"factor_analysis_{target_date.strftime('%Y%m%d')}.csv"
    if output_file.exists():
        print(f"   ⏭️  Skipping {date_str} - already exists")
        return pd.DataFrame()  # Return empty but successful
    
    print(f"   🔄 Processing {date_str}...")
    
    results = {}
    
    try:
        # Load required data files
        roster_files = sorted(data_dir.glob('yahoo_fantasy_rosters_*.csv'))
        if not roster_files:
            print(f"      ⚠️  No roster file found, skipping")
            return None
        
        roster_df = pd.read_csv(roster_files[-1])
        players = roster_df['player_name'].unique().tolist()
        
        # Run each factor analysis
        factors = [
            ('vegas', vegas_odds_fa),
            ('statcast', statcast_metrics_fa),
            ('matchup', matchup_fa),
            ('bullpen', bullpen_fatigue_fa),
            ('platoon', platoon_fa),
            ('home_away', home_away_fa),
            ('injury', injury_fa),
            ('park', park_factors_fa),
            ('recent_form', recent_form_fa),
            ('wind', wind_analysis),
            ('rest', rest_day_fa),
            ('temperature', temperature_fa),
            ('lineup', lineup_position_fa),
            ('umpire', umpire_fa),
            ('pitch_mix', pitch_mix_fa),
            ('time_of_day', time_of_day_fa),
            ('humidity', humidity_elevation_fa),
            ('defense', defensive_positions_fa),
            ('monthly', monthly_splits_fa),
            ('momentum', team_momentum_fa)
        ]
        
        all_scores = []
        
        for player in players:
            player_scores = {'player_name': player, 'date': date_str}
            
            for factor_name, factor_module in factors:
                try:
                    # Call the analyze function with date
                    if hasattr(factor_module, 'analyze'):
                        result = factor_module.analyze(player, data_dir, as_of_date=target_date)
                        if isinstance(result, dict):
                            player_scores[f'{factor_name}_score'] = result.get('score', 0)
                        else:
                            player_scores[f'{factor_name}_score'] = result if result else 0
                    else:
                        player_scores[f'{factor_name}_score'] = 0
                except Exception as e:
                    # Silently fail individual factors to continue processing
                    player_scores[f'{factor_name}_score'] = 0
            
            all_scores.append(player_scores)
        
        # Combine into dataframe
        df_results = pd.DataFrame(all_scores)
        
        # Save to file
        df_results.to_csv(output_file, index=False)
        print(f"      ✅ Saved {len(df_results)} player records")
        
        return df_results
        
    except Exception as e:
        print(f"      ❌ Error processing {date_str}: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Backfill factor analysis for historical data')
    parser.add_argument('--year', type=int, help='Process specific year (e.g., 2023)')
    parser.add_argument('--start-date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    parser.add_argument('--force-restart', action='store_true', help='Restart from beginning, ignoring checkpoint')
    
    args = parser.parse_args()
    
    # Determine date range
    if args.year:
        start_date = f"{args.year}-01-01"
        end_date = f"{args.year}-12-31"
    elif args.start_date and args.end_date:
        start_date = args.start_date
        end_date = args.end_date
    else:
        # Default: 2022-2024 full backfill
        start_date = "2022-01-01"
        end_date = "2024-12-31"
    
    print("="*80)
    print("🔄 Factor Analysis Backfill Tool")
    print("="*80)
    print(f"\n📅 Date Range: {start_date} to {end_date}")
    
    # Initialize backfill manager
    manager = BackfillManager(start_date, end_date, force_restart=args.force_restart)
    
    # Get dates to process
    dates_to_process = manager.get_dates_to_process()
    
    if not dates_to_process:
        print("\n✅ All dates already processed!")
        return
    
    print(f"📊 Total dates to process: {len(dates_to_process)}")
    
    # Show progress stats
    stats = manager.get_progress_stats()
    print(f"\n📈 Progress:")
    print(f"   Completed: {stats['processed']}/{stats['total_dates']} ({stats['percent_complete']:.1f}%)")
    print(f"   Remaining: {stats['remaining']} dates")
    print(f"   Elapsed: {stats['elapsed_time']}")
    print(f"   Estimated remaining: {stats['estimated_remaining']}")
    if stats['failed_dates'] > 0:
        print(f"   ⚠️  Failed: {stats['failed_dates']} dates")
    
    print(f"\n🚀 Starting backfill...")
    print(f"💾 Checkpoint file: {CHECKPOINT_FILE}")
    print(f"📁 Output directory: {OUTPUT_DIR}")
    print(f"\n{'='*80}\n")
    
    data_dir = Path('data')
    
    # Process each date
    for i, current_date in enumerate(dates_to_process, 1):
        date_str = current_date.strftime('%Y-%m-%d')
        
        print(f"\n[{i}/{len(dates_to_process)}] Processing {date_str}")
        
        start_time = time.time()
        
        # Run factor analysis
        result = run_factor_analysis_for_date(current_date, data_dir)
        
        elapsed = time.time() - start_time
        
        # Save checkpoint
        success = result is not None
        manager._save_checkpoint(current_date, success=success)
        
        if success:
            print(f"   ✅ Completed in {elapsed:.1f}s")
        else:
            print(f"   ❌ Failed after {elapsed:.1f}s")
        
        # Update progress
        stats = manager.get_progress_stats()
        print(f"   📊 Progress: {stats['percent_complete']:.1f}% | ETA: {stats['estimated_remaining']}")
    
    print(f"\n{'='*80}")
    print("✅ Backfill Complete!")
    print(f"{'='*80}")
    
    final_stats = manager.get_progress_stats()
    print(f"\n📈 Final Statistics:")
    print(f"   Total processed: {final_stats['processed']} dates")
    print(f"   Total time: {final_stats['elapsed_time']}")
    print(f"   Failed dates: {final_stats['failed_dates']}")
    
    if manager.checkpoint['failed_dates']:
        print(f"\n⚠️  Failed dates that need attention:")
        for date in manager.checkpoint['failed_dates']:
            print(f"   - {date}")


if __name__ == '__main__':
    main()
