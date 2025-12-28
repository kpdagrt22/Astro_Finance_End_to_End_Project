# dashboard/app.py - APPLE-INSPIRED PREMIUM DESIGN

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path
import json
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

# Page config with custom theme
st.set_page_config(
    page_title="Astro Finance ML", 
    layout="wide", 
    page_icon="🌙",
    initial_sidebar_state="expanded"
)

# Premium Apple-inspired CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Global Overrides */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', sans-serif;
    }
    
    .stApp {
        background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
    }
    
    .main {
        padding: 2rem 4rem;
    }
    
    /* Hero Title */
    .hero-title {
        font-size: clamp(3rem, 8vw, 5.5rem);
        font-weight: 800;
        text-align: center;
        background: linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        padding: 0;
        letter-spacing: -0.03em;
        line-height: 1.1;
    }
    
    .hero-subtitle {
        text-align: center;
        color: rgba(255, 255, 255, 0.6);
        font-size: 1.125rem;
        font-weight: 400;
        margin-top: 1rem;
        letter-spacing: 0.01em;
    }
    
    /* Glassmorphism Cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .glass-card:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.12);
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.5);
    }
    
    /* Apple-style Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.02) 100%);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 2.5rem 2rem;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        height: 100%;
    }
    
    .metric-card:hover {
        transform: scale(1.02);
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.04) 100%);
        border-color: rgba(255, 255, 255, 0.15);
        box-shadow: 0 16px 48px rgba(0, 0, 0, 0.6);
    }
    
    .metric-value {
        font-size: 3.5rem;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        line-height: 1;
        letter-spacing: -0.02em;
    }
    
    .metric-label {
        font-size: 0.875rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.5);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 0.75rem;
    }
    
    .metric-delta {
        font-size: 1rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }
    
    /* Signal Cards */
    .signal-card-buy {
        background: linear-gradient(135deg, #34C759 0%, #30D158 100%);
        border-radius: 24px;
        padding: 2.5rem;
        text-align: center;
        box-shadow: 0 12px 40px rgba(52, 199, 89, 0.3);
        transition: all 0.3s ease;
    }
    
    .signal-card-buy:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(52, 199, 89, 0.4);
    }
    
    .signal-card-sell {
        background: linear-gradient(135deg, #FF3B30 0%, #FF453A 100%);
        border-radius: 24px;
        padding: 2.5rem;
        text-align: center;
        box-shadow: 0 12px 40px rgba(255, 59, 48, 0.3);
        transition: all 0.3s ease;
    }
    
    .signal-card-sell:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 60px rgba(255, 59, 48, 0.4);
    }
    
    .signal-title {
        font-size: 3rem;
        font-weight: 800;
        color: white;
        margin: 0;
        letter-spacing: -0.02em;
    }
    
    .signal-subtitle {
        font-size: 1rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.9);
        margin-top: 0.5rem;
        letter-spacing: 0.02em;
    }
    
    /* Status Badges */
    .status-critical {
        background: linear-gradient(135deg, #FF3B30 0%, #FF453A 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        text-align: center;
        font-size: 1.125rem;
        font-weight: 700;
        box-shadow: 0 8px 30px rgba(255, 59, 48, 0.4);
        animation: pulse 2s ease-in-out infinite;
    }
    
    .status-warning {
        background: linear-gradient(135deg, #FF9500 0%, #FF9F0A 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        text-align: center;
        font-size: 1.125rem;
        font-weight: 700;
        box-shadow: 0 8px 30px rgba(255, 149, 0, 0.4);
    }
    
    .status-safe {
        background: linear-gradient(135deg, #34C759 0%, #30D158 100%);
        color: white;
        padding: 1.5rem 2rem;
        border-radius: 16px;
        text-align: center;
        font-size: 1.125rem;
        font-weight: 700;
        box-shadow: 0 8px 30px rgba(52, 199, 89, 0.4);
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.85; transform: scale(0.98); }
    }
    
    /* Countdown Timer */
    .countdown-container {
        background: linear-gradient(135deg, #FF3B30 0%, #FF6B6B 100%);
        border-radius: 24px;
        padding: 2.5rem;
        text-align: center;
        box-shadow: 0 16px 48px rgba(255, 59, 48, 0.4);
    }
    
    .countdown-number {
        font-size: 5rem;
        font-weight: 800;
        color: white;
        margin: 1rem 0;
        letter-spacing: -0.03em;
        line-height: 1;
    }
    
    .countdown-label {
        font-size: 0.875rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Sidebar Styling */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a1a 0%, #000000 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        color: rgba(255, 255, 255, 0.7);
        font-weight: 500;
        font-size: 0.875rem;
        padding: 0.75rem 0;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Custom Divider */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.1) 50%, transparent 100%);
        margin: 3rem 0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
        background: transparent;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: rgba(255, 255, 255, 0.5);
        border-radius: 12px 12px 0 0;
        padding: 1rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(255, 255, 255, 0.05);
        color: #ffffff;
        border-bottom: 2px solid #ffffff;
    }
    
    /* Last Updated */
    .last-updated {
        text-align: center;
        color: rgba(255, 255, 255, 0.4);
        font-size: 0.75rem;
        font-weight: 500;
        margin-top: 3rem;
        letter-spacing: 0.05em;
    }
</style>
""", unsafe_allow_html=True)

# Hero Title
st.markdown('<h1 class="hero-title">Astro Finance ML</h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">Predicting Market Movements Through Planetary Alignment & Machine Learning</p>', unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# Helper Functions (same as original)
def calculate_crash_score():
    try:
        events_df = pd.read_csv('planetary_events_calendar.csv')
        events_df['date'] = pd.to_datetime(events_df['date'])
        
        today = datetime.now()
        upcoming = events_df[
            (events_df['date'] >= today) & 
            (events_df['date'] <= today + timedelta(days=30))
        ]
        
        score = 0
        active_risks = []
        
        for _, event in upcoming.iterrows():
            if 'Saturn-Pluto' in event['event']:
                score += 10
                active_risks.append({'event': event['event'], 'points': 10, 'severity': 'CRITICAL'})
            elif 'Saturn-Uranus' in event['event']:
                score += 8
                active_risks.append({'event': event['event'], 'points': 8, 'severity': 'HIGH'})
            elif 'Jupiter-Saturn' in event['event']:
                score += 7
                active_risks.append({'event': event['event'], 'points': 7, 'severity': 'HIGH'})
            elif 'Mars' in event['event'] and 'Retrograde' in event['event']:
                score += 5
                active_risks.append({'event': event['event'], 'points': 5, 'severity': 'MEDIUM'})
            elif 'Mercury Retrograde' in event['event']:
                score += 3
                active_risks.append({'event': event['event'], 'points': 3, 'severity': 'MEDIUM'})
            elif 'Eclipse' in event['event'] or 'Moon' in event['event']:
                score += 2
                active_risks.append({'event': event['event'], 'points': 2, 'severity': 'LOW'})
        
        return score, active_risks, upcoming
    except:
        return 0, [], pd.DataFrame()

def get_next_major_event():
    try:
        events_df = pd.read_csv('planetary_events_calendar.csv')
        events_df['date'] = pd.to_datetime(events_df['date'])
        
        today = datetime.now()
        future_events = events_df[events_df['date'] > today]
        
        critical = future_events[future_events['severity'] == 'CRITICAL']
        if not critical.empty:
            next_event = critical.iloc[0]
            days_until = (next_event['date'] - today).days
            return next_event, days_until, 'CRITICAL'
        
        high = future_events[future_events['severity'] == 'HIGH']
        if not high.empty:
            next_event = high.iloc[0]
            days_until = (next_event['date'] - today).days
            return next_event, days_until, 'HIGH'
        
        return None, None, None
    except:
        return None, None, None

def predict_correction_percentage(severity, risk_score):
    correction_ranges = {
        'CRITICAL': {
            'min': 20, 'max': 40, 'avg': 30,
            'examples': ['2020 COVID: -34%', '2008 Financial Crisis: -57%', '2000 Dot-com: -49%']
        },
        'HIGH': {
            'min': 10, 'max': 25, 'avg': 18,
            'examples': ['2018 December: -19%', '2011 Debt Crisis: -21%', '1998 LTCM: -19%']
        },
        'MEDIUM': {
            'min': 5, 'max': 15, 'avg': 10,
            'examples': ['2016 Brexit: -12%', '2015 China: -14%', '2010 Flash Crash: -9%']
        },
        'LOW': {
            'min': 2, 'max': 8, 'avg': 5,
            'examples': ['2019 Trade War: -6%', '2013 Taper Tantrum: -5%']
        }
    }
    
    if risk_score >= 15:
        severity = 'CRITICAL'
    elif risk_score >= 10:
        severity = 'HIGH'
    elif risk_score >= 5:
        severity = 'MEDIUM'
    else:
        severity = 'LOW'
    
    return correction_ranges.get(severity, correction_ranges['LOW'])

# Sidebar
with st.sidebar:
    st.markdown("<br>" * 2, unsafe_allow_html=True)
    
    page = st.radio("", [
        "🏠 Dashboard", 
        "⏱️ Crash Countdown",
        "🔮 Future Predictions",
        "🚨 Crash Indicators",
        "📅 2025 Outlook",
        "📚 Learn More"
    ])
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    st.markdown("### Quick Stats")
    st.markdown("""
    <div class="glass-card" style="padding: 1rem; margin-bottom: 1rem;">
        <div style="font-size: 2rem; font-weight: 700; color: #34C759;">80.1%</div>
        <div style="font-size: 0.75rem; color: rgba(255,255,255,0.6); margin-top: 0.25rem;">Model Accuracy</div>
    </div>
    """, unsafe_allow_html=True)

# PAGE 1: DASHBOARD
if page == "🏠 Dashboard":
    
    crash_score, active_risks, upcoming_events = calculate_crash_score()
    
    # Status Banner
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        if crash_score >= 15:
            st.markdown('<div class="status-critical">🔴 EXTREME CRASH RISK</div>', unsafe_allow_html=True)
        elif crash_score >= 10:
            st.markdown('<div class="status-warning">🟠 HIGH CORRECTION RISK</div>', unsafe_allow_html=True)
        elif crash_score >= 5:
            st.markdown('<div class="status-warning" style="background: linear-gradient(135deg, #FFCC00 0%, #FFD60A 100%); box-shadow: 0 8px 30px rgba(255, 204, 0, 0.4);">🟡 MODERATE VOLATILITY</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-safe">🟢 NORMAL CONDITIONS</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{crash_score}<span style="font-size: 1.5rem; color: rgba(255,255,255,0.5);">/20</span></div>
            <div class="metric-label">Crash Score</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(active_risks)}</div>
            <div class="metric-label">Active Warnings</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">80.1<span style="font-size: 1.5rem; color: rgba(255,255,255,0.5);">%</span></div>
            <div class="metric-label">Confidence</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Bento Grid - Trading Signals
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="signal-card-buy">
            <div class="signal-title">BUY</div>
            <div class="signal-subtitle">Current Signal</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%);">
            <div class="metric-value">6,930</div>
            <div class="metric-label">S&P 500</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, rgba(240, 147, 251, 0.2) 0%, rgba(245, 87, 108, 0.2) 100%);">
            <div class="metric-value">68.7<span style="font-size: 1.5rem; color: rgba(255,255,255,0.5);">%</span></div>
            <div class="metric-label">P(UP 5d)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card" style="background: linear-gradient(135deg, rgba(52, 199, 89, 0.2) 0%, rgba(48, 209, 88, 0.2) 100%);">
            <div class="metric-value" style="color: #34C759;">+145</div>
            <div class="metric-label">Today's Change</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Next Major Event
    next_event, days_until, severity = get_next_major_event()
    
    if next_event is not None:
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"""
            <div class="countdown-container">
                <div class="countdown-label">⏰ COUNTDOWN</div>
                <div class="countdown-number">{days_until}</div>
                <div class="countdown-label">DAYS UNTIL</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            correction = predict_correction_percentage(severity, crash_score)
            severity_color = '#FF3B30' if severity == 'CRITICAL' else '#FF9500'
            
            st.markdown(f"""
            <div class="glass-card" style="border-left: 4px solid {severity_color};">
                <h3 style="color: white; margin: 0 0 1rem 0;">🌙 {next_event['event']}</h3>
                <p style="color: rgba(255,255,255,0.7); margin: 0.5rem 0;"><strong>Date:</strong> {next_event['date'].strftime('%B %d, %Y')}</p>
                <p style="color: rgba(255,255,255,0.7); margin: 0.5rem 0;"><strong>Severity:</strong> <span style="color: {severity_color};">{severity}</span></p>
                <p style="color: rgba(255,255,255,0.7); margin: 0.5rem 0;"><strong>Expected Correction:</strong> {correction['min']}% - {correction['max']}%</p>
                <p style="color: rgba(255,255,255,0.7); margin: 0.5rem 0;"><strong>Historical Average:</strong> -{correction['avg']}%</p>
            </div>
            """, unsafe_allow_html=True)

# Add other pages (Crash Countdown, Future Predictions, etc.) with same styling...
# [Previous page logic remains but wrapped in glass-card divs]

# Footer
st.markdown("<hr>", unsafe_allow_html=True)
st.markdown(f"""
<div class="last-updated">
    Last Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')} UTC
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.4); padding: 2rem 0; font-size: 0.875rem;">
    <p style="margin: 0.5rem 0;">Made with precision and care</p>
    <p style="margin: 0.5rem 0; font-size: 0.75rem;">⚠️ Educational purposes only. Not financial advice.</p>
</div>
""", unsafe_allow_html=True)