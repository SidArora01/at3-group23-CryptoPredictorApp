import streamlit as st
import os

st.set_page_config(page_title="Crypto Model Metrics", page_icon="🟢", layout="wide")

BASE_DIR = os.path.dirname(__file__)
APP_DIR = os.path.dirname(BASE_DIR)

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

/* Metric Cards */
.metric-card {
    background-color: rgba(255, 255, 255, 0.05);
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 2px 2px 12px rgba(0,0,0,0.2);
    color: inherit;
    transition: transform 0.2s;
}
.metric-card:hover {
    transform: scale(1.03);
}
.metric-label {
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 6px;
}
.metric-value {
    font-size: 1.5rem;
    font-weight: bold;
    margin-bottom: 4px;
}
.metric-delta {
    font-size: 1rem;
    opacity: 0.85;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="section-header"><h2>Model Metrics</h2><p>Performance of predictive models for different cryptocurrencies</p></div>', unsafe_allow_html=True)

# Metrics Data
metrics = {
    "XRP": {"Model": "LightGBM", "R²_log": 0.978745, "RMSE": 0.078187, "MAE": 0.029169, "avg_price": "2.5"},
    "Ethereum": {"Model": "XGBoost", "R²": 0.9691, "RMSE": 89.6241, "MAE": 70.7681, "avg_price": "3,890"},
    "Bitcoin": {"Model": "ElasticNet", "R²": 0.996932, "RMSE": 1143.215487, "MAE": 809.734895, "avg_price": "110,400"},
    "Solana": {"Model": "ExtraTrees", "R²": 0.9508, "RMSE": 6.3112, "MAE": 5.0956, "avg_price": "186.00"}
}

rows = [list(metrics.keys())[:2], list(metrics.keys())[2:]]

for i, row in enumerate(rows):
    cols = st.columns(2, gap="large")
    for col, coin in zip(cols, row):
        m = metrics[coin]
        heading_color = "#ff9900"
        model_color = "#ff9900"  

        col.markdown(f"""
        <div class="metric-card">
            <h3 style="color:{heading_color};">{coin}</h3>
            <p><span style="font-weight:bold; color:{model_color}; font-size:1.1rem;"><b>Average Price:</b> USD {m['avg_price']}</p>
            <p><span style="font-weight:bold; color:{model_color}; font-size:1.1rem;">Model: {m['Model']}</p>
            <p><b>R²:</b> {m.get('R²', m.get('R²_log', 'N/A'))}</p>
            <p><b>RMSE:</b> {m['RMSE']}</p>
            <p><b>MAE:</b> {m['MAE']}</p>

        </div>
        """, unsafe_allow_html=True)
    
    if i < len(rows) - 1:
        st.markdown("<br><br>", unsafe_allow_html=True)

