# scripts/future_predictions.py - PREDICT NEXT 90 DAYS

import pandas as pd
import numpy as np
import joblib
import yfinance as yf
from datetime import datetime, timedelta
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.planetary_data import compute_planetary_positions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def predict_future_90_days():
    """Generate predictions for next 90 days"""
    
    logger.info("🔮 GENERATING 90-DAY FORECAST")
    logger.info("=" * 60)
    
    # Load model
    model = joblib.load('models/xgboost_model.pkl')
    
    # Get historical context (last 60 days for features)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60)
    
    # Historical financial data
    djia = yf.download('^GSPC', start=start_date.strftime('%Y-%m-%d'), 
                       end=end_date.strftime('%Y-%m-%d'), progress=False)
    
    # Future dates (next 90 days)
    future_dates = pd.date_range(start=end_date + timedelta(days=1), periods=90, freq='D')
    
    # Compute future planetary positions
    logger.info("Computing future planetary positions...")
    future_planetary = compute_planetary_positions(
        (end_date + timedelta(days=1)).strftime('%Y-%m-%d'),
        (end_date + timedelta(days=90)).strftime('%Y-%m-%d')
    )
    future_planetary['date'] = pd.to_datetime(future_planetary['date'])
    
    # Generate predictions
    predictions = []
    last_price = float(djia['Close'].iloc[-1])
    
    for i, date in enumerate(future_dates):
        # Simple feature vector (volume patterns + planetary)
        X = np.zeros((1, 85))
        X[0, 0] = float(djia['Volume'].tail(7).mean()) / 1e9
        X[0, 1] = float(djia['Volume'].tail(14).mean()) / 1e9
        X[0, 5] = np.log(last_price)
        
        # Add planetary features
        planetary_row = future_planetary[future_planetary['date'] == date]
        if not planetary_row.empty:
            if 'moon_velocity' in planetary_row.columns:
                moon_vel = planetary_row['moon_velocity'].iloc[0]
                if not pd.isna(moon_vel):
                    X[0, 60] = moon_vel
            if 'saturn_longitude' in planetary_row.columns:
                saturn_lon = planetary_row['saturn_longitude'].iloc[0]
                if not pd.isna(saturn_lon):
                    X[0, 56] = saturn_lon
        
        # Predict
        proba = model.predict_proba(X)[0, 1]
        direction = 'UP' if proba > 0.5 else 'DOWN'
        
        # Simulate price (simple random walk)
        change_pct = np.random.normal(0.001 if proba > 0.5 else -0.001, 0.015)
        last_price = last_price * (1 + change_pct)
        
        predictions.append({
            'date': date,
            'predicted_price': last_price,
            'probability_up': proba,
            'direction': direction,
            'confidence': max(proba, 1-proba)
        })
    
    predictions_df = pd.DataFrame(predictions)
    predictions_df.to_csv('predictions_future_90d.csv', index=False)
    
    logger.info(f"✓ Generated 90-day forecast")
    logger.info(f"📅 Period: {predictions_df['date'].min().date()} to {predictions_df['date'].max().date()}")
    logger.info(f"📈 Predicted DJIA at +90d: ${predictions_df['predicted_price'].iloc[-1]:,.0f}")
    logger.info(f"📊 Bullish days: {(predictions_df['direction']=='UP').sum()}/90")
    
    return predictions_df

if __name__ == "__main__":
    df = predict_future_90_days()
    print("\n📊 Next 7 Days Preview:")
    print(df.head(7)[['date', 'direction', 'probability_up', 'predicted_price']])
