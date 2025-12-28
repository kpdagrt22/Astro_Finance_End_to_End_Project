# components/live_chart.py
import plotly.graph_objects as go
import yfinance as yf

@st.cache_data(ttl=30)
def get_live_data():
    sp500 = yf.download("^GSPC", period="1d", interval="5m")
    return sp500

live_data = get_live_data()
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=live_data.index,
    open=live_data['Open'],
    high=live_data['High'],
    low=live_data['Low'],
    close=live_data['Close']
))
st.plotly_chart(fig, use_container_width=True)
