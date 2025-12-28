# pages/4_🧮_Calculators.py
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.style_loader import load_custom_css
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer

st.set_page_config(page_title="Calculators", page_icon="🧮", layout="wide")

load_custom_css()
render_header()
render_sidebar()

st.title("🧮 Trading Calculators")

calc_type = st.selectbox("Choose Calculator", [
    "💸 Crash Loss Calculator",
    "🎯 Buy Target Calculator"
])

st.markdown("---")

if "Crash Loss" in calc_type:
    st.subheader("💸 Calculate Potential Loss")
    
    portfolio = st.number_input("Portfolio Value ($)", value=100000, step=1000)
    crash_pct = st.slider("Expected Crash %", 0, 50, 30)
    
    loss = portfolio * (crash_pct / 100)
    remaining = portfolio - loss
    
    st.error(f"💸 **Potential Loss:** ${loss:,.0f}")
    st.info(f"💼 **Remaining Value:** ${remaining:,.0f}")
    st.warning(f"📈 **Recovery Needed:** {(loss/remaining)*100:.1f}%")

elif "Buy Target" in calc_type:
    st.subheader("🎯 Buy Targets During Crash")
    
    current_price = st.number_input("Current Price ($)", value=185.50)
    cash = st.number_input("Available Cash ($)", value=10000)
    
    target1 = current_price * 0.90
    target2 = current_price * 0.80
    target3 = current_price * 0.70
    
    st.success(f"🎯 **Target 1 (-10%):** ${target1:.2f}")
    st.info(f"🎯 **Target 2 (-20%):** ${target2:.2f}")
    st.warning(f"🎯 **Target 3 (-30%):** ${target3:.2f}")

render_footer()
