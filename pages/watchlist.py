# pages/1_📌_Watchlist.py
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.style_loader import load_custom_css
from utils.calculations import get_stock_prediction
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer

st.set_page_config(page_title="Watchlist", page_icon="📌", layout="wide")

load_custom_css()
render_header()
render_sidebar()

st.title("📌 My Watchlist")

# Add stock
col1, col2 = st.columns([3, 1])
with col1:
    new_symbol = st.text_input("Add Stock", placeholder="AAPL, TSLA...").upper()
with col2:
    if st.button("➕ Add", use_container_width=True):
        if new_symbol and new_symbol not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_symbol)
            st.success(f"✅ Added {new_symbol}")
        elif new_symbol in st.session_state.watchlist:
            st.info("Already in watchlist")

st.markdown("---")

# Display watchlist
for symbol in st.session_state.watchlist:
    pred = get_stock_prediction(symbol)
    
    if pred:
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        
        with col1:
            st.markdown(f"### {symbol}")
        with col2:
            st.metric("Price", f"${pred['price']:.2f}")
        with col3:
            st.metric("Change", f"{pred['change']:+.2f}%")
        with col4:
            signal_emoji = "🟢" if pred['signal'] == "BUY" else "🟡" if pred['signal'] == "HOLD" else "🔴"
            st.metric("Signal", f"{signal_emoji} {pred['signal']}")
        with col5:
            if st.button("🗑️", key=f"del_{symbol}"):
                st.session_state.watchlist.remove(symbol)
                st.rerun()
        
        st.markdown("---")

render_footer()
