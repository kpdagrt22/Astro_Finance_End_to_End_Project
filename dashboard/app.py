# dashboard/app.py - WORKING VERSION
import streamlit as st
from pathlib import Path
import sys

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import components (now fixed)
from components.header import render_elite_header
from components.sidebar import render_elite_sidebar
from utils.cache_manager import initialize_cache, load_crash_score

# Page config
st.set_page_config(
    page_title="🌙 Astro Finance ML",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'is_premium' not in st.session_state:
    st.session_state.is_premium = False

# Initialize cache
initialize_cache()

# Render components
render_elite_header()
render_elite_sidebar()

# Main content
st.markdown("---")
st.subheader("📊 Current Market Status")

# Get crash score
crash_score = load_crash_score()

# Display crash score
col1, col2, col3 = st.columns(3)

with col1:
    if crash_score >= 15:
        st.markdown("""
        <div style='background: #ff4444; color: white; padding: 30px; border-radius: 15px; text-align: center;'>
            <h1 style='margin: 0; font-size: 4rem;'>{}</h1>
            <h3 style='margin: 10px 0;'>/ 20 POINTS</h3>
            <h2 style='margin: 10px 0;'>🔴 EXTREME CRASH RISK</h2>
        </div>
        """.format(crash_score), unsafe_allow_html=True)
    elif crash_score >= 10:
        st.markdown("""
        <div style='background: #ff9800; color: white; padding: 30px; border-radius: 15px; text-align: center;'>
            <h1 style='margin: 0; font-size: 4rem;'>{}</h1>
            <h3 style='margin: 10px 0;'>/ 20 POINTS</h3>
            <h2 style='margin: 10px 0;'>🟠 HIGH CORRECTION RISK</h2>
        </div>
        """.format(crash_score), unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background: #4CAF50; color: white; padding: 30px; border-radius: 15px; text-align: center;'>
            <h1 style='margin: 0; font-size: 4rem;'>{}</h1>
            <h3 style='margin: 10px 0;'>/ 20 POINTS</h3>
            <h2 style='margin: 10px 0;'>🟢 NORMAL CONDITIONS</h2>
        </div>
        """.format(crash_score), unsafe_allow_html=True)

with col2:
    st.metric("S&P 500", "6,040", "+2.7% YTD")
    st.metric("Model Confidence", "80.1%", "+2.3%")

with col3:
    st.metric("Predictions Made", "5,475")
    st.metric("Next Event", "76 days")

# Navigation hint
st.markdown("---")
st.info("💡 **Navigate using the sidebar** to access predictions, watchlist, calculators, and more!")

# Quick links
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; border-radius: 10px; text-align: center; color: white;'>
        <h3>📌 Watchlist</h3>
        <p>Track your stocks</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                padding: 20px; border-radius: 10px; text-align: center; color: white;'>
        <h3>🔮 Predictions</h3>
        <p>90-day forecast</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); 
                padding: 20px; border-radius: 10px; text-align: center; color: white;'>
        <h3>🧮 Calculators</h3>
        <p>Free tools</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                padding: 20px; border-radius: 10px; text-align: center; color: white;'>
        <h3>📅 2025 Outlook</h3>
        <p>Yearly analysis</p>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 20px; color: #666;'>
    <p>Made with ❤️ combining celestial wisdom with AI</p>
    <p style='font-size: 12px;'>⚠️ Not financial advice. Trade at your own risk.</p>
    <p style='font-size: 10px;'>© 2025 Astro Finance ML. All rights reserved.</p>
</div>
""", unsafe_allow_html=True)
