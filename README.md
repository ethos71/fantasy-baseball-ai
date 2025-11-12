# Fantasy Baseball AI

An automated machine learning system for fantasy baseball optimization that combines MLB statistics, real-time weather data, and Yahoo Fantasy Sports integration to provide data-driven sit/start decisions.

## Overview

This system analyzes **13 key factors** using 3+ years of historical data to recommend optimal lineup decisions. Run it **30 minutes before game time** for best results.

### 13 Factor Analysis System

1. **Wind Analysis** - Weather conditions impact on performance
2. **Historical Matchup** - Player vs. opponent track record  
3. **Home/Away Venue** - Location-based performance splits
4. **Rest Day Impacts** - How rest affects performance
5. **Injury/Recovery** - Post-injury performance monitoring
6. **Umpire Strike Zone** - Home plate umpire tendencies
7. **Platoon Advantages** - Left/Right matchup optimization
8. **Temperature** - Temperature effects on ball flight
9. **Pitch Mix** - Pitcher types vs. batter strengths
10. **Park Factors** - Ballpark characteristics impact
11. **Lineup Position** - Batting order position effects
12. **Time of Day** - Day/night game performance
13. **Defensive Positions** - Team defensive quality

**🎯 Automated Weight Tuning:** System optimizes factor weights for each player based on 3+ years of historical backtesting!

## Quick Start

### Prerequisites

**System dependencies:**
```bash
sudo apt update && sudo apt install python3 python3-pip python3-xgboost python3-sklearn python3-numpy
```

**Python packages:**
```bash
pip install requests pandas xgboost scikit-learn numpy scipy
```

### Yahoo Fantasy Setup

1. Get API credentials from [Yahoo Developer Console](https://developer.yahoo.com/apps/)
2. Create `oauth2.json` in project root with your credentials
3. Set browser path: `echo 'BROWSER_PATH=/usr/bin/google-chrome' > .env`

### Initial Setup (First Time Only)

```bash
python src/fb_ai.py --refresh
```

This will:
- Clear any existing data files
- Fetch 4 years of MLB statistics (2022-2025)
- Get current weather for all 30 stadiums
- Fetch your Yahoo Fantasy rosters
- Run all 13 factor analyses
- Takes ~5-10 minutes

### Daily Workflow (Run 30 mins before game time)

**🎯 Simple Command (Recommended)**
```bash
./fb-ai                                # Auto mode (smart defaults)
./fb-ai --when                         # Check game times
./fb-ai --quick                        # Quick mode (1-2 min)
./fb-ai --last                         # Show last recommendations
./fb-ai --help                         # See all options
```

The `fb-ai` prompt command automatically:
- Uses full mode (with weight tuning) before 10 AM
- Uses quick mode (skip tuning) after 10 AM for speed
- Shows recommendations immediately after completion

_Note: `fb-ai` is a symlink to `.github/prompts/fb-ai` for convenience._

**📋 Full Command Options**
```bash
python src/scripts/daily_sitstart.py                    # Full analysis with tuning
python src/scripts/daily_sitstart.py --skip-tune        # Quick mode (1-2 min)
python src/scripts/daily_sitstart.py --date 2025-09-29  # Specific date
python src/scripts/daily_sitstart.py --tune-only        # Tune weights only
```

**⏰ Game Schedule Helper**
```bash
python src/scripts/schedule_helper.py                  # Today's games
python src/scripts/schedule_helper.py --date 2025-09-29 # Specific date
python src/scripts/schedule_helper.py --cron            # Cron examples
```

### Check Data Status

```bash
python src/fb_ai.py --status
```

Shows current data files, freshness, and available commands.

## Understanding the Output

### Score Interpretation

| Score Range | Recommendation | Action |
|-------------|----------------|--------|
| +1.5 to +2.0 | 🌟 VERY FAVORABLE | Strong start, high confidence |
| +0.5 to +1.5 | ✅ FAVORABLE | Start if available |
| -0.5 to +0.5 | ⚖️ NEUTRAL | Use other factors |
| -1.5 to -0.5 | ⚠️ UNFAVORABLE | Consider benching |
| -2.0 to -1.5 | 🚫 VERY UNFAVORABLE | Bench if possible |

### Output Files

**sitstart_recommendations_YYYYMMDD.csv** ⭐ PRIMARY OUTPUT
- Final scores and recommendations
- All 13 factor scores per player
- Individual factor weights
- Use this for your lineup decisions!

**matchup_advantage_analysis_YYYYMMDD.csv**
- Combined multi-factor analysis
- Historical data integration

**weather_advantage_analysis_YYYYMMDD.csv**
- Wind and weather factor details

---

## Advanced Features

### Weight Tuning & Backtesting

The system optimizes factor weights for each player based on historical performance.

**View current weights:**
```bash
python src/scripts/weight_config.py --show                    # Global defaults
python src/scripts/weight_config.py --show --player "Ohtani"  # Player-specific
python src/scripts/weight_config.py --list                    # All custom weights
```

**Manual weight optimization:**
```bash
python src/scripts/backtest_weights.py                       # Backtest entire roster
python src/scripts/backtest_weights.py --optimize --save     # Optimize and save
python src/scripts/backtest_weights.py --player "Ohtani" --optimize --save
```

**Reset weights:**
```bash
python src/scripts/weight_config.py --reset --player "Ohtani"
```

**When to retune:**
- New season starts
- Player changes teams  
- After 20+ games into season
- Player returns from injury

See [docs/WEIGHT_TUNING_GUIDE.md](docs/WEIGHT_TUNING_GUIDE.md) for details.

---

## Project Structure

```
fantasy-baseball-ai/
├── data/                              # Generated data files
│   ├── mlb_all_teams.csv              # All 30 MLB teams
│   ├── mlb_YYYY_schedule.csv          # Schedules (4 years)
│   ├── mlb_all_players_*.csv          # Player databases
│   ├── mlb_stadium_weather.csv        # Current weather
│   ├── yahoo_fantasy_rosters_*.csv    # Your rosters
│   └── sitstart_recommendations_*.csv # Daily recommendations ⭐
├── src/
│   ├── fb_ai.py                       # Main data manager
│   └── scripts/
│       ├── daily_sitstart.py          # 🎯 Daily workflow (run this!)
│       ├── run_all_fa.py              # Run all factor analyses
│       ├── schedule_helper.py         # Game time scheduler
│       ├── backtest_weights.py        # Weight optimization
│       ├── weight_config.py           # Weight management
│       ├── scrape/                    # Data collection
│       │   ├── mlb_scrape.py          # Full MLB scrape
│       │   ├── mlb_delta_scrape.py    # Quick updates
│       │   ├── weather_scrape.py      # Weather prediction
│       │   ├── weather_delta_scrape.py # Weather updates
│       │   └── yahoo_scrape.py        # Yahoo roster
│       └── fa/                        # Factor analyses (13)
│           ├── wind_analysis.py
│           ├── matchup_fa.py
│           ├── home_away_fa.py
│           ├── rest_day_fa.py
│           ├── injury_fa.py
│           ├── umpire_fa.py
│           ├── platoon_fa.py
│           ├── temperature_fa.py
│           ├── pitch_mix_fa.py
│           ├── park_factors_fa.py
│           ├── lineup_position_fa.py
│           ├── time_of_day_fa.py
│           └── defensive_positions_fa.py
├── config/
│   └── player_weights.json            # Tuned weights
├── docs/
│   ├── FACTOR_ANALYSIS_FA.md          # Factor details
│   └── WEIGHT_TUNING_GUIDE.md         # Weight tuning guide
└── oauth2.json                        # Yahoo credentials
```

---

## Manual Scraper Usage (Advanced)

Run individual components if needed:

**Full data collection:**
```bash
python src/scripts/scrape/mlb_scrape.py          # All MLB data (5-8 min)
python src/scripts/scrape/weather_scrape.py      # Stadium weather (1-2 min)
python src/scripts/scrape/yahoo_scrape.py        # Fantasy rosters (30 sec)
```

**Quick daily updates:**
```bash
python src/scripts/scrape/mlb_delta_scrape.py    # Recent games (~30 sec)
python src/scripts/scrape/weather_delta_scrape.py # Current weather (~15 sec)
```

**Individual factor analyses:**
```bash
python src/scripts/fa/wind_analysis.py
python src/scripts/fa/matchup_fa.py
# ... etc for all 13 factors
```

💡 **Tip:** Use `daily_sitstart.py` instead - it runs everything automatically.

---

## Technical Details

**Data Sources:**
- **MLB Stats API** - Official MLB statistics (4 years: 2022-2025)
- **Open-Meteo API** - Weather forecasting (free, no key required)
- **Yahoo Fantasy API** - Your roster data (OAuth authentication)

**Machine Learning:**
- Random Forest classifier for weather prediction
- Differential evolution for weight optimization
- 3+ years historical backtesting

**Analysis:**
- 13 independent factor analyses
- Player-specific weight tuning
- Real-time data integration

For detailed documentation:
- **Factor Analysis:** [docs/FACTOR_ANALYSIS_FA.md](docs/FACTOR_ANALYSIS_FA.md)
- **Weight Tuning:** [docs/WEIGHT_TUNING_GUIDE.md](docs/WEIGHT_TUNING_GUIDE.md)

---

## Resources

- [MLB Stats API Documentation](https://github.com/MajorLeagueBaseball/google-cloud-mlb-hackathon/tree/main/datasets/mlb-statsapi-docs)
- [Baseball Analytics Research](https://www.mdpi.com/2076-3417/15/13/7081)
- [Open-Meteo Weather API](https://open-meteo.com/)
- [XGBoost Tutorial](https://machinelearningmastery.com/develop-first-xgboost-model-python-scikit-learn/)

---

## Quick Command Reference

**Super Simple (Just type this!):**
```bash
./fb-ai                                # Run sit/start analysis (auto mode)
./fb-ai --when                         # Check game times
./fb-ai --last                         # Show last recommendations
```

**Full Commands:**
```bash
# Initial setup (first time)
python src/fb_ai.py --refresh

# Daily sit/start
./fb-ai                                # Simple way (recommended)
python src/scripts/daily_sitstart.py  # Full way

# Quick mode (skip weight tuning)
./fb-ai --quick
python src/scripts/daily_sitstart.py --skip-tune

# Specific date
./fb-ai --date 2025-09-29

# Check game times (when to run)
./fb-ai --when
python src/scripts/schedule_helper.py

# Check data status
python src/fb_ai.py --status

# Tune weights only (weekly)
python src/scripts/daily_sitstart.py --tune-only

# View weights
python src/scripts/weight_config.py --list
```

---

## License

This project uses publicly available MLB data through their official Stats API.
