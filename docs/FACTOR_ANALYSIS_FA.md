# Factor Analysis (FA) Modules

This documentation covers all analysis factors used by the Fantasy Baseball AI system to generate start/sit recommendations.

## Overview

Each factor analysis module evaluates a specific aspect of player performance and generates scores from -2.0 (very unfavorable) to +2.0 (very favorable). These scores are weighted and combined to produce final recommendations.

> **Note:** All current and future Factor Analysis documentation is consolidated in this file. Individual module README files are no longer maintained separately.

---

## Available Factor Analysis Modules

### 1. Wind Analysis (`wind_analysis.py`)

**Weight:** 15%

**What it analyzes:** How wind conditions at the game stadium affect pitcher and hitter performance.

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

**Real Impact:** Studies show 15+ mph tailwinds can increase home runs by 20-30%

**Usage:**
```python
from src.scripts.fa.wind_analysis import analyze_wind_advantage
scores = analyze_wind_advantage(roster_df, weather_df)
```

---

### 2. Historical Matchup Performance (`matchup_fa.py`)

**Weight:** 20%

**What it analyzes:** How a player has performed historically against today's specific opponent.

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

**Why it matters:** Players often have "nemesis teams" or "favorite opponents"

**Usage:**
```python
from src.scripts.fa.matchup_fa import analyze_matchup_history
scores = analyze_matchup_history(roster_df, mlb_data)
```

---

### 3. Home/Away Venue Splits (`home_away_fa.py`)

**Weight:** 15%

**What it analyzes:** Whether a player performs better at their home stadium or on the road.

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

**Why it matters:** Venue effects can be as impactful as matchup history (50+ BA point swings)

**Usage:**
```python
from src.scripts.fa.home_away_fa import analyze_venue_splits
scores = analyze_venue_splits(roster_df, mlb_data)
```

---

### 4. Rest Day Impacts (`rest_day_fa.py`)

**Weight:** 13%

**What it analyzes:** How days of rest between games affect player performance.

**Key Concepts:**
- **Rested (2+ days off):** Some players benefit from rest
  - Fresh legs, recovered from minor injuries
  - Better focus and energy levels
  
- **Back-to-Back Games (0-1 days):** Some players thrive on rhythm
  - Stay in groove, maintain timing
  - May experience fatigue over time

**How it scores:**
- Calculates batting average when rested (2+ days) vs back-to-back (0-1 days)
- Compares current game's rest status to player's historical splits
- If playing with preferred rest pattern = positive score
- If playing against preferred pattern = negative score

**Real Impact:** Can be 30-50 BA point difference for some players

**Usage:**
```python
from src.scripts.fa.rest_day_fa import analyze_rest_impacts
scores = analyze_rest_impacts(roster_df, mlb_data)
```

---

### 5. Injury/Recovery Tracking (`injury_fa.py`)

**Weight:** 13%

**What it analyzes:** Player performance immediately following injury recovery.

**Key Concepts:**
- **Injury Detection:** Identifies gaps of 14+ days in game logs (likely IL stint)
- **Recovery Period (30 days post-return):** Critical monitoring window
  - Players may be tentative, rusty, or not at full strength
- **Post-Injury Performance:** Tracks actual results vs. pre-injury baseline

**How it scores:**
- Identifies most recent injury gap (14+ consecutive days missed)
- Calculates pre-injury baseline
- Measures post-injury performance
- Applies recency penalty (recently returned = more uncertainty)
- Generates score: -2.0 (struggling post-injury) to +2.0 (thriving post-injury)

**Special Labels:**
- **"STRUGGLING POST-INJURY"** (≤ -1.0): Significant performance decline
- **"RECOVERING"** (-0.3 to -1.0): Minor decline, still finding form
- **"NEUTRAL"** (-0.3 to +0.3): Performing at baseline
- **"STRONG POST-INJURY"** (≥ +1.0): Performing better than before injury
- **"HEALTHY"**: No recent injury gaps detected (score = 0.0)

**Real Impact:** 60% of players underperform first 5 games back (avg -35 BA points)

**Usage:**
```python
from src.scripts.fa.injury_fa import analyze_injury_recovery
scores = analyze_injury_recovery(roster_df, mlb_data)
```

---

### 6. Umpire Strike Zone Analysis (`umpire_fa.py`)

**Weight:** 12%

**What it analyzes:** How the home plate umpire's strike zone tendencies affect pitcher and hitter performance.

**Key Concepts:**
- **Strike Zone Size:**
  - **Large Zone:** More strikes → Favors pitchers
  - **Small Zone:** More walks → Favors hitters
  - **Inconsistent Zone:** Unpredictable → Disadvantages both
  
- **Umpire Consistency:** Accuracy rate of strike/ball calls
  - **High Consistency (90%+):** Predictable, fair
  - **Low Consistency (<80%):** Frustrating, unpredictable

**How it scores:**
- Identifies home plate umpire assigned to the game
- Analyzes umpire's historical zone size, consistency, and bias
- Large zone + pitcher = positive (more strikes)
- Small zone + hitter = positive (more walks/better pitches)
- Generates score: -1.5 (very unfavorable) to +1.5 (very favorable)

**Real Impact:** Umpire zones vary by 3-5 inches (15-20% strike rate changes)

**Usage:**
```python
from src.scripts.fa.umpire_fa import analyze_umpire_effects
scores = analyze_umpire_effects(roster_df, game_data)
```

---

### 7. Platoon Advantages (`platoon_fa.py`)

**Weight:** 12%

**What it analyzes:** Left-handed vs. right-handed pitcher/hitter matchups.

**Key Concepts:**
- **Favorable Platoon Matchups:** Opposite-handed matchups
  - **LHB vs RHP:** FAVORABLE (better ball visibility, breaking balls move toward hitter)
  - **RHB vs LHP:** FAVORABLE (same advantages)
  
- **Unfavorable Platoon Matchups:** Same-handed matchups
  - **LHB vs LHP:** UNFAVORABLE (-30 to -50 BA points typical)
  - **RHB vs RHP:** SLIGHTLY UNFAVORABLE (-15 to -25 BA points)

**How it scores:**
- Determines hitter's batting handedness (L/R/S)
- Identifies opposing pitcher's throwing hand (L/R)
- Analyzes historical splits (vs LHP vs RHP) if available
- Weighs expected platoon (30%) vs actual player splits (70%)
- Generates score: -1.5 (very unfavorable) to +1.5 (very favorable)

**Real Impact:** MLB-wide, opposite-handed matchups yield ~15-20 points higher BA

**Usage:**
```python
from src.scripts.fa.platoon_fa import analyze_platoon_advantages
scores = analyze_platoon_advantages(roster_df, pitcher_data)
```

---

### 8. Temperature Analysis (`temperature_fa.py`)

**Weight:** 10%

**What it analyzes:** How temperature conditions affect hitting and pitching performance through air density and ball flight physics.

**Key Concepts:**
- **Warm Weather (75-95°F / 24-35°C):** Ball travels further
  - Air is less dense → More carry on fly balls
  - Benefits: Hitters ✅ | Hurts: Pitchers ❌
  
- **Cold Weather (<55°F / 13°C):** Ball doesn't carry
  - Denser air → Less ball flight distance
  - Benefits: Pitchers ✅ | Hurts: Hitters ❌

- **Extreme Heat (>95°F / 35°C):** Player fatigue
  - Ball carries well BUT players tire faster
  - Mixed impact on performance

**How it scores:**
- Cold (<55°F): -2.0 for hitters (strong pitcher advantage)
- Cool (55-65°F): -1.0 for hitters (slight pitcher advantage)
- Moderate (65-75°F): -0.5 to 0.0 (neutral to slight pitcher edge)
- Warm (75-85°F): +1.5 for hitters (favorable)
- Hot (85-95°F): +2.0 for hitters (very favorable)
- Very Hot (>95°F): +1.0 for hitters (reduced due to fatigue)

**Real Impact:** 
- Studies show every 10°F increase in temperature adds ~5 feet to fly ball distance
- Home runs increase by ~1% for every 1°F above 70°F
- Cold weather games (<50°F) see 15-20% fewer home runs

**Output Metrics:**
- **temperature_f:** Game-time temperature in Fahrenheit
- **temperature_c:** Game-time temperature in Celsius
- **temp_category:** Cold/Cool/Moderate/Warm/Hot/Very Hot
- **hitter_advantage:** Score for hitters (-2.0 to +2.0)
- **pitcher_advantage:** Score for pitchers (inverted from hitter)
- **carry_factor:** Expected ball flight distance multiplier
- **impact:** Descriptive analysis of temperature effects

**Strategic Applications:**
- **Start Power Hitters:** Prioritize in warm/hot weather games
- **Bench in Cold:** Consider benching contact/power hitters in <55°F games
- **Pitcher Streaming:** Target pitchers in cold weather games
- **DFS Leverage:** Stack hitters in hot weather games for leverage

**Limitations:**
- Does not account for humidity effects (high humidity = denser air)
- Wind can amplify or negate temperature effects
- Player tolerance to temperature varies by background/experience
- Indoor stadiums not affected by temperature

**Usage:**
```python
from src.scripts.fa.temperature_fa import analyze_temperature_effects
scores = analyze_temperature_effects(roster_df, weather_df)
```

---

### 9. Park Factors (`park_factors_fa.py`)

**Weight:** 9%

**What it analyzes:** How specific ballpark characteristics affect offensive and pitching performance.

**Key Concepts:**
- **Park Factor:** Statistical measure comparing scoring at stadium vs league average
  - **Factor > 1.0:** Hitter-friendly park (more runs, HRs, hits)
  - **Factor = 1.0:** Neutral park
  - **Factor < 1.0:** Pitcher-friendly park (fewer runs, HRs, hits)

- **Why Parks Differ:**
  - Dimensions (wall distances, height)
  - Altitude (Coors Field = thinner air)
  - Weather patterns (marine layer in SF/SD/SEA)
  - Playing surface (grass vs turf)

**How it scores:**
- Identifies game location and stadium
- Retrieves park factors (runs, HR, hits)
- For hitters: High factor = positive score
- For pitchers: Low factor = positive score (inverted)
- Generates score: -2.0 (very unfavorable) to +2.0 (very favorable)

**Real Impact:**
- Coors Field: +30% runs, +35% HRs vs average
- Oracle Park: -20% HRs, -12% runs vs average

**Usage:**
```python
from src.scripts.fa.park_factors_fa import analyze_park_factors
scores = analyze_park_factors(roster_df, stadium_data)
```

---

### 10. Pitch Mix Analysis (`pitch_mix_fa.py`)

**Weight:** 8%

**What it analyzes:** Pitcher's pitch type usage and batter's historical performance against different pitch types to identify favorable/unfavorable matchups.

**Key Concepts:**
- **Pitch Categories:**
  - **Fastballs (55% avg):** 4-seam, 2-seam/Sinker, Cutter
  - **Breaking Balls (25% avg):** Slider, Curveball, Slurve
  - **Offspeed (20% avg):** Changeup, Splitter, Split-Finger

- **Matchup Analysis:**
  - Pitcher's primary pitch vs batter's weakness = FAVORABLE
  - Pitcher's primary pitch vs batter's strength = UNFAVORABLE
  - High usage of batter's strong pitch = BAD for pitcher
  - High usage of batter's weak pitch = GOOD for pitcher

**How it scores:**
- Analyzes pitcher's pitch mix distribution (% usage per pitch type)
- Evaluates batter's BA against each pitch type
- Calculates weighted matchup score based on usage × performance
- For batters: Positive score when facing pitchers who throw their favorite pitches
- For pitchers: Positive score when opponents struggle vs their pitch mix
- Generates score: -2.0 (very unfavorable) to +2.0 (very favorable)

**Real Impact:** 
- Batters hitting .300+ vs fastballs face 65% fastball pitcher = GREAT matchup
- Batters hitting .180 vs breaking balls face slider specialist = POOR matchup
- 50+ BA point swings possible based on pitch mix matchup

**Pitch Type Details:**

**Fastballs (55% avg):**
- **4-Seam (FF):** High velocity, straight, most common pitch
- **2-Seam/Sinker (SI):** Movement, induces ground balls
- **Cutter (FC):** Late movement, hybrid between fastball and slider

**Breaking Balls (25% avg):**
- **Slider (SL):** Lateral movement, swing-and-miss pitch
- **Curveball (CU):** Vertical drop, slow speed differential
- **Slurve:** Combination of slider and curve movement

**Offspeed (20% avg):**
- **Changeup (CH):** Speed differential, fades away from opposite-handed hitters
- **Splitter (FS):** Late drop, mimics fastball initially
- **Split-Finger:** Extreme drop, difficult to control

**Analysis Methodology:**

1. **Pitch Mix Profiling:**
   - Categorize pitcher's arsenal by pitch type
   - Calculate usage percentage for each pitch
   - Identify primary, secondary, and tertiary pitches

2. **Batter Performance Analysis:**
   - Historical BA vs each pitch type
   - Sample size weighting (confidence levels)
   - Identify strengths and weaknesses

3. **Matchup Scoring:**
   ```
   Matchup Score = Σ (Pitch Usage% × Batter Performance vs Pitch)
   ```

4. **Confidence Adjustment:**
   - High sample size (100+ pitches seen) = full weight
   - Medium sample (50-99 pitches) = 75% weight
   - Low sample (<50 pitches) = 50% weight (use league averages)

**Output Metrics:**
- **pitcher_primary_pitch:** Most frequently thrown pitch type
- **pitch_usage_distribution:** Percentage breakdown of all pitch types
- **batter_vs_fastball_avg:** Batting average vs fastballs
- **batter_vs_breaking_avg:** Batting average vs breaking balls
- **batter_vs_offspeed_avg:** Batting average vs offspeed pitches
- **matchup_advantage:** Weighted matchup score
- **pitch_mix_score:** Final advantage score (-2.0 to +2.0)
- **impact:** Descriptive analysis of pitch matchup

**Strategic Applications:**

**For Daily Lineups:**
- Start hitters facing pitchers who throw their best pitch types heavily
- Bench hitters facing pitchers who exploit their weaknesses
- Prioritize matchups with >100 pitch sample size

**For DFS:**
- Target underpriced hitters with elite pitch mix matchups
- Stack teams facing pitch-to-contact starters
- Fade popular picks with poor pitch mix matchups

**For Season-Long:**
- Trade for players with favorable upcoming schedule of pitch matchups
- Stream pitchers facing lineups weak against their primary pitch
- Avoid pitchers whose arsenal matches opponent's strengths

**Real-World Examples:**
- **Power hitter vs fastball-heavy starter:** EXCELLENT (can sit on heat)
- **Contact hitter vs breaking ball specialist:** POOR (struggles with movement)
- **Patient hitter vs control pitcher:** NEUTRAL (fewer mistakes to capitalize on)
- **Free swinger vs strikeout pitcher:** POOR (plays into pitcher's strength)

**Limitations:**
- Pitch mix data may be simulated when Statcast unavailable
- Small sample sizes reduce reliability
- Pitcher injury/velocity changes not reflected in historical data
- Does not account for sequencing or pitch tunneling
- Weather and fatigue can affect pitch quality/usage

**Future Enhancements:**
- Integration with Statcast pitch-level data
- Pitch velocity and spin rate analysis
- Pitch sequencing patterns
- Tunneling effectiveness metrics
- Fatigue-adjusted pitch mix (late innings)
- Umpire strike zone correlation with pitch types

**Usage:**
```python
from src.scripts.fa.pitch_mix_fa import analyze_pitch_mix
scores = analyze_pitch_mix(roster_df, mlb_data, pitcher_data)
```

---

### 11. Time of Day Analysis (`time_of_day_fa.py`)

**Weight:** 7%

**What it analyzes:** How game timing (day vs. twilight vs. night games) affects player fantasy production through visibility, circadian rhythms, and environmental factors.

**Key Concepts:**
- **Day Games (10 AM - 4 PM):** Natural lighting with shadows
  - Warmer temperatures (early season)
  - Higher scoring historically
  - More stolen base opportunities
  - Challenging sun positioning for hitters
  
- **Twilight Games (4 PM - 7 PM):** Most difficult visibility
  - Sun directly in sight lines
  - Hardest time to track ball
  - Strong advantage for pitchers
  - Lowest offensive production period
  
- **Night Games (After 7 PM):** Consistent lighting
  - Artificial lighting (no shadows)
  - Cooler temperatures
  - Better visibility than twilight
  - Most common game time

**How it scores:**
- Classifies game time into Day/Twilight/Night categories
- Retrieves player's historical day/night splits (BA, ERA, OPS)
- Applies league-wide adjustment factors for each time period
- Calculates performance multiplier based on player tendencies
- For hitters: Higher in favorable time windows
- For pitchers: Considers command/visibility advantages
- Generates score: -2.0 (struggles at this time) to +2.0 (excels at this time)

**Real Impact:**
- Twilight games see 8% lower batting averages league-wide
- Some players show 50+ BA point differences between day/night
- Power pitchers benefit more from twilight conditions
- Contact hitters less affected than power hitters by time of day

**Performance Factors:**

**For Hitters:**
- **Vision & Tracking:** Ball visibility varies with lighting and time of day
- **Power:** Temperature affects how far balls travel
- **Splits:** Historical day/night batting averages and OPS
- **Timing:** Circadian rhythms affect reaction time and energy levels

**For Pitchers:**
- **Command:** Lighting can affect pitcher's release point visibility to batters
- **Advantage:** Twilight games favor pitchers due to difficult hitting conditions
- **Splits:** Historical day/night ERA and performance metrics
- **Fatigue:** Day games after night games can impact performance

**League Average Adjustments:**
```
Day Games:
- Batting Average: Baseline (1.00x)
- Power: -2% (0.98x)
- Speed: +2% (1.02x)
- Pitcher ERA: +5% worse (1.05x)

Twilight Games:
- Batting Average: -8% (0.92x)
- Power: -6% (0.94x)
- Speed: Baseline (1.00x)
- Pitcher ERA: -5% better (0.95x)

Night Games:
- Batting Average: Baseline (1.00x)
- Power: +2% (1.02x)
- Speed: -2% (0.98x)
- Pitcher ERA: -2% better (0.98x)
```

**Output Metrics:**
- **time_category:** Day, Twilight, Night, or Unknown
- **day_avg_era:** Player's performance in day games
- **night_avg_era:** Player's performance in night games
- **performance_multiplier:** Adjustment factor for expected performance
- **time_advantage_score:** Overall advantage rating (0-10)
- **impact:** Descriptive analysis of time-of-day effect
- **category_info:** Detailed explanation of game time characteristics

**Score Interpretation:**
- **8-10:** Strong advantage - Player excels at this game time
- **5-7:** Moderate advantage - Player performs well at this time
- **3-5:** Neutral - No significant time-of-day effect
- **0-3:** Struggles - Player underperforms at this game time

**Strategic Applications:**

**Start/Sit Decisions:**
- Favor players with strong day game splits in afternoon contests
- Consider benching players who struggle in twilight games
- Weight time-of-day data alongside other factors

**DFS Optimization:**
- Target underpriced players with favorable time splits
- Avoid popular picks with poor day/night matchups
- Build stacks considering game timing

**Trade Evaluation:**
- Assess player value based on team's typical game times
- Consider schedule strength regarding day/night game distribution
- Factor in ballpark lighting quality

**Real-World Insights:**

**Common Patterns:**
- **Young Power Hitters:** Often perform better at night (better ball tracking)
- **Veterans:** May prefer day games (less taxing on body)
- **Speed Players:** Day games typically offer more SB opportunities
- **Contact Hitters:** Less affected by lighting than power/patience hitters
- **Finesse Pitchers:** Excel in twilight conditions

**Team Considerations:**
- **Cubs:** High number of day games at Wrigley Field
- **West Coast:** More night games due to time zones
- **Double Headers:** Often include day games with different dynamics

**Limitations:**
- Simulated split data when actual historical splits unavailable
- Does not account for stadium-specific lighting quality
- Player circadian preferences estimated from performance data
- Weather interaction with time of day not fully modeled
- Travel and fatigue impacts simplified

**Future Enhancements:**
- Integration with actual MLB split statistics API
- Stadium-specific lighting quality ratings
- Travel and schedule fatigue modeling
- Weather correlation with game time effects
- Individual player circadian rhythm profiling
- Seasonal adjustments (day games warmer in summer, cooler in spring)

**Related Factor Analyses:**
- **Temperature FA:** Complements time analysis (day games = warmer)
- **Umpire FA:** Strike zone may vary by visibility conditions
- **Rest Day FA:** Day games after night games affect fatigue
- **Park Factors FA:** Some parks have better lighting than others

**Usage:**
```python
from src.scripts.fa.time_of_day_fa import analyze_time_of_day
scores = analyze_time_of_day(roster_df, weather_df)
```

---

### 12. Lineup Position Analysis (`lineup_position_fa.py`)

**Weight:** 6%

**What it analyzes:** Impact of a player's batting order position on their fantasy production opportunities.

**Key Concepts:**
- **Lineup Position Impact:**
  - **Leadoff (1-2):** Maximum plate appearances, run scoring focus
  - **Heart of Order (3-4-5):** Best RBI opportunities, power spots
  - **Bottom Third (6-7-8-9):** Fewer chances, minimal protection

- **Position Effects:**
  - **Plate Appearances:** Position 1 gets ~4.6 PA vs Position 9 ~3.6 PA
  - **RBI Opportunities:** Positions 3-4-5 get 1.2-1.4x more runners on base
  - **Run Scoring:** Leadoff spots score 1.4x more runs than bottom order
  - **Pitcher Matchups:** Top of order sees starter more, bottom may face reliever

**How it scores:**
- Identifies player's lineup position for the game (1-9)
- Calculates PA multiplier (more PA = better opportunities)
- Applies RBI opportunity factor (middle order = more chances)
- Applies run scoring factor (top order = more chances)
- Combines into overall multiplier weighted to PA (50%), RBI (25%), Runs (25%)
- Generates score: Higher position = higher score (9.0 for leadoff to 0.0 for 9-hole)

**Real Impact:**
- Moving from 6th to 3rd in lineup = ~0.4 more PA per game = 65 more PA per season
- Cleanup hitters see ~40% more RBI opportunities than leadoff
- Leadoff hitters score ~50% more runs than 8-hole hitters

**Position Tiers:**
- **Excellent (1-4):** Maximum fantasy value, must-start spots
- **Good (5):** Above average opportunities, solid value
- **Fair (6-7):** Below average PA, reduced upside
- **Poor (8-9):** Minimum opportunities, avoid if possible

**Output Metrics:**
- **Lineup Spot:** Batting order position (1-9)
- **Lineup Tier:** Top (1-2), Middle (3-4-5), Bottom (6-7-8-9)
- **Expected PA:** Projected plate appearances for the game
- **PA Multiplier:** Plate appearance opportunity vs average
- **RBI Multiplier:** RBI opportunity vs average
- **Run Multiplier:** Run scoring opportunity vs average
- **Lineup Score:** Overall fantasy value score
- **Impact:** Description of position characteristics

**Interpretation:**
- **Excellent Positions (1-4):** Maximum plate appearances, best run/RBI opportunities, highest fantasy ceiling
- **Good Position (5):** Above average opportunities, solid protection, good fantasy value
- **Fair Positions (6-7):** Below average plate appearances, limited RBI opportunities, reduced fantasy upside
- **Poor Positions (8-9):** Minimum plate appearances, fewest scoring opportunities, lowest fantasy value

**Strategic Insights:**
- **Lineup Movement:** Moving up = significant fantasy boost; Moving down = notable penalty
- **Fantasy Impact:** Leadoff best for runs/steals; 3-4-5 best for HRs/RBIs; Bottom order avoid in daily lineups
- **Usage Recommendations:** Must Start (1-5), Situation Dependent (6-7), Fade (8-9) unless elite talent

**Limitations:**
- Lineup cards change daily
- Injuries affect lineup construction
- Platooning impacts consistency
- Simulated data when actual lineups unavailable

**Usage:**
```python
from src.scripts.fa.lineup_position_fa import analyze_lineup_position
scores = analyze_lineup_position(roster_df, mlb_data)
```

---

## Combined Scoring Formula

```python
FINAL_SCORE = (
    matchup_score      × 0.20   +  # Historical performance vs opponent
    venue_score        × 0.15   +  # Home/away splits  
    wind_score         × 0.12   +  # Weather conditions - wind
    rest_score         × 0.11   +  # Rest day impacts
    injury_score       × 0.10   +  # Injury/recovery status
    umpire_score       × 0.09   +  # Umpire strike zone tendencies
    platoon_score      × 0.09   +  # Platoon advantages (L/R matchups)
    temperature_score  × 0.08   +  # Temperature effects on ball flight
    time_of_day_score  × 0.07   +  # Day/Night/Twilight game timing
    pitch_mix_score    × 0.07   +  # Pitch type matchups
    lineup_position    × 0.06   +  # Batting order position
    park_score         × 0.06      # Park factors (ballpark environment)
)
```

---

## Score Interpretation

| Score Range | Recommendation | Action |
|-------------|---------------|--------|
| +1.5 to +2.0 | 🌟 VERY FAVORABLE | Strong start, high confidence |
| +0.5 to +1.5 | ✅ FAVORABLE | Good play, start if available |
| -0.5 to +0.5 | ⚖️ NEUTRAL | Use other factors/gut feel |
| -1.5 to -0.5 | ⚠️ UNFAVORABLE | Consider benching |
| -2.0 to -1.5 | 🚫 VERY UNFAVORABLE | Bench if possible |

---

## Usage in Main System

All factors are automatically called by `src/fb_ai.py`:

```python
from src.scripts.fa.wind_analysis import analyze_wind_advantage
from src.scripts.fa.matchup_fa import analyze_matchup_history
from src.scripts.fa.home_away_fa import analyze_venue_splits
from src.scripts.fa.rest_day_fa import analyze_rest_impacts
from src.scripts.fa.injury_fa import analyze_injury_recovery
from src.scripts.fa.umpire_fa import analyze_umpire_effects
from src.scripts.fa.platoon_fa import analyze_platoon_advantages
from src.scripts.fa.temperature_fa import analyze_temperature_effects
from src.scripts.fa.time_of_day_fa import analyze_time_of_day
from src.scripts.fa.pitch_mix_fa import analyze_pitch_mix
from src.scripts.fa.lineup_position_fa import analyze_lineup_position
from src.scripts.fa.park_factors_fa import analyze_park_factors

# Run all analyses
wind_scores = analyze_wind_advantage(roster, weather)
matchup_scores = analyze_matchup_history(roster, mlb_data)
venue_scores = analyze_venue_splits(roster, mlb_data)
rest_scores = analyze_rest_impacts(roster, mlb_data)
injury_scores = analyze_injury_recovery(roster, mlb_data)
umpire_scores = analyze_umpire_effects(roster, game_data)
platoon_scores = analyze_platoon_advantages(roster, pitcher_data)
temperature_scores = analyze_temperature_effects(roster, weather)
pitch_mix_scores = analyze_pitch_mix(roster, mlb_data, pitcher_data)
park_scores = analyze_park_factors(roster, stadium_data)

# Combine with weights
final_score = (
    matchup_scores * 0.20 +
    venue_scores * 0.15 +
    wind_scores * 0.13 +
    rest_scores * 0.12 +
    injury_scores * 0.11 +
    umpire_scores * 0.10 +
    platoon_scores * 0.10 +
    temperature_scores * 0.09 +
    pitch_mix_scores * 0.08 +
    park_scores * 0.08
)
```

---

## Future Factor Analysis Modules

---

### 13. Defensive Positions Analysis (`defensive_positions_fa.py`)

**Weight:** 8%

**What it analyzes:** How opponent defensive quality and positioning strategies affect a player's expected offensive production in fantasy baseball where rosters are locked before games.

**Key Concepts:**
- **Team Defense Rating:** Overall defensive quality (0.0-1.0 scale)
  - Elite defense (>0.65): Reduces opponent offensive stats significantly
  - Average defense (0.35-0.65): Neutral impact
  - Poor defense (<0.35): Increases opponent offensive opportunities
  
- **Position-Specific Quality:** Individual position strength/weakness
  - Elite defender at position: Fewer hits/opportunities (-1.5 to score)
  - Weak defender at position: More hits/opportunities (+1.5 to score)
  - Position importance varies (SS/2B/CF > LF/RF/1B)

- **Defensive Shifts:** Strategic positioning against hitters
  - Heavy shift usage vs LHB: Reduces BABIP by ~.020-.030
  - Moderate shifting vs RHB: Smaller but measurable impact
  - Affects primarily ground ball hitters

- **Fantasy Context:** Rosters lock 30 minutes pre-game
  - Cannot exploit mid-game defensive changes
  - Focus on starting lineup defensive quality
  - Pre-game defensive strategies known and predictable

**How it scores:**

1. **Team Defense Impact:**
   ```
   Team Impact = (Team Rating - 0.5) × -2.0
   ```
   Good defense = negative score for hitters

2. **Position-Specific Impact:**
   ```
   Position Impact = (Position Quality - 0.5) × -1.5 × Position Weight
   ```
   Position weights:
   - Premium positions (SS, 2B, CF): 1.2-1.3x
   - Standard positions (3B, LF, RF): 0.7-1.0x
   - Low impact positions (1B, C, DH): 0.3-0.5x

3. **Shift Tendency Impact:**
   ```
   Shift Impact = Shift Rate × Hand Modifier
   ```
   - LHB vs shifty team: -0.8 multiplier
   - RHB vs shifty team: -0.3 multiplier
   - Switch hitters: Neutral

4. **Defensive Opportunity Adjustment:**
   - Multiplies score by expected fielding plays at position
   - SS/2B see most plays: 1.3x multiplier
   - Corner OF/DH see fewer: 0.8-0.9x multiplier

**Output Metrics:**
- **defensive_impact_score:** Final score (-2.0 to +2.0)
- **team_def_rating:** Opponent team defensive quality (0.0-1.0)
- **pos_def_quality:** Position-specific defender quality (0.0-1.0)
- **shift_tendency:** Likelihood of defensive shifts (0.0-1.0)
- **def_quality:** Categorical rating (Strong/Average/Weak)
- **position_note:** Descriptor of defender skill
- **opportunity_mult:** Position-based adjustment factor

**Real Impact:**
- Elite team defense reduces opponent BA by ~.015-.025
- Weak defensive teams increase opponent BA by ~.020-.030
- Position-specific weakness (e.g., poor SS) creates exploitable matchups
- Heavy shift usage reduces pull-side grounders effectiveness by ~25-30%

**Strategic Applications:**

**For Hitters:**
- **Target weak defenses:** More hits, fewer outs, higher scoring
- **Exploit position weaknesses:** Attack games where opponent has poor defender at key position
- **Consider shift tendencies:** LHB pull hitters hurt more by shifts
- **Prioritize up-the-middle defense:** Weak SS/2B creates more hits through infield

**For Pitchers:**
- **Elite defense helps:** Reduces BABIP, more ground ball outs
- **Poor defense hurts:** More hits on balls in play, higher pitch counts
- **Shift-friendly teams:** Better for extreme ground ball pitchers
- **Premium defensive CF:** Helps pitchers who allow fly balls

**Position-Specific Considerations:**

| Position | Defensive Impact on Hitters | Fantasy Relevance |
|----------|----------------------------|-------------------|
| **SS**   | Very High (1.3x weight)   | Most infield plays, critical range |
| **2B**   | Very High (1.3x weight)   | Many double play opportunities |
| **CF**   | High (1.2x weight)        | Most fly balls, largest territory |
| **3B**   | High (1.1x weight)        | Hot corner reaction plays |
| **1B**   | Medium (1.1x weight)      | Scooping throws, less range needed |
| **LF/RF**| Medium (0.9x weight)      | Corner outfield, fewer opportunities |
| **C**    | Low (0.8x weight)         | Framing/blocking, not fielding hits |
| **DH**   | None (0.0x weight)        | No defensive impact |

**Real-World Examples:**
- **Weak SS/2B combo:** +0.8 to +1.2 score for opposing hitters (more hits up middle)
- **Elite defensive team (Royals, Cardinals):** -1.0 to -1.5 for opponent offense
- **Heavy shift team vs LHB pull hitter:** -0.6 to -0.8 (reduced pull-side success)
- **Poor corner OF defense:** +0.5 to +0.7 for fly ball hitters
- **Elite CF + poor corner OF:** Neutral to slightly positive (mixed bag)

**Limitations:**
- Defensive metrics simulated when full data unavailable
- Mid-game defensive substitutions not captured (rosters locked)
- Does not account for park dimensions (covered in park_factors_fa)
- Shift data may be incomplete for recent rule changes
- DRS/UZR metrics not fully integrated (uses synthetic ratings)

**Future Enhancements:**
- Integration with Statcast OAA (Outs Above Average)
- DRS (Defensive Runs Saved) and UZR (Ultimate Zone Rating) data
- Shift effectiveness by batter profile
- Catcher framing impact on umpire factor
- Double play tendency by middle infield combo
- Outfield arm strength (affects extra base hits)
- Defensive positioning heat maps
- Weather impact on defensive plays (wet field, wind)

**Usage:**
```python
from src.scripts.fa.defensive_positions_fa import DefensivePositionsFactorAnalyzer

analyzer = DefensivePositionsFactorAnalyzer(data_dir="data/")
scores = analyzer.analyze(games_df, game_logs_df, roster_df)
```

**Example Output:**
```
Player: Mike Trout
Game Date: 2025-10-05
Position: CF
Opponent: Athletics (Weak defense, 0.28 rating)
Batter Hand: R
Shift Tendency: 0.42 (moderate)
Defensive Impact Score: +1.15 (FAVORABLE)
Notes: Weak team defense, average CF defender
Impact: More hits expected vs poor defensive team
```

---

🔜 **Coming Soon:**

- **Pitcher Quality:** Facing ace vs. rookie starter
- **Recent Form:** Last 7/14/30 day performance trends
- **Bullpen Usage:** Relief pitcher fatigue and availability
- **Catcher Framing:** Impact on called strikes
- **Contact Quality:** Exit velocity and barrel rates

---

## Weight Tuning & Backtesting

The Fantasy Baseball AI system includes an advanced **weight tuning system** that optimizes factor analysis weights based on historical performance data. This allows you to customize recommendations for each player on your roster.

### Overview

Each factor analysis has a **weight** (e.g., wind = 10%, matchup = 15%) that determines its influence on the final sit/start recommendation. The weight tuning system:

1. **Backtests** predictions against actual game results from 2022 onwards
2. **Optimizes** weights using differential evolution algorithm
3. **Personalizes** weights for each player on your roster
4. **Validates** using correlation, MAE, and RMSE metrics

### Default Weights

```python
DEFAULT_WEIGHTS = {
    'wind': 0.10,                    # 10%
    'matchup': 0.15,                 # 15%
    'home_away': 0.12,               # 12%
    'platoon': 0.10,                 # 10%
    'park_factors': 0.08,            # 8%
    'rest_day': 0.08,                # 8%
    'injury': 0.12,                  # 12%
    'umpire': 0.05,                  # 5%
    'temperature': 0.05,             # 5%
    'pitch_mix': 0.05,               # 5%
    'lineup_position': 0.05,         # 5%
    'time_of_day': 0.03,             # 3%
    'defensive_positions': 0.02      # 2%
}
# Total: 100%
```

### Running Backtests

**Backtest entire roster:**
```bash
python src/scripts/backtest_weights.py
```

**Backtest specific player:**
```bash
python src/scripts/backtest_weights.py --player "Shohei Ohtani"
```

**Optimize weights (uses historical data to find best weights):**
```bash
python src/scripts/backtest_weights.py --optimize
```

**Optimize and save to config:**
```bash
python src/scripts/backtest_weights.py --optimize --save
```

### How Backtesting Works

1. **Load Historical Data:** Pulls all game data from 2022 to present (3+ years)
2. **Calculate Predictions:** For each historical game, calculates composite score using current weights
3. **Compare to Actuals:** Compares predictions to actual fantasy points scored
4. **Measure Accuracy:** 
   - **Correlation:** How well predictions match actual performance (-1 to +1)
   - **MAE (Mean Absolute Error):** Average prediction error
   - **RMSE (Root Mean Square Error):** Weighted prediction error

### Weight Optimization

The optimization process uses **Differential Evolution**, a genetic algorithm that:

1. Tests thousands of weight combinations
2. Finds the combination that maximizes prediction accuracy
3. Normalizes weights to sum to 100%
4. Saves player-specific configurations

**Optimization takes 2-5 minutes per player** depending on game history.

### Managing Weights

**View global weights:**
```bash
python src/scripts/weight_config.py --show
```

**View player-specific weights:**
```bash
python src/scripts/weight_config.py --show --player "Mike Trout"
```

**List players with custom weights:**
```bash
python src/scripts/weight_config.py --list
```

**Reset player to default weights:**
```bash
python src/scripts/weight_config.py --reset --player "Mike Trout"
```

### Weight Storage

Weights are stored in JSON configuration files:

- **Global weights:** `config/factor_weights.json`
- **Player-specific weights:** `config/player_weights.json`

### Example Output

```
=======================================================================
Backtesting: Shohei Ohtani
=======================================================================
Found 143 games for Shohei Ohtani

✓ Analyzed 143 games
  Accuracy (correlation): 0.723
  MAE: 0.342
  RMSE: 0.456

=======================================================================
OPTIMIZED WEIGHTS
=======================================================================

Shohei Ohtani:
  matchup                  : 0.1842
  platoon                  : 0.1523
  wind                     : 0.1201
  home_away                : 0.1145
  injury                   : 0.0987
  park_factors             : 0.0876
  rest_day                 : 0.0765
  temperature              : 0.0543
  lineup_position          : 0.0421
  pitch_mix                : 0.0389
  umpire                   : 0.0198
  time_of_day              : 0.0087
  defensive_positions      : 0.0023
```

### When to Retune Weights

Re-run optimization when:

- **New season starts** (player tendencies change)
- **Player changes teams** (different park, lineup)
- **After 20+ games** into season (more data available)
- **Player coming off injury** (performance patterns shift)
- **New factors added** to the system

### Integration with fb_ai.py

The main system automatically loads appropriate weights:

1. Checks for player-specific weights in `config/player_weights.json`
2. Falls back to global weights in `config/factor_weights.json`
3. Uses default weights if no config exists

No manual configuration needed—just run the backtest with `--save` flag!

### Best Practices

✅ **DO:**
- Run full backtest early in season (Week 2-3)
- Optimize weights mid-season after ~40 games
- Use player-specific weights for your core roster
- Re-optimize after major roster changes

❌ **DON'T:**
- Over-optimize with limited data (need 30+ games minimum)
- Tune weights daily (weekly or bi-weekly is sufficient)
- Ignore poor accuracy scores (< 0.3 correlation means factor doesn't work for that player)
- Use another player's weights without testing

### Technical Details

**Objective Function:**
```python
def objective(weights):
    predictions = calculate_predictions(games, weights)
    actuals = get_actual_fantasy_points(games)
    return -correlation(predictions, actuals)  # Minimize negative correlation
```

**Optimization Constraints:**
- Each weight: 0.0 to 0.3 (0% to 30%)
- Weights normalized to sum to 1.0
- Differential evolution population: 10
- Max iterations: 20 (adjustable)

**Performance Metrics:**
- **Correlation > 0.5:** Good predictive power
- **Correlation > 0.7:** Excellent predictions
- **Correlation < 0.3:** Factor not useful for this player
- **MAE < 0.5:** Low average error
- **RMSE < 0.6:** Consistent predictions

---

## Development Guidelines

### Adding a New Factor

When adding a new Factor Analysis module:

1. Create new file: `src/scripts/fa/new_factor_fa.py`
2. Implement analysis function that returns scores (-2.0 to +2.0)
3. Add to `src/fb_ai.py` with appropriate weight
4. **Update this README (`docs/FACTOR_ANALYSIS_FA.md`)** with complete factor description including:
   - Weight percentage
   - What it analyzes
   - Key concepts
   - How it scores
   - Real impact/examples
   - Output metrics (if applicable)
   - Strategic applications (if applicable)
   - Limitations (if applicable)
   - Usage example
5. Test with sample roster data

**Important:** Do NOT create individual README files for new factors. All documentation should be added directly to this consolidated document.

### Module Structure

```python
def analyze_new_factor(roster_df, data_source):
    """
    Analyze [factor name] for players on roster.
    
    Args:
        roster_df: DataFrame with player roster
        data_source: Required data for analysis
        
    Returns:
        dict: {player_id: score} where score is -2.0 to +2.0
    """
    scores = {}
    for player in roster_df:
        # Analysis logic here
        score = calculate_score(player, data_source)
        scores[player.id] = score
    return scores
```

---

## Questions?

Each factor analysis module is designed to be independent and modular. Review individual module code in `src/scripts/fa/` for implementation details or extend with custom analysis logic.

All Factor Analysis documentation updates should be made to this file: `docs/FACTOR_ANALYSIS_FA.md`
