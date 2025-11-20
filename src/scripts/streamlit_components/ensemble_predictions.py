"""
Ensemble Predictions Component for Streamlit Dashboard

Adds ensemble model predictions alongside weighted sum predictions
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, 'src')

def load_ensemble_predictions(player_data):
    """
    Generate ensemble predictions for players
    
    Args:
        player_data: DataFrame with factor scores
        
    Returns:
        DataFrame with ensemble predictions added
    """
    try:
        from scripts.hybrid_ensemble import HybridEnsemblePredictor
        
        # Initialize predictor
        predictor = HybridEnsemblePredictor(Path('data'))
        
        # Load trained models
        models_dir = Path('models/ensemble')
        if not models_dir.exists():
            st.warning("⚠️ Ensemble models not found. Using weighted sum only.")
            return player_data
        
        predictor.load_models(models_dir)
        
        # Map column names from sitstart format to training format
        column_mapping = {
            'defense_score': 'defensive_positions_score',
            'humidity_score': 'humidity_and_elevation_score',
            'momentum_score': 'team_momentum_score',
            'monthly_score': 'monthly_splits_score',
            'park_score': 'park_factors_score',
            'rest_score': 'rest_day_score',
            'statcast_score': 'statcast_metrics_score',
            'vegas_score': 'vegas_odds_score',
        }
        
        # Create a copy for prediction
        pred_data = player_data.copy()
        
        # Rename columns to match training data
        for old_name, new_name in column_mapping.items():
            if old_name in pred_data.columns:
                pred_data[new_name] = pred_data[old_name]
        
        # Add missing columns with neutral values if needed
        required_cols = [
            'bullpen_fatigue_score', 'defensive_positions_score', 
            'lineup_position_score', 'time_of_day_score'
        ]
        for col in required_cols:
            if col not in pred_data.columns:
                pred_data[col] = 0.0  # Neutral score
        
        # Generate predictions
        predictions = predictor.predict_ensemble(pred_data)
        
        # Merge predictions with original data
        if 'player_name' in player_data.columns:
            result = player_data.merge(
                predictions[['player_name', 'pred_weighted_sum', 'pred_lightgbm', 
                            'pred_catboost', 'pred_ensemble', 'confidence']],
                on='player_name',
                how='left'
            )
        else:
            result = pd.concat([player_data, predictions], axis=1)
        
        return result
        
    except Exception as e:
        st.warning(f"⚠️ Ensemble predictions unavailable: {str(e)}")
        return player_data


def render_ensemble_comparison(df):
    """
    Render ensemble prediction comparison section
    
    Shows side-by-side comparison of prediction methods
    """
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<div class="section-header-container"><h2>🤖 Ensemble Predictions vs Baseline</h2></div>', 
                unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="section-content">', unsafe_allow_html=True)
        
        # Check if ensemble predictions exist
        has_ensemble = all(col in df.columns for col in ['pred_ensemble', 'pred_weighted_sum', 'confidence'])
        
        if not has_ensemble:
            st.info("💡 Ensemble predictions not available. Train models to enable.")
            st.markdown('</div></div>', unsafe_allow_html=True)
            return
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Players Analyzed",
                f"{len(df):,}",
                help="Total players with ensemble predictions"
            )
        
        with col2:
            avg_ensemble = df['pred_ensemble'].mean()
            st.metric(
                "Avg Ensemble Score",
                f"{avg_ensemble:.2f}",
                help="Average ensemble prediction"
            )
        
        with col3:
            avg_confidence = df['confidence'].mean()
            st.metric(
                "Avg Confidence",
                f"{avg_confidence:.1%}",
                help="Average prediction confidence"
            )
        
        with col4:
            high_conf = (df['confidence'] > 0.8).sum()
            st.metric(
                "High Confidence",
                f"{high_conf}",
                help="Players with >80% confidence"
            )
        
        st.markdown("---")
        
        # Comparison table
        st.subheader("📊 Prediction Comparison")
        
        # Prepare display data
        display_cols = ['player_name']
        if 'position' in df.columns:
            display_cols.append('position')
        
        display_cols.extend([
            'pred_weighted_sum', 
            'pred_lightgbm', 
            'pred_catboost', 
            'pred_ensemble',
            'confidence'
        ])
        
        available_cols = [c for c in display_cols if c in df.columns]
        display_df = df[available_cols].copy()
        
        # Rename for clarity
        display_df = display_df.rename(columns={
            'pred_weighted_sum': 'Weighted Sum',
            'pred_lightgbm': 'LightGBM',
            'pred_catboost': 'CatBoost',
            'pred_ensemble': 'Ensemble',
            'confidence': 'Confidence'
        })
        
        # Sort by ensemble score
        display_df = display_df.sort_values('Ensemble', ascending=False)
        
        # Format numbers
        for col in ['Weighted Sum', 'LightGBM', 'CatBoost', 'Ensemble']:
            if col in display_df.columns:
                display_df[col] = display_df[col].round(2)
        
        if 'Confidence' in display_df.columns:
            display_df['Confidence'] = display_df['Confidence'].apply(lambda x: f"{x:.1%}")
        
        # Display with highlighting
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            height=400
        )
        
        # Model performance explanation
        with st.expander("ℹ️ Understanding Ensemble Predictions"):
            st.markdown("""
            ### How Ensemble Predictions Work
            
            **Three Models Combined:**
            1. **Weighted Sum (30%)** - Your current baseline using factor weights
            2. **LightGBM (40%)** - Gradient boosting model, captures non-linear patterns
            3. **CatBoost (30%)** - Specialized for categorical features (teams, parks)
            
            **Ensemble Score** = Weighted average of all three models
            
            **Confidence Score** = How much the models agree (higher = more reliable)
            
            **Model Performance (Sept 2024 validation):**
            - Weighted Sum: RMSE 1.92
            - LightGBM: RMSE 0.84 ⭐ (best individual)
            - CatBoost: RMSE 0.87
            - Ensemble: RMSE 0.96
            
            **Why use ensemble?**
            - Combines strengths of different approaches
            - More robust to unusual situations
            - Confidence scores help identify reliable predictions
            
            **Trained on:** 304 players from September 2024
            """)
        
        st.markdown('</div></div>', unsafe_allow_html=True)


def add_ensemble_to_recommendations(df):
    """
    Add ensemble-based sit/start recommendations
    
    Args:
        df: DataFrame with ensemble predictions
        
    Returns:
        DataFrame with recommendation column added
    """
    if 'pred_ensemble' not in df.columns:
        return df
    
    # Use ensemble score for recommendations
    df = df.copy()
    
    # Calculate threshold (median or 0)
    threshold = max(df['pred_ensemble'].median(), 0)
    
    # Add recommendations
    df['ensemble_recommendation'] = df['pred_ensemble'].apply(
        lambda x: 'START ⭐' if x > threshold else 'SIT 🔻'
    )
    
    # High confidence recommendations
    if 'confidence' in df.columns:
        df['ensemble_recommendation'] = df.apply(
            lambda row: f"{row['ensemble_recommendation']} 🎯" 
            if row['confidence'] > 0.8 else row['ensemble_recommendation'],
            axis=1
        )
    
    return df
