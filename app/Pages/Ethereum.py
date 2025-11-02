import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
import os
from datetime import datetime
import time
import datetime
from datetime import timezone


st.set_page_config(page_title="Ethereum", page_icon="💎", layout="centered")

#Title and Info
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    st.title("Ethereum Dashboard")
    img_col1, img_col2, img_col3 = st.columns([1, 2, 1])
    with img_col2:
        st.image("assets/eth.svg", width=200)

st.subheader("The blockchain that powers smart contracts and decentralized apps")
st.write("""
**Ethereum (ETH)** is a decentralized platform that introduced smart contracts, 
enabling developers to build decentralized applications (DApps). 

""")
st.write("""
It is the foundation for NFTs, DeFi, and countless other blockchain innovations.
""")
st.markdown("---")

st.subheader("Dashboard Offerings")
st.markdown(
    """
    This Ethereum Dashboard gives you real-time and historical insights using interactive features (clickable charts):

    1. **Historical Candle Charts** – Daily OHLC data visualized with candlestick charts (last 100 days & last 2 years for short and long term analysis).  
    2. **Key Market Metrics** – Latest daily candle values including price, high, low, VWAP, trading volume, and number of trades for quick and realtime decision making.  
    3. **Machine Learning Predictions** – Next-day high price predictions using our trained ML model for informed decisions.  
    """
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

st.subheader("Historical Candle Charts")

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

st.subheader("Key Metrics")


#Key Market Metrics
st.subheader("Key Market Metrics (Latest Daily Candle)")
latest = df.iloc[-1]

col1, col2 = st.columns(2)
col1.metric("Current Price (USD)", f"{latest['close']:.2f}")
col2.metric("High (24h)", f"{latest['high']:.2f}")

col3, col4 = st.columns(2)
col3.metric("Low (24h)", f"{latest['low']:.2f}")
col4.metric("VWAP (24h)", f"{latest['vwap']:.2f}")

col5, col6 = st.columns(2)
col5.metric("24h Trading Volume (ETH)", f"{latest['volume']:.2f}")
col6.metric("Number of Trades (24h)", f"{latest['count']}")


st.markdown("---")


# ML Prediction


st.subheader("High Price Predictions for Tomorrow")

utc_now = datetime.datetime.now(timezone.utc)
formatted_date = utc_now.strftime("%b %d, %Y")
formatted_time = utc_now.strftime("%H:%M:%S")

st.metric(
    label="Current UTC time",
    value=formatted_date
)
st.markdown(formatted_time)


st.info("Click the button to get the predicted next-day high price for Ethereum (ETH).")

url = "https://at3-25106954-api.onrender.com/predict/eth"


if st.button("Predict Tomorrow"):
    with st.spinner("Fetching next-day prediction... (may take a few minutes if server is asleep)"):
        time.sleep(3)
        try:
            response = requests.get(url, timeout=1200) 
            response.raise_for_status()
            data = response.json()

            predicted_date = data.get("predicted_date", "N/A")
            date_obj = datetime.datetime.strptime(predicted_date, "%Y-%m-%d")
            formatted_date = date_obj.strftime("%b %d, %Y")  # "Nov 05, 2025"
            predicted_high = data.get("predicted_tomorrow_high", None)

            if predicted_high is not None:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Prediction Date", formatted_date)
                with col2:
                    st.metric("Predicted ETH High (USD)", f"${predicted_high:,.2f}")
            else:
                st.warning("Prediction data not available.")

        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching prediction: {e}")
