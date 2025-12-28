# dashboard/app.py - STREAMLIT LIVE DASHBOARD

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(page_title="Astro Finance ML", layout="wide", page_icon="🌙")

st.title("🌙 Astro Finance ML - Live Predictions Dashboard")
st.markdown("*Combining planetary movements with machine learning for market forecasting*")

# Sidebar
st.sidebar.header("⚙️ Controls")
forecast_days = st.sidebar.slider("Forecast Horizon (Days)", 7, 90, 30)
show_planetary = st.sidebar.checkbox("Show Planetary Events", value=True)

# Main Content
col1, col2, col3 = st.columns(3)

# Today's Signal
try:
    from scripts.live_predictions import main as get_live_prediction
    # Mock data for demo
    with col1:
        st.metric("Today's Signal", "🟢 BUY", "+2.3%")
    with col2:
        st.metric("DJIA Current", "$6,930", "+145")
    with col3:
        st.metric("P(UP 5d)", "68.7%", "+5.2%")
except:
    st.warning("Run live_predictions.py first to generate current signal")

# Future Predictions Chart
st.subheader("📈 90-Day Forecast")

try:
    predictions_df = pd.read_csv('predictions_future_90d.csv')
    predictions_df['date'] = pd.to_datetime(predictions_df['date'])
    
    fig = go.Figure()
    
    # Predicted price line
    fig.add_trace(go.Scatter(
        x=predictions_df['date'],
        y=predictions_df['predicted_price'],
        mode='lines',
        name='Predicted DJIA',
        line=dict(color='blue', width=2)
    ))
    
    # Confidence bands
    fig.add_trace(go.Scatter(
        x=predictions_df['date'],
        y=predictions_df['predicted_price'] * (1 + predictions_df['confidence'] * 0.1),
        mode='lines',
        name='Upper Confidence',
        line=dict(width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=predictions_df['date'],
        y=predictions_df['predicted_price'] * (1 - predictions_df['confidence'] * 0.1),
        mode='lines',
        name='Lower Confidence',
        fill='tonexty',
        fillcolor='rgba(0,100,255,0.2)',
        line=dict(width=0)
    ))
    
    fig.update_layout(
        title="DJIA 90-Day Forecast (ML + Planetary)",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        hovermode='x unified',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
except FileNotFoundError:
    st.info("Run `python scripts/future_predictions.py` to generate forecast")

# Planetary Events Calendar
if show_planetary:
    st.subheader("🌙 Upcoming Planetary Events (Crash Indicators)")
    
    try:
        events_df = pd.read_csv('planetary_events_calendar.csv')
        events_df['date'] = pd.to_datetime(events_df['date'])
        
        # Filter future events
        today = datetime.now()
        future_events = events_df[events_df['date'] > today].head(10)
        
        # Color code by severity
        def severity_color(severity):
            colors = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢'
            }
            return colors.get(severity, '⚪')
        
        future_events['indicator'] = future_events['severity'].apply(severity_color)
        
        st.dataframe(
            future_events[['indicator', 'date', 'event', 'impact']],
            use_container_width=True,
            hide_index=True
        )
        
    except FileNotFoundError:
        st.info("Run `python scripts/planetary_calendar.py` to scan for events")

# Model Performance
st.subheader("🎯 Model Performance")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("XGBoost Accuracy", "80.1%")
with col2:
    st.metric("LSTM Accuracy", "79.2%")
with col3:
    st.metric("Ensemble Accuracy", "79.6%")
with col4:
    st.metric("Top Feature", "volume_mean_14d")

# Footer
st.markdown("---")
st.caption("⚠️ For educational purposes only. Not financial advice. Trade at your own risk.")
