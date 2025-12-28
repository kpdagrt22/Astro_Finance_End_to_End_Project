# pages/1_🏠_Dashboard.py
import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from components.crash_score_card import render_crash_score_card
from ml.crash_scorer import get_cached_crash_score
from components.footer import render_footer

st.set_page_config(page_title="Dashboard", page_icon="🏠", layout="wide")

# Main content
st.title("🏠 Dashboard")

crash_score = get_cached_crash_score()
render_crash_score_card(crash_score)

# Rest of dashboard content...

render_footer()
