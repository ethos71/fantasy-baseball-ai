#!/usr/bin/env python3
"""
Train Hybrid Ensemble Model using September 2024 data

Uses actual game logs to create fantasy points and trains the ensemble.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
import numpy as np
from datetime import datetime
from scripts.hybrid_ensemble import HybridEnsemblePredictor

def calculate_fantasy_points(game_logs_df):
    """
    Calculate fantasy points from game logs
    Standard scoring: H=1, 2B=2, 3B=3, HR=4, R=1, RBI=1, SB=2, BB=1
    """
    df = game_logs_df.copy()
    
    # Calculate doubles, triples (if not already present)
    if 'doubles' not in df.columns and '2B' in df.columns:
        df['doubles'] = df['2B']
    if 'triples' not in df.columns and '3B' in df.columns:
        df['triples'] = df['3B']
    if 'HR' in df.columns:
        df['home_runs'] = df['HR']
    
    # Standard fantasy scoring
    points = 0
    if 'H' in df.columns:
        points += df['H'] * 1  # Singles/Hits
    if 'doubles' in df.columns:
        points += df['doubles'] * 1  # Extra point for double
    if 'triples' in df.columns:
        points += df['triples'] * 2  # Extra points for triple
    if 'home_runs' in df.columns:
        points += df['home_runs'] * 3  # Extra points for HR
    if 'R' in df.columns:
        points += df['R'] * 1  # Runs
    if 'RBI' in df.columns:
        points += df['RBI'] * 1  # RBIs
    if 'SB' in df.columns:
        points += df['SB'] * 2  # Stolen bases
    if 'BB' in df.columns:
        points += df['BB'] * 1  # Walks
    
    df['fantasy_points'] = points
    return df

def train_ensemble_model():
    """Train ensemble on September 2024 data"""
    
    print("\n" + "="*80)
    print("TRAINING HYBRID ENSEMBLE - SEPTEMBER 2024 DATA")
    print("="*80 + "\n")
    
    data_dir = Path('data')
    
    # Load September 2024 game logs
    print("Loading game logs...")
    game_logs = pd.read_csv(data_dir / 'mlb_game_logs_2024.csv')
    game_logs['game_date'] = pd.to_datetime(game_logs['game_date'])
    
    # Filter to September
    sept_logs = game_logs[game_logs['game_date'].dt.month == 9].copy()
    print(f"✓ Loaded {len(sept_logs):,} games from September 2024\n")
    
    # Calculate fantasy points
    print("Calculating fantasy points...")
    sept_logs = calculate_fantasy_points(sept_logs)
    
    # Aggregate by player (average per game)
    player_stats = sept_logs.groupby('player_name').agg({
        'fantasy_points': 'mean',
        'game_date': 'count'
    }).reset_index()
    player_stats.columns = ['player_name', 'fantasy_points', 'games_played']
    
    # Filter players with at least 5 games
    player_stats = player_stats[player_stats['games_played'] >= 5]
    print(f"✓ Calculated fantasy points for {len(player_stats)} players (5+ games)\n")
    
    # Load training data
    print("Loading factor analysis scores...")
    training_file = data_dir / 'ensemble_training' / 'training_data.csv'
    
    if not training_file.exists():
        print(f"❌ Training file not found: {training_file}")
        print("   Run: python src/scripts/ensemble/collect_training_data.py")
        return None
    
    training_data = pd.read_csv(training_file)
    print(f"✓ Loaded {len(training_data)} players with factor scores\n")
    
    # Merge fantasy points with factor scores
    print("Merging fantasy points with factor scores...")
    merged = training_data.merge(
        player_stats[['player_name', 'fantasy_points']],
        on='player_name',
        how='inner',
        suffixes=('_old', '')
    )
    
    # Remove old fantasy_points column if it exists
    if 'fantasy_points_old' in merged.columns:
        merged = merged.drop('fantasy_points_old', axis=1)
    
    print(f"✓ Merged dataset: {len(merged)} players\n")
    
    if len(merged) < 50:
        print(f"⚠️  Warning: Only {len(merged)} players with both factors and fantasy points")
        print("   Recommend at least 50-100 players for training")
        print("   Continuing anyway...\n")
    
    # Prepare features
    print("Preparing features...")
    predictor = HybridEnsemblePredictor(data_dir)
    
    X, feature_names = predictor.prepare_features(merged)
    y = merged['fantasy_points'].values
    
    print(f"✓ Features: {len(feature_names)}")
    print(f"✓ Samples: {len(X)}\n")
    
    # Split train/validation
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"Train set: {len(X_train)} samples")
    print(f"Val set: {len(X_val)} samples\n")
    
    # Train LightGBM
    print("="*80)
    print("Training LightGBM...")
    print("="*80)
    predictor.train_lightgbm(X_train, y_train, X_val, y_val)
    print("✓ LightGBM trained\n")
    
    # Train CatBoost
    print("="*80)
    print("Training CatBoost...")
    print("="*80)
    predictor.train_catboost(X_train, y_train, X_val, y_val)
    print("✓ CatBoost trained\n")
    
    # Evaluate
    print("="*80)
    print("EVALUATING ENSEMBLE")
    print("="*80 + "\n")
    
    # Get predictions
    val_data = merged.iloc[X_val.index]
    predictions = predictor.predict_ensemble(val_data)
    
    # Calculate metrics
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    
    y_pred_ws = predictions['pred_weighted_sum'].values
    y_pred_lgb = predictions['pred_lightgbm'].values
    y_pred_cat = predictions['pred_catboost'].values
    y_pred_ens = predictions['pred_ensemble'].values
    y_true = val_data['fantasy_points'].values
    
    results = {
        'Weighted Sum': y_pred_ws,
        'LightGBM': y_pred_lgb,
        'CatBoost': y_pred_cat,
        'Ensemble': y_pred_ens
    }
    
    print(f"{'Model':<15} {'RMSE':<10} {'MAE':<10} {'R²':<10}")
    print("-" * 45)
    
    for name, preds in results.items():
        rmse = np.sqrt(mean_squared_error(y_true, preds))
        mae = mean_absolute_error(y_true, preds)
        r2 = r2_score(y_true, preds)
        print(f"{name:<15} {rmse:<10.2f} {mae:<10.2f} {r2:<10.3f}")
    
    # Save models
    print("\n" + "="*80)
    print("SAVING MODELS")
    print("="*80 + "\n")
    
    models_dir = Path('models/ensemble')
    predictor.save_models(models_dir)
    
    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80 + "\n")
    
    print("Models saved to: models/ensemble/")
    print("  • lightgbm_model.txt")
    print("  • catboost_model.cbm")
    print("  • ensemble_weights.pkl")
    print("  • factor_weights.pkl")
    print()
    print("To use in production:")
    print("  from scripts.hybrid_ensemble import HybridEnsemblePredictor")
    print("  predictor = HybridEnsemblePredictor(data_dir)")
    print("  predictor.load_models('models/ensemble')")
    print("  predictions = predictor.predict_ensemble(player_data)")
    print()
    
    return predictor

if __name__ == "__main__":
    train_ensemble_model()
