# Fantasy Baseball AI

An advanced machine learning system for fantasy baseball optimization that combines MLB statistics, real-time weather data, and Yahoo Fantasy Sports integration to provide actionable insights for your fantasy baseball roster.

## Project Overview

This project uses MLB's official Stats API, machine learning models (XGBoost), weather prediction, and multi-factor analysis to help you make informed decisions about your fantasy baseball lineup. The system analyzes seven key factors to determine optimal start/sit decisions:

1. **Wind Analysis** - How weather conditions affect pitcher/hitter performance
2. **Historical Matchup Performance** - Player vs. opponent track record
3. **Home/Away Venue Splits** - Player performance by location
4. **Rest Day Impacts** - How days of rest affect player performance
5. **Injury/Recovery Tracking** - Post-injury performance monitoring
6. **Umpire Strike Zone Analysis** - How home plate umpire affects pitcher/hitter success
7. **Platoon Advantages** - Left-handed vs. right-handed matchup optimization

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
- **Run 7-Factor Analysis** (wind + matchups + home/away + rest days + injury + umpire + platoon)
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
- **Run 7-Factor Analysis** on your current roster
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

## 🎯 Seven-Factor Analysis System

The heart of this project is a sophisticated multi-factor analysis that evaluates every player on your roster for optimal start/sit decisions. Each factor is weighted and combined to produce actionable recommendations.

### Factor 1: Wind Analysis (15% weight)

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

### Factor 2: Historical Matchup Performance (20% weight)

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

### Factor 3: Home/Away Venue Splits (15% weight)

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

### Factor 4: Rest Day Impacts (13% weight)

**What it does:** Analyzes how days of rest between games affect player performance.

**Key Concepts:**
- **Rested (2+ days off):** Some players benefit from rest
  - Fresh legs, recovered from minor injuries
  - Better focus and energy levels
  - May lose timing/rhythm with too much rest
  
- **Back-to-Back Games (0-1 days):** Some players thrive on rhythm
  - Stay in groove, maintain timing
  - May experience fatigue over time
  - Mental sharpness from continuous play

**How it scores:**
- Calculates batting average when rested (2+ days) vs back-to-back (0-1 days)
- Compares current game's rest status to player's historical splits
- If playing with preferred rest pattern = positive score
- If playing against preferred pattern = negative score

**Example:**
```
🛌 Player: Rest-Dependent Slugger
Rested BA: .320 (20 games) | Back-to-Back BA: .245 (35 games) → 75-point drop!
Today's Rest Status: 3 days since last game (RESTED)
Analysis: Performs significantly better with rest
Result: +1.4 score → STRONG START (plays to strength)

⚡ Player: Rhythm Hitter
Rested BA: .260 (15 games) | Back-to-Back BA: .305 (40 games) → 45-point boost!
Today's Rest Status: 0 days since last game (BACK-TO-BACK)
Analysis: Thrives on continuous play, stays in rhythm
Result: +1.1 score → FAVORABLE START (optimal pattern)
```

**Why it matters:** 
- Players respond differently to rest patterns
- Some veterans need rest to stay fresh
- Younger players often prefer rhythm of daily play
- Can be 30-50 BA point difference for some players
- Especially important in fantasy playoffs when every decision counts

**Real Impact:** Studies show fatigue effects vary widely:
- Power hitters often lose 10-15% HR distance when fatigued
- Contact hitters may maintain BA but lose power
- Speed players experience reduced stolen base success
- Catchers particularly affected by back-to-back games

---

### Factor 5: Injury/Recovery Tracking (13% weight)

**What it does:** Monitors player performance immediately following injury recovery and identifies players still working back to full strength.

**Key Concepts:**
- **Injury Detection:** Identifies gaps of 14+ days in game logs (likely IL stint)
  - Common injuries: hamstring, oblique, finger, concussion
  - IL stints typically 10-60 days depending on severity
  
- **Recovery Period (30 days post-return):** Critical monitoring window
  - Players may be tentative, rusty, or not at full strength
  - Performance often dips initially before returning to normal
  - Some players return STRONGER (extra rest, focused rehab)
  
- **Post-Injury Performance:** Tracks actual results vs. pre-injury baseline
  - Compares last 10 games before injury to games after return
  - Red flags: Significant BA drop, reduced power, loss of speed

**How it scores:**
- Identifies most recent injury gap (14+ consecutive days missed)
- Calculates pre-injury baseline (.300 BA in 10 games before IL)
- Measures post-injury performance (.245 BA in 5 games since return)
- Applies recency penalty (recently returned = more uncertainty)
- Adjusts for sample size confidence
- Generates score: -2.0 (struggling post-injury) to +2.0 (thriving post-injury)

**Special Labels:**
- **"STRUGGLING POST-INJURY"** (score ≤ -1.0): Significant performance decline
- **"RECOVERING"** (score -0.3 to -1.0): Minor decline, still finding form
- **"NEUTRAL"** (score -0.3 to +0.3): Performing at baseline
- **"STRONG POST-INJURY"** (score ≥ +1.0): Performing better than before injury
- **"HEALTHY"**: No recent injury gaps detected (score = 0.0)

**Example 1: Struggling Return**
```
🩹 Player: Star Slugger (HOU)
Injury: Hamstring strain (missed 21 days)
Games Since Return: 6 games
Pre-Injury BA: .315 (last 10 games before IL)
Post-Injury BA: .182 (6 games since return)
Analysis: Significant 133-point drop, may still be hobbled
Days Since Return: 8 days (very recent)
Result: -1.6 score → BENCH UNTIL IMPROVES
Reason: Not back to full health, avoid starting
```

**Example 2: Strong Recovery**
```
💪 Player: Veteran Hitter (LAD)
Injury: Oblique strain (missed 18 days)
Games Since Return: 12 games
Pre-Injury BA: .285 (last 10 games before IL)
Post-Injury BA: .340 (12 games since return)
Analysis: Actually improved (+55 points!), rest helped
Days Since Return: 21 days (gaining confidence)
Result: +1.4 score → STRONG START
Reason: Fully recovered and performing better than before
```

**Example 3: Recovering Progress**
```
🔄 Player: Young Outfielder (ATL)
Injury: Wrist contusion (missed 15 days)
Games Since Return: 8 games
Pre-Injury BA: .295 (last 10 games before IL)
Post-Injury BA: .265 (8 games since return)
Analysis: Slight 30-point dip, trending back to normal
Days Since Return: 12 days (still adjusting)
Result: -0.5 score → NEUTRAL/MONITOR
Reason: Give it a few more games, should bounce back
```

**Why it matters:**
- **Avoid Traps:** Don't start players who aren't fully healed
  - They may re-injure or play cautiously
  - Performance typically 20-50 BA points below normal
  
- **Find Values:** Identify players who return STRONGER
  - Extra rest can help veterans recover from nagging issues
  - Some players use IL time for swing adjustments
  
- **Monitor Trends:** Track game-by-game progress
  - Is player improving or still struggling?
  - When to confidently start them again?

**Real Impact:** Post-injury statistics:
- 60% of players underperform first 5 games back (avg -35 BA points)
- 25% match pre-injury performance immediately
- 15% actually improve (rest/recovery benefit)
- By game 15 post-return, 80% are back to baseline
- Power stats (HR, SLG) recover slower than BA

**Critical for Fantasy:**
- Starting a player in their first week back is risky (-1.0 to -1.5 score typical)
- Wait 10-15 games for confidence unless they show immediate success
- Veterans (age 32+) often need longer recovery periods
- Speed/hamstring injuries particularly problematic for performance

---

### Factor 6: Umpire Strike Zone Analysis (12% weight)

**What it does:** Analyzes how the home plate umpire's strike zone tendencies affect pitcher and hitter performance for the game.

**Key Concepts:**
- **Strike Zone Size:** Each umpire has unique zone characteristics
  - **Large Zone:** More pitches called strikes → Favors pitchers
  - **Small Zone:** Fewer strikes, more walks → Favors hitters
  - **Inconsistent Zone:** Unpredictable calls → Disadvantages both pitchers and hitters
  - **Medium Zone:** Balanced, follows rulebook → Neutral impact

- **Umpire Consistency:** Accuracy rate of strike/ball calls
  - **High Consistency (90%+):** Predictable, fair for both sides
  - **Medium Consistency (80-89%):** Some variability
  - **Low Consistency (<80%):** Frustrating for players, unpredictable

- **Pitcher/Hitter Bias:** Some umpires statistically favor one side
  - **Pro-Pitcher Umpire:** Expands zone on edges, gives benefit of doubt
  - **Pro-Hitter Umpire:** Stricter zone enforcement, favors batters
  - **Neutral Umpire:** No statistical bias either direction

**How it scores:**
- Identifies home plate umpire assigned to the game
- Analyzes umpire's historical zone size, consistency, and bias
- Calculates advantage based on player type (pitcher vs hitter)
- Large zone + pitcher = positive score (more strikes)
- Large zone + hitter = negative score (harder to work counts)
- Small zone + hitter = positive score (more walks/better pitches)
- Small zone + pitcher = negative score (harder to get strikes)
- Consistency bonus applied universally (predictability helps all)
- Generates score: -1.5 (very unfavorable umpire) to +1.5 (very favorable umpire)

**Example 1: Pitcher-Friendly Umpire**
```
⚾ Umpire: Joe West
Strike Zone: LARGE (2.5 inches wider than average)
Consistency: 85% (above average)
Bias: Pro-Pitcher (+0.4 favor rating)
═══════════════════════════════════════════════

Player: Gerrit Cole (NYY) - Pitcher
Analysis: Large zone + high consistency = Perfect for Cole
          Can work edges, get called strikes on borderline pitches
          High consistency means he can trust his location
Result: +1.3 score → VERY FAVORABLE START
Reason: Command pitcher benefits from expanded, consistent zone

Player: Aaron Judge (NYY) - Hitter  
Analysis: Large zone = Fewer walks, must protect bigger area
          More called strikes on pitches off the plate
          Harder to work deep counts
Result: -0.9 score → SLIGHT DISADVANTAGE
Reason: Power hitter faces tougher zone, less favorable counts
```

**Example 2: Hitter-Friendly Umpire**
```
⚾ Umpire: Lance Barksdale
Strike Zone: SMALL (1.8 inches tighter than average)
Consistency: 82% (solid)
Bias: Pro-Hitter (-0.2 favor rating)
═══════════════════════════════════════════════

Player: Juan Soto (SD) - Hitter
Analysis: Small zone + pro-hitter bias = Excellent for plate discipline
          More walks, pitchers forced to come into zone
          Better pitches to hit, improved count leverage
Result: +1.1 score → FAVORABLE START
Reason: Patient hitter thrives with small zone and walks

Player: Shane Bieber (CLE) - Pitcher
Analysis: Small zone = Must be more precise, less margin for error
          Borderline pitches won't be called strikes
          May struggle to put hitters away
Result: -0.8 score → UNFAVORABLE
Reason: Command pitcher loses edge with tight zone
```

**Example 3: Inconsistent Umpire**
```
⚾ Umpire: CB Bucknor
Strike Zone: INCONSISTENT (varies throughout game)
Consistency: 70% (well below MLB average)
Bias: NEUTRAL (0.0)
═══════════════════════════════════════════════

Player: Max Scherzer (TEX) - Pitcher
Analysis: Unpredictable zone = Can't trust location/calls
          Frustrating for precise pitchers
          May get squeezed or get generous calls randomly
Result: -0.5 score → NEUTRAL/NEGATIVE
Reason: Inconsistency disrupts command pitchers' game plans

Player: Mookie Betts (LAD) - Hitter
Analysis: Unpredictable zone = Hard to lay off close pitches
          Can't anticipate strike calls
          May chase or take strikes without pattern
Result: -0.4 score → SLIGHT DISADVANTAGE  
Reason: Patient hitters struggle with unpredictable zones
```

**Why it matters:**
- **Measurable Impact:** Studies show umpire zones vary by 3-5 inches
  - Wide zone: ~15% more called strikes
  - Tight zone: ~20% more walks issued
  
- **Game Flow:** Umpire affects entire game rhythm
  - Large zone = Faster games, fewer walks, more swing decisions
  - Small zone = Longer at-bats, more walks, pitcher fatigue
  
- **Player-Specific:** Some players particularly affected
  - **Command Pitchers:** (Maddux, Glavine style) - Need consistent edge calls
  - **Power Pitchers:** (Chapman, Hader style) - Less affected by zone size
  - **Patient Hitters:** (Soto, Betts) - Thrive with small zones
  - **Aggressive Hitters:** (Baez, Castellanos) - Less impacted by zone

**Real Impact Statistics:**
- Elite umpires (95%+ accuracy): Minimal bias, ~neutral effect
- Average umpires (82-88% accuracy): 0.3-0.5 advantage swings
- Poor umpires (<80% accuracy): 0.5-1.0 advantage swings
- Umpire-specific data shows 30+ run differential per season
- Fantasy relevance: Can be 1-2 points difference in weekly matchups

**Strategic Use:**
- **For Pitchers:** Start pitchers facing hitter-friendly umps less confidently
- **For Hitters:** Target games with small-zone umpires for OBP leagues
- **Ace Pitchers:** Less affected - elite stuff overcomes zone size
- **Platoon Decisions:** Use umpire as tiebreaker between similar players

---

### Factor 7: Platoon Advantages (12% weight)

**What it does:** Analyzes left-handed vs. right-handed pitcher/hitter matchups to identify favorable and unfavorable platoon situations.

**Key Concepts:**
- **Favorable Platoon Matchups:** Opposite-handed matchups
  - **LHB vs RHP (Left-handed Batter vs Right-handed Pitcher):** FAVORABLE
    - Batter sees ball better from opposite side
    - Breaking balls move toward hitter (easier to track)
    - Historical MLB avg: .260 BA for same-side, .275 BA for opposite-side
  
  - **RHB vs LHP (Right-handed Batter vs Left-handed Pitcher):** FAVORABLE
    - Same advantages as LHB vs RHP
    - Most batters face fewer LHP (only 25% of MLB pitchers are lefties)
    - Less familiarity with LHP delivery can actually help RHB

- **Unfavorable Platoon Matchups:** Same-handed matchups
  - **LHB vs LHP:** UNFAVORABLE
    - Ball harder to pick up from same-side delivery
    - Breaking balls move away from hitter (slider/cutter fade away)
    - Historical drop: -30 to -50 BA points typical
  
  - **RHB vs RHP:** SLIGHTLY UNFAVORABLE
    - Most common matchup in baseball (65% RHB × 75% RHP = ~49% of all ABs)
    - Moderate disadvantage but players are more experienced
    - Historical drop: -15 to -25 BA points vs opposite-side

- **Switch Hitters:** NEUTRAL
  - Can bat from favorable side (LH vs RHP, RH vs LHP)
  - Theoretically removes platoon disadvantage
  - In practice, most switch hitters have a stronger side

**How it scores:**
- Determines hitter's batting handedness (L/R/S)
- Identifies opposing pitcher's throwing hand (L/R)
- Calculates expected platoon advantage/disadvantage
- Analyzes historical splits (vs LHP vs vs RHP) if available
- Weighs expected platoon (30%) vs actual player splits (70%)
- Applies confidence weighting based on sample size
- Generates score: -1.5 (very unfavorable platoon) to +1.5 (very favorable platoon)

**Example 1: Strong Platoon Advantage**
```
👊 Player: Freddie Freeman (LAD) - Left-handed Batter
Opposing Pitcher: Right-handed
Matchup Type: LHB vs RHP → FAVORABLE PLATOON
═══════════════════════════════════════════════

Historical Splits (2024):
  vs RHP: .310 BA, 22 HR in 95 games
  vs LHP: .245 BA, 6 HR in 25 games
  Split Difference: +65 BA points vs RHP!

Analysis: Massive platoon advantage confirmed by splits
          Should absolutely start vs RHP
          Struggles significantly vs LHP

Result: +1.4 score → STRONG PLATOON ADVANTAGE
Reason: Perfect matchup, elite splits, high confidence
```

**Example 2: Platoon Disadvantage**
```
⚠️ Player: Max Muncy (LAD) - Left-handed Batter  
Opposing Pitcher: Left-handed
Matchup Type: LHB vs LHP → UNFAVORABLE PLATOON
═══════════════════════════════════════════════

Historical Splits (2024):
  vs RHP: .275 BA, 28 HR in 110 games
  vs LHP: .195 BA, 7 HR in 35 games
  Split Difference: -80 BA points vs LHP!

Analysis: Extreme platoon disadvantage
          Team may even bench him vs LHP
          Significant fantasy liability

Result: -1.3 score → STRONG PLATOON DISADVANTAGE
Reason: Terrible matchup, confirmed by severe splits
```

**Example 3: Switch Hitter (Neutral)**
```
↔️ Player: Jorge Polanco (SEA) - Switch Hitter
Opposing Pitcher: Right-handed
Matchup Type: SWITCH vs RHP → NEUTRAL (will bat LH)
═══════════════════════════════════════════════

Historical Splits (2024):
  Batting LH (vs RHP): .285 BA, 15 HR in 80 games
  Batting RH (vs LHP): .270 BA, 8 HR in 45 games
  Switch Advantage: Always has favorable platoon

Analysis: Switch hitting eliminates platoon penalty
          Can bat from favorable side vs any pitcher
          Provides lineup flexibility

Result: 0.0 score → NEUTRAL PLATOON
Reason: Switch hitters don't get platoon penalty or bonus
```

**Example 4: RHB vs RHP (Slight Disadvantage)**
```
⚾ Player: Aaron Judge (NYY) - Right-handed Batter
Opposing Pitcher: Right-handed
Matchup Type: RHB vs RHP → SLIGHTLY UNFAVORABLE
═══════════════════════════════════════════════

Historical Splits (2024):
  vs RHP: .295 BA, 38 HR in 115 games
  vs LHP: .320 BA, 24 HR in 40 games
  Split Difference: +25 BA points vs LHP

Analysis: Elite hitter performs well vs both
          Slight preference for LHP but still dominant vs RHP
          Power compensates for platoon disadvantage

Result: -0.5 score → SLIGHT PLATOON DISADVANTAGE
Reason: Same-side matchup but elite talent overcomes it
```

**Why it matters:**
- **Lineup Construction:** Teams platoon players based on handedness
  - Lefty-heavy lineup vs RHP starter
  - Righty-heavy lineup vs LHP starter
  - Some players don't start vs same-handed pitchers
  
- **Performance Swings:** Can be 30-80 BA points difference
  - Moderate disadvantage: -30 BA points
  - Severe disadvantage: -50 to -80 BA points (bench-worthy)
  - Strong advantage: +30 to +50 BA points (must-start)
  
- **Fantasy Strategy:**
  - **Check Starting Pitchers:** Know opposing pitcher's handedness
  - **Platoon Players:** Some only face favorable matchups
  - **Daily Lineup Decisions:** Start opposite-handed matchups when possible
  - **DFS/Season-Long:** Target favorable platoons for upside

**Real Impact Statistics:**
- MLB-wide: Opposite-handed matchups yield ~15-20 points higher BA
- Extreme platoon hitters: 60-100 point BA splits
- Power numbers even more pronounced (30-50% more HR vs favorable side)
- Switch hitters: Typically .260 BA both sides (remove 15-point penalty)
- Fantasy relevance: 2-5 points per week in categorical leagues

**Strategic Use:**
- **Bench extreme platoon players** vs unfavorable matchups
  - Example: LHB hitting .180 vs LHP → definitely bench
- **Target favorable platoons** for DFS tournaments
  - Stack LH hitters vs weak RHP = high upside
- **Stream pitchers** with favorable platoon vs opponent lineup
  - RHP vs lefty-heavy lineup can struggle
- **Tiebreakers:** Use platoon to decide between two similar players

**Player Types Most Affected:**
1. **Pure Pull Hitters:** Struggle with same-side breaking balls
2. **High-K Hitters:** Can't adjust to different arm angles
3. **Veterans:** Splits often worsen with age
4. **Specialty Relievers:** LOOGY (Lefty-One-Out-Guy) exists for reason

**Player Types Least Affected:**
1. **Elite Hitters:** (Trout, Judge, Soto) - Overcome platoon splits
2. **Switch Hitters:** (Lindor, Polanco) - Always have advantage
3. **Contact Hitters:** Adjust better than power hitters
4. **Young Players:** Still developing splits, less pronounced

---

### Combined Scoring Formula

```python
FINAL_SCORE = (
    matchup_score    × 0.20   +  # Historical performance vs opponent
    venue_score      × 0.15   +  # Home/away splits  
    wind_score       × 0.15   +  # Weather conditions
    rest_score       × 0.13   +  # Rest day impacts
    injury_score     × 0.13   +  # Injury/recovery status
    umpire_score     × 0.12   +  # Umpire strike zone tendencies
    platoon_score    × 0.12      # Platoon advantages (L/R matchups)
)
```

**Why these weights?**
- **Matchup (20%):** Most predictive - direct head-to-head history
- **Venue (15%):** Very significant - proven statistical impact
- **Wind (15%):** Important but variable - weather changes daily
- **Rest Days (13%):** Player-dependent - some affected more than others
- **Injury (13%):** Critical safety factor - avoid players not at full strength
- **Umpire (12%):** Measurable edge - consistent but smaller impact
- **Platoon (12%):** Fundamental baseball advantage - affects all hitters

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

FACTOR 4: REST DAY IMPACTS
Last Game: 2 days ago (RESTED)
Rested BA: .315 (28 games) | Back-to-Back BA: .290 (85 games)
Analysis: Slightly better when rested (+25 points)
Rest Score: +0.6

FACTOR 5: INJURY/RECOVERY
Recent Injury: None detected (last 60 days)
Status: HEALTHY - No performance concerns
Injury Score: 0.0

FACTOR 6: UMPIRE STRIKE ZONE
Umpire: Ron Kulpa
Strike Zone: MEDIUM (balanced)
Consistency: 90% (excellent)
Effect on Judge (power hitter): SLIGHT ADVANTAGE
Umpire Score: +0.3
Analysis: Consistent zone helps hitters read pitches

═══════════════════════════════════════════════
COMBINED SCORE: +1.1 (VERY FAVORABLE)

Calculation:
(1.6 × 0.22) + (0.9 × 0.18) + (1.8 × 0.18) + (0.6 × 0.15) + (0.0 × 0.15) + (0.3 × 0.12)
= 0.352 + 0.162 + 0.324 + 0.090 + 0.0 + 0.036
= +0.964 → Rounded to +1.1

RECOMMENDATION: 🌟 START WITH HIGH CONFIDENCE
- Strong tailwind will carry fly balls
- Excellent history vs Red Sox pitching
- Better hitter on the road
- Fresh after 2-day rest
- No injury concerns
- Consistent umpire with slight hitter advantage
- FIVE OF SIX FACTORS ALIGN = OPTIMAL PLAY
```

---

### 🔜 Future Analysis Factors Coming Soon

The system is designed to incorporate additional factors:

- **Pitcher Quality:** Facing ace vs. rookie starter
- **Recent Form:** Last 7/14/30 day performance trends
- **Time of Day:** Day/night game splits
- **Temperature:** Extreme heat/cold effects
- **Park Factors:** Ballpark dimensions and hitting environment
- **Platoon Splits:** L/R matchup advantages
- **Lineup Position:** Batting order impact on opportunities

Each new factor will be weighted and integrated into the combined scoring system.

---

### Output Files

**weather_advantage_analysis_YYYYMMDD.csv**
- Wind analysis only
- Per-player wind effects
- Stadium conditions

**matchup_advantage_analysis_YYYYMMDD.csv** ⭐ PRIMARY OUTPUT
- **ALL SIX FACTORS** combined
- Final scores and recommendations
- Detailed breakdowns per player
- Rest day, injury, and umpire analysis included
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

### Four Analysis Factors

| Factor | Weight | What It Measures | Key Insight |
|--------|--------|------------------|-------------|
| **🌪️ Wind** | 25% | Wind speed/direction at stadium | Tailwind = more HRs, Headwind = fewer HRs |
| **📊 Matchup** | 30% | Historical performance vs opponent | Past success predicts future performance |
| **🏠 Venue** | 25% | Home vs. away performance splits | Some players excel at home, others on road |
| **😴 Rest Days** | 20% | Rested vs back-to-back performance | Some need rest, others thrive on rhythm |

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
- Day/night game splits
- Temperature effects
- Park factors
- Platoon advantages

---

## License

This project uses publicly available MLB data through their official Stats API.
