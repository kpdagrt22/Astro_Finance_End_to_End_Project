# components/crash_score_card.py - Animated Score Card
import streamlit as st

def render_crash_score_card(score: int):
    """Render animated crash score card"""
    
    # Determine color and status
    if score >= 15:
        color = "#ff4444"
        status = "🔴 EXTREME RISK"
    elif score >= 10:
        color = "#ff9800"
        status = "🟠 HIGH RISK"
    elif score >= 5:
        color = "#ffc107"
        status = "🟡 MEDIUM RISK"
    else:
        color = "#4CAF50"
        status = "🟢 NORMAL"
    
    st.markdown(f"""
    <div class="crash-score-card" style="background: linear-gradient(135deg, {color}, {color});">
        <div class="score-number">{score}</div>
        <div class="score-label">/ 20 POINTS</div>
        <div class="score-status">{status}</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {(score/20)*100}%;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
