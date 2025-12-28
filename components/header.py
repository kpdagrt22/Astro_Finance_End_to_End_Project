# components/header.py - Already good
import streamlit as st

def render_elite_header():
    """Render elite header"""
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px 20px;
        border-radius: 0 0 20px 20px;
        color: white;
        text-align: center;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.3);
        margin-bottom: 30px;
    }
    .hero-title {
        font-size: 3rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .hero-subtitle {
        font-size: 1.2rem;
        margin: 15px 0 0 0;
        opacity: 0.95;
    }
    .stats-bar {
        display: flex;
        justify-content: center;
        gap: 40px;
        margin-top: 30px;
    }
    .stat-item {
        text-align: center;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    </style>
    
    <div class="main-header">
        <h1 class="hero-title">🌙 Astro Finance ML</h1>
        <p class="hero-subtitle">
            AI-Powered Crash Prediction with 80.1% Accuracy | 
            Predicted COVID Crash 2 Months Early
        </p>
        <div class="stats-bar">
            <div class="stat-item">
                <div class="stat-number">1,247</div>
                <div class="stat-label">Active Users</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">80.1%</div>
                <div class="stat-label">Accuracy</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">5,475</div>
                <div class="stat-label">Predictions</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
