# ml/crash_scorer.py - Crash Score Engine
import streamlit as st
from datetime import datetime, timedelta
from utils.data_loader import DataLoader

@st.cache_data(ttl=60)
def get_cached_crash_score():
    """Get cached crash score"""
    return calculate_crash_score()

def calculate_crash_score():
    """Calculate crash risk score"""
    loader = DataLoader()
    events = loader.load_events()
    
    today = datetime.now()
    upcoming = events[
        (events['date'] >= today) & 
        (events['date'] <= today + timedelta(days=30))
    ]
    
    score = 0
    for _, event in upcoming.iterrows():
        if 'Saturn-Pluto' in event['event']:
            score += 10
        elif 'Saturn-Uranus' in event['event']:
            score += 8
        # ... rest of scoring logic
    
    return score
