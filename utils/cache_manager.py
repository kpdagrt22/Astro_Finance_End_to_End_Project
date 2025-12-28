# utils/cache_manager.py - FIXED (Minimal dependencies)
import streamlit as st
import pandas as pd
from pathlib import Path

def initialize_cache():
    """Initialize caching system"""
    # Clear old cache
    st.cache_data.clear()
    return True

@st.cache_data(ttl=300)  # 5 minutes
def load_predictions():
    """Load predictions with caching"""
    try:
        df = pd.read_csv('predictions_future_90d.csv')
        df['date'] = pd.to_datetime(df['date'])
        return df
    except FileNotFoundError:
        return pd.DataFrame()

@st.cache_data(ttl=60)  # 1 minute
def load_crash_score():
    """Load crash score with caching"""
    try:
        # Try to load from CSV if exists
        import pandas as pd
        events_df = pd.read_csv('planetary_events_calendar.csv')
        events_df['date'] = pd.to_datetime(events_df['date'])
        
        from datetime import datetime, timedelta
        today = datetime.now()
        upcoming = events_df[
            (events_df['date'] >= today) & 
            (events_df['date'] <= today + timedelta(days=30))
        ]
        
        score = 0
        for _, event in upcoming.iterrows():
            if 'Saturn-Pluto' in str(event.get('event', '')):
                score += 10
            elif 'Saturn-Uranus' in str(event.get('event', '')):
                score += 8
            elif 'Jupiter-Saturn' in str(event.get('event', '')):
                score += 7
            elif 'Mars' in str(event.get('event', '')) and 'Retrograde' in str(event.get('event', '')):
                score += 5
            elif 'Mercury Retrograde' in str(event.get('event', '')):
                score += 3
            elif 'Eclipse' in str(event.get('event', '')) or 'Moon' in str(event.get('event', '')):
                score += 2
        
        return score
    except:
        return 0
