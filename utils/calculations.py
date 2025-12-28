# utils/calculations.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

@st.cache_data(ttl=60)
def get_crash_score():
    """Calculate crash risk score"""
    try:
        events_df = pd.read_csv('planetary_events_calendar.csv')
        events_df['date'] = pd.to_datetime(events_df['date'])
        
        today = datetime.now()
        upcoming = events_df[
            (events_df['date'] >= today) & 
            (events_df['date'] <= today + timedelta(days=30))
        ]
        
        score = 0
        for _, event in upcoming.iterrows():
            event_name = str(event.get('event', ''))
            if 'Saturn-Pluto' in event_name:
                score += 10
            elif 'Saturn-Uranus' in event_name:
                score += 8
            elif 'Jupiter-Saturn' in event_name:
                score += 7
            elif 'Mars' in event_name and 'Retrograde' in event_name:
                score += 5
            elif 'Mercury Retrograde' in event_name:
                score += 3
            elif 'Eclipse' in event_name or 'Moon' in event_name:
                score += 2
        
        return min(score, 20)  # Cap at 20
    except:
        return 0

@st.cache_data(ttl=300)
def get_predictions():
    """Load predictions"""
    try:
        df = pd.read_csv('predictions_future_90d.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except:
        return pd.DataFrame()

def get_stock_prediction(symbol):
    """Get prediction for stock"""
    try:
        import yfinance as yf
        stock = yf.Ticker(symbol)
        hist = stock.history(period="30d")
        
        if hist.empty:
            return None
        
        current_price = float(hist['Close'].iloc[-1])
        change_30d = ((current_price - float(hist['Close'].iloc[0])) / float(hist['Close'].iloc[0])) * 100
        
        crash_score = get_crash_score()
        
        if crash_score >= 15:
            direction = "SELL"
            confidence = 0.85
        elif crash_score >= 10:
            direction = "HOLD"
            confidence = 0.70
        else:
            direction = "BUY"
            confidence = 0.75
        
        return {
            'symbol': symbol,
            'price': current_price,
            'change': change_30d,
            'signal': direction,
            'confidence': confidence
        }
    except:
        return None
