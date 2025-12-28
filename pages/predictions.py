# pages/3_🔮_Predictions.py
import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.style_loader import load_custom_css
from utils.calculations import get_predictions, get_crash_score
from components.header import render_header
from components.sidebar import render_sidebar
from components.footer import render_footer

st.set_page_config(page_title="Predictions", page_icon="🔮", layout="wide")

load_custom_css()
render_header()
render_sidebar()

st.title("🔮 90-Day Market Forecast")

predictions_df = get_predictions()

if not predictions_df.empty:
    # Show 7 days for free, 90 for premium
    if not st.session_state.get('is_premium', False):
        predictions_df = predictions_df.head(7)
        st.warning("⚠️ Free tier: 7-day forecast. Upgrade for 90 days!")
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    bullish = (predictions_df['direction'] == 'UP').sum()
    avg_prob = predictions_df['probability_up'].mean() * 100
    pred_return = ((predictions_df['predicted_price'].iloc[-1] / predictions_df['predicted_price'].iloc[0]) - 1) * 100
    
    col1.metric("Bullish Days", f"{bullish}/{len(predictions_df)}")
    col2.metric("Avg Probability", f"{avg_prob:.1f}%")
    col3.metric("Predicted Return", f"{pred_return:+.2f}%")
    
    # Chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=predictions_df['date'],
        y=predictions_df['predicted_price'],
        mode='lines',
        name='Predicted',
        line=dict(color='#667eea', width=3)
    ))
    
    fig.update_layout(
        title=f'{len(predictions_df)}-Day Forecast',
        xaxis_title='Date',
        yaxis_title='Price ($)',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("⚠️ Run: `python scripts/future_predictions.py`")

render_footer()
