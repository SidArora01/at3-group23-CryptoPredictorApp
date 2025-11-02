import os
import requests
import pandas as pd
import altair as alt
import streamlit as st
from datetime import datetime, timezone,date
import plotly

# Page Setup 
st.set_page_config(page_title="Solana Dashboard", page_icon="🪙", layout="wide")

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



BASE_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(BASE_DIR) 


st.markdown('<div class="section-header"><h2>Solana Dashboard</h2><p>A high performance blockchain for decentralized apps</p></div>', unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    sol = os.path.join(APP_DIR, "assets", "solana.jpg")
    st.image(sol)


st.write("""
**Solana (SOL)** is a high-performance public blockchain that can process thousands of transactions per second
with minimal fees. This type of cryptocurrency is particularly popular in gaming, NFTs, and decentralized finance projects.
""")

st.markdown("---")

# Helper: Fetch CoinGecko OHLC 
@st.cache_data(ttl=600)
def get_sol_ohlc(days: int = 90):
    url = "https://api.coingecko.com/api/v3/coins/solana/ohlc"
    params = {"vs_currency": "usd", "days": days}
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        return df.sort_values("timestamp").reset_index(drop=True)
    except Exception as e:
        st.warning(f"Could not fetch OHLC data: {e}")
        return pd.DataFrame()


# Fetch both timeframes
df_3m = get_sol_ohlc(90)
df_1y = get_sol_ohlc(365)

# Function to create a Plotly candlestick
def plot_candlestick(df, title):
    import plotly.graph_objects as go

    if df.empty:
        st.warning("No data available for this period.")
        return

    fig = go.Figure(
        data=[
            go.Candlestick(
                x=df["timestamp"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                increasing_line_color="#2ecc71",  # green
                decreasing_line_color="#e74c3c",  # red
                name="Solana"
            )
        ]
    )

    fig.update_layout(
        title=title,
        xaxis_title="Date (UTC)",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
        template="plotly_white",
        height=420,
        margin=dict(l=40, r=40, t=60, b=40),
        font=dict(family="Arial", size=12, color="black"),
        title_font=dict(size=18, color="black", family="Arial"),
    )

    st.plotly_chart(fig, use_container_width=True)


# --- Header ---
st.markdown('<div class="section-header"><h2>Historical Trend</h2></div>', unsafe_allow_html=True)

st.write("Take a look at how Solana’s price has changed over time to get a feel for its market journey.")

st.markdown(
    """
    <div style='background-color:#e3f2fd; padding:10px 15px; border-radius:8px;'>
    <p style='color:#0d47a1; font-size:14px; margin:0;'>
    Price movements of <b>Solana</b> from CoinGecko. All times are in UTC.
    </p>
    </div>
    """,
    unsafe_allow_html=True
)

# --- Charts ---
st.subheader("Solana – Past 3 Months")
plot_candlestick(df_3m, "")

st.subheader("Solana – Past 1 Year")
plot_candlestick(df_1y, "")

st.markdown("---")

# Key Market Metrics
@st.cache_data(ttl=300)
def get_sol_metrics():
    """Fetch latest Solana market data from CoinGecko (cached for 5 minutes)."""
    url = "https://api.coingecko.com/api/v3/coins/solana"
    r = requests.get(url, timeout=20)
    r.raise_for_status()
    d = r.json()["market_data"]

    return {
        "price": d["current_price"]["usd"],
        "change_24h": d["price_change_percentage_24h"],
        "volume": d["total_volume"]["usd"],
        "market_cap": d["market_cap"]["usd"],
        "circ_supply": d.get("circulating_supply"),
        "last_updated": datetime.fromisoformat(d["last_updated"].replace("Z", "+00:00"))
    }

# Key Market Metrics Display Section 

st.markdown('<div class="section-header"><h2>Key Market Metrics</h2></div>', unsafe_allow_html=True)

st.write(
    "These live indicators show Solana’s overall market health, combining price, activity, and supply data to help you spot key market trends before generating predictions."
)

if st.button("Refresh Metrics"):
    st.cache_data.clear()

try:
    metrics = get_sol_metrics()

    # Helper: Format numbers automatically
    def fmt_value(val):
        if val >= 1_000_000_000:
            return f"${val / 1_000_000_000:,.2f} B"
        elif val >= 1_000_000:
            return f"${val / 1_000_000:,.2f} M"
        else:
            return f"${val:,.2f}"

    # Row 1: Spot Price + 24h Change
    col1, col2 = st.columns([1, 1])
    with col1:
        st.metric(
            "Spot Price (USD)",
            f"${metrics['price']:,.2f}",
            help="Current price of 1 SOL in US dollars."
        )

    with col2:
        delta_value = metrics["change_24h"]
        arrow = "▲" if delta_value > 0 else "▼" if delta_value < 0 else ""
        color = "green" if delta_value > 0 else "red" if delta_value < 0 else "white"
        formatted_change = f"{arrow} {abs(delta_value):.2f}%"
        st.markdown(
            f"**24h Change (USD)**  \n"
            f"<span style='font-size:24px; color:{color}; font-weight:700;'>{formatted_change}</span>",
            unsafe_allow_html=True,
            help="The percentage change in Solana’s price over the last 24 hours."
        )

    # Row 2: Volume + Market Cap 
    st.markdown("")
    col3, col4 = st.columns(2)
    col3.metric(
        "24h Volume (USD)",
        fmt_value(metrics["volume"]),
        help="Total value of all Solana transactions traded in the last 24 hours."
    )
    col4.metric(
        "Market Cap (USD)",
        fmt_value(metrics["market_cap"]),
        help="Total market value of all circulating SOL tokens (price × circulating supply)."
    )

    # Row 3: Circulating Supply + Market Health
    st.markdown("")
    col5, col6 = st.columns(2)
    col5.metric(
        "Circulating Supply",
        f"{metrics['circ_supply']/1_000_000:,.2f} M SOL",
        help="The number of SOL tokens currently available for trading and use in the market."
    )

    # Simple health index logic
    change = metrics["change_24h"]
    if change > 1:
        health = "Bullish"
        health_color = "green"
    elif change < -1:
        health = "Bearish"
        health_color = "red"
    else:
        health = "Stable"
        health_color = "white"

    # Market Health Index with tooltip + larger label
    with col6:
        st.metric(
            "Market Health Index",
            "",
            help="A simplified indicator describing the overall market mood — "
                 "‘Bullish’ if price trends strongly upward, ‘Bearish’ if downward, or ‘Stable’ if neutral."
        )
        st.markdown(
            f"<div style='font-size:28px; font-weight:700; color:{health_color}; margin-top:-10px;'>{health}</div>",
            unsafe_allow_html=True,
        )
    st.caption(f"Last updated: {metrics['last_updated'].strftime('%Y-%m-%d %H:%M:%S UTC')}")

except Exception as e:
    st.warning(f"Could not fetch Solana metrics: {e}")

st.markdown("---")

# Machine Learning Prediction

st.markdown('<div class="section-header"><h2>Prediction of Tomorrows High Price</h2><p></p></div>', unsafe_allow_html=True)


st.write("""
Predict **Solana’s high price prediction for tomorrow** using the latest live market data 
automatically pulled from **CoinGecko**. Click the button below to generate the prediction.
""")

predict_url = "https://at3-group23-solana-api.onrender.com/predict/SOL"

# Big centered button
col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    predict = st.button("Predict Tomorrow's High Price", use_container_width=True)

# Prediction logic
if predict:
    with st.spinner("Fetching latest data and predicting..."):
        try:
            r = requests.get(predict_url, timeout=25)
            if r.status_code == 200:
                data = r.json()

                #Compact vertical spacing for immediate result
                st.write("")  # small space only
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    st.markdown(
                        f"<h1 style='text-align:center; font-size:56px; font-weight:700; margin-top:10px; margin-bottom:4px;'>"
                        f"${data['predicted_next_day_high']:,.2f}</h1>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(
                        f"<p style='text-align:center; font-size:15px; color:gray; margin-top:0;'>"
                        f"Prediction generated as of {datetime.fromisoformat(data['as_of']).strftime('%Y-%m-%d %H:%M:%S UTC')}"
                        f"</p>",
                        unsafe_allow_html=True,
                    )

                with st.expander("View Model Inputs"):
                    st.json(data["inputs_used"])

            else:
                st.error(f"API Error {r.status_code}: {r.text[:300]}")
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")