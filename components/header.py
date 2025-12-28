# components/header.py
import streamlit as st

def render_header():
    """Render main header"""
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 50px 20px; border-radius: 0 0 30px 30px; color: white; 
                text-align: center; box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3); 
                margin: -80px -80px 30px -80px;'>
        <h1 style='font-size: 3.5rem; font-weight: 900; margin: 0; 
                   text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
            🌙 Astro Finance ML
        </h1>
        <p style='font-size: 1.3rem; margin: 15px 0; opacity: 0.95;'>
            AI-Powered Stock Market Crash Prediction with 80.1% Accuracy
        </p>
        <p style='font-size: 1rem; margin: 10px 0; opacity: 0.85;'>
            📊 Predicted COVID Crash 2 Months Early | 🎯 Real-time Planetary Analysis
        </p>
    </div>
    """, unsafe_allow_html=True)
