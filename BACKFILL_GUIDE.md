# Factor Analysis Backfill Guide

This guide explains how to backfill factor analysis data for historical dates (2022-2024).

## Overview

The backfill process generates factor analysis scores for all players across historical dates. This is useful for:
- Training machine learning models
- Backtesting strategies
- Historical performance analysis
- Building comprehensive datasets

## Scripts

### 1. `batch_backfill.py` (Recommended)
Simple, reliable batch processor. Processes dates one at a time using the existing `daily_sitstart.py` script.

**Advantages:**
- Uses proven, tested code path
- Automatic checkpointing
- Easy to resume after interruption
- Simple error handling
- Low memory footprint

### 2. `backfill_factor_analysis.py` (Advanced)
More sophisticated backfill with per-date factor analysis.

**Advantages:**
- Direct factor analysis calls
- Custom output format
- Detailed progress tracking
- Batch processing optimizations

## Quick Start

### Process a Single Month (Recommended First Test)

```bash
# Test with April 2024
python src/scripts/batch_backfill.py --month 2024-04
```

This will:
1. Process each day in April 2024
2. Save checkpoint after each successful day
3. Create logs in `data/backfill_logs/`
4. Skip days that already have data

### Process Entire Year

```bash
# Process all of 2023
python src/scripts/batch_backfill.py --year 2023
```

### Process Custom Date Range

```bash
# Process Q1 2024
python src/scripts/batch_backfill.py --start 2024-01-01 --end 2024-03-31
```

### Resume After Interruption

```bash
# Auto-resume from last checkpoint
python src/scripts/batch_backfill.py --auto
```

Or use the same command as before - it will automatically resume:

```bash
# Will skip already processed dates
python src/scripts/batch_backfill.py --year 2023
```

## Full 3-Year Backfill Strategy

Processing 3 years of data will take significant time. Here's the recommended approach:

### Step 1: Test with One Month
```bash
python src/scripts/batch_backfill.py --month 2024-09
```

Verify:
- Data files are created correctly
- Factor analysis runs successfully
- Checkpoints work
- Time per day is reasonable

### Step 2: Process in Chunks (Recommended)

Process year by year:

```bash
# 2024 (most recent data)
python src/scripts/batch_backfill.py --year 2024

# 2023
python src/scripts/batch_backfill.py --year 2023

# 2022
python src/scripts/batch_backfill.py --year 2022
```

Or by quarter:

```bash
# Q4 2024
python src/scripts/batch_backfill.py --start 2024-10-01 --end 2024-12-31

# Q3 2024
python src/scripts/batch_backfill.py --start 2024-07-01 --end 2024-09-30

# ... etc
```

### Step 3: Run in Background (For Long Jobs)

```bash
# Use nohup to run in background
nohup python src/scripts/batch_backfill.py --year 2023 > backfill_2023.log 2>&1 &

# Check progress
tail -f backfill_2023.log

# Or use screen/tmux
screen -S backfill
python src/scripts/batch_backfill.py --year 2023
# Ctrl+A, D to detach
# screen -r backfill to reattach
```

## Time Estimates

Approximate processing times (will vary based on system):
- Single day: 30-120 seconds
- One month: 30-60 minutes
- One year: 6-24 hours
- Three years: 18-72 hours

## Monitoring Progress

### Check Checkpoint File
```bash
cat data/batch_checkpoint.txt
```

Shows last successfully processed date.

### View Recent Logs
```bash
ls -lt data/backfill_logs/ | head -10
tail -50 data/backfill_logs/backfill_20240415.log
```

### Count Processed Files
```bash
# Count recommendation files
ls data/sitstart_recommendations_*.csv | wc -l

# List recent outputs
ls -lt data/sitstart_recommendations_*.csv | head -20
```

## Error Handling

### If Process Fails

The script will:
1. Log the error to the date-specific log file
2. Ask if you want to continue
3. Save checkpoint before the failed date

You can:
- Continue (skip the failed date): Press 'y'
- Stop to investigate: Press 'n'
- Resume later from checkpoint

### View Failed Date Logs
```bash
# Find error logs
grep -l "Error\|Exception\|Failed" data/backfill_logs/*.log

# View specific error
cat data/backfill_logs/backfill_20240415.log
```

### Manual Fix and Resume
```bash
# Fix the issue, then process specific date
python src/scripts/batch_backfill.py --date 2024-04-15

# Then resume auto mode
python src/scripts/batch_backfill.py --auto
```

## Output Files

Each processed date creates:
- `data/sitstart_recommendations_YYYYMMDD_HHMMSS.csv` - Main output
- `data/backfill_logs/backfill_YYYYMMDD.log` - Processing log
- Various factor analysis files in `data/`

## Advanced Usage

### Parallel Processing (Experimental)

You can run multiple months in parallel (different years/months):

```bash
# Terminal 1
python src/scripts/batch_backfill.py --month 2024-01 &

# Terminal 2  
python src/scripts/batch_backfill.py --month 2023-01 &

# Terminal 3
python src/scripts/batch_backfill.py --month 2022-01 &
```

**⚠️ Warning:** Ensure they don't overlap dates or compete for resources.

### Custom Checkpoint Location

Edit the script to change checkpoint file location if needed:
```python
CHECKPOINT_FILE = Path("data/batch_checkpoint.txt")
```

## Disk Space Requirements

Approximate space needed:
- Per day: 1-5 MB
- Per month: 30-150 MB
- Per year: 365 MB - 1.8 GB
- Three years: ~1-5 GB

Check available space:
```bash
df -h .
du -sh data/
```

## Best Practices

1. **Start Small**: Test with one month before full backfill
2. **Use Background Jobs**: Run long jobs with nohup or screen
3. **Monitor Logs**: Check logs periodically for issues
4. **Backup Data**: Copy important data before long runs
5. **Check Disk Space**: Ensure sufficient space before starting
6. **Resume Friendly**: Use checkpoint system, don't restart from scratch

## Troubleshooting

### "No roster file found"
Ensure `data/yahoo_fantasy_rosters_*.csv` exists.

### "No game logs found"
Run `python src/scripts/fetch_2025_gamelogs.py` first (adjust for historical years).

### Process is too slow
- Reduce date range (process by month instead of year)
- Check system resources (CPU, memory, disk I/O)
- Optimize factor analysis modules if needed

### Checkpoint not working
Check file permissions:
```bash
ls -la data/batch_checkpoint.txt
chmod 644 data/batch_checkpoint.txt
```

## Example Workflow

Complete 3-year backfill workflow:

```bash
# 1. Test with one month
python src/scripts/batch_backfill.py --month 2024-09

# 2. Verify outputs
ls -lh data/sitstart_recommendations_202409*.csv

# 3. Process 2024 in background
nohup python src/scripts/batch_backfill.py --year 2024 > backfill_2024.log 2>&1 &

# 4. Monitor progress
tail -f backfill_2024.log

# 5. After 2024 completes, start 2023
nohup python src/scripts/batch_backfill.py --year 2023 > backfill_2023.log 2>&1 &

# 6. Finally 2022
nohup python src/scripts/batch_backfill.py --year 2022 > backfill_2022.log 2>&1 &

# 7. Verify completion
cat data/batch_checkpoint.txt
ls data/sitstart_recommendations_*.csv | wc -l
```

## Support

For issues or questions:
1. Check log files in `data/backfill_logs/`
2. Review this documentation
3. Check factor analysis module documentation in `docs/`
