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
st.set_page_config(page_title="Bitcoin Dashboard", page_icon="₿", layout="wide")

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




os.environ["SERVICE_BTC_PREDICT_URL"] = "https://btc-high-api.onrender.com/predict/bitcoin"

# %%
# Purpose: three-column header and hero image (use repo-relative path)

BASE_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(BASE_DIR)  

st.markdown('<div class="section-header"><h2>Bitcoin Dashboard</h2><p>World’s first decentralized digital currency</p></div>', unsafe_allow_html=True)


col1, col2, col3 = st.columns([1, 1, 1])
with col2:
    bit = os.path.join(APP_DIR, "assets", "btc.png")
    st.image(bit)


# %%
# Purpose: short context about BTC

st.write("""
**Bitcoin (BTC)** was created in 2009 by the pseudonymous developer *Satoshi Nakamoto*.
It remains the most valuable and widely recognized cryptocurrency, often described as
**digital gold** due to its limited supply of 21 million coins.
""")

st.markdown("---")

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


# --- Step 1: Fetch and prepare Kraken OHLC data (daily, last N days) ---

@st.cache_data(ttl=3600)  # cache for 1 hour (Kraken is stable; reduces API hits)
def get_kraken_ohlc(days: int = 90, pair: str = "XXBTZUSD", interval: int = 1440):
    """
    Fetch daily OHLC for Bitcoin from Kraken.
    - pair: "XXBTZUSD" = BTC/USD on Kraken
    - interval: 1440 = 1 day candles
    Returns DataFrame: timestamp (UTC), open, high, low, close, volume.
    """
    url = "https://api.kraken.com/0/public/OHLC"
    params = {"pair": pair, "interval": interval}

    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        payload = r.json()

        if payload.get("error"):
            raise RuntimeError(", ".join(payload["error"]))

        key = next(iter(payload["result"].keys()))
        rows = payload["result"][key]

        df = pd.DataFrame(
            rows,
            columns=["ts", "open", "high", "low", "close", "vwap", "volume", "count"]
        )
        # Convert ts → datetime UTC
        df["timestamp"] = pd.to_datetime(df["ts"], unit="s", utc=True)
        df = df.sort_values("timestamp").reset_index(drop=True)

        # Convert numeric columns to float (skip timestamp)
        for col in ["open", "high", "low", "close", "vwap", "volume", "count"]:
            df[col] = df[col].astype(float)

        # Keep only last N days
        if days and len(df) > days:
            df = df.tail(days).reset_index(drop=True)

        return df[["timestamp", "open", "high", "low", "close", "volume"]]

    except Exception as e:
        st.warning(f"⚠️ Failed to fetch Kraken OHLC data: {e}")
        return pd.DataFrame()

# Fetch and validate
df_ohlc = get_kraken_ohlc(90)

if df_ohlc.empty:
    st.warning("⚠️ Failed to fetch Kraken OHLC data or dataset is empty; stopping app.")
    st.stop()



# %%
# --- Step 2: Build unified frame (Kraken has volume; market cap not provided) ---

# Kraken does not provide market_cap. Create a placeholder so downstream code keeps working.
df_full = df_ohlc.copy()
df_full["market_cap"] = np.nan  # placeholder; we’ll decide later whether to drop or compute proxy

# Now df_full columns: timestamp, open, high, low, close, volume, market_cap (NaN)


# %%
# --- Step 3: Historical Trends (Kraken daily candles) ---
# Purpose:
#   (A) 4-line chart for open/high/low/close with tighter y-range + last-3 markers
#   (B) Split high–low range bars (low→close, close→high) with a close marker
#   Uses a slider to "zoom" by limiting the visible window (ordinal x doesn't scale-zoom well)

import altair as alt
import pandas as pd
import numpy as np
import streamlit as st

# Guard: ensure merged Kraken OHLC is available (built earlier as df_full)
if 'df_full' in locals() and isinstance(df_full, pd.DataFrame) and not df_full.empty:

    # Prep a plotting frame
    df_plot = df_full.copy()
    # Add both a temporal date (for continuous x) and a string date (for ordinal x)
    df_plot["date"] = df_plot["timestamp"].dt.date
    df_plot["date_str"] = df_plot["timestamp"].dt.strftime("%Y-%m-%d")

    st.markdown('<div class="section-header"><h2>Historical Trends</h2></div>', unsafe_allow_html=True)

    st.info(
        "Price movements of Bitcoin (Open, High, Low, Close) using **Kraken daily candles**. "
        "All times are UTC."
    )

    # ---- Global window slider to control both charts ----
    max_len = int(min(180, len(df_plot)))  # cap for performance
    default_window = 60 if max_len >= 60 else max_len
    window_days = st.slider(
        "Visible window (days)", min_value=15, max_value=max_len,
        value=default_window, step=1,
        help="Adjust to zoom/pan both charts."
    )

    # Slice to the requested window (most recent N days)
    df_win = df_plot.tail(window_days).reset_index(drop=True)

    # =====================  (A) LINE CHART  =====================
    # Tighter y-range based on what's visible
    y_min = float(df_win[["open", "high", "low", "close"]].min().min()) * 0.985
    y_max = float(df_win[["open", "high", "low", "close"]].max().max()) * 1.015

    base_line = (
        alt.Chart(df_win)
        .encode(x=alt.X("date:T", title="Date (UTC)"))
        .properties(height=420)
    )

    line_chart = (
        base_line
        .transform_fold(
            ["open", "high", "low", "close"],
            as_=["variable", "value"]
        )
        .mark_line(strokeWidth=2)
        .encode(
            y=alt.Y("value:Q", title="Price (USD)",
                    scale=alt.Scale(domain=[y_min, y_max])),
            color=alt.Color("variable:N", title="Series"),
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("variable:N", title="Series"),
                alt.Tooltip("value:Q", title="Price", format=",.2f"),
            ],
        )
        .properties(title="Bitcoin OHLC — Last N Days (Kraken daily)")
    )

    # Mark the last 3 closes in the visible window
    last3 = df_win.tail(3)
    markers = (
        alt.Chart(last3)
        .mark_point(size=80, filled=True)
        .encode(
            x="date:T",
            y="close:Q",
            tooltip=[
                alt.Tooltip("date:T", title="Date"),
                alt.Tooltip("close:Q", title="Close", format=",.2f"),
            ],
        )
    )
    labels = (
        alt.Chart(last3)
        .mark_text(align="left", dx=6, dy=-6)
        .encode(x="date:T", y="close:Q", text=alt.Text("close:Q", format=",.0f"))
    )

    st.altair_chart(
        (line_chart + markers + labels).configure_axis(grid=True).interactive(),
        use_container_width=True
    )

    # =====================  (B) RANGE BAR CHART  =====================
    # Ordinal x -> no true drag-zoom; use the same window slider for a clean zoom experience
    y_min2 = float(df_win["low"].min()) * 0.985
    y_max2 = float(df_win["high"].max()) * 1.015

    low_to_close = (
        alt.Chart(df_win)
        .mark_bar(size=8, opacity=0.85, color="#4C78A8")
        .encode(
            x=alt.X("date_str:O", title="Date (UTC)"),
            y=alt.Y("low:Q", title="Low ↔ High",
                    scale=alt.Scale(domain=[y_min2, y_max2])),
            y2="close:Q",
            tooltip=[
                alt.Tooltip("date_str:O", title="Date"),
                alt.Tooltip("low:Q", title="Low",   format=",.2f"),
                alt.Tooltip("close:Q", title="Close", format=",.2f"),
                alt.Tooltip("high:Q", title="High",  format=",.2f"),
            ],
        )
        .properties(height=420, title="High–Low Range with Close Marker (Kraken daily)")
    )

    close_to_high = (
        alt.Chart(df_win)
        .mark_bar(size=8, opacity=0.85, color="#F58518")
        .encode(x="date_str:O", y="close:Q", y2="high:Q")
    )

    close_points = (
        alt.Chart(df_win)
        .mark_point(size=55, filled=True)
        .encode(x="date_str:O", y="close:Q")
    )

    st.altair_chart(
        (low_to_close + close_to_high + close_points).configure_axis(grid=True),
        use_container_width=True
    )

else:
    st.warning("⚠️ Historical data not available for plotting (Kraken OHLC frame is empty).")


st.markdown("---")

# %%
# --- Step 4: Key Market Metrics (Kraken) ---
# Purpose:
#   A) 24h KPIs from Kraken Ticker (spot, ≈24h change using 24h VWAP, 24h volume, 24h VWAP)
#   B) Last 10 days daily panel (open/high/low/close/volume/return_%) with a pretty table
#      + two mini charts (Close line, Volume bar). All values in UTC.

import math
import pandas as pd
import altair as alt
import streamlit as st
from datetime import datetime, timezone
import requests

# ---------- A) 24h metrics (Kraken Ticker) ----------

@st.cache_data(ttl=120)  # refresh often; ticker is live
def get_kraken_ticker(pair: str = "XXBTZUSD"):
    """
    Kraken Ticker returns last price and 24h stats.
    Fields: 'c' (last), 'v' (vol today, vol 24h), 'p' (vwap today, vwap 24h),
            'h' (high today, high 24h), 'l' (low today, low 24h), 'o' (today open).
    """
    r = requests.get("https://api.kraken.com/0/public/Ticker", params={"pair": pair}, timeout=15)
    r.raise_for_status()
    payload = r.json()
    if payload.get("error"):
        raise RuntimeError(", ".join(payload["error"]))
    key = next(iter(payload["result"].keys()))
    t = payload["result"][key]
    return {
        "last": float(t["c"][0]),      # last traded price (USD)
        "vol_24h": float(t["v"][1]),   # volume over the last 24h (BTC)
        "vwap_24h": float(t["p"][1]),  # volume-weighted avg price over the last 24h (USD)
        "open_today": float(t["o"]),   # today's opening price (USD)
        "ts_utc": datetime.now(timezone.utc),
    }

# Small helper other steps can reuse
def get_spot_price_usd():
    try:
        return float(get_kraken_ticker()["last"])
    except Exception:
        return float("nan")

# ----- Render A) KPIs -----
try:
    m24 = get_kraken_ticker()
    # Approximate 24h change using last vs 24h VWAP (Kraken doesn’t expose “price 24h ago” directly)
    pct_24h = ((m24["last"] - m24["vwap_24h"]) / m24["vwap_24h"]) * 100.0 if m24["vwap_24h"] else float("nan")


    st.markdown('<div class="section-header"><h2>Key Market Metrics</h2></div>', unsafe_allow_html=True)

    st.info("Aggregated from Kraken (1-day interval). All values in UTC. VOLUME not available in USD on Kraken.")

    c1, c2 = st.columns(2)
    c1.metric("Spot Price (USD)", f"${m24['last']:,.2f}")
    c2.metric("≈ 24h Change", f"{pct_24h:+.3f}%")
    c3, c4 = st.columns(2)
    c3.metric("24h Volume not Available", f"{m24['vol_24h']/1000000:,.2f} M")
    c4.metric("24h VWAP (USD)", f"${m24['vwap_24h']/1000000:,.2f} M")
    st.caption(f"Last updated: {m24['ts_utc'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
except Exception as e:
    st.warning(f"⚠️ Could not fetch Kraken ticker: {e}")

# ---------- B) Last 10 days (built from Kraken OHLC set in Step 2) ----------

@st.cache_data(ttl=3600)
def build_daily_last10_from_ohlc(df_ohlc: pd.DataFrame) -> pd.DataFrame:
    """
    From Kraken daily OHLC (df_full), keep last 10 rows and compute day-over-day return %.
    Expects columns: timestamp, open, high, low, close, volume
    """
    if df_ohlc is None or df_ohlc.empty:
        return pd.DataFrame()
    df10 = df_ohlc.tail(10).copy().reset_index(drop=True)
    df10["date"] = df10["timestamp"].dt.date
    df10["return_%"] = df10["close"].pct_change() * 100.0
    return df10[["date", "open", "high", "low", "close", "volume", "return_%"]]

try:
    # df_full should have been produced in Step 2 (Kraken OHLC merge)
    df10 = build_daily_last10_from_ohlc(df_full if "df_full" in locals() else pd.DataFrame())
    if not df10.empty:
        # Summary metrics
        avg_vol_10d = df10["volume"].mean()
        vol_10d = df10["return_%"].std(ddof=1)

        st.subheader("Last 10 Days (Daily)")
        mc1, mc2 = st.columns(2)
        mc1.metric("10-Day Avg Volume (BTC)", f"{avg_vol_10d:,.2f}")
        mc2.metric("10-Day Volatility (σ of returns)", f"{vol_10d:.2f}%")

        # ---- Pretty table view (commas + 2 decimals). Keep numeric df10 for charts. ----
        df10_fmt = pd.DataFrame({
            "date": df10["date"],
            "open":   df10["open"].map(lambda x: f"{x:,.2f}"),
            "high":   df10["high"].map(lambda x: f"{x:,.2f}"),
            "low":    df10["low"].map(lambda x: f"{x:,.2f}"),
            "close":  df10["close"].map(lambda x: f"{x:,.2f}"),
            "volume (BTC)": df10["volume"].map(lambda x: f"{x:,.2f}"),
            "return_%": df10["return_%"].map(lambda x: "" if pd.isna(x) else f"{x:.2f}"),
        })
        st.dataframe(df10_fmt, hide_index=True, use_container_width=True)

        # ---- Mini charts (use numeric df10) ----
        left, right = st.columns(2)

        close_chart = (
            alt.Chart(df10)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date (UTC)"),
                y=alt.Y("close:Q", title="Close (USD)"),
                tooltip=[
                    alt.Tooltip("date:T", title="Date"),
                    alt.Tooltip("close:Q", title="Close", format=",.2f"),
                    alt.Tooltip("return_%:Q", title="Return %", format=".2f"),
                ],
            )
            .properties(height=260)
            .interactive()
        )
        left.altair_chart(close_chart, use_container_width=True)

        vol_chart = (
            alt.Chart(df10)
            .mark_bar()
            .encode(
                x=alt.X("date:T", title="Date (UTC)"),
                y=alt.Y("volume:Q", title="Volume (BTC)"),
                tooltip=[
                    alt.Tooltip("date:T", title="Date"),
                    alt.Tooltip("volume:Q", title="Volume (BTC)", format=",.2f"),
                ],
            )
            .properties(height=260)
            .interactive()
        )
        right.altair_chart(vol_chart, use_container_width=True)

    else:
        st.warning("⚠️ No 10-day data available from Kraken.")
except Exception as e:
    st.warning(f"⚠️ Could not build 10-day panel: {e}")




# %%
# Purpose: placeholder for next-day HIGH prediction


st.markdown('<div class="section-header"><h2>Machine Learning Predictions</h2></div>', unsafe_allow_html=True)

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
# --- Step 5: ML Prediction input modes (Yesterday / Today / Manual) WITH pretty previews ---
# Purpose:
#   • Three editable input modes, each producing the 7 raw features the FastAPI expects.
#   • Each numeric input shows a small, formatted preview with thousands separators.
#   • Values are saved in st.session_state as: inputs_yday / inputs_today / inputs_manual

import numpy as np
import pandas as pd
import streamlit as st
from datetime import datetime, timezone

st.subheader("Next-Day HIGH Prediction — Input Modes")
st.caption(
    "Choose an input mode. All timestamps and data are **UTC**. "
    "Kraken `/OHLC` provides **daily candles** (we pre-fill `open` → for `body = close - open`). "
    "Daily `close` and `volume` come from the same OHLC. "
    "You can edit any value below.  \n\n"
    "👉 **Manual (What-If)** starts pre-filled with **Today (partial)** values."
)

# ---------- helpers ----------

def safe_get(series, idx, default=np.nan) -> float:
    """Return series.iloc[idx] if possible, else default (as float)."""
    try:
        return float(series.iloc[idx])
    except Exception:
        return float(default)

def build_inputs_from_indices(df_daily: pd.DataFrame, idx_today: int):
    """
    Build the 7 RAW inputs using the daily OHLC frame `df_daily`.
    - close/volume from `df_daily`
    - body = close - open (same row)
    - lags from prior rows
    - timeHigh_year = current UTC year
    """
    close_t   = safe_get(df_daily["close"],  idx_today)
    volume_t  = safe_get(df_daily["volume"], idx_today)
    open_t    = safe_get(df_daily["open"],   idx_today)

    close_lag1 = safe_get(df_daily["close"], idx_today - 1)
    close_lag3 = safe_get(df_daily["close"], idx_today - 3)
    close_lag7 = safe_get(df_daily["close"], idx_today - 7)

    body = float(close_t - open_t) if np.isfinite(open_t) and np.isfinite(close_t) else np.nan
    year = datetime.now(timezone.utc).year

    return {
        "close_lag1": close_lag1,
        "close_lag3": close_lag3,
        "close_lag7": close_lag7,
        "body": body,
        "timeHigh_year": int(year),
        "close": close_t,
        "volume": volume_t,
        "_open_t": open_t,  # exposed for UI reference
    }

def fmt_money(x: float) -> str:
    """Format with thousands separator and 2 decimals."""
    try:
        return f"{float(x):,.2f}"
    except Exception:
        return "—"

def preview(value, prefix="↳ "):
    """Small, subdued one-line preview under an input (commas, 2 decimals)."""
    st.caption(f"{prefix}{fmt_money(value)}")

def num_input_with_preview(label: str, key: str, value: float, step: float = 0.01):
    """
    Render a Streamlit number_input (raw numeric, no commas) and a pretty preview below it.
    Returns the numeric value.
    """
    v = st.number_input(label, key=key, value=float(value), step=step, format="%.2f")
    preview(v)
    return v

# ---------- guards & presets ----------

if ('df_full' not in locals()) or df_full.empty:
    st.warning("⚠️ Not enough data to pre-fill inputs. Make sure Kraken daily OHLC (`df_full`) loaded.")
else:
    # df_full is daily OHLC; last row is 'today (partial)'
    idx_today  = len(df_full) - 1
    idx_yday   = len(df_full) - 2

    # Build presets
    preset_today = build_inputs_from_indices(df_full, idx_today)
    preset_yday  = build_inputs_from_indices(df_full, idx_yday)
    preset_man   = preset_today.copy()  # Manual starts from today’s values

    # ---------- tabs ----------
    t1, t2, t3 = st.tabs([
        "📅 Yesterday → Predict Today (complete)",
        "🟡 Today (partial) → Predict Tomorrow (estimate)",
        "✍️ Manual (What-If)"
    ])

    # ===== Tab 1: Yesterday (complete) =====
    with t1:
        st.caption("Uses **yesterday’s** completed daily candle for a clean, reproducible prediction.")
        c1, c2, c3 = st.columns(3)

        with c1:
            close_lag1_t1 = num_input_with_preview("close_lag1", "t1_l1", preset_yday["close_lag1"])
            close_lag3_t1 = num_input_with_preview("close_lag3", "t1_l3", preset_yday["close_lag3"])
            close_lag7_t1 = num_input_with_preview("close_lag7", "t1_l7", preset_yday["close_lag7"])
        with c2:
            open_t1  = num_input_with_preview("open (for body)", "t1_open", preset_yday["_open_t"])
            close_t1 = num_input_with_preview("close", "t1_close", preset_yday["close"])
            body_t1  = num_input_with_preview("body = close - open", "t1_body", preset_yday["body"])
        with c3:
            volume_t1 = num_input_with_preview("volume", "t1_vol", preset_yday["volume"])
            year_t1   = st.number_input("timeHigh_year", key="t1_year",
                                        value=int(preset_yday["timeHigh_year"]), step=1, format="%d")
            st.caption(f"↳ {year_t1:,}")

        st.session_state["inputs_yday"] = {
            "close_lag1": close_lag1_t1,
            "close_lag3": close_lag3_t1,
            "close_lag7": close_lag7_t1,
            "body": body_t1,
            "timeHigh_year": int(year_t1),
            "close": close_t1,
            "volume": volume_t1,
        }

    # ===== Tab 2: Today (partial) =====
    with t2:
        st.caption("Uses **today’s partial** intraday candle. Values may change before day close.")
        c1, c2, c3 = st.columns(3)

        with c1:
            close_lag1_t2 = num_input_with_preview("close_lag1", "t2_l1", preset_today["close_lag1"])
            close_lag3_t2 = num_input_with_preview("close_lag3", "t2_l3", preset_today["close_lag3"])
            close_lag7_t2 = num_input_with_preview("close_lag7", "t2_l7", preset_today["close_lag7"])
        with c2:
            open_t2  = num_input_with_preview("open (for body)", "t2_open", preset_today["_open_t"])
            close_t2 = num_input_with_preview("close", "t2_close", preset_today["close"])
            body_t2  = num_input_with_preview("body = close - open", "t2_body", preset_today["body"])
        with c3:
            volume_t2 = num_input_with_preview("volume", "t2_vol", preset_today["volume"])
            year_t2   = st.number_input("timeHigh_year", key="t2_year",
                                        value=int(preset_today["timeHigh_year"]), step=1, format="%d")
            st.caption(f"↳ {year_t2:,}")

        st.session_state["inputs_today"] = {
            "close_lag1": close_lag1_t2,
            "close_lag3": close_lag3_t2,
            "close_lag7": close_lag7_t2,
            "body": body_t2,
            "timeHigh_year": int(year_t2),
            "close": close_t2,
            "volume": volume_t2,
        }

    # ===== Tab 3: Manual (What-If) =====
    with t3:
        st.caption("Starts pre-filled with **Today (partial)** values. Edit freely to test hypothetical scenarios.")
        c1, c2, c3 = st.columns(3)

        with c1:
            close_lag1_m = num_input_with_preview("close_lag1", "m_l1", preset_man["close_lag1"])
            close_lag3_m = num_input_with_preview("close_lag3", "m_l3", preset_man["close_lag3"])
            close_lag7_m = num_input_with_preview("close_lag7", "m_l7", preset_man["close_lag7"])
        with c2:
            open_m  = num_input_with_preview("open (for body)", "m_open", preset_man["_open_t"])
            close_m = num_input_with_preview("close", "m_close", preset_man["close"])
            body_m  = num_input_with_preview("body = close - open", "m_body", preset_man["body"])
        with c3:
            volume_m = num_input_with_preview("volume", "m_vol", preset_man["volume"])
            year_m   = st.number_input("timeHigh_year", key="m_year",
                                       value=int(preset_man["timeHigh_year"]), step=1, format="%d")
            st.caption(f"↳ {year_m:,}")

        st.session_state["inputs_manual"] = {
            "close_lag1": close_lag1_m,
            "close_lag3": close_lag3_m,
            "close_lag7": close_lag7_m,
            "body": body_m,
            "timeHigh_year": int(year_m),
            "close": close_m,
            "volume": volume_m,
        }

    st.info("Inputs are prepared. Next: run predictions (buttons) using these values.")



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
st.markdown("# Run Prediction")

def panel(mode_title: str, payload_key: str, disclaimer: str | None = None):
    """
    One panel = title + (optional) disclaimer + button.
    • On click: call API, draw fresh results, save to session, append to history, RETURN EARLY.
    • On normal rerun: render last saved result once (no duplicates).
    """
    st.markdown(f"#### {mode_title}")
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
