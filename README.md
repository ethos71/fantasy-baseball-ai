# Fantasy Baseball AI

An advanced machine learning system for fantasy baseball optimization that combines MLB statistics, real-time weather data, and Yahoo Fantasy Sports integration to provide actionable insights for your fantasy baseball roster.

## Project Overview

This project uses MLB's official Stats API, machine learning models (XGBoost), weather prediction, and multi-factor analysis to help you make informed decisions about your fantasy baseball lineup. The system analyzes three key factors to determine optimal start/sit decisions:

1. **Wind Analysis** - How weather conditions affect pitcher/hitter performance
2. **Historical Matchup Performance** - Player vs. opponent track record
3. **Home/Away Venue Splits** - Player performance by location

**More analysis factors coming soon!**

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
- **Run 3-Factor Analysis** (wind + matchups + home/away)
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
- **Run 3-Factor Analysis** on your current roster
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

## 🎯 Three-Factor Analysis System

The heart of this project is a sophisticated multi-factor analysis that evaluates every player on your roster for optimal start/sit decisions. Each factor is weighted and combined to produce actionable recommendations.

### Factor 1: Wind Analysis (30% weight)

**What it does:** Analyzes how wind conditions at the game stadium affect pitcher and hitter performance.

**Key Concepts:**
- **Favorable Wind (Tailwind):** Wind blowing from pitcher's mound toward home plate
  - Helps fly balls carry further → MORE home runs
  - Benefits: Hitters ✅ | Hurts: Pitchers ❌
  
- **Unfavorable Wind (Headwind):** Wind blowing from home plate toward pitcher
  - Knocks down fly balls → FEWER home runs
  - Benefits: Pitchers ✅ | Hurts: Hitters ❌

**How it scores:**
- Calculates wind vector from pitcher mound to home plate
- Compares actual wind direction to optimal direction
- Wind speed amplifies the effect (15+ mph = significant impact)
- Generates score: -2.0 (very unfavorable) to +2.0 (very favorable)

**Example:**
```
🌪️ Yankee Stadium - Game Day Analysis
Wind: 18 mph from SW (225°)
Pitcher Mound to Home: 45° (NE direction)
Analysis: Wind is blowing TOWARD home plate (175° from optimal)
Result: FAVORABLE for hitters (+1.5 score)
        UNFAVORABLE for pitchers (-1.5 score)
```

**Real Impact:** Studies show 15+ mph tailwinds can increase home runs by 20-30%

---

### Factor 2: Historical Matchup Performance (40% weight)

**What it does:** Analyzes how a player has performed historically against today's specific opponent.

**Key Concepts:**
- **Sample Size Matters:** More games = higher confidence
  - 10+ games = 100% confidence (full weight)
  - 5-9 games = 50-90% confidence
  - <5 games = <50% confidence (reduced weight)

- **Batting Average Threshold:**
  - .300+ vs opponent = EXCELLENT matchup
  - .250-.299 = GOOD matchup
  - .200-.249 = NEUTRAL matchup
  - <.200 = POOR matchup

**How it scores:**
- Pulls all historical at-bats vs specific opponent
- Calculates BA, HR, and sample size
- Applies confidence weighting based on games played
- Generates score: -2.0 (terrible history) to +2.0 (dominant history)

**Example:**
```
📊 Player: Juan Soto
Opponent: Boston Red Sox (Today)
Historical Stats: .385 BA, 4 HR in 12 games vs BOS
Sample Size: 12 games = 100% confidence
Analysis: DOMINANT against Red Sox pitching
Result: +1.8 score → STRONG START CANDIDATE
```

**Why it matters:** Players often have "nemesis teams" or "favorite opponents" - this captures that edge.

---

### Factor 3: Home/Away Venue Splits (30% weight)

**What it does:** Evaluates whether a player performs better at their home stadium or on the road.

**Key Concepts:**
- **Home Field Advantage:** Many players hit better at home
  - Familiar surroundings, sleep in own bed, fan support
  - Altitude effects (Colorado), short porches (Yankee Stadium)
  
- **Road Warriors:** Some players thrive away from home
  - Less pressure, better focus, certain ballpark dimensions

**How it scores:**
- Calculates separate batting averages for home vs away games
- Compares current game location to player's splits
- If playing where they excel = positive score
- If playing where they struggle = negative score

**Example:**
```
🏠 Player: Coors Field Regular (COL)
Home BA: .320 | Away BA: .245 → 75-point difference!
Today's Game: Home
Analysis: Huge home advantage (altitude + familiarity)
Result: +1.6 score → MUST START

🛣️ Player: Road Warrior (NYY)
Home BA: .255 | Away BA: .310 → 55-point difference!
Today's Game: Away
Analysis: Performs significantly better on road
Result: +1.2 score → START WITH CONFIDENCE
```

**Why it matters:** Venue effects can be as impactful as matchup history. Some players gain/lose 50+ BA points based on location.

---

### Combined Scoring Formula

```python
FINAL_SCORE = (
    matchup_score    × 0.40 +  # Historical performance (highest weight)
    venue_score      × 0.30 +  # Home/away splits
    wind_score       × 0.30    # Weather conditions
)
```

**Why these weights?**
- **Matchup (40%):** Most predictive - direct head-to-head history
- **Venue (30%):** Very significant - proven statistical impact
- **Wind (30%):** Important but variable - weather changes daily

**Score Interpretation:**
- **+1.5 to +2.0:** 🌟 VERY FAVORABLE - Strong start, high confidence
- **+0.5 to +1.5:** ✅ FAVORABLE - Good play, start if roster spot available
- **-0.5 to +0.5:** ⚖️ NEUTRAL - Toss-up, use other factors (gut feel, opposing pitcher)
- **-1.5 to -0.5:** ⚠️ UNFAVORABLE - Consider benching
- **-2.0 to -1.5:** 🚫 VERY UNFAVORABLE - Bench if possible

---

### Real-World Example: Full Analysis

```
Player: Aaron Judge (NYY)
Date: September 15, 2025
Opponent: @ Boston Red Sox
═══════════════════════════════════════════════

FACTOR 1: WIND ANALYSIS
Stadium: Fenway Park
Wind: 22 mph from WSW (260°)
Direction: Blowing OUT to right field
Effect on Judge (RH power hitter): VERY FAVORABLE
Wind Score: +1.8

FACTOR 2: MATCHUP HISTORY  
Career vs BOS: .312 BA, 8 HR in 15 games
Sample Size: 15 games = 100% confidence
Historical Performance: EXCELLENT
Matchup Score: +1.6

FACTOR 3: HOME/AWAY SPLITS
Judge's Stats: Home .285 | Away .305
Today: Playing Away
Venue Effect: Performs 20 points BETTER on road
Venue Score: +0.9

═══════════════════════════════════════════════
COMBINED SCORE: +1.5 (VERY FAVORABLE)

Calculation:
(1.6 × 0.40) + (0.9 × 0.30) + (1.8 × 0.30)
= 0.64 + 0.27 + 0.54
= +1.45 → Rounded to +1.5

RECOMMENDATION: 🌟 START WITH HIGH CONFIDENCE
- Strong tailwind will carry fly balls
- Excellent history vs Red Sox pitching
- Better hitter on the road
- ALL THREE FACTORS ALIGN = OPTIMAL PLAY
```

---

### 🔜 Future Analysis Factors Coming Soon

The system is designed to incorporate additional factors:

- **Pitcher Quality:** Facing ace vs. rookie starter
- **Recent Form:** Last 7/14/30 day performance trends
- **Umpire Analysis:** Strike zone size and consistency
- **Rest Days:** Performance on back-to-backs vs. rested
- **Time of Day:** Day/night game splits
- **Temperature:** Extreme heat/cold effects
- **Park Factors:** Ballpark dimensions and hitting environment
- **Platoon Splits:** L/R matchup advantages

Each new factor will be weighted and integrated into the combined scoring system.

---

### Output Files

**weather_advantage_analysis_YYYYMMDD.csv**
- Wind analysis only
- Per-player wind effects
- Stadium conditions

**matchup_advantage_analysis_YYYYMMDD.csv** ⭐ PRIMARY OUTPUT
- **ALL THREE FACTORS** combined
- Final scores and recommendations
- Detailed breakdowns per player
- Use this for your start/sit decisions!

---

## ⚡ Manual Scraper Usage (Advanced)

You can run individual scrapers if needed:

### MLB Data Scraper
```bash
python src/scripts/mlb_scrape.py
```
Fetches comprehensive data for current year + last 3 years (2025, 2024, 2023, 2022):
- All 30 MLB teams with complete details
- All game schedules (9,888 games across 4 years)
- All player rosters (5,969 player-season records)

### Weather Scraper
```bash
python src/scripts/weather_scrape.py
```
Fetches current weather for all 30 MLB stadium locations with ML predictions.

### Yahoo Fantasy Scraper
```bash
python src/scripts/yahoo_scrape.py
```
Authenticates via browser and fetches your Yahoo Fantasy rosters.

---

## ⚡ Delta Updates (Fast Incremental Updates)

For **quick daily updates** without full data refresh:

### Update Recent Games & Rosters (~30 seconds)
```bash
python src/scripts/mlb_delta_scrape.py
```

**What it does:**
- ✅ Fetches only NEW games since last update
- ✅ Updates current player rosters
- ✅ Appends to existing CSV files
- ⚡ Much faster than full scrape (30 sec vs 5 min)

**Use this for:**
- Daily updates during season
- Quick roster checks
- Recent game additions

### Update Weather Only (~15 seconds)
```bash
python src/scripts/weather_delta_scrape.py
```

**What it does:**
- ✅ Fetches current weather for all stadiums
- ✅ Overwrites weather CSV with fresh data
- ⚡ Ultra-fast update

**Use this for:**
- Pre-game weather checks
- Daily condition updates
- Quick weather snapshots

**💡 Pro Tip:** `fb_ai.py` automatically runs delta updates after operations to ensure you have the absolute latest data!

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

### Yahoo Fantasy Sports Integration

### Yahoo Fantasy Sports Integration

The system uses Yahoo Fantasy Sports API with browser-based OAuth authentication:

**Configuration (`oauth2.json`):**
```json
{
  "consumer_key": "your_client_id",
  "consumer_secret": "your_client_secret"
}
```

**Environment Variables (`.env`):**
```
BROWSER_PATH=/usr/bin/google-chrome
```

**Authentication Flow:**
1. Opens browser for Yahoo login
2. User authorizes application
3. Captures OAuth tokens automatically
4. Fetches roster for specified team names

**Supported Teams:**
- Configure your team names in `yahoo_scrape.py`
- Default: "I like big bunts" and "Pure uncut adam west"

### MLB Stats API

A Python scraper implementation based on the [MLB Google Cloud Hackathon repository](https://github.com/MajorLeagueBaseball/google-cloud-mlb-hackathon).

### Features

- **Game Schedules**: Regular season, postseason, and spring training for all years
- **Live Game Feeds**: Real-time GUMBO (Grand Unified Master Baseball Object) data
- **Team Information**: All 30 MLB teams with complete rosters, details, and stats
- **Player Information**: All players across multiple seasons with profiles, stats, and career data
- **Multi-Year Support**: Automatically fetches current year + previous 3 years
- **Weather Predictions**: ML-based weather forecasting for all 30 MLB stadiums
- **CSV Export**: Export all data to CSV for analysis and machine learning

### Usage Example

```python
from mlb_scrape import MLBStatsScraper

scraper = MLBStatsScraper()

# Get 2024 schedule
schedule = scraper.get_schedule(season=2024, game_type='R')

# Get team roster
roster = scraper.get_team_roster(team_id=119, season=2024)  # LA Dodgers

# Get player info
player = scraper.get_player_info(player_id=660271)  # Shohei Ohtani

# Get live game feed
game_feed = scraper.get_live_game_feed(game_pk=745444)
```

### Key Methods

#### Schedule & Games
- `get_schedule(season, game_type, team_id, start_date, end_date)` - Get game schedules
- `get_live_game_feed(game_pk, timecode)` - Get complete game state (GUMBO feed)
- `get_game_timestamps(game_pk)` - Get available timestamps for a game

#### Teams
- `get_all_teams(season)` - Get all MLB teams
- `get_team_info(team_id, season)` - Get detailed team information
- `get_team_roster(team_id, season)` - Get team roster

#### Players
- `get_player_info(player_id, season)` - Get player information
- `get_player_stats(player_id, season, stats_group)` - Get player statistics

#### Export
- `export_schedule_to_csv(schedule_data, filename)` - Export schedule to CSV
- `export_roster_to_csv(roster_data, filename)` - Export roster to CSV

### MLB Stats API Endpoints

- Base URL: `https://statsapi.mlb.com/api`
- Schedule: `/v1/schedule`
- Game Feed: `/v1.1/game/{game_pk}/feed/live`
- Teams: `/v1/teams/{team_id}`
- Players: `/v1/people/{player_id}`

### Common Team IDs

- Los Angeles Dodgers: 119
- New York Yankees: 147
- Boston Red Sox: 111
- San Francisco Giants: 137
- Chicago Cubs: 112

### Game Types

- `R` - Regular Season
- `P` - Postseason
- `S` - Spring Training

### MLB Data Availability

- **1901-1968**: Boxscore level
- **1969-1988**: Play-by-play level
- **1989-2007**: Pitch-by-pitch level
- **2008-2014**: Pitch-by-pitch with speed/break (Pitch F/x)
- **2015-Present**: Enhanced metrics (exit velocity, HR distance)

---

## MLB Stadium Weather Predictor

A machine learning weather prediction system based on [FELIX-GEORGE/WeatherPrediction_ML_Model](https://github.com/FELIX-GEORGE/WeatherPrediction_ML_Model).

### Features

- **Real-Time Weather**: Fetches current conditions for all 30 MLB stadiums
- **ML Predictions**: Random Forest classifier predicts Rainy/Sunny conditions
- **Comprehensive Data**: Temperature, humidity, pressure, wind speed, cloud cover
- **Stadium Coordinates**: Precise lat/lon for every MLB venue
- **Weather API**: Uses Open-Meteo (free, no API key required)

### Weather Data Collected

For each stadium, the following metrics are gathered:
- Temperature (°C)
- Humidity (%)
- Atmospheric Pressure (hPa)
- Wind Speed (km/h)
- Wind Direction (degrees and cardinal: N, NE, E, SE, S, SW, W, NW)
- Wind Gusts (km/h)
- Cloud Cover (%)
- Precipitation (mm)
- ML Prediction (Rainy/Sunny)
- Confidence Score

### Example Output

```
☀️  Sunny Stadiums: 8/30 (26.7%)
🌧️  Rainy Stadiums: 22/30 (73.3%)

💨 WIND ANALYSIS:
   Average Wind Speed: 10.6 km/h
   Max Wind Gusts: 48.2 km/h
   Most Common Wind Direction: NW (4 stadiums)

🌪️  Windiest Stadiums:
   New York Yankees: 24.8 km/h WNW (gusts 44.3)
   Philadelphia Phillies: 23.8 km/h WNW (gusts 48.2)
   Boston Red Sox: 22.0 km/h W (gusts 45.0)

🌧️  Rainiest Conditions:
   Seattle Mariners: 9.9°C, 85% humidity, Wind 13.1 km/h S (83.0% confidence)
   Houston Astros: 16.2°C, 99% humidity, Wind 5.4 km/h E (80.0% confidence)

☀️  Best Weather:
   Arizona Diamondbacks: 14.5°C, 46% humidity, Wind 6.9 km/h E (71.0% confidence)
   Kansas City Royals: 7.7°C, 56% humidity, Wind 18.7 km/h SE (71.0% confidence)
```

### Use Cases

- **Game Planning**: Identify potential weather delays and wind impacts
- **Fantasy Baseball**: Account for weather and wind impact on player performance
  - Strong winds can affect fly balls and home runs
  - Wind direction matters for hitting (outgoing vs. incoming)
- **Stadium Operations**: Prepare for weather-related issues
- **Fan Experience**: Know what to expect at the ballpark
- **Betting Analytics**: Wind conditions can significantly impact scoring

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

## 📝 Quick Reference Summary

### Three Analysis Factors

| Factor | Weight | What It Measures | Key Insight |
|--------|--------|------------------|-------------|
| **🌪️ Wind** | 30% | Wind speed/direction at stadium | Tailwind = more HRs, Headwind = fewer HRs |
| **📊 Matchup** | 40% | Historical performance vs opponent | Past success predicts future performance |
| **🏠 Venue** | 30% | Home vs. away performance splits | Some players excel at home, others on road |

### Command Cheat Sheet

```bash
# First time setup
python src/fb_ai.py --refresh

# Daily recommendations (fastest)
python src/fb_ai.py

# Just check data status
python src/fb_ai.py --status

# Manual scrapers (advanced)
python src/scripts/mlb_scrape.py          # Full MLB data
python src/scripts/weather_scrape.py      # Weather predictions
python src/scripts/yahoo_scrape.py        # Yahoo rosters
python src/scripts/mlb_delta_scrape.py    # Quick MLB update
python src/scripts/weather_delta_scrape.py # Quick weather update
```

### Key Output Files

- **`matchup_advantage_analysis_*.csv`** ← YOUR MAIN FILE
  - All 3 factors combined
  - Final scores and recommendations
  - Use this for start/sit decisions

- **`weather_advantage_analysis_*.csv`**
  - Wind analysis only
  - Stadium conditions

- **`yahoo_fantasy_rosters_*.csv`**
  - Your current roster snapshot

### Score Interpretation

| Score Range | Recommendation | Action |
|-------------|---------------|--------|
| +1.5 to +2.0 | 🌟 VERY FAVORABLE | Strong start, high confidence |
| +0.5 to +1.5 | ✅ FAVORABLE | Good play, start if available |
| -0.5 to +0.5 | ⚖️ NEUTRAL | Use other factors/gut feel |
| -1.5 to -0.5 | ⚠️ UNFAVORABLE | Consider benching |
| -2.0 to -1.5 | 🚫 VERY UNFAVORABLE | Bench if possible |

### What's Next?

🔜 **Coming Soon:** Additional analysis factors including:
- Pitcher quality metrics
- Recent form trends (7/14/30 day)
- Umpire strike zone analysis
- Rest day impacts
- Day/night game splits
- Temperature effects
- Park factors
- Platoon advantages

---

## License

This project uses publicly available MLB data through their official Stats API.
