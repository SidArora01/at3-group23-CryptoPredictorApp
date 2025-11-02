#Home
import streamlit as st
from datetime import date
import os

st.set_page_config(
    page_title="Cryptocurrency Prediction Dashboard",
    page_icon="🪙",
    layout="wide"
)


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

st.markdown('<div class="section-header"><h2>Real-Time Cryptocurrency Prediction Hub</h2><p>Experience the Power of Machine Learning to Reveal Tomorrow\'s Market Trends Today</p></div>', unsafe_allow_html=True)
st.markdown("""
Welcome to the Hub! Ready to dive into the world of crypto? We’ve built an interactive data product designed to **analyze and predict** the short-term performance of today’s most popular cryptocurrencies.
""")

# HEADER SECTION
# title
#st.title ("Real-Time Cryptocurrency Prediction Hub")
## sub-heading
#st.subheader("Experience the Power of AI to Reveal Tomorrow's Market Trends Today")
## welcome message 
#st.markdown(
#    """
#    Welcome to the Hub! Ready to dive into the world of crypto? 
#    We’ve built an interactive data product designed to **analyze and predict** the short-term performance of today’s most popular cryptocurrencies.  
#    """
#)
BASE_DIR = os.path.dirname(__file__)

# VISUAL REPRESENTATION 
image2 = os.path.join(BASE_DIR, "assets", "image2.jpg")
#st.image(image2)

st.markdown("---")
st.header("Features Offered")

# Create three columns
col1, col2, col3 = st.columns(3, gap="large")

card_style = """
    background-color: rgba(255, 255, 255, 0.05);
    padding: 20px; 
    border-radius: 15px; 
    text-align: center; 
    box-shadow: 2px 2px 10px rgba(0,0,0,0.2);
    color: inherit;
    height: 280px;  /* fixed height */
    display: flex;
    flex-direction: column;
    justify-content: center;
"""

# Card 1: Latest Coin Info
with col1:
    st.markdown(
        f"""
        <div style="{card_style}">
            <h3>Latest Info</h3>
            <p>Get up-to-date prices, market capitalization, 24-hour volume, and percentage changes for the most popular cryptocurrencies. Real-time data ensures you never miss market movements.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Card 2: Historical Trends & Charts
with col2:
    st.markdown(
        f"""
        <div style="{card_style}">
            <h3>Historical Trends</h3>
            <p>Explore detailed charts showing open, high, low, and close prices. Zoom, pan, and hover over data points for precise insights. Identify trends and patterns easily.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# Card 3: Next-Day Prediction
with col3:
    st.markdown(
        f"""
        <div style="{card_style}">
            <h3>Next-Day Prediction</h3>
            <p>Leverage our machine learning models to estimate the next-day high price. Use the manual 'what-if' mode to test scenarios and explore predictive insights before they happen.</p>
        </div>
        """,
        unsafe_allow_html=True
    )



st.markdown("---")
st.markdown('<div class="section-header"><h2>Coins Available</h2></div>', unsafe_allow_html=True)
#INSTRUCTIONS FOR THE USER
st.markdown(
    """ 
    Select any cryptocurrency to explore its **historical trends**, **key metrics**, and **next-day high price predictions** — all powered by machine learning models.
    """
)

# crypto coin selection 
col1, col2, col3, col4 = st.columns(4, gap="large") 
# Bitcoin 
with col1: 
    bitcoin = os.path.join(BASE_DIR, "assets", "btc.png") 
    st.image(bitcoin) 
    st.write("") 
    if st.button("Bitcoin", use_container_width=True): 
        st.switch_page("pages/Bitcoin.py") 
        
# Ethereum 
with col2: 
    eth = os.path.join(BASE_DIR, "assets", "ethereum.jpg") 
    st.image(eth) 
    st.write("") 
    if st.button("Ethereum", use_container_width=True): 
        st.switch_page("pages/Ethereum.py") 
        
# XRP 
with col3: 
    xrp = os.path.join(BASE_DIR, "assets", "xrp.jpg") 
    st.image(xrp) 
    st.write("") 
    if st.button("XRP", use_container_width=True): 
        st.switch_page("pages/Ripple.py") 

# Solana 
with col4: 
    sol = os.path.join(BASE_DIR, "assets", "solana.jpg") 
    st.image(sol) 
    st.write("") 
    if st.button("Solana", use_container_width=True): 
        st.switch_page("pages/Solana.py")




# --- Project Info Section ---
st.markdown("---")
st.markdown('<div class="section-header"><h2>Project Info</h2></div>', unsafe_allow_html=True)
st.markdown("""
This project focuses on four major cryptocurrencies — **Bitcoin (BTC)**, **Ethereum (ETH)**, **XRP**, and **Solana (SOL)**.  
It integrates live data from **Kraken**, **CoinGecko**, **TokenMetrics**, and **CoinDesk APIs** to provide accurate and up-to-date market insights. Each cryptocurrency is supported by a distinct **machine learning model** developed by individual team members, aimed at predicting the next-day high price with precision.  

The application is built using **Streamlit** for interactivity, **FastAPI** for model deployment, and **Python 3.11.4** as the core development framework, delivering a seamless and intelligent data-driven experience.
""")

# --- Footer ---
st.markdown("---")
st.caption(f"Last updated: {date.today().strftime('%B %d, %Y')} | UTS 36120 AT3 - Data Product with Machine Learning")



