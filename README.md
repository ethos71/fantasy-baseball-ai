# Fantasy Baseball AI

An advanced machine learning system for fantasy baseball optimization that combines MLB statistics, real-time weather data, and Yahoo Fantasy Sports integration to provide actionable insights for your fantasy baseball roster.

## Project Overview

This project uses MLB's official Stats API, machine learning models (XGBoost), weather prediction, and multi-factor analysis to help you make informed decisions about your fantasy baseball lineup. The system analyzes thirteen key factors to determine optimal start/sit decisions:

1. **Wind Analysis** - How weather conditions affect pitcher/hitter performance
2. **Historical Matchup Performance** - Player vs. opponent track record
3. **Home/Away Venue Splits** - Player performance by location
4. **Rest Day Impacts** - How days of rest affect player performance
5. **Injury/Recovery Tracking** - Post-injury performance monitoring
6. **Umpire Strike Zone Analysis** - How home plate umpire affects pitcher/hitter success
7. **Platoon Advantages** - Left-handed vs. right-handed matchup optimization
8. **Temperature Analysis** - How temperature affects ball flight and player performance
9. **Pitch Mix Analysis** - Pitcher pitch types vs. batter strengths/weaknesses
10. **Park Factors** - How ballpark characteristics affect offensive/pitching stats
11. **Lineup Position** - Impact of batting order position on fantasy opportunities
12. **Time of Day** - How day/night/twilight games affect player performance
13. **Defensive Positions** - Team defensive quality and matchups

**🆕 Automated Weight Tuning:** The system backtests predictions against 3+ years of historical data to optimize factor weights for each player on your roster!

## Installation

### System Dependencies
```bash
sudo apt update
sudo apt install python3 python3-pip python3-xgboost python3-sklearn python3-numpy
```

### Python Dependencies
```bash
pip install requests pandas xgboost scikit-learn numpy
```

## Project Structure

```
fantasy-baseball-ai/
├── data/                              # Generated data files
│   ├── mlb_all_teams.csv              # All 30 MLB teams
│   ├── mlb_YYYY_schedule.csv          # Schedules for each year (4 files)
│   ├── mlb_all_players_YYYY.csv       # Players by year (4 files)
│   ├── mlb_all_players_complete.csv   # Complete player database (5,969 records)
│   ├── mlb_stadium_weather.csv        # Current weather at all MLB stadiums
│   ├── yahoo_fantasy_rosters_*.csv    # Your Yahoo fantasy rosters
│   ├── weather_advantage_analysis_*.csv # Weather/wind analysis output
│   └── matchup_advantage_analysis_*.csv # Combined 3-factor analysis output
├── src/
│   ├── fb_ai.py                       # 🎯 Main orchestrator - runs all analysis
│   └── scripts/
│       ├── xgboost_ml.py              # XGBoost ML model example
│       ├── mlb_scrape.py              # MLB Stats API scraper (full)
│       ├── mlb_delta_scrape.py        # ⚡ MLB incremental updates
│       ├── weather_scrape.py          # MLB stadium weather predictor (full)
│       ├── weather_delta_scrape.py    # ⚡ Weather quick updates
│       ├── yahoo_scrape.py            # Yahoo Fantasy roster fetcher
│       ├── weather_advantage.py       # 🌪️ Factor 1: Wind analysis
│       └── matchup_analysis.py        # 📊 Factors 2 & 3: Matchup + Home/Away
├── README.md
├── oauth2.json                        # Yahoo API credentials
└── .env                               # Environment variables (browser auth)
```

## Quick Start

### 0. Configure Yahoo Fantasy Access

Before running the system, set up Yahoo Fantasy Sports API access:

1. **Get Yahoo API Credentials** from [Yahoo Developer Console](https://developer.yahoo.com/apps/)
   - Create an app and note your App ID, Client ID, and Client Secret
   - Add these to `oauth2.json` in the root directory

2. **Set Browser Path** for authentication:
   ```bash
   echo 'BROWSER_PATH=/path/to/your/browser' > .env
   # Example: BROWSER_PATH=/usr/bin/google-chrome
   ```

### 1. First Time Setup - Complete Data Refresh
```bash
python src/fb_ai.py --refresh
```

This will:
- ⚠️ **Delete** all existing CSV files in `data/`
- Run MLB scraper to fetch all statistics (current + last 3 years)
- Run weather scraper to get current conditions
- Fetch your Yahoo Fantasy rosters
- Run delta updates to get the absolute latest data
- **Run 12-Factor Analysis** (wind + matchups + venue + rest + injury + umpire + platoon + temperature + pitch mix + park + lineup + time of day)
- Display recommendations in console
- Takes 5-10 minutes to complete

**Use this when:**
- Starting fresh with the project
- Major roster changes in your fantasy league
- Beginning of a new week/matchup period

### 2. Daily Quick Update (Recommended)
```bash
python src/fb_ai.py
```

This will:
- Run delta scrapers to update recent games and current weather
- Fetch latest Yahoo rosters
- **Run 12-Factor Analysis** on your current roster
- Display start/sit recommendations
- Takes ~1 minute

**Use this:**
- Daily before setting your lineup
- Before each matchup period
- To get quick recommendations without full refresh

### 3. View Data Status Only
```bash
python src/fb_ai.py --status
```

Shows:
- Current data files and their sizes
- Last update times
- Available commands
- Data completeness check

---

## 🎯 Thirteen-Factor Analysis System

The heart of this project is a sophisticated multi-factor analysis that evaluates every player on your roster for optimal start/sit decisions. Each factor is weighted and combined to produce actionable recommendations.

**🆕 NEW: Automated Weight Tuning** - The system can now analyze 3+ years of historical data to optimize factor weights for each player on your roster!

For detailed documentation on each factor analysis module, see [docs/FACTOR_ANALYSIS_FA.md](docs/FACTOR_ANALYSIS_FA.md)

### Quick Overview

| Factor | Default Weight | What It Measures |
|--------|----------------|------------------|
| **🌪️ Wind Analysis** | 10% | How weather conditions affect pitcher/hitter performance |
| **📊 Historical Matchup** | 15% | Player vs. opponent track record |
| **🏠 Home/Away Venue** | 12% | Player performance by location |
| **😴 Rest Day Impacts** | 8% | How days of rest affect performance |
| **🩹 Injury/Recovery** | 12% | Post-injury performance monitoring |
| **⚾ Umpire Strike Zone** | 5% | How home plate umpire affects success |
| **↔️ Platoon Advantages** | 10% | Left-handed vs. right-handed matchup optimization |
| **🌡️ Temperature** | 5% | Temperature effects on ball flight and player performance |
| **🎯 Pitch Mix** | 5% | Pitcher types vs. batter strengths |
| **🏟️ Park Factors** | 8% | How ballpark characteristics affect stats |
| **📋 Lineup Position** | 5% | Impact of batting order on opportunities |
| **🕐 Time of Day** | 3% | Day/night/twilight game performance |
| **🛡️ Defensive Positions** | 2% | Team defensive quality and matchups |

**Note:** Weights can be customized per player using the automated weight tuning system!

### Combined Scoring Formula

```python
FINAL_SCORE = (
    matchup_score    × 0.20   +  # Historical performance vs opponent
    venue_score      × 0.15   +  # Home/away splits  
    wind_score       × 0.15   +  # Weather conditions
    rest_score       × 0.13   +  # Rest day impacts
    injury_score     × 0.13   +  # Injury/recovery status
    umpire_score     × 0.12   +  # Umpire strike zone tendencies
    platoon_score    × 0.12   +  # Platoon advantages (L/R matchups)
    park_score       × 0.10      # Park factors (ballpark environment)
)
```

### Score Interpretation

| Score Range | Recommendation | Action |
|-------------|---------------|--------|
| +1.5 to +2.0 | 🌟 VERY FAVORABLE | Strong start, high confidence |
| +0.5 to +1.5 | ✅ FAVORABLE | Good play, start if available |
| -0.5 to +0.5 | ⚖️ NEUTRAL | Use other factors/gut feel |
| -1.5 to -0.5 | ⚠️ UNFAVORABLE | Consider benching |
| -2.0 to -1.5 | 🚫 VERY UNFAVORABLE | Bench if possible |

### Output Files

**matchup_advantage_analysis_YYYYMMDD.csv** ⭐ PRIMARY OUTPUT
- **ALL EIGHT FACTORS** combined
- Final scores and recommendations
- Detailed breakdowns per player
- Use this for your start/sit decisions!

**weather_advantage_analysis_YYYYMMDD.csv**
- Wind analysis only
- Per-player wind effects
- Stadium conditions

### 🔜 Future Factors Coming Soon

- **Pitcher Quality:** Facing ace vs. rookie starter
- **Recent Form:** Last 7/14/30 day performance trends

---

## 🎛️ Automated Weight Tuning System

The Fantasy Baseball AI includes an advanced **backtesting and weight optimization** system that analyzes historical game data from 2022 onwards to find the optimal factor weights for each player on your roster.

### Why Tune Weights?

Not all players respond the same way to different factors. For example:
- **Power hitters** may be more affected by wind (20% vs. 10% default)
- **Contact hitters** may rely more on matchup history (18% vs. 15% default)
- **Streaky players** may weight temperature higher (8% vs. 5% default)

### Quick Start

**Backtest your entire roster:**
```bash
python src/scripts/backtest_weights.py
```

**Optimize weights for best performance:**
```bash
python src/scripts/backtest_weights.py --optimize --save
```

**Optimize a specific player:**
```bash
python src/scripts/backtest_weights.py --player "Shohei Ohtani" --optimize --save
```

### How It Works

1. **Loads Historical Data:** Analyzes 3+ years of game data (2022-present)
2. **Calculates Predictions:** For each historical game, computes factor scores using current weights
3. **Compares to Actual Performance:** Matches predictions against actual fantasy points scored
4. **Optimizes Weights:** Uses differential evolution to find weight combination with highest accuracy
5. **Saves Configuration:** Stores player-specific weights in `config/player_weights.json`

### Performance Metrics

The system measures prediction accuracy using:
- **Correlation:** How well predictions match actual performance (-1 to +1, higher is better)
- **MAE (Mean Absolute Error):** Average prediction error (lower is better)
- **RMSE (Root Mean Square Error):** Weighted prediction error (lower is better)

**Good Performance:**
- Correlation > 0.5 (Good predictive power)
- Correlation > 0.7 (Excellent predictions)
- MAE < 0.5 (Low average error)

### Managing Weights

**View current weights:**
```bash
python src/scripts/weight_config.py --show                    # Global defaults
python src/scripts/weight_config.py --show --player "Ohtani"  # Player-specific
python src/scripts/weight_config.py --list                    # All custom weights
```

**Reset weights:**
```bash
python src/scripts/weight_config.py --reset --player "Ohtani"  # Reset one player
```

### When to Retune

Re-run optimization when:
- **New season starts** (player tendencies change)
- **Player changes teams** (different park, lineup)
- **After 20+ games** into season (more data available)
- **Player coming off injury** (performance patterns shift)

### Integration

The system automatically loads appropriate weights when running analysis:
1. Checks for player-specific weights in `config/player_weights.json`
2. Falls back to global weights in `config/factor_weights.json`
3. Uses default weights if no config exists

For detailed documentation, see [docs/FACTOR_ANALYSIS_FA.md](docs/FACTOR_ANALYSIS_FA.md#weight-tuning--backtesting)

---

## ⚡ Manual Scraper Usage (Advanced)

You can run individual scrapers if needed. For detailed documentation on each scraper, see [src/scripts/scrape/README.md](src/scripts/scrape/README.md)

### Quick Reference

**Full Data Collection:**
```bash
python src/scripts/scrape/mlb_scrape.py          # All MLB data (5-8 min)
python src/scripts/scrape/weather_scrape.py      # Stadium weather (1-2 min)
python src/scripts/scrape/yahoo_scrape.py        # Your fantasy rosters (20-30 sec)
```

**Fast Daily Updates:**
```bash
python src/scripts/scrape/mlb_delta_scrape.py    # Recent games only (~30 sec)
python src/scripts/scrape/weather_delta_scrape.py # Current weather (~15 sec)
```

**💡 Pro Tip:** `fb_ai.py` automatically manages all scrapers - use `--refresh` for full scrape or run without flags for delta updates.

---

## 📁 Generated Data Files

After running the scraper, the following files will be created in the `data/` directory:

```
data/
├── MLB Data (Scraped from MLB Stats API)
│   ├── mlb_all_teams.csv                    # All 30 MLB teams with details
│   ├── mlb_2025_schedule.csv                # 2025 regular season (2,464 games)
│   ├── mlb_2024_schedule.csv                # 2024 regular season (2,469 games)
│   ├── mlb_2023_schedule.csv                # 2023 regular season (2,476 games)
│   ├── mlb_2022_schedule.csv                # 2022 regular season (2,479 games)
│   ├── mlb_all_players_2025.csv             # All players for 2025
│   ├── mlb_all_players_2024.csv             # All players for 2024
│   ├── mlb_all_players_2023.csv             # All players for 2023
│   ├── mlb_all_players_2022.csv             # All players for 2022
│   └── mlb_all_players_complete.csv         # Consolidated all players (5,969 records)
│
├── Weather Data (Machine Learning Predictions)
│   └── mlb_stadium_weather.csv              # Current weather at all 30 MLB stadiums
│
├── Fantasy Roster Data (Yahoo API)
│   └── yahoo_fantasy_rosters_YYYYMMDD.csv   # Your fantasy team rosters
│
└── Analysis Output (Generated by fb_ai.py)
    ├── weather_advantage_analysis_YYYYMMDD.csv   # Wind/weather factor scores
    └── matchup_advantage_analysis_YYYYMMDD.csv   # ⭐ Combined 3-factor analysis
```

---

## 🔧 Technical Details

For detailed technical documentation:
- **Scrapers:** See [src/scripts/scrape/README.md](src/scripts/scrape/README.md)
- **Factor Analysis:** See [docs/FACTOR_ANALYSIS_FA.md](docs/FACTOR_ANALYSIS_FA.md)
- **Weight Tuning:** See [docs/FACTOR_ANALYSIS_FA.md#weight-tuning--backtesting](docs/FACTOR_ANALYSIS_FA.md#weight-tuning--backtesting)

### Quick Overview

**Yahoo Fantasy Integration:**
- Browser-based OAuth authentication
- Configure credentials in `oauth2.json`
- Set `BROWSER_PATH` in `.env`

**MLB Stats API:**
- Official MLB Stats API implementation
- 4 years of historical data (2022-2025)
- 5,969+ player records
- Base URL: `https://statsapi.mlb.com/api`

**Weather Prediction:**
- ML-based weather forecasting
- Open-Meteo API (free, no key required)
- Random Forest classifier
- Wind speed/direction critical for analysis

## Resources

### Research & Tutorials
- [Baseball Analytics Research Paper](https://www.mdpi.com/2076-3417/15/13/7081)
- [XGBoost Tutorial](https://machinelearningmastery.com/develop-first-xgboost-model-python-scikit-learn/)

### MLB Data Sources
- [MLB Stats API Documentation](https://github.com/MajorLeagueBaseball/google-cloud-mlb-hackathon/tree/main/datasets/mlb-statsapi-docs)
- [MLB Glossary](https://www.mlb.com/glossary)
- [Google Cloud x MLB Hackathon](https://next2025challenge.devpost.com/)

### Weather Prediction
- [Weather Prediction ML Model](https://github.com/FELIX-GEORGE/WeatherPrediction_ML_Model)
- [Open-Meteo Weather API](https://open-meteo.com/)

### Related Projects
- [Fantasy Baseball AI by ethos71](https://github.com/ethos71/fantasy-baseball-ai)

---

## 📝 Quick Reference

### Command Cheat Sheet

```bash
# First time setup - Full data refresh
python src/fb_ai.py --refresh

# Daily recommendations (fastest, recommended)
python src/fb_ai.py

# Check data status only
python src/fb_ai.py --status
```

### Key Output Files

- **`matchup_advantage_analysis_*.csv`** ⭐ YOUR MAIN FILE
  - All 8 factors combined
  - Final scores and recommendations
  - Use this for start/sit decisions

- **`weather_advantage_analysis_*.csv`**
  - Wind analysis details
  - Stadium conditions

- **`yahoo_fantasy_rosters_*.csv`**
  - Your current roster snapshot

### Score Interpretation

| Score Range | Recommendation |
|-------------|---------------|
| +1.5 to +2.0 | 🌟 VERY FAVORABLE - Strong start |
| +0.5 to +1.5 | ✅ FAVORABLE - Good play |
| -0.5 to +0.5 | ⚖️ NEUTRAL - Use judgment |
| -1.5 to -0.5 | ⚠️ UNFAVORABLE - Consider benching |
| -2.0 to -1.5 | 🚫 VERY UNFAVORABLE - Bench |

---

## License

This project uses publicly available MLB data through their official Stats API.
