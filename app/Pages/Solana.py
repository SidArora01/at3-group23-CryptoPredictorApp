import os
import requests
import pandas as pd
import altair as alt
import streamlit as st
from datetime import datetime, timezone

# Page Setup 
st.set_page_config(page_title="Solana Dashboard", page_icon="🪙", layout="centered")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("Solana (SOL)")
    st.image("assets/solana.jpg")

st.subheader("A high performance blockchain for decentralized apps")
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

df_ohlc = get_sol_ohlc(90)
if not df_ohlc.empty:
    st.header("Historical Trends")
    st.write("Take a look at how Solana’s price has changed over time to get a feel for its market journey.")

    # --- Info box ---
    st.markdown(
        """
        <div style='background-color:#e3f2fd; padding:10px 15px; border-radius:8px;'>
        <p style='color:#0d47a1; font-size:14px; margin:0;'>
        💡 Price movements of <b>Solana</b> over the past ~90 days (from CoinGecko). 
        All times are in UTC.
        </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    df_ohlc["date"] = df_ohlc["timestamp"].dt.date

    base = alt.Chart(df_ohlc).encode(
        x=alt.X(
            "date:T",
            title="Date (UTC)",
            axis=alt.Axis(
                labelAngle=-35,
                labelFontSize=11,
                titleFontSize=12,
                labelColor="black",
                titleColor="black",
                grid=False
            )
        )
    )

    # Line Chart
    line = (
        base.transform_fold(
            ["open", "high", "low", "close"], as_=["Type", "Price (USD)"]
        )
        .mark_line(point=alt.OverlayMarkDef(size=25, filled=True, fillOpacity=0.25), strokeWidth=2.2)
        .encode(
            y=alt.Y(
                "Price (USD):Q",
                title="Price (USD)",
                axis=alt.Axis(
                    labelFontSize=11,
                    titleFontSize=12,
                    labelColor="black",
                    titleColor="black",
                    gridColor="#e0e0e0"
                ),
                scale=alt.Scale(
                    domain=[
                        df_ohlc[["open", "high", "low", "close"]].min().min() - 10,
                        df_ohlc[["open", "high", "low", "close"]].max().max() + 10,
                    ]
                )
            ),
            color=alt.Color(
                "Type:N",
                title=None,
                scale=alt.Scale(
                    domain=["open", "high", "low", "close"],
                    range=["#007bff", "#2ecc71", "#e74c3c", "#f39c12"],  # blue, green, red, gold
                ),
                legend=alt.Legend(
                    orient="right",
                    labelFontSize=12,
                    labelColor="black",
                    symbolSize=130,
                ),
            ),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("Type:N", title="Metric"),
                alt.Tooltip("Price (USD):Q", title="Value", format="$.2f"),
            ],
        )
    )

    chart = line.properties(
        height=420,
        width="container",
        background="white"
    ).configure_view(
        strokeOpacity=0
    ).configure_axis(
        labelColor="black",
        titleColor="black",
    )

    st.altair_chart(chart.interactive(), use_container_width=True)

else:
    st.warning("Unable to load Solana price data for historical trends.")

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
st.header("Key Market Metrics")
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

# Prediction Input
st.header("Machine Learning Prediction")

st.write("""
Enter Solana’s recent market data below, or keep everything blank (0) and the FastAPI model will automatically pull live data from CoinGecko for prediction.
""")

predict_url = "https://at3-group23-solana-api.onrender.com/predict/SOL"

with st.form("sol_predict_form"):
    # --- Easier numeric navigation (practical step sizes and defaults) ---
    close = st.number_input(
        "Closing price (USD)",
        min_value=0.0, max_value=500.0,   # ✅ allow 0.0
        step=1.0, value=0.0, format="%.2f",
        help="End-of-day SOL price. Usually around $150–$200."
    )
    open_ = st.number_input(
        "Opening price (USD)",
        min_value=0.0, max_value=500.0,   # ✅ allow 0.0
        step=1.0, value=0.0, format="%.2f",
        help="Start-of-day SOL price. Usually around $150–$200."
    )
    low = st.number_input(
        "Lowest price (USD)",
        min_value=0.0, max_value=500.0,   # ✅ allow 0.0
        step=1.0, value=0.0, format="%.2f",
        help="Lowest SOL price of the day. Typically $140–$180."
    )
    volume = st.number_input(
        "Trading volume (USD)",
        min_value=0.0, max_value=10_000_000_000.0,
        step=100_000_000.0, value=0.0, format="%.0f",
        help="Total USD value of SOL traded during the day (around 3 billion)."
    )
    marketCap = st.number_input(
        "Market capitalization (USD)",
        min_value=0.0, max_value=200_000_000_000.0,
        step=5_000_000_000.0, value=0.0, format="%.0f",
        help="Total market value of all circulating SOL tokens (around 100 billion)."
    )
    price_range = st.number_input(
        "Price range (highest price - lowest price)",
        min_value=0.0, max_value=100.0,
        step=1.0, value=0.0, format="%.2f",
        help="Difference between highest and lowest SOL price during the day (around 5–15)."
    )
    volume_per_marketcap = st.number_input(
        "Volume / MarketCap ratio",
        min_value=0.0, max_value=0.2,
        step=0.005, value=0.0, format="%.4f",
        help="Ratio of trading volume to market capitalization (usually 0.03–0.05)."
    )

    submitted = st.form_submit_button("Predict Next-Day High")

# Prediction Logic
if submitted:
    # Only send fields with non-zero user-specified values
    params = {
        "close": close if close > 0 else None,
        "open": open_ if open_ > 0 else None,
        "low": low if low > 0 else None,
        "volume": volume if volume > 0 else None,
        "marketCap": marketCap if marketCap > 0 else None,
        "price_range": price_range if price_range > 0 else None,
        "volume_per_marketcap": volume_per_marketcap if volume_per_marketcap > 0 else None,
    }
    params = {k: v for k, v in params.items() if v is not None}

    with st.spinner("Fetching prediction from Solana API..."):
        try:
            r = requests.get(predict_url, params=params, timeout=25)
            if r.status_code == 200:
                data = r.json()
                st.success("Prediction successful!")

                # Centered and larger predicted value
                st.markdown(
                    f"""
                    <div style="text-align:center; margin-top:1rem;">
                        <p style="font-size:18px; font-weight:600; margin-bottom:0;">Predicted Next-Day High (USD)</p>
                        <p style="font-size:42px; font-weight:700; margin-top:0; color:#4CAF50;">
                            ${data['predicted_next_day_high']:,.2f}
                        </p>
                        <p style="font-size:13px; color:gray;">
                            As of {datetime.fromisoformat(data['as_of']).strftime('%Y-%m-%d %H:%M:%S UTC')}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                with st.expander("Input Features Used"):
                    st.json(data["inputs_used"])

            else:
                st.error(f"API Error {r.status_code}: {r.text[:300]}")
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")

st.markdown("---")
st.caption("Tip: Leaving all fields blank will let the model fetch real-time CoinGecko data.")
