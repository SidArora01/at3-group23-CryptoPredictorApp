# streamlit_app.py
import os, time, base64, requests
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

BASE_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(BASE_DIR) 
########################################### Page config ################################################

st.set_page_config(page_title="XRP", page_icon="💠", layout="wide")


################################# Light CSS adjustments (theme adaptive) ###############################
##------------ Adds lightweight, theme-adaptive CSS for improved layout and clean UI 

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

/* Status box (top-right) */
.status-box {
  position: absolute; top: 15px; right: 25px;
  font-size: 14px; color: var(--secondary-text-color, #888);
}

/* Segmented radio (hide default dots, show pills) */
div[role="radiogroup"] { gap: 12px !important; }
div[role="radiogroup"] > label {
  border: 1px solid rgba(128,128,128,0.35);
  border-radius: 10px; padding: 8px 18px;
  cursor: pointer; user-select: none;
}
div[role="radiogroup"] > label:hover {
  background: rgba(127,127,127,0.08);
}
div[role="radiogroup"] > label[aria-checked="true"] {
  background: var(--primary-color); color: #fff; border-color: var(--primary-color);
}
div[role="radiogroup"] svg { display: none !important; } /* hide dots */
</style>
""", unsafe_allow_html=True)


################################## Config variables #################################
##------ API base, image path, session state and cooldown timers

API_BASE = os.getenv("XRP_API_BASE", "https://advml-at3-api-25664525.onrender.com")
xrp = os.path.join(APP_DIR, "assets", "xrp.jpg")



HISTORY_TTL = 300  #5 min

if "hist_cache" not in st.session_state:
    st.session_state.hist_cache = {}

if "hist_refreshed_at" not in st.session_state:
    st.session_state.hist_refreshed_at = 0.0

if "window" not in st.session_state:
    st.session_state.window = "day"


################################### API Helper Functions  ##################################
#### ---------------- Data fetching, caching and retries

def get_json(path, params=None, retries=3, timeout=15):
    url = f"{API_BASE.rstrip('/')}/{str(path).lstrip('/')}"
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            return r.json(), None
        except requests.exceptions.RequestException as e:
            if i == retries - 1:
                return None, str(e)
            time.sleep(2 * (i + 1))  #2s, 4s, 6s backoff

@st.cache_data(ttl=30, show_spinner=False)
def fetch_health():
    return get_json("health")

@st.cache_data(ttl=300, show_spinner=False)
def fetch_predict_cached():
    return get_json("predict/XRP")

def refresh_all_histories():
    """
    Fetch day/week/month/year histories once and store in session.
    st.session_state.hist_cache will be:
        { window: {"df": pandas.DataFrame, "as_of": str} }
    """
    cache = {}
    for w in ["day", "week", "month", "year"]:
        js, err = get_json("history", params={"window": w})
        if err or not js or "data" not in js:
            return None, f"{w}: {err or 'no data'}"

        df = pd.DataFrame(js["data"])
        df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
        df["price"] = pd.to_numeric(df.get("price"), errors="coerce")
        df = df.dropna(subset=["ts", "price"]).sort_values("ts").reset_index(drop=True)

        cache[w] = {
            "df": df,
            "as_of": js.get("as_of", "?"),
        }
    return cache, None



#################################### Header section ###################################
##----------------------App title, status badge and XRP introduction


#---status badge (top-right)
st.markdown("""
<div class="status-box"><b>Status:</b> ✅ Online &nbsp;|&nbsp; <b>Model:</b> v1.0.0</div>
""", unsafe_allow_html=True)
st.markdown("<br><br>", unsafe_allow_html=True)

##--Title and icon
st.markdown('<div class="section-header"><h2>Ripple (XRP) Dashboard</h2><p>Fast, scalable digital asset for global payments (all times <b>UTC</b>)</p></div>', unsafe_allow_html=True)



def _img_b64(path):
    with open(path, "rb") as f: return base64.b64encode(f.read()).decode()

st.markdown(
    f"<div style='text-align:center;margin-top:-10px;'><img src='data:image/png;base64,{_img_b64(xrp)}' width='200'></div>",
    unsafe_allow_html=True
)
st.markdown("<br>", unsafe_allow_html=True)

#---Intro
st.write("""
**XRP** is a digital asset built for payments, enabling fast and efficient value transfer across the globe.
It runs on the XRP Ledger, a decentralised, open-source blockchain that supports low-cost transactions
and energy efficiency."""
)


st.markdown("---")


##################################### History controls  ####################################
##---------------------- Window selection, refresh button and cooldown

#Section header with info tooltip 


st.markdown('<div class="section-header"><h2>Price History</h2><p></p></div>', unsafe_allow_html=True)
st.markdown("""
<div style='display:flex;justify-content:space-between;align-items:center;'>
  <span title="Day - 1-hour candles (last 24h)&#10;Week - 4-hour candles (last 7 days)&#10;Month - Daily closes (last 30 days)&#10;Year - Weekly closes (last 52 weeks)"
        style="cursor:help;font-size:18px;opacity:.75;">ℹ️</span>
</div>
""", unsafe_allow_html=True)

st.markdown("")
#buttons alignment, left: windows, right: refresh
left, right = st.columns([1, 0.22])

with left:
    choice = st.radio(
        label="Window",
        options=["Day", "Week", "Month", "Year"],
        index=["day", "week", "month", "year"].index(st.session_state.window),
        horizontal=True,
        label_visibility="collapsed",
    )
#map choice to session_state
key_map = {"Day": "day", "Week": "week", "Month": "month", "Year": "year"}
st.session_state.window = key_map[choice]
window = st.session_state.window

#first-time data load
if st.session_state.hist_refreshed_at == 0.0:
    cache, err = refresh_all_histories()
    if not err:
        st.session_state.hist_cache = cache
        st.session_state.hist_refreshed_at = time.time()


#cooldown (5 min for all windows)
_now = time.time()
_remaining = max(0, HISTORY_TTL - int(_now - st.session_state.hist_refreshed_at))
_disabled_refresh = _remaining > 0
_refresh_help = (
    f"Next refresh available in {_remaining//60}m {_remaining%60}s."
    if _disabled_refresh else "Fetch latest data for all windows"
)

#manual refresh trigger
with right:
    if st.button(
        "Refresh history",
        key="refresh_history_top",
        use_container_width=True,
        disabled=_disabled_refresh,
        help=_refresh_help,
    ):
        with st.spinner("Refreshing all windows…"):
            cache, err = refresh_all_histories()
        if err:
            st.warning(f"History refresh failed ({err}). Please try again.")
        else:
            st.session_state.hist_cache = cache
            st.session_state.hist_refreshed_at = time.time()
        st.rerun()


st.markdown("<br>", unsafe_allow_html=True)


###################################### Price History Chart #####################################
#----------------------------- visualises Kraken OHLC data with Altair

##retrieve the cached DataFrame for the selected window 
item = st.session_state.hist_cache.get(window)
if not item:
    st.info("No history loaded yet. Click **Refresh history** to load data for all windows.")
    st.stop()

df = item["df"]
as_of = item.get("as_of", "?")

#for 'day' window, show last 24h only
if window == "day":
    cutoff = pd.Timestamp.utcnow() - pd.Timedelta(days=1)
    df = df[df["ts"] >= cutoff].reset_index(drop=True)

# KPIs
last_price = float(df["price"].iloc[-1]) if len(df) else np.nan
prev_price = float(df["price"].iloc[-2]) if len(df) > 1 else np.nan
pct = ((last_price - prev_price) / prev_price * 100.0) if np.isfinite(prev_price) and prev_price else np.nan
win_high = float(df["price"].max()) if len(df) else np.nan
win_low  = float(df["price"].min()) if len(df) else np.nan

c1, c2, c3, c4 = st.columns(4)
c1.metric("Last price (USD)", f"${last_price:,.4f}")
c2.metric("Δ vs prev", (f"{pct:+.2f}%" if np.isfinite(pct) else "—"))
c3.metric("High price", f"${win_high:,.4f}")
c4.metric("Low price",  f"${win_low:,.4f}")

##format timestamps for tooltips and adjust axis depending on selected window
df["ts_utc_str"] = df["ts"].dt.strftime("%Y-%m-%d %H:%M UTC")
axis_fmt = "%H:%M, %d %b" if window in ["day", "week"] else "%d %b %Y"

#configure axis encodings
x_enc = alt.X(
    "ts:T",
    title="Time (UTC)",
    scale=alt.Scale(type="utc"),
    axis=alt.Axis(format=axis_fmt),
)
y_enc = alt.Y("price:Q", title="Price (USD)", scale=alt.Scale(zero=False))

##price line with timestamp and price tooltips
line = (
    alt.Chart(df)
    .mark_line()
    .encode(x=x_enc, y=y_enc,
            tooltip=[
                alt.Tooltip("ts_utc_str:N", title="Timestamp"),
                alt.Tooltip("price:Q", title="Price (USD)", format="$.4f"),
            ])
)

##highlight data values on the same chart
points = (
    alt.Chart(df)
    .mark_point(size=20, filled=True, opacity=0.9)
    .encode(x=x_enc, y=y_enc,
            tooltip=[
                alt.Tooltip("ts_utc_str:N", title="Timestamp"),
                alt.Tooltip("price:Q", title="Price (USD)", format="$.4f"),
            ])
)

##combine both layers, set height and enable interactivity (zoom/pan)
chart = alt.layer(line, points).properties(height=360).interactive()
st.altair_chart(chart, use_container_width=True)

#caption for data source and timestamp
st.caption(f"as of (UTC): {as_of} • source: Kraken OHLC API")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")


####################################### Prediction ######################################
## ---------------- calls model API and renders styled prediction card

st.markdown('<div class="section-header"><h2>Prediction</h2><p></p></div>', unsafe_allow_html=True)

COOLDOWN_SEC = 300  #5 minutes

##initialise session state for storing last prediction and timestamp 
if "last_prediction" not in st.session_state:
    st.session_state.last_prediction = None
    st.session_state.last_pred_time = 0.0

##calculate remaining cooldown time before the user can predict again
_now = time.time()
_remaining_pred = max(0, COOLDOWN_SEC - int(_now - st.session_state.last_pred_time))
_disabled_pred = _remaining_pred > 0

##predict button 
col_pred, _ = st.columns([1, 2])
with col_pred:
    if st.button(
        "Predict next-day HIGH",
        use_container_width=True,
        disabled=_disabled_pred,
        help=(f"Please wait {_remaining_pred//60}m {_remaining_pred%60}s to run again."
              if _disabled_pred else "Run prediction"),
    ):
        with st.spinner("Predicting…"):
            pred, err = fetch_predict_cached()
        if not err and pred and "yhat" in pred:
            st.session_state.last_prediction = pred
            st.session_state.last_pred_time = time.time()
        else:
            st.warning("Prediction failed. Please try again in ~30-60 seconds.")

##display results
pred = st.session_state.last_prediction
if pred:
    yhat = float(pred["yhat"])
    last_close = float(df["price"].iloc[-1]) if len(df) else np.nan
    delta = (yhat - last_close) / last_close * 100.0 if np.isfinite(last_close) else np.nan
    up = delta >= 0
    delta_colour = "#16a34a" if up else "#dc2626"
    delta_emoji = "▲" if up else "▼"
    as_of_str = pred.get("as_of", "?")
    try:
        gen_dt = pd.to_datetime(as_of_str)
        gen_formatted = gen_dt.strftime("%A, %d %B %Y %H:%M UTC")
        pred_day = (gen_dt + pd.Timedelta(days=1)).strftime("%A, %d %B %Y")
    except Exception:
        gen_formatted = as_of_str
        pred_day = "Tomorrow"

    ##custom style for prediction card
    st.markdown("""
    <style>
      .pred-card {
        border: 1px solid rgba(127,127,127,.25);
        border-radius: 14px;
        padding: 18px 22px;
        margin-top: 10px;
        background: rgba(127,127,127,.06);
      }
      .pred-grid {
        display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap;
      }
      .pred-label {
        font-size: 0.95rem; opacity: .85; margin: 0;
      }
      .pred-value {
        font-size: 2.6rem; font-weight: 700; margin: 0; line-height: 1;
      }
      .pred-chip {
        font-size: 1rem; padding: 6px 10px; border-radius: 999px;
        border: 1px solid currentColor; color: inherit;
        background: transparent; white-space: nowrap;
      }
      .pred-info {
        font-size: 0.9rem; opacity: 0.8; margin-top: 8px; line-height: 1.4;
      }
      @media (max-width: 680px){
        .pred-grid { flex-direction: column; align-items: flex-start; }
      }
    </style>
    """, unsafe_allow_html=True)

    ##render prediction card
    st.markdown(
        f"""
        <div class="pred-card">
          <div class="pred-grid">
            <div>
              <p class="pred-label">Predicted next-day HIGH (USD)</p>
              <h1 class="pred-value">${yhat:,.4f}</h1>
            </div>
            <div style="display:flex;align-items:center;">
              <span class="pred-chip" style="color:{delta_colour};">
                {delta_emoji} {delta:+.2f}% vs last close
              </span>
            </div>
          </div>
          <div class="pred-info">
            <b>Predicted for:</b> {pred_day}<br>
            <b>Generated at:</b> {gen_formatted}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")


######################################## Footer #######################################
#--------------Notes, metric definitions and attribution

st.caption("""
**Notes**  
• All timestamps and prices are shown in **UTC** to ensure global consistency.  
• Daily and weekly data use hourly and 4-hour intervals; monthly and yearly data use daily and weekly closes.  
• Today's information is **partial** and updates continuously until UTC midnight.  
• Refreshing history updates all windows simultaneously (cooldown: 5 min).  
• Model predictions refresh independently (cooldown: 5 min).  

**Metric definitions**  
• **Last price** - Most recent price within the selected window.  
• **Δ vs prev** - Percentage change compared with the previous interval.  
• **High price** - Maximum observed value within the window.  
• **Low price** - Minimum observed value within the window.  
""")
st.caption("Source: Kraken OHLC API • Predictions powered by Group 23 (UTS AdvML AT3) • Not financial advice.")

