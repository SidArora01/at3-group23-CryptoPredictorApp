import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import os
from datetime import datetime
import time
import datetime
from datetime import timezone

BASE_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(BASE_DIR) 
st.set_page_config(page_title="Ethereum", page_icon="💎", layout="wide")

st.markdown("""
<style>
/* Body & background */
body {
    background: linear-gradient(135deg, #1f1c2c, #282843);
    color: #f0f0f0;
}

/* Fonts */
h1, h2, h3 {
    font-family: 'Poppins', sans-serif;
}
p {
    font-family: 'Roboto', sans-serif;
    font-size: 1rem;
    line-height: 1.5rem;
}

/* Crypto cards */
.crypto-card {
    border-radius: 20px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    transition: transform 0.2s;
    text-align: center;
    background-color: #2a2a3e;
    padding: 15px;
    margin-bottom: 20px;
}
.crypto-card:hover {
    transform: scale(1.05);
}

/* Images hover effect */
.crypto-card img {
    border-radius: 15px;
    transition: transform 0.3s ease-in-out;
}
.crypto-card img:hover {
    transform: scale(1.05);
}

/* Buttons */
.stButton>button {
    background: linear-gradient(45deg, #ff9900, #ff6600);
    color: white;
    font-weight: bold;
    border-radius: 12px;
    padding: 8px 16px;
    transition: all 0.3s ease;
    width: 100%;
}
.stButton>button:hover {
    transform: translateY(-3px);
    box-shadow: 0 5px 15px rgba(255, 153, 0, 0.6);
}

/* Section header */
.section-header {
    background-color: #3a3a55;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 25px;
    text-align: center;
}
.section-header h2 {
    color: #ff9900;
    margin: 0;
}
.section-header p {
    color: #ffffff;
    margin: 5px 0 0 0;
}
</style>
""", unsafe_allow_html=True)

#Title and Info
st.markdown('<div class="section-header"><h2>Ethereum Dashboard</h2><p>The blockchain that powers smart contracts and decentralized apps</p></div>', unsafe_allow_html=True)



col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    img_col1, img_col2, img_col3 = st.columns([1, 2, 1])
    with img_col2:
        eth = os.path.join(APP_DIR, "assets", "eth.svg")
        st.image(eth)

st.write("""
**Ethereum (ETH)** is a decentralized platform that introduced smart contracts, 
enabling developers to build decentralized applications (DApps). 

""")
st.write("""
It is the foundation for NFTs, DeFi, and countless other blockchain innovations.
""")
st.markdown("---")

st.markdown('<div class="section-header"><h2>Dashboard Features</h2></div>', unsafe_allow_html=True)

# Create three columns
col1, col2, col3 = st.columns(3, gap="large")

card_style = """
    background-color: rgba(255, 255, 255, 0.05);
    padding: 20px; 
    border-radius: 15px; 
    text-align: center; 
    box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    color: inherit;
    height: 300px;
"""

# Card 1: Historical Candle Charts
with col1:
    st.markdown(
        f"""
        <div style="{card_style}">
            <h3>Historical Candle Charts</h3>
            <p>Visualize daily OHLC data using interactive candlestick charts for both short-term (last 100 days) and long-term (last 2 years) trend analysis. Zoom, pan, and hover over points for precise insights.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Card 2: Key Market Metrics
with col2:
    st.markdown(
        f"""
        <div style="{card_style}">
            <h3>Key Market Metrics</h3>
            <p>Access real-time prices, high/low, VWAP, trading volume, and number of trades to make informed decisions quickly. Metrics are updated continuously for accurate monitoring.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Card 3: Machine Learning Predictions
with col3:
    st.markdown(
        f"""
        <div style="{card_style}">
            <h3>ML Predictions</h3>
            <p>Leverage our trained machine learning model to predict next-day high prices. Experiment with different input scenarios to explore potential market outcomes.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

#Data Fetch - Kraken Endpoint

@st.cache_data(ttl=3600)
def fetch_kraken_ohlc(pair="ETHUSD", interval=1440):
    """
    Fetch OHLC data from Kraken.
    interval=1440 -> daily candles
    Returns a DataFrame.
    """
    url = "https://api.kraken.com/0/public/OHLC"
    params = {
        "pair": pair,
        "interval": interval,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    ohlc = data['result'][list(data['result'].keys())[0]]  # get the pair key
    df = pd.DataFrame(ohlc, columns=[
        "timestamp", "open", "high", "low", "close", "vwap", "volume", "count"
    ])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit='s')
    df.set_index("timestamp", inplace=True)
    
    # Convert numeric columns to float
    for col in ["open", "high", "low", "close", "vwap", "volume"]:
        df[col] = df[col].astype(float)
    df["count"] = df["count"].astype(int)
    
    return df

df = fetch_kraken_ohlc()

# Historic Candle Plots
st.markdown("---")

st.markdown('<div class="section-header"><h2>Trend Candle Chart</h2><p></p></div>', unsafe_allow_html=True)


df_hist = df.iloc[:-1].tail(100)

fig = go.Figure(data=[go.Candlestick(
    x=df_hist.index,
    open=df_hist['open'],
    high=df_hist['high'],
    low=df_hist['low'],
    close=df_hist['close'],
    name = 'Eth'
)])
fig.update_layout(
    title="ETH Daily OHLC - Last 100 Days",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    xaxis_rangeslider_visible=False
)
st.plotly_chart(fig, use_container_width=True)

df_hist = df.iloc[:-1].tail(100)

fig = go.Figure(data=[go.Candlestick(
    x=df.index,
    open=df['open'],
    high=df['high'],
    low=df['low'],
    close=df['close'],
    name = 'Eth'
)])
fig.update_layout(
    title="ETH Daily OHLC - Last 2 Years",
    xaxis_title="Date",
    yaxis_title="Price (USD)",
    xaxis_rangeslider_visible=False
)
st.plotly_chart(fig, use_container_width=True)




#Key Market Metrics

st.markdown("---")
st.markdown('<div class="section-header"><h2>Key Market Metrics (Latest Daily Candle)</h2><p></p></div>', unsafe_allow_html=True)



latest = df.iloc[-1]
previous = df.iloc[-2]

def percent_change(new, old):
    try:
        return ((new - old) / old) * 100
    except ZeroDivisionError:
        return 0

price_delta = percent_change(latest['close'], previous['close'])
high_delta = percent_change(latest['high'], previous['high'])
low_delta = percent_change(latest['low'], previous['low'])
vwap_delta = percent_change(latest['vwap'], previous['vwap'])
vol_delta = percent_change(latest['volume'], previous['volume'])
count_delta = percent_change(latest['count'], previous['count'])

col1, col2 = st.columns(2)
col1.metric(
    "Current Price (USD)", 
    f"{latest['close']:.2f}", 
    delta=f"{price_delta:.2f}%",
    delta_color="normal"
)
col2.metric(
    "High (24h)", 
    f"{latest['high']:.2f}", 
    delta=f"{high_delta:.2f}%",
    delta_color="normal"
)

col3, col4 = st.columns(2)
col3.metric(
    "Low (24h)", 
    f"{latest['low']:.2f}", 
    delta=f"{low_delta:.2f}%",
    delta_color="normal"
)
col4.metric(
    "VWAP (24h)", 
    f"{latest['vwap']:.2f}", 
    delta=f"{vwap_delta:.2f}%",
    delta_color="normal"
)

col5, col6 = st.columns(2)
col5.metric(
    "Trading Volume Current",
    f"{latest['volume']:.2f}", 
    delta=f"{vol_delta:.2f}%",
    delta_color="normal"
)
col6.metric(
    "Number of Trades Current", 
    f"{latest['count']}", 
    delta=f"{count_delta:.2f}%",
    delta_color="normal"
)

st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 1.5rem;
    color: #f5f5f5;
}
[data-testid="stMetricDelta"] {
    font-weight: bold;
    font-size: 1.1rem;
}
</style>
""", unsafe_allow_html=True)




# ML Prediction

st.markdown("---")
st.markdown('<div class="section-header"><h2>High Price Predictions for Tomorrow</h2><p></p></div>', unsafe_allow_html=True)




utc_now = datetime.datetime.now(timezone.utc)
formatted_date = utc_now.strftime("%b %d, %Y")
formatted_time = utc_now.strftime("%H:%M:%S")

st.metric(
    label="Current UTC Time",
    value=formatted_date
)
st.markdown(formatted_time)


st.info("Click the button to get the predicted next-day high price for Ethereum (ETH).")

url = "https://at3-25106954-api.onrender.com/predict/eth"

import requests, time

if st.button("Predict Tomorrow's High Price"):
    with st.spinner("Waking up prediction server... this may take a few minutes if asleep"):
        max_retries = 60       
        wait_seconds = 10      
        data = None
        success = False

        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    success = True
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(wait_seconds)

        if not success:
            st.error("The prediction server is still waking up. Please try again in a few minutes.")
        else:
            predicted_date = data.get("predicted_date", "N/A")
            date_obj = datetime.datetime.strptime(predicted_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%b %d, %Y")
            predicted_high = data.get("predicted_tomorrow_high", None)

            if predicted_high is not None:
                latest_high = df.iloc[-1]["high"]
                diff = predicted_high - latest_high
                perc_change = (diff / latest_high) * 100

                date_obj = datetime.datetime.strptime(predicted_date, "%Y-%m-%d")
                formatted_date = date_obj.strftime("%b %d, %Y")

                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Prediction Date", formatted_date)
                with col2:
                    st.metric(
                        label="Predicted ETH High (USD)",
                        value=f"${predicted_high:,.2f}",
                        delta=f"{perc_change:+.2f}%",
                        delta_color="normal"  
                    )

                st.success("Prediction successfully fetched!")
            else:
                st.warning("Prediction data not available. Please try again later")

st.caption("""
**Notes**  
• All timestamps and prices are shown in **UTC**.  
• Today's information is **partial** and updates continuously until UTC midnight.  
""")
st.caption("Source: Kraken OHLC API • Predictions Group 23 (UTS AdvML AT3) • Not financial advice.")
