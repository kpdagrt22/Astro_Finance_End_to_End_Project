# dashboard/app.py - PRODUCTION DASHBOARD

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import sys
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.email_alerts import send_crash_alerts

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data' / 'processed'
RESULTS_FILE = Path(__file__).parent.parent / 'pipeline_results.json'

st.set_page_config(
    page_title="🌙 Astro Finance ML",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 50px 20px;
        border-radius: 0 0 30px 30px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        margin: -80px -80px 30px -80px;
    }
    .hero-title { font-size: 3.5rem; font-weight: 900; margin: 0; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header"><h1 class="hero-title">🌙 Astro Finance ML</h1></div>', 
            unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Control Panel")
    
    if st.button("🔄 Run Full Pipeline", use_container_width=True):
        st.info("Running pipeline... Check console for progress")
        import subprocess
        result = subprocess.run([sys.executable, "scripts/orchestrate.py"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            st.success("✅ Pipeline completed!")
            st.rerun()
        else:
            st.error(f"❌ Pipeline failed: {result.stderr}")
    
    st.markdown("---")
    
    # Check pipeline status
    if RESULTS_FILE.exists():
        with open(RESULTS_FILE, 'r') as f:
            results = json.load(f)
        
        if results['success']:
            st.success("✅ Pipeline: SUCCESS")
        else:
            st.error("❌ Pipeline: FAILED")
        
        st.caption(f"Last run: {results['timestamp'][:10]}")

# Main content
st.markdown("---")

# Load data
@st.cache_data(ttl=300)
def load_data():
    data = {}
    
    # Events
    events_file = DATA_DIR / 'planetary_events_calendar.csv'
    if events_file.exists():
        data['events'] = pd.read_csv(events_file)
    
    # Predictions
    pred_file = DATA_DIR / 'predictions_future_90d.csv'
    if pred_file.exists():
        data['predictions'] = pd.read_csv(pred_file)
    
    # Outlook
    outlook_file = DATA_DIR / 'market_outlook_2025.json'
    if outlook_file.exists():
        with open(outlook_file, 'r') as f:
            data['outlook'] = json.load(f)
    
    return data

data = load_data()

# Display metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    if 'events' in data:
        critical_events = (data['events']['severity'] == 'CRITICAL').sum()
        st.metric("Critical Events", critical_events)
    else:
        st.metric("Critical Events", "N/A")

with col2:
    if 'predictions' in data:
        bullish = (data['predictions']['direction'] == 'UP').sum()
        st.metric("Bullish Days", f"{bullish}/90")
    else:
        st.metric("Bullish Days", "N/A")

with col3:
    if 'outlook' in data:
        st.metric("Year", data['outlook']['year'])
    else:
        st.metric("Year", "2025")

with col4:
    st.metric("Status", "✅ Ready" if data else "⚠️ No Data")

st.markdown("---")

# Display events
if 'events' in data:
    st.subheader("📅 Upcoming Events")
    st.dataframe(
        data['events'].head(10)[['date', 'event', 'severity', 'impact']],
        use_container_width=True
    )

# Display predictions
if 'predictions' in data:
    st.subheader("🔮 90-Day Forecast")
    
    fig = go.Figure()
    pred_df = data['predictions']
    
    fig.add_trace(go.Scatter(
        x=pred_df['date'],
        y=pred_df['predicted_price'],
        mode='lines',
        line=dict(color='#667eea', width=3)
    ))
    
    fig.update_layout(
        title='S&P 500 90-Day Forecast',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("⚠️ Not financial advice. Run pipeline regularly for updates.")
