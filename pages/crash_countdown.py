# pages/2_⏱️_Crash_Countdown.py
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.style_loader import load_custom_css
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer

st.set_page_config(page_title="Crash Countdown", page_icon="⏱️", layout="wide")

load_custom_css()
render_header()
render_sidebar()

st.title("⏱️ Major Event Countdown")

try:
    events_df = pd.read_csv('planetary_events_calendar.csv')
    events_df['date'] = pd.to_datetime(events_df['date'])
    
    today = datetime.now()
    future_events = events_df[events_df['date'] > today]
    major_events = future_events[future_events['severity'].isin(['CRITICAL', 'HIGH'])].head(5)
    
    for _, event in major_events.iterrows():
        days_until = (event['date'] - today).days
        severity_color = '#ff4444' if event['severity'] == 'CRITICAL' else '#ff9800'
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown(f"""
            <div style='background: {severity_color}; color: white; padding: 30px; 
                        border-radius: 15px; text-align: center;'>
                <h1 style='margin: 0; font-size: 3rem;'>{days_until}</h1>
                <p style='margin: 5px 0;'>DAYS</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background: #2c2c2c; color: white; padding: 20px; border-radius: 15px;'>
                <h3>{event['event']}</h3>
                <p><b>Date:</b> {event['date'].strftime('%B %d, %Y')}</p>
                <p><b>Severity:</b> <span style='color: {severity_color};'>{event['severity']}</span></p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")

except FileNotFoundError:
    st.error("⚠️ Run: `python scripts/planetary_calendar.py`")

render_footer()
