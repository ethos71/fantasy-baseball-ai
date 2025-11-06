#!/usr/bin/env python3
"""
Quick Example: Weight Tuning System

This script demonstrates how to use the weight tuning system for a single player.
Run this to see how backtesting and optimization work.
"""

from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.weight_config import WeightConfig
from scripts.backtest_weights import WeightTuner


def main():
    """Run a simple weight tuning example"""
    
    print("\n" + "="*80)
    print("FANTASY BASEBALL AI - WEIGHT TUNING EXAMPLE".center(80))
    print("="*80)
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    
    print("\n📊 Step 1: Loading Default Weights")
    print("-" * 80)
    
    # Load configuration
    config = WeightConfig(project_root)
    config.display_weights()
    
    print("\n\n📈 Step 2: Example - Backtesting a Player")
    print("-" * 80)
    print("""
The backtest process:
1. Loads all historical games for the player (2022-present)
2. For each game, calculates factor scores using current weights
3. Compares predictions to actual fantasy points scored
4. Calculates accuracy metrics (correlation, MAE, RMSE)

To run backtest for your roster:
    python src/scripts/backtest_weights.py

To optimize weights:
    python src/scripts/backtest_weights.py --optimize --save
    """)
    
    print("\n\n🎯 Step 3: Example - Player-Specific Weights")
    print("-" * 80)
    print("""
After optimization, you might get player-specific weights like:

Shohei Ohtani (Power Hitter + Pitcher):
    matchup:              18.4%  (↑ from 15%) - History matters more
    wind:                 12.0%  (↑ from 10%) - Power hitter benefits from wind
    platoon:              15.2%  (↑ from 10%) - Strong platoon advantage
    home_away:            11.5%  (↓ from 12%) - Performs well anywhere
    injury:                9.9%  (↓ from 12%) - Rarely injured
    park_factors:          8.8%  (~ same)
    rest_day:              7.7%  (↓ from 8%)  - Durable player
    temperature:           5.4%  (~ same)
    lineup_position:       4.2%  (↓ from 5%)  - Always bats high
    pitch_mix:             3.9%  (↓ from 5%)  - Handles all pitch types
    umpire:                2.0%  (↓ from 5%)  - Less sensitive
    time_of_day:           0.9%  (↓ from 3%)  - Performs anytime
    defensive_positions:   0.1%  (↓ from 2%)  - Minimal impact

These optimized weights improve prediction accuracy from 0.52 to 0.73!
    """)
    
    print("\n\n⚙️  Step 4: Using Custom Weights")
    print("-" * 80)
    print("""
Once weights are optimized and saved, the system automatically uses them:

1. Run analysis as usual:
   python src/fb_ai.py

2. The system checks for player-specific weights in:
   config/player_weights.json

3. Falls back to global weights if not found:
   config/factor_weights.json

4. Each player gets optimal recommendations based on their unique profile!
    """)
    
    print("\n\n📋 Step 5: Managing Weights")
    print("-" * 80)
    print("""
View weights:
    python src/scripts/weight_config.py --show
    python src/scripts/weight_config.py --show --player "Ohtani"

List customized players:
    python src/scripts/weight_config.py --list

Reset to defaults:
    python src/scripts/weight_config.py --reset --player "Ohtani"
    """)
    
    print("\n" + "="*80)
    print("NEXT STEPS".center(80))
    print("="*80)
    print("""
1. Ensure you have historical data:
   python src/fb_ai.py --refresh

2. Run backtest on your roster:
   python src/scripts/backtest_weights.py

3. If accuracy looks good, optimize weights:
   python src/scripts/backtest_weights.py --optimize --save

4. Use optimized weights in daily analysis:
   python src/fb_ai.py

For more details, see: docs/FACTOR_ANALYSIS_FA.md#weight-tuning--backtesting
    """)
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
