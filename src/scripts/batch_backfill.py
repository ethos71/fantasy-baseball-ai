#!/usr/bin/env python3
"""
Daily Batch Processor for Factor Analysis Backfill

Processes factor analysis in daily batches with better error handling
and memory management. Designed for long-running operations.

Usage:
    # Process single day
    python src/scripts/batch_backfill.py --date 2023-04-15
    
    # Process month
    python src/scripts/batch_backfill.py --month 2023-04
    
    # Process year
    python src/scripts/batch_backfill.py --year 2023
    
    # Auto-resume mode (processes next pending date)
    python src/scripts/batch_backfill.py --auto
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import time

# Constants
CHECKPOINT_FILE = Path("data/batch_checkpoint.txt")
LOG_DIR = Path("data/backfill_logs")


def get_last_processed_date():
    """Get the last successfully processed date from checkpoint"""
    if CHECKPOINT_FILE.exists():
        with open(CHECKPOINT_FILE, 'r') as f:
            date_str = f.read().strip()
            if date_str:
                return datetime.strptime(date_str, '%Y-%m-%d')
    return None


def save_checkpoint(date):
    """Save checkpoint for date"""
    CHECKPOINT_FILE.parent.mkdir(exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        f.write(date.strftime('%Y-%m-%d'))


def process_single_date(date):
    """Process factor analysis for a single date using daily_sitstart.py
    
    Args:
        date: datetime object
        
    Returns:
        bool: True if successful, False otherwise
    """
    date_str = date.strftime('%Y-%m-%d')
    
    print(f"\n{'='*80}")
    print(f"Processing: {date_str}")
    print(f"{'='*80}\n")
    
    # Create log file
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"backfill_{date.strftime('%Y%m%d')}.log"
    
    start_time = time.time()
    
    try:
        # Run daily_sitstart.py for this date
        cmd = [
            'python3',
            'src/scripts/daily_sitstart.py',
            '--date', date_str,
            '--skip-tune'  # Skip weight tuning for faster processing
        ]
        
        print(f"Command: {' '.join(cmd)}")
        print(f"Log file: {log_file}\n")
        
        with open(log_file, 'w') as log:
            result = subprocess.run(
                cmd,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True
            )
        
        elapsed = time.time() - start_time
        
        if result.returncode == 0:
            print(f"\n✅ Success! Completed in {elapsed:.1f}s")
            save_checkpoint(date)
            return True
        else:
            print(f"\n❌ Failed with exit code {result.returncode}")
            print(f"   Check log: {log_file}")
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n❌ Exception after {elapsed:.1f}s: {str(e)}")
        return False


def process_date_range(start_date, end_date):
    """Process a range of dates
    
    Args:
        start_date: datetime
        end_date: datetime
    """
    current = start_date
    total_days = (end_date - start_date).days + 1
    
    print(f"\n🔄 Batch Processing: {total_days} days")
    print(f"   Start: {start_date.strftime('%Y-%m-%d')}")
    print(f"   End:   {end_date.strftime('%Y-%m-%d')}")
    
    # Check for resume
    last_processed = get_last_processed_date()
    if last_processed and last_processed >= start_date:
        current = last_processed + timedelta(days=1)
        print(f"\n📍 Resuming from: {current.strftime('%Y-%m-%d')}")
    
    processed = 0
    failed = 0
    
    while current <= end_date:
        day_num = (current - start_date).days + 1
        
        print(f"\n[{day_num}/{total_days}] Date: {current.strftime('%Y-%m-%d')}")
        
        success = process_single_date(current)
        
        if success:
            processed += 1
        else:
            failed += 1
            response = input(f"\n⚠️  Processing failed. Continue? (y/n): ")
            if response.lower() != 'y':
                break
        
        current += timedelta(days=1)
        
        # Brief pause between dates
        time.sleep(1)
    
    print(f"\n{'='*80}")
    print(f"Batch Complete!")
    print(f"{'='*80}")
    print(f"✅ Processed: {processed}")
    print(f"❌ Failed: {failed}")


def main():
    parser = argparse.ArgumentParser(description='Batch process factor analysis by date')
    parser.add_argument('--date', type=str, help='Process single date (YYYY-MM-DD)')
    parser.add_argument('--month', type=str, help='Process entire month (YYYY-MM)')
    parser.add_argument('--year', type=int, help='Process entire year (YYYY)')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--auto', action='store_true', help='Auto process next pending date')
    
    args = parser.parse_args()
    
    if args.date:
        # Single date
        date = datetime.strptime(args.date, '%Y-%m-%d')
        process_single_date(date)
        
    elif args.month:
        # Entire month
        year, month = map(int, args.month.split('-'))
        start_date = datetime(year, month, 1)
        
        # Last day of month
        if month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        
        process_date_range(start_date, end_date)
        
    elif args.year:
        # Entire year
        start_date = datetime(args.year, 1, 1)
        end_date = datetime(args.year, 12, 31)
        process_date_range(start_date, end_date)
        
    elif args.start and args.end:
        # Custom range
        start_date = datetime.strptime(args.start, '%Y-%m-%d')
        end_date = datetime.strptime(args.end, '%Y-%m-%d')
        process_date_range(start_date, end_date)
        
    elif args.auto:
        # Auto mode - process next date
        last = get_last_processed_date()
        if last:
            next_date = last + timedelta(days=1)
            print(f"📍 Last processed: {last.strftime('%Y-%m-%d')}")
            print(f"🔄 Next date: {next_date.strftime('%Y-%m-%d')}")
            process_single_date(next_date)
        else:
            print("❌ No checkpoint found. Use --start and --end to begin.")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
