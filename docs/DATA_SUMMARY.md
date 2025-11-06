# MLB Data Collection Summary

## Overview

Complete MLB statistics database covering **4 years** (2022-2025) with all teams, players, and game schedules.

## Data Statistics

### Teams
- **Total**: 30 MLB teams
- **American League**: 15 teams
- **National League**: 15 teams

### Players
- **Total Records**: 5,969 player-season combinations
- **Unique Players**: 2,369 individual players
- **Years Covered**: 2022, 2023, 2024, 2025

### Game Schedules
- **2025**: 2,464 games
- **2024**: 2,469 games
- **2023**: 2,476 games
- **2022**: 2,479 games
- **Total**: 9,888 games

### Position Distribution (All Years)
- **Pitchers**: 3,276 (54.9%)
- **Infielders**: 1,222 (20.5%)
- **Outfielders**: 981 (16.4%)
- **Catchers**: 417 (7.0%)
- **Hitters**: 69 (1.2%)
- **Two-Way Players**: 4 (0.1%)

## Files Generated

### Team Data
- `mlb_all_teams.csv` - Complete team information for all 30 MLB teams

### Schedule Data
- `mlb_2025_schedule.csv` - 2025 regular season games
- `mlb_2024_schedule.csv` - 2024 regular season games
- `mlb_2023_schedule.csv` - 2023 regular season games
- `mlb_2022_schedule.csv` - 2022 regular season games

### Player Data
- `mlb_all_players_2025.csv` - All players for 2025 season
- `mlb_all_players_2024.csv` - All players for 2024 season
- `mlb_all_players_2023.csv` - All players for 2023 season
- `mlb_all_players_2022.csv` - All players for 2022 season
- `mlb_all_players_complete.csv` - **Consolidated database** with all player-season records

## Database Schema

### mlb_all_teams.csv
| Column | Description |
|--------|-------------|
| team_id | Unique team identifier |
| team_name | Full team name |
| team_abbreviation | Team abbreviation (e.g., LAD, NYY) |
| location_name | City/location |
| league | American League or National League |
| division | Division name (e.g., AL West, NL East) |
| venue_name | Home stadium name |
| first_year | Year franchise started |

### mlb_all_players_complete.csv
| Column | Description |
|--------|-------------|
| player_id | Unique player identifier |
| player_name | Player's full name |
| team_id | Team identifier |
| team_name | Team name |
| season | Year (2022-2025) |
| jersey_number | Jersey number |
| position | Specific position (e.g., Shortstop) |
| position_type | Position category (Pitcher, Infielder, etc.) |
| status | Player status (Active, Injured, etc.) |

### mlb_YYYY_schedule.csv
| Column | Description |
|--------|-------------|
| game_pk | Unique game identifier |
| game_date | Date of game |
| game_type | R=Regular, P=Playoff, S=Spring |
| season | Year |
| away_team | Visiting team name |
| away_team_id | Visiting team ID |
| home_team | Home team name |
| home_team_id | Home team ID |
| venue | Stadium name |
| status | Game status (Final, Scheduled, etc.) |

## Top Teams by Roster Size (2024)

1. **Miami Marlins**: 70 players
2. **Los Angeles Angels**: 64 players
3. **Chicago White Sox**: 62 players
4. **Baltimore Orioles**: 60 players
5. **Los Angeles Dodgers**: 60 players

## Use Cases

This comprehensive dataset is ideal for:

- **Fantasy Baseball Analysis**: Player performance prediction
- **Machine Learning Models**: Training models on historical player/team data
- **Statistical Analysis**: Trends, patterns, and insights
- **Player Comparison**: Cross-season and cross-team comparisons
- **Team Strategy**: Roster composition and optimization
- **Game Prediction**: Using historical schedule and performance data

## Data Source

All data is sourced from the official MLB Stats API (statsapi.mlb.com) which provides:
- Real-time game data (GUMBO feeds)
- Complete historical records back to 1901
- Pitch-by-pitch data since 2008
- Enhanced metrics (exit velocity, home run distance) since 2015

## Next Steps

With this data, you can:

1. Build XGBoost models to predict player performance
2. Analyze team roster strategies across seasons
3. Create fantasy baseball draft rankings
4. Predict game outcomes based on historical matchups
5. Identify breakout players and statistical trends

---

**Generated**: November 2024  
**Data Coverage**: 2022-2025 MLB Seasons  
**Total Records**: 5,969 player-season combinations across 9,888 games
