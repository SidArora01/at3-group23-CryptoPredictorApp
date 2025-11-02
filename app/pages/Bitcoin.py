# Bitcoin
# --- Imports (clean and organized) ---

# Standard library
import os
import time
from datetime import datetime, timezone

# Third-party libraries
import numpy as np
import pandas as pd
import requests
import altair as alt
import streamlit as st

# --- Page config ---

st.set_page_config(page_title="Bitcoin Dashboard", page_icon="₿", layout="centered")

os.environ["SERVICE_BTC_PREDICT_URL"] = "https://btc-high-api.onrender.com/predict/bitcoin"

# %%
# Purpose: three-column header and hero image (use repo-relative path)

BASE_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(BASE_DIR)  

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.title("Bitcoin (BTC)")
    bit = os.path.join(APP_DIR, "assets", "bitcoin.jpg")
    st.image(bit)


# %%
# Purpose: short context about BTC

st.subheader("The world’s first decentralized digital currency")
st.write("""
**Bitcoin (BTC)** was created in 2009 by the pseudonymous developer *Satoshi Nakamoto*.
It remains the most valuable and widely recognized cryptocurrency, often described as
**digital gold** due to its limited supply of 21 million coins.
""")

# --- Current UTC time and explanation ---

# Get current UTC time and date
utc_now = datetime.now(timezone.utc)
utc_time = utc_now.strftime("%H:%M:%S")
utc_date = utc_now.strftime("%Y-%m-%d")

# Display clock and info
st.markdown(f"### 🕒 Current UTC Time:  {utc_time}")
st.markdown(f"**Date:** {utc_date}")
if st.button("🔄 Refresh Time"):
    st.rerun()

st.caption(
    "All timestamps and data on this dashboard are displayed in **Coordinated Universal Time (UTC)** "
    "to match the format provided by the CoinGecko API."
)

st.markdown("---")


# %%
# --- Step 1: Fetch and prepare CoinGecko OHLC data (90 days) ---

@st.cache_data(ttl=600)  # cache for 10 minutes
def get_coingecko_ohlc(days: int = 90):
    """
    Fetch daily OHLC data for Bitcoin from CoinGecko.
    Returns a pandas DataFrame with UTC dates and open, high, low, close.
    """
    url = f"https://api.coingecko.com/api/v3/coins/bitcoin/ohlc"
    params = {"vs_currency": "usd", "days": days}

    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()
        # Convert to DataFrame
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
        # Convert UNIX ms → datetime UTC
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    except Exception as e:
        st.warning(f"⚠️ Failed to fetch OHLC data: {e}")
        return pd.DataFrame()

# Fetch and preview
df_ohlc = get_coingecko_ohlc(90)

if df_ohlc.empty:
    st.warning("⚠️ Failed to fetch OHLC data or dataset is empty; stopping app.")
    st.stop()


# %%
# --- Step 2: Fetch and merge Volume & Market Cap data (CoinGecko market_chart) ---

@st.cache_data(ttl=600)
def get_coingecko_market_chart(days: int = 90):
    """
    Fetch daily market data for Bitcoin from CoinGecko.
    Returns a DataFrame with UTC timestamps, volume, and market_cap.
    """
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": days, "interval": "daily"}

    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        data = r.json()

        # Convert nested lists to DataFrames
        df_vol = pd.DataFrame(data["total_volumes"], columns=["timestamp", "volume"])
        df_cap = pd.DataFrame(data["market_caps"], columns=["timestamp", "market_cap"])

        # Merge on timestamp (both are UNIX ms UTC)
        df_vol["timestamp"] = pd.to_datetime(df_vol["timestamp"], unit="ms", utc=True)
        df_cap["timestamp"] = pd.to_datetime(df_cap["timestamp"], unit="ms", utc=True)
        df = pd.merge(df_vol, df_cap, on="timestamp", how="outer").sort_values("timestamp")

        return df.reset_index(drop=True)

    except Exception as e:
        st.warning(f"⚠️ Failed to fetch volume/market cap data: {e}")
        return pd.DataFrame()

# Fetch and merge with df_ohlc
df_market = get_coingecko_market_chart(90)

if not df_market.empty and not df_ohlc.empty:
    # Merge OHLC with market data on UTC timestamp
    df_full = pd.merge(df_ohlc, df_market, on="timestamp", how="left")
    
# Now df_full contains: timestamp, open, high, low, close, volume, market_cap

# %%
# --- Step 3: Historical Trends with better zoom, tooltips & styling ---
# Purpose: build two interactive charts:
#  (A) 4-line chart for open/high/low/close with tighter y-range + last-3 markers
#  (B) Split high–low range bars (low→close, close→high) with a close marker, no empty gaps


# Guard: ensure merged data is available
if 'df_full' in locals() and not df_full.empty:

    # Prep a plotting frame
    df_plot = df_full.copy()
    df_plot["date"] = df_plot["timestamp"].dt.date  # datetime -> date for clean axis labels

    st.header("Historical Trends")
    st.info("Price movements of Bitcoin (Open, High, Low, Close) over the past ~90 days (CoinGecko OHLC replies every 4 days data for 90 days query). All times in UTC.")

    # -------- (A) LINE CHART: 4 series + tighter y-range + last-3 markers --------

    recent = df_plot.tail(12)  # ~last 12 candles
    y_min = float(recent[["open", "high", "low", "close"]].min().min()) * 0.98
    y_max = float(recent[["open", "high", "low", "close"]].max().max()) * 1.02

    base = (
        alt.Chart(df_plot)
        .encode(x=alt.X("date:T", title="Date (UTC)"))
        .properties(width=900, height=500)
    )

    line_chart = (
        base.transform_fold(
            ["open", "high", "low", "close"], 
            as_=["variable", "value"]
        )
        .mark_line(strokeWidth=2)
        .encode(
            y=alt.Y("value:Q", title="Price (USD)", scale=alt.Scale(domain=[y_min, y_max])),
            color=alt.Color("variable:N", title="Series"),
            tooltip=[
                alt.Tooltip("date:T", title="Date (UTC)"),
                alt.Tooltip("variable:N", title="Series"),
                alt.Tooltip("value:Q", title="Price", format=",.2f"),
            ],
        )
        .properties(title="Bitcoin OHLC – Last ~90 Days (4-day candles)")
    )

    # Highlight the last 3 rows (use close markers + labels)
    last3 = df_plot.tail(3)
    markers = (
        alt.Chart(last3)
        .mark_point(size=80, filled=True)
        .encode(
            x="date:T",
            y="close:Q",
            tooltip=[alt.Tooltip("date:T"), alt.Tooltip("close:Q", title="Close", format=",.2f")],
        )
    )
    labels = (
        alt.Chart(last3)
        .mark_text(align="left", dx=5, dy=-5)
        .encode(x="date:T", y="close:Q", text=alt.Text("close:Q", format=",.0f"))
    )

    st.altair_chart(
        (line_chart + markers + labels).configure_axis(grid=True).interactive(),  # interactive = zoom/pan
        use_container_width=True
    )

    # -------- (B) RANGE BAR: split low→close and close→high, remove empty day gaps --------

    # Use ordinal x to avoid gaps between non-daily candles

    df_plot2 = df_plot.copy()
    df_plot2["date_str"] = df_plot2["timestamp"].dt.strftime("%Y-%m-%d")

    # Y zoom for the range plot (based on recent window)
    y_min2 = float(recent["low"].min()) * 0.98
    y_max2 = float(recent["high"].max()) * 1.02

    low_to_close = (
        alt.Chart(df_plot2)
        .mark_bar(size=8, opacity=0.8)
        .encode(
            x=alt.X("date_str:O", title="Date (UTC)"),
            y=alt.Y("low:Q", title="Low ↔ High", scale=alt.Scale(domain=[y_min2, y_max2])),
            y2="close:Q",
            color=alt.value("#4C78A8"),  # segment color 1
            tooltip=[
                alt.Tooltip("date_str:O", title="Date (UTC)"),
                alt.Tooltip("low:Q", title="Low", format=",.2f"),
                alt.Tooltip("close:Q", title="Close", format=",.2f"),
                alt.Tooltip("high:Q", title="High", format=",.2f"),
            ],
        )
        .properties(width=900, height=500, title="High–Low Range with Close Marker (4-day candles)")
    )

    close_to_high = (
        alt.Chart(df_plot2)
        .mark_bar(size=8, opacity=0.8)
        .encode(
            x="date_str:O",
            y="close:Q",
            y2="high:Q",
            color=alt.value("#F58518"),  # segment color 2
        )
    )

    close_points = (
        alt.Chart(df_plot2)
        .mark_point(size=55, filled=True)
        .encode(x="date_str:O", y="close:Q")
    )

    st.altair_chart(
        (low_to_close + close_to_high + close_points).configure_axis(grid=True).interactive(),
        use_container_width=True
    )

else:
    st.warning("⚠️ Historical data not available for plotting.")


# %%
# --- Step 4: Key Market Metrics ---
#
# Purpose:
#   A) 24h KPIs (spot, 24h change %, 24h volume, market cap)
#   B) Last 10 days daily panel (close, volume, market cap, returns)
#      - Table shows volume/market_cap in **millions** with comma separators (string view)
#      - Charts keep numeric values (millions) for proper scaling

# ---------- A) 24h metrics (CoinGecko simple/price) ----------

@st.cache_data(ttl=300)  # refresh every 5 minutes
def get_coingecko_24h():
    """Return dict with price, 24h change %, 24h volume, market cap, last_updated_at (UTC)."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": "bitcoin",
        "vs_currencies": "usd",
        "include_24hr_change": "true",
        "include_24hr_vol": "true",
        "include_market_cap": "true",
        "include_last_updated_at": "true",
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    d = r.json()["bitcoin"]
    return {
        "price": d.get("usd"),
        "change_24h_pct": d.get("usd_24h_change"),
        "volume_24h": d.get("usd_24h_vol"),
        "market_cap": d.get("usd_market_cap"),
        "last_updated_at": datetime.fromtimestamp(d.get("last_updated_at", 0), tz=timezone.utc),
    }

# ---------- B) Last 10 daily (CoinGecko market_chart) ----------

@st.cache_data(ttl=600)
def get_coingecko_daily_10():
    """
    Fetch last 10 daily closes, volumes, and market caps for BTC.
    Returns a tidy DataFrame with date (UTC), close, volume, market_cap and daily return %.
    """
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
    params = {"vs_currency": "usd", "days": 10, "interval": "daily"}
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()

    # Build frames
    df_p = pd.DataFrame(data["prices"], columns=["ts", "close"])
    df_v = pd.DataFrame(data["total_volumes"], columns=["ts", "volume"])
    df_mc = pd.DataFrame(data["market_caps"], columns=["ts", "market_cap"])

    # Convert time and merge
    for df in (df_p, df_v, df_mc):
        df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
    df = (
        df_p.merge(df_v, on="ts")
            .merge(df_mc, on="ts")
            .sort_values("ts")
            .reset_index(drop=True)
    )

    # Derive date + daily return %
    df["date"] = df["ts"].dt.date
    df["ret_pct"] = df["close"].pct_change() * 100.0
    return df[["date", "close", "volume", "market_cap", "ret_pct"]]


# ---------------- Render ----------------

# 24h KPIs
try:
    m24 = get_coingecko_24h()
    st.header("Key Market Metrics")

    c1, c2 = st.columns(2)
    c1.metric("Spot Price (USD)", f"${m24['price']:,.2f}")
    c2.metric("24h Change", f"{m24['change_24h_pct']:.3f}%")
    c3, c4 = st.columns(2)
    c3.metric("24h Volume (USD)", f"${m24['volume_24h']/1000000:,.2f} M")
    c4.metric("Market Cap (USD)", f"${m24['market_cap']/1000000:,.2f} M")
    st.caption(f"Last updated: {m24['last_updated_at'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
except Exception as e:
    st.warning(f"⚠️ Could not fetch 24h stats: {e}")

# 10-day panel
try:
    df10 = get_coingecko_daily_10()
    if not df10.empty:
        # Metrics
        avg_vol_10d = df10["volume"].mean()
        vol_10d = df10["ret_pct"].std(ddof=1)  # volatility ≈ stdev of daily returns

        st.subheader("Last 10 Days (Daily)")
        mc1, mc2 = st.columns(2)
        mc1.metric("10-Day Avg Volume", f"${avg_vol_10d/1_000_000:,.2f} M")
        mc2.metric("10-Day Volatility (σ of returns)", f"{vol_10d:.2f}%")


        # ---- Table: show volume & market_cap in millions with commas (string view) ----

        df10_disp = df10.copy()
        df10_disp["volume_M"] = df10_disp["volume"] / 1_000_000
        df10_disp["market_cap_M"] = df10_disp["market_cap"] / 1_000_000

        df10_tbl = pd.DataFrame({
            "date": df10_disp["date"],
            "close": df10_disp["close"].map(lambda x: f"{x:,.4f}"),
            "volume (M USD)": df10_disp["volume_M"].map(lambda x: f"{x:,.2f}"),
            "market_cap (M USD)": df10_disp["market_cap_M"].map(lambda x: f"{x:,.2f}"),
            "return_%": df10_disp["ret_pct"].map(lambda x: "" if pd.isna(x) else f"{x:.2f}"),
        })

        st.dataframe(df10_tbl, hide_index=True, use_container_width=True)


        # ---- Charts: keep numeric frame (millions) ----

        left, right = st.columns(2)

        close_chart = (
            alt.Chart(df10_disp)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date (UTC)"),
                y=alt.Y("close:Q", title="Close (USD)"),
                tooltip=[
                    alt.Tooltip("date:T", title="Date"),
                    alt.Tooltip("close:Q", title="Close", format=",.2f"),
                    alt.Tooltip("ret_pct:Q", title="Return %", format=".2f"),
                ],
            )
            .properties(height=260)
            .interactive()
        )
        left.altair_chart(close_chart, use_container_width=True)

        vol_chart = (
            alt.Chart(df10_disp)
            .mark_bar()
            .encode(
                x=alt.X("date:T", title="Date (UTC)"),
                y=alt.Y("volume_M:Q", title="Volume (M USD)"),
                tooltip=[
                    alt.Tooltip("date:T", title="Date"),
                    alt.Tooltip("volume_M:Q", title="Volume (M USD)", format=",.2f"),
                ],
            )
            .properties(height=260)
            .interactive()
        )
        right.altair_chart(vol_chart, use_container_width=True)

    else:
        st.warning("⚠️ No 10-day daily data available.")
except Exception as e:
    st.warning(f"⚠️ Could not fetch 10-day data: {e}")



# %%
# Purpose: placeholder for next-day HIGH prediction

st.header("Machine Learning Predictions")
st.info("This section will display the Next-Day High Price prediction using ElasticNet v1 model. You only need to provide the 7 RAW input features as described next:")


# %%
# # Test API connection and endpoints

# # --- API connection check (robust URL handling) ---

# import os, requests, streamlit as st

# st.header("Machine Learning Predictions")
# st.subheader("API Connection Check")

# api_input = os.getenv("SERVICE_BTC_PREDICT_URL")
# if not api_input:
#     try:
#         api_input = st.secrets["SERVICE_BTC_PREDICT_URL"]
#     except Exception:
#         api_input = None

# if not api_input:
#     st.warning("Set SERVICE_BTC_PREDICT_URL in env or .streamlit/secrets.toml")
#     st.stop()

# # Normalize: accept base or full predict URL
# api_input = api_input.rstrip("/")
# if "/predict/" in api_input:
#     base_url = api_input.split("/predict")[0]
#     predict_url = api_input
# else:
#     base_url = api_input
#     predict_url = f"{base_url}/predict/bitcoin"

# root_url = f"{base_url}/"
# health_url = f"{base_url}/health/"

# st.caption(f"Using base: `{base_url}`")
# st.caption(f"Predict endpoint: `{predict_url}`")

# try:
#     r_root = requests.get(root_url, timeout=15)
#     r_health = requests.get(health_url, timeout=15)
#     st.success("✅ FastAPI reachable.")
#     st.write("**Root (/):**");   st.json(r_root.json())
#     st.write("**Health (/health/):**"); st.json(r_health.json())
# except Exception as e:
#     st.error(f"❌ Unable to reach FastAPI. Details: {e}")

# %%
# --- Step 5: ML Prediction input modes (Yesterday / Today / Manual) ---
# Purpose:
#   Provide 3 ways to prepare the 7 RAW inputs required by the FastAPI endpoint.
#   Display inputs with 2 decimals in the boxes, plus a comma-formatted preview underneath.


st.subheader("Next-Day HIGH Prediction — Input Modes")
st.markdown(
    """
Choose an input mode. All timestamps and data are UTC.<br><br>
**Note:** CoinGecko `/ohlc` uses ~4-day “candles” for long lookbacks. We pre-fill **open** (for `body`) from that source.<br><br>
Daily **close/volume** come from `market_chart` (last 10 days). You can edit any value below.<br><br>
**Manual (What-If)** starts **pre-filled with Today (partial)** values so you can tweak scenarios quickly.
    """,
    unsafe_allow_html=True,
)

# ---- Helpers ---------------------------------------------------------------

def safe_get(series, idx, default=np.nan):
    """Return series.iloc[idx] if possible, else default."""
    try:
        return float(series.iloc[idx])
    except Exception:
        return float(default)

def build_inputs_from_indices(df_daily: pd.DataFrame, df_ohlc4d: pd.DataFrame,
                              idx_today_daily: int, idx_open_ohlc: int):
    """
    Build the 7 RAW inputs using:
      - df_daily: daily close & volume (10 days)
      - df_ohlc4d: 4-day OHLC to get 'open' for 'body'
      - idx_today_daily: index for 'today' (daily)
      - idx_open_ohlc: index in 4-day OHLC that best aligns with 'today' (approx; user can edit)
    Returns a dict with keys expected by the API plus _open_t for transparency.
    """
    
    # Daily features (close & volume) — from df_daily (10-day daily series)
    close_t   = safe_get(df_daily["close"],  idx_today_daily)
    volume_t  = safe_get(df_daily["volume"], idx_today_daily)
    close_lag1 = safe_get(df_daily["close"],  idx_today_daily - 1)
    close_lag3 = safe_get(df_daily["close"],  idx_today_daily - 3)
    close_lag7 = safe_get(df_daily["close"],  idx_today_daily - 7)

    
    # Open for 'body' — from 4-day OHLC (approximation; user can edit)
    open_t = safe_get(df_ohlc4d["open"], idx_open_ohlc)
    body   = float(close_t - open_t) if np.isfinite(open_t) and np.isfinite(close_t) else np.nan

    # Year (UTC)
    timeHigh_year = datetime.now(timezone.utc).year

    return {
        "close_lag1": close_lag1,
        "close_lag3": close_lag3,
        "close_lag7": close_lag7,
        "body": body,
        "timeHigh_year": timeHigh_year,
        "close": close_t,
        "volume": volume_t,
        "_open_t": open_t,  # exposed so users can see/tweak 'body'
    }

def num_input(label: str, value: float, key: str | None = None):
    """
    Render a numeric input with 2 decimals and a small comma-formatted preview below.
    Returns the float value.
    """
    v = st.number_input(label, value=float(value), format="%.2f", key=key)
    st.caption(f"↳ {v:,.2f}")
    return v

# ---- Guard: ensure data exists --------------------------------------------

if ('df10' not in locals()) or df10.empty or ('df_full' not in locals()) or df_full.empty:
    st.warning("⚠️ Not enough data to pre-fill inputs. Ensure both daily (`df10`) and OHLC (`df_full`) fetches succeeded.")
else:
    # Indices for daily series (df10): last row = 'today (partial)', previous row = 'yesterday (complete)'
    idx_today_daily = len(df10) - 1
    idx_yday_daily  = len(df10) - 2

    # Indices for 4-day OHLC (df_full): last row is most recent candle
    idx_today_ohlc4d = len(df_full) - 1
    idx_yday_ohlc4d  = len(df_full) - 2

    # Pre-build the three presets
    preset_yday  = build_inputs_from_indices(df10, df_full, idx_yday_daily,  idx_yday_ohlc4d)
    preset_today = build_inputs_from_indices(df10, df_full, idx_today_daily, idx_today_ohlc4d)
    preset_man   = preset_today.copy()  # Manual starts from today's (partial) values

    # --- UI: tabs for the three modes --------------------------------------
    t1, t2, t3 = st.tabs([
        "📅 Yesterday → Predict Today (complete)",
        "🟡 Today (partial) → Predict Tomorrow (estimate)",
        "✍️ Manual (What-If)",
    ])

    # ===== Tab 1: Yesterday (complete day) =====
    with t1:
        st.caption("Uses yesterday’s completed daily data. Best for a clean, reproducible prediction.")
        c1, c2, c3 = st.columns(3)
        with c1:
            close_lag1_t1 = num_input("close_lag1", preset_yday["close_lag1"])
            close_lag3_t1 = num_input("close_lag3", preset_yday["close_lag3"])
            close_lag7_t1 = num_input("close_lag7", preset_yday["close_lag7"])
        with c2:
            open_t1 = num_input("open (for body)", preset_yday["_open_t"])
            close_t1 = num_input("close", preset_yday["close"])
            body_t1  = num_input("body = close - open", preset_yday["body"])
        with c3:
            volume_t1 = num_input("volume", preset_yday["volume"])
            timeHigh_year_t1 = st.number_input("timeHigh_year", value=int(preset_yday["timeHigh_year"]), step=1, format="%d")
            st.caption(f"↳ {int(timeHigh_year_t1)}")

        # Persist inputs for the next step (prediction call)
        st.session_state["inputs_yday"] = {
            "close_lag1": close_lag1_t1,
            "close_lag3": close_lag3_t1,
            "close_lag7": close_lag7_t1,
            "body": body_t1,
            "timeHigh_year": int(timeHigh_year_t1),
            "close": close_t1,
            "volume": volume_t1,
        }

    # ===== Tab 2: Today (partial) =====
    with t2:
        st.caption("Uses today’s **partial** data (intraday). Values may change before the day closes.")
        c1, c2, c3 = st.columns(3)
        with c1:
            close_lag1_t2 = num_input("close_lag1", preset_today["close_lag1"], key="t2_l1")
            close_lag3_t2 = num_input("close_lag3", preset_today["close_lag3"], key="t2_l3")
            close_lag7_t2 = num_input("close_lag7", preset_today["close_lag7"], key="t2_l7")
        with c2:
            open_t2 = num_input("open (for body)", preset_today["_open_t"], key="t2_open")
            close_t2 = num_input("close", preset_today["close"], key="t2_close")
            body_t2  = num_input("body = close - open", preset_today["body"], key="t2_body")
        with c3:
            volume_t2 = num_input("volume", preset_today["volume"], key="t2_vol")
            timeHigh_year_t2 = st.number_input("timeHigh_year", value=int(preset_today["timeHigh_year"]), step=1, format="%d", key="t2_year")
            st.caption(f"↳ {int(timeHigh_year_t2)}")

        st.session_state["inputs_today"] = {
            "close_lag1": close_lag1_t2,
            "close_lag3": close_lag3_t2,
            "close_lag7": close_lag7_t2,
            "body": body_t2,
            "timeHigh_year": int(timeHigh_year_t2),
            "close": close_t2,
            "volume": volume_t2,
        }

    # ===== Tab 3: Manual (What-If) =====
    with t3:
        st.caption("Starts pre-filled with Today (partial) values. Edit freely to test hypothetical scenarios.")
        c1, c2, c3 = st.columns(3)
        with c1:
            close_lag1_m = num_input("close_lag1", preset_man["close_lag1"], key="m_l1")
            close_lag3_m = num_input("close_lag3", preset_man["close_lag3"], key="m_l3")
            close_lag7_m = num_input("close_lag7", preset_man["close_lag7"], key="m_l7")
        with c2:
            open_m = num_input("open (for body)", preset_man["_open_t"], key="m_open")
            close_m = num_input("close", preset_man["close"], key="m_close")
            body_m  = num_input("body = close - open", preset_man["body"], key="m_body")
        with c3:
            volume_m = num_input("volume", preset_man["volume"], key="m_vol")
            timeHigh_year_m = st.number_input("timeHigh_year", value=int(preset_man["timeHigh_year"]), step=1, format="%d", key="m_year")
            st.caption(f"↳ {int(timeHigh_year_m)}")

        st.session_state["inputs_manual"] = {
            "close_lag1": close_lag1_m,
            "close_lag3": close_lag3_m,
            "close_lag7": close_lag7_m,
            "body": body_m,
            "timeHigh_year": int(timeHigh_year_m),
            "close": close_m,
            "volume": volume_m,
        }

    st.info("Inputs are prepared. In the next step we’ll add the **Predict** buttons that call FastAPI using the values above.")


# %%
# --- Step 6: Run Prediction Panels + History ---
#
#  Purpose
#   • Resolve FastAPI predict URL (accept base or full /predict/bitcoin)
#   • Helpers: API call with retry + current BTC spot fetch
#   • Three panels (Yesterday / Today / Manual) – each keeps its last result visible
#   • Fix “double render on click” by returning early after drawing fresh results
#   • Append every run to a Prediction History section

# --------------------------- 1) Resolve predict URL ---------------------------
api_input = os.getenv("SERVICE_BTC_PREDICT_URL") or st.secrets.get("SERVICE_BTC_PREDICT_URL", None)
predict_url = None
if api_input:
    api_input = api_input.rstrip("/")
    predict_url = api_input if "/predict/" in api_input else f"{api_input}/predict/bitcoin"

# ------------------------------- 2) Helpers -----------------------------------
def call_predict(url: str, payload: dict, retries: int = 1, timeout: int = 20):
    """
    Call GET {url} with params=payload. Retry once for transient 5xx/cold starts.
    Returns (ok: bool, data_or_error: dict|str)
    """
    try:
        r = requests.get(url, params=payload, timeout=timeout)
        if r.status_code == 200:
            return True, r.json()
        if retries > 0 and r.status_code in (502, 503, 504, 524):
            time.sleep(2)
            r = requests.get(url, params=payload, timeout=timeout)
            if r.status_code == 200:
                return True, r.json()
        return False, f"HTTP {r.status_code}: {r.text[:500]}"
    except Exception as e:
        if retries > 0:
            time.sleep(2)
            try:
                r = requests.get(url, params=payload, timeout=timeout)
                if r.status_code == 200:
                    return True, r.json()
                return False, f"HTTP {r.status_code}: {r.text[:500]}"
            except Exception as e2:
                return False, f"{type(e2).__name__}: {e2}"
        return False, f"{type(e).__name__}: {e}"

def get_spot_price_usd():
    """Return current BTC/USD spot (reuse cached 24h dict if available; else quick fetch)."""
    try:
        if "m24" in globals() and isinstance(m24, dict) and "price" in m24:
            return float(m24["price"])
        r = requests.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd"},
            timeout=15,
        )
        r.raise_for_status()
        return float(r.json()["bitcoin"]["usd"])
    except Exception:
        return float("nan")

def render_metrics_two_rows(pred_value: float, spot: float):
    """Two-row layout to avoid truncation: (Pred/Current) then (Δ USD / Δ %)."""
    # Row 1
    r1c1, r1c2 = st.columns(2)
    r1c1.metric("Predicted High (Next Day)", f"${pred_value:,.2f}")
    r1c2.metric("Current Price (USD)", f"${spot:,.2f}")
    # Row 2
    r2c1, r2c2 = st.columns(2)
    if spot == spot:  # not NaN
        delta = pred_value - spot
        pct = (delta / spot) * 100.0 if spot else float("nan")
        r2c1.metric("Δ vs Current (USD)", f"${delta:,.2f}")
        r2c2.metric("Δ vs Current (%)", f"{pct:.2f}%")
        return delta, pct
    else:
        r2c1.metric("Δ vs Current (USD)", "N/A")
        r2c2.metric("Δ vs Current (%)", "N/A")
        return None, None

# -------------------------- 3) Session state init -----------------------------
if "pred_history" not in st.session_state:
    st.session_state["pred_history"] = []  # list of dicts in click order
if "panel_results" not in st.session_state:
    st.session_state["panel_results"] = {}  # {mode_title: last_result_dict}

# ------------------------------- 4) UI Panels --------------------------------
st.subheader("Run Prediction")

def panel(mode_title: str, payload_key: str, disclaimer: str | None = None):
    """
    One panel = title + (optional) disclaimer + button.
    • On click: call API, draw fresh results, save to session, append to history, RETURN EARLY.
    • On normal rerun: render last saved result once (no duplicates).
    """
    st.markdown("----")
    st.markdown(f"### {mode_title}")
    if disclaimer:
        st.caption(disclaimer)

    payload = st.session_state.get(payload_key)
    if not payload:
        st.warning(f"Missing inputs for **{mode_title}**.")
        return

    clicked = st.button(f"🔮 Predict ({mode_title})", use_container_width=True, key=f"btn_{payload_key}")

    # --- Case A: button clicked → run + render fresh, then return (avoid double) ---
    if clicked:
        if not predict_url:
            st.error("SERVICE_BTC_PREDICT_URL is not set.")
            return
        ok, data = call_predict(predict_url, payload)
        if not ok:
            st.error(f"Prediction failed: {data}")
            return

        pred = float(data["predicted_high_next_day"])
        spot = get_spot_price_usd()
        delta, pct = render_metrics_two_rows(pred, spot)
        st.success(f"Model: {data.get('model_version','n/a')}")

        result = {
            "ts": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "model": data.get("model_version", ""),
            "pred": pred,
            "spot": spot,
            "delta": delta,
            "pct": pct,
            "payload": payload,
        }
        st.session_state["panel_results"][mode_title] = result
        st.session_state["pred_history"].append({**result, "mode": mode_title})

        with st.expander("Show inputs sent to the model"):
            st.json(payload)
        return  # important: do NOT also render the saved block now

    # --- Case B: no click → show last saved result (if any) once ---
    saved = st.session_state["panel_results"].get(mode_title)
    if saved:
        st.info(f"Last result · {saved['ts']} · model `{saved['model']}`")
        render_metrics_two_rows(saved["pred"], saved["spot"])
        with st.expander("Inputs used (last run)"):
            st.json(saved["payload"])

if not predict_url:
    st.warning("Set `SERVICE_BTC_PREDICT_URL` in env or `.streamlit/secrets.toml` to enable predictions.")
else:
    panel("Yesterday → Predict Today (complete)", "inputs_yday")
    panel(
        "Today (partial) → Predict Tomorrow (estimate)",
        "inputs_today",
        "Note: using **partial** intraday data; values may change before day close.",
    )
    panel("Manual (What-If)", "inputs_manual")

st.markdown("----")

# --------------------------- 5) Prediction History ----------------------------
if st.session_state["pred_history"]:
    st.markdown("### Prediction History (this session)")
    for i, h in enumerate(st.session_state["pred_history"], start=1):
        st.markdown(f"**#{i} · {h.get('mode','')}** · _{h['ts']}_ · model: `{h['model']}`")
        render_metrics_two_rows(h["pred"], h["spot"])
        with st.expander("Inputs used"):
            st.json(h["payload"])
        st.markdown("---")

