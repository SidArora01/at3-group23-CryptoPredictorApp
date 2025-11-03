# Cryptocurrency Prediction Dashboard

```
https://g23cryptopredict.streamlit.app/
```

A **real-time cryptocurrency prediction dashboard** built using **Streamlit**. This app provides historical trends, key market metrics, and next-day high price predictions for major cryptocurrencies including Bitcoin (BTC), Ethereum (ETH), XRP, and Solana (SOL). It leverages **machine learning models** to provide predictive insights and interactive visualizations.

All dashboards and metrics are fully ***UTC-based***, ensuring consistent, global timing and enabling users from any region to interpret market data and predictions accurately.

---

## Project Structure
```
CryptoPredictorApp/
│
├─ assets/ # Images and icons for cryptocurrencies
│ ├─ btc.png
│ ├─ ethereum.jpg
│ ├─ xrp.jpg
│ └─ solana.jpg
│
├─ pages/ # Individual cryptocurrency pages
│ ├─ Bitcoin.py
│ ├─ Ethereum.py
│ ├─ Ripple.py
│ └─ Solana.py
│
├─ Home.py # Main landing page
├─ requirements.txt # Python dependencies
└─ README.md # Project documentation
```

---

## Features

- **Real-Time Data**: Fetches live cryptocurrency market data including prices, trading volume, and historical OHLC values.  
- **Historical Trends**: Interactive candlestick charts for daily, weekly, monthly, and yearly trends.  
- **Key Metrics**: Displays high, low, VWAP, volume, and trade count for selected cryptocurrencies.  
- **Next-Day Prediction**: Uses machine learning models (XGBoost, LightGBM, ElasticNet, ExtraTrees) to predict the next-day high price.  
- **User-Friendly Dashboard**: Clean, responsive UI with styled cards, sections, and hover effects.  

---

## Pages
### Bitcoin
The Bitcoin.py page is a dedicated dashboard for Bitcoin (BTC).
1. Historical OHLC Data (Kraken)
    - Fetches daily OHLC data for BTC/USD from Kraken API.
    - Line chart: open, high, low, close
    - Range bar chart: low→close and close→high with markers
    - Allows zooming with a slider to control visible window (days).

2. Key Market Metrics (24h)
    - Spot Price (USD)
    - Approx. 24h Change
    - 24h Volume (BTC)
    - 24h VWAP (USD)
    - Also shows a 10-day panel with:
    - Open, High, Low, Close, Volume, Return %
    - Mini charts for Close and Volume
    - Pretty table formatting

3. Machine Learning Predictions
    - Yesterday → Predict Today (complete)
    - Today (partial) → Predict Tomorrow (estimate)
    - Manual (What-If)
    - Pre-fills inputs from historical OHLC data.
    - Users can edit numeric inputs (close_lag1, close_lag3, close_lag7, body, timeHigh_year, close, volume).

### Ethereum
The Ethereum.py page is a dedicated dashboard for Ethereum (ETH).

1. Historical OHLC Data (Kraken)

    - Fetches daily OHLC data for ETH/USD from Kraken API.
    - Candlestick charts:
    - Last 100 days (short-term)
    - Last 2 years (long-term)
    - Interactive charts: zoom, pan, and hover for precise price details.

2. Key Market Metrics (Latest Daily Candle)
    - Current Price (USD)
    - High / Low (24h)
    - VWAP (24h)
    - Trading Volume (current)
    - Number of Trades (current)
    - Shows percentage change from the previous day.
    - Metrics are updated continuously and displayed with clear formatting.

3. Machine Learning Predictions
    - Predicts next-day high price for Ethereum (ETH).
    - Users click a button to fetch predictions from an API.
    - Displays:
    - Prediction date
    - Predicted high (USD)
    - Δ vs current high (USD and %)

### Ripple
The XRP.py page is a dedicated dashboard for Ripple (XRP).

1. Price History (Kraken / XRP API)

    - Fetches historical price data for XRP/USD for multiple time windows:
    - Day (last 24h, 1-hour candles)
    - Week (last 7 days, 4-hour candles)
    - Month (last 30 days, daily closes)
    - Year (last 52 weeks, weekly closes)
    - Interactive Altair line charts with points: zoom, pan, hover tooltips.
    - Shows KPIs: Last Price, Δ vs Previous, High, Low.
    - Data cached in session state with cooldown (5 min) to reduce API load.

2. Key Metrics / KPIs

    - Last price in USD
    - Δ vs previous interval
    - High / Low prices for the selected window
    - All metrics automatically update based on selected window and cached history.

3. Machine Learning Predictions

    - Predicts next-day HIGH price for XRP (USD)
    - Δ vs last close (both % and arrow indicator ▲/▼)
    - Prediction date and generation timestamp in UTC
    - Styled prediction card for clarity and responsive layout.

### Solana
The Solana.py page is a dedicated dashboard for Solana (SOL).

1. Historical OHLC Data (CoinGecko)

    - Fetches OHLC data for SOL/USD for multiple timeframes:
    - Past 3 months (daily candles)
    - Past 1 year (daily candles)
    - Candlestick charts rendered with Plotly:
    - Interactive: zoom, pan, hover tooltips
    - Colored candles: green for up, red for down
    - Allows quick visual insight into short-term and long-term price trends.

2. Key Market Metrics (Live)

    - Spot Price (USD)
    - 24h Price Change (%)
    - 24h Volume (USD)
    - Market Cap (USD)
    - Circulating Supply (SOL)
    - Market Health Index (Bullish / Bearish / Stable)
    - Metrics auto-refresh with caching (5–10 minutes), with a refresh button to update live.

3. Machine Learning Predictions

    - Predicts tomorrow’s high price for SOL.
    - Uses latest market data from CoinGecko and a hosted ML API.
    - Predicted high (USD)
    - Generation timestamp in UTC
    - Option to view model inputs via an expandable JSON panel
    - Styled with a large centered value and clear formatting for instant readability.


## Installation & Setup

### 1. Clone the repository

```bash
(https://github.com/SidArora01/at3-group23-CryptoPredictorApp.git)
cd CryptoPredictorApp
poetry install
poetry shell
```

### 2. Running the App

```bash
cd app
streamlit run Home.py
```
The app will open in your default browser at http://localhost:8501.
Navigate between cryptocurrencies using the buttons on the homepage or on the navigation bar in the left side


## Dependencies

### Key Python packages:
- streamlit
- pandas
- numpy
- requests
- plotly
- datetime
- altair

See requirements.txt for the full list.



# Authors
Group 23 

Created by: Siddharth Arora (25106954) Email: siddharth.arora@student.uts.edu.au GitHub: SidArora01

Created by: Alison Barbosa Guzman (25664525) Email: alison.barbosaguzman@student.uts.edu.au GitHub: alibg3

Created by: Victor Garcia Ortiz (10522504) Email: Victor.garciaortiz@student.uts.edu.au  GitHub: vgarciachile

Created by: Britney Odria (14131609) Email: Britney.R.Odria@student.uts.edu.au GitHub: britodri007
