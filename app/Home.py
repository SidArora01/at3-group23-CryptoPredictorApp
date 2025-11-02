#Home
import streamlit as st
from datetime import date
import os

st.set_page_config(
    page_title="Cryptocurrency Prediction Dashboard",
    page_icon="🪙",
    layout="centered"
)

# HEADER SECTION
# title
st.title ("Real-Time Cryptocurrency Prediction Hub")
# sub-heading
st.subheader("Experience the Power of Machine Learning to Reveal Tomorrow's Market Trends Today")
# welcome message 
st.markdown(
    """
    Welcome to the Hub! Ready to dive into the world of crypto? We’ve built an interactive data product designed to **analyze and predict** the short-term performance of today’s most popular cryptocurrencies.  
    """
)
BASE_DIR = os.path.dirname(__file__)

# VISUAL REPRESENTATION 
image2 = os.path.join(BASE_DIR, "assets", "image2.jpg")
st.image(image2)


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
    bitcoin = os.path.join(BASE_DIR, "assets", "bitcoin.jpg")
    st.image(bitcoin)
    st.write("")  # spacing
    if st.button("Bitcoin", use_container_width=True):
        st.switch_page("pages/Bitcoin.py")

# Ethereum
with col2:
    eth = os.path.join(BASE_DIR, "assets", "ethereum.jpg")    
    st.image(eth)
    st.write("")
    if st.button("Ethereum"):
        eth_tab = os.path.join(BASE_DIR, "pages", "Ethereum.py")
        st.switch_page("Ethereum")

# XRP 
with col3:
    xrp = os.path.join(BASE_DIR, "assets", "xrp.jpg")
    st.image(xrp)
    st.write("")
    if st.button("XRP", use_container_width=True):
        xrp_tab = os.path.join(BASE_DIR, "pages", "xrp.py")
        st.switch_page(xrp_tab)
    
# Solana
with col4:
    sol = os.path.join(BASE_DIR, "assets", "solana.jpg")
    st.image(sol)
    st.write("")
    if st.button("Solana", use_container_width=True):
        sol_tab = os.path.join(BASE_DIR, "pages", "Solana.py")
        st.switch_page(sol_tab)

# PROJECT INFO
st.markdown("---")
st.markdown("Project Info")
st.markdown(
    """
    This project focuses on four major cryptocurrencies — **Bitcoin (BTC)**, **Ethereum (ETH)**, **XRP**, and **Solana (SOL)**. It integrates live data from **Kraken**, **CoinGecko**, **TokenMetrics**, and **CoinDesk APIs** to provide accurate and up-to-date market insights. Each cryptocurrency is supported by a distinct **machine learning model** developed by individual team members, aimed at predicting the next-day high price with precision. The application is built using **Streamlit** for interactivity, **FastAPI** for model deployment, and **Python 3.11.4** as the core development framework, delivering a seamless and intelligent data-driven experience.
    """
)

st.markdown("---")
st.caption(f"Last updated: {date.today().strftime('%B %d, %Y')} | UTS 36120 AT3 - Data Product with Machine Learning")

