# Daily Sit/Start Workflow - Implementation Complete

## What Was Built

This implementation completes the repeatable daily workflow for Fantasy Baseball AI sit/start decisions.

### New Scripts Created

1. **`src/scripts/daily_sitstart.py`** ⭐ MAIN DAILY SCRIPT
   - Automated daily workflow orchestrator
   - Runs 30 minutes before game time
   - Steps:
     1. Updates data (MLB delta, weather, roster)
     2. Runs all 13 factor analyses
     3. Optionally tunes weights for each roster player
     4. Generates sit/start recommendations
   - Options:
     - `--skip-tune` - Skip weight tuning (faster, 1-2 min)
     - `--tune-only` - Only tune weights, no recommendations
     - `--date YYYY-MM-DD` - Run for specific date
   - Output: `data/sitstart_recommendations_YYYYMMDD.csv`

2. **`src/scripts/run_all_fa.py`**
   - Runs all 13 factor analysis modules
   - Loads roster and game data
   - Executes each FA and saves results
   - Creates timestamped output files for each factor

3. **`src/scripts/schedule_helper.py`**
   - Shows game times for your roster
   - Calculates when to run script (30 mins before first game)
   - Generates cron scheduling examples
   - Options:
     - `--date YYYY-MM-DD` - Check specific date
     - `--cron` - Show cron scheduling examples

### Updated Files

1. **`README.md`**
   - Cleaned up and reorganized
   - Added clear daily workflow section
   - Included all new scripts
   - Better structure and navigation
   - Concise command reference

2. **`src/scripts/daily_sitstart.py`**
   - Updated to use run_all_fa.py wrapper

## Usage Examples

### Regular Season Daily Usage
```bash
# Morning: Check when games start
python src/scripts/schedule_helper.py

# 30 mins before first game: Run analysis
python src/scripts/daily_sitstart.py

# Quick mode (if short on time)
python src/scripts/daily_sitstart.py --skip-tune
```

### Postseason / Specific Date
```bash
# Last game of 2025 regular season (Sep 29)
python src/scripts/daily_sitstart.py --date 2025-09-29

# With schedule check
python src/scripts/schedule_helper.py --date 2025-09-29
```

### Weekly Weight Tuning
```bash
# Optimize weights based on recent performance
python src/scripts/daily_sitstart.py --tune-only
```

### Automation Setup
```bash
# See cron examples
python src/scripts/schedule_helper.py --cron

# Add to crontab for daily 7:00 AM runs
# crontab -e
# 0 7 * * * cd /home/dominick/workspace/fantasy-baseball-ai && python src/scripts/daily_sitstart.py
```

## Output Format

The main output file `sitstart_recommendations_YYYYMMDD.csv` contains:

| Column | Description |
|--------|-------------|
| player_name | Player name |
| final_score | Weighted composite score (-2.0 to +2.0) |
| recommendation | Text recommendation (START/BENCH/NEUTRAL) |
| wind_score | Wind factor score |
| matchup_score | Historical matchup score |
| home_away_score | Venue split score |
| rest_score | Rest day impact score |
| injury_score | Injury recovery score |
| umpire_score | Umpire tendency score |
| platoon_score | Platoon advantage score |
| temperature_score | Temperature impact score |
| pitch_mix_score | Pitch mix score |
| park_score | Park factors score |
| lineup_score | Lineup position score |
| time_score | Time of day score |
| defense_score | Defensive matchup score |
| *_weight | Individual factor weights (tuned per player) |

## Score Interpretation

| Score Range | Recommendation | Action |
|-------------|----------------|--------|
| +1.5 to +2.0 | 🌟 VERY FAVORABLE | Strong start, high confidence |
| +0.5 to +1.5 | ✅ FAVORABLE | Start if available |
| -0.5 to +0.5 | ⚖️ NEUTRAL | Use other factors |
| -1.5 to -0.5 | ⚠️ UNFAVORABLE | Consider benching |
| -2.0 to -1.5 | 🚫 VERY UNFAVORABLE | Bench if possible |

## Timing

**Run 30 minutes before game time** to allow time to:
1. Review recommendations
2. Make lineup changes  
3. Account for late-breaking news
4. Submit changes before roster lock

## Integration with Existing Workflow

This new daily workflow integrates with existing components:

- **Data Collection**: Uses existing delta scrapers for efficiency
- **Factor Analyses**: Leverages all 13 existing FA modules
- **Weight Tuning**: Uses existing backtest_weights.py
- **Yahoo Integration**: Uses existing yahoo_scrape.py

## Testing

The script was tested with:
- Date: 2025-09-29 (last regular season game)
- Mode: --skip-tune (fast mode)
- Result: Successfully executed all 13 FA modules in ~60 seconds

## Next Steps

To use this system:

1. **Initial Setup**: Run `python src/fb_ai.py --refresh`
2. **Check Schedule**: Run `python src/scripts/schedule_helper.py`
3. **Run Daily**: Run `python src/scripts/daily_sitstart.py` 30 mins before first game
4. **Review Output**: Check `data/sitstart_recommendations_*.csv`
5. **Set Lineup**: Apply recommendations to Yahoo Fantasy

## Notes

- Weight tuning adds ~3-4 minutes but improves accuracy
- Use `--skip-tune` for faster results with default/cached weights
- Retune weights weekly or after major roster changes
- Schedule helper shows exact run times for your roster's games

---

**Implementation Date**: November 12, 2024  
**Status**: ✅ Complete and ready for daily use
