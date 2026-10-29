import datetime
import math
import numpy as np
import pandas as pd
from scipy.stats import norm
import streamlit as st
import yfinance as yf

# --- Financial Core Formulas & Greeks ---
def calculate_historical_volatility(ticker_symbol, period="60d"):
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=period)
    if len(hist) < 10:
        return 0.30 
    hist['Log_Returns'] = np.log(hist['Close'] / hist['Close'].shift(1))
    daily_vol = hist['Log_Returns'].std()
    return daily_vol * math.sqrt(252)

def black_scholes_all_greeks(S, K, T, r, sigma):
    """Calculates Price, Delta, Gamma, and Theta for a Call Option."""
    if T <= 0:
        return max(0.0, S - K), 1.0 if S > K else 0.0, 0.0, 0.0
    
    if sigma <= 0:
        sigma = 0.001
        
    d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)
    
    # Price
    price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
    
    # Delta
    delta = norm.cdf(d1)
    
    # Gamma
    gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
    
    # Theta (Daily Decay)
    theta_term1 = -(S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
    theta_term2 = -r * K * math.exp(-r * T) * norm.cdf(d2)
    theta_daily = (theta_term1 + theta_term2) / 365.0
    
    return price, delta, gamma, theta_daily

# --- Streamlit Dashboard UI Setup ---
st.set_page_config(layout="wide")
st.title("Call Option Optimization Tool")
st.markdown("Use the advanced sidebar matrix on the left to filter contracts precisely down to your risk limits.")

# --- SIDEBAR FILTERS ---
st.sidebar.header("Target Underlying")
ticker_input = st.sidebar.text_input("Stock Ticker:", value="AAPL").upper().strip()

st.sidebar.header("Core Filters")
min_yield_filter = st.sidebar.slider("Minimum Annualized Return (%)", min_value=0, max_value=50, value=15)

# Moneyness Toggle
moneyness_filter = st.sidebar.radio(
    "Moneyness State:",
    options=["All", "Only OTM (Out-of-the-Money)", "Only ITM (In-the-Money)"],
    index=1 # Defaults to OTM since that is best practice for covered calls
)

# Valuation Filter Toggle
valuation_filter = st.sidebar.checkbox("Show ONLY Overvalued Contracts", value=True)

st.sidebar.header("Greek Sliders")
# Delta Constraints
delta_range = st.sidebar.slider("Delta Range (Probability of Assignment)", min_value=0.0, max_value=1.0, value=(0.10, 0.40), step=0.05)

# Implied Volatility Constraints
iv_range = st.sidebar.slider("Implied Volatility (IV) Range (%)", min_value=0, max_value=150, value=(10, 100), step=5)

# Theta Decay Filter
max_theta_decay = st.sidebar.slider("Minimum Daily Time Decay (Theta) ($ Loss/Day)", min_value=-1.0, max_value=0.0, value=-1.0, step=0.01)

# Advanced Configuration Hidden Container
with st.sidebar.expander("Advanced Environment Settings"):
    risk_free_rate = st.number_input("Risk Free Rate (Decimal)", min_value=0.0, max_value=0.10, value=0.045, step=0.005)

# --- BACKEND PROCESSING ENGINE ---
if ticker_input:
    try:
        ticker = yf.Ticker(ticker_input)
        todays_data = ticker.history(period='1d')
        
        if todays_data.empty:
            st.error("Could not fetch underlying equity data. Check symbol spelling.")
        else:
            S = todays_data['Close'].iloc[-1]
            hv_sigma = calculate_historical_volatility(ticker_input)
            
            # Header Block Metrics
            col1, col2 = st.columns(2)
            col1.metric(label=f"Current {ticker_input} Share Value", value=f"${S:.2f}")
            col2.metric(label="60-Day Historic Benchmark Volatility", value=f"{hv_sigma*100:.2f}%")
            
            all_calls_analyzed = []
            expirations = ticker.options
            
            if not expirations:
                st.warning("No option listings available.")
            else:
                for exp_date in expirations:
                    today = datetime.date.today()
                    target_date = datetime.datetime.strptime(exp_date, "%Y-%m-%d").date()
                    days_to_expiry = (target_date - today).days
                    T = days_to_expiry / 365.0
                    
                    if days_to_expiry <= 0 or days_to_expiry > 60:
                        continue
                        
                    opt_chain = ticker.option_chain(exp_date)
                    calls = opt_chain.calls
                    
                    for _, contract in calls.iterrows():
                        K = contract['strike']
                        market_premium = (contract['bid'] + contract['ask']) / 2 if contract['bid'] > 0 else contract['lastPrice']
                        
                        if market_premium <= 0.05: 
                            continue
                            
                        # Annualized Return Calculations
                        flat_return = (market_premium / S) * 100
                        annual_factor = 365.0 / days_to_expiry
                        flat_return_annual = flat_return * annual_factor
                        
                        # Gather actual Option Metrics
                        market_iv = contract['impliedVolatility']
                        market_iv_pct = market_iv * 100
                        
                        # Calculations
                        fair_price, _, _, _ = black_scholes_all_greeks(S, K, T, risk_free_rate, hv_sigma)
                        _, delta, gamma, theta = black_scholes_all_greeks(S, K, T, risk_free_rate, market_iv)
                        
                        # Determine Moneyness Flag
                        is_itm = S > K
                        moneyness_state = "ITM (In-the-Money)" if is_itm else "OTM (Out-of-the-Money)"
                        
                        # Mispricing Logic
                        variance = ((market_premium - fair_price) / fair_price) if fair_price > 0 else 0
                        is_overvalued = variance > 0.05
                        
                        if is_overvalued:
                            status = "OVERVALUED"
                        elif variance < -0.05:
                            status = "UNDERVALUED"
                        else:
                            status = "FAIR VALUE"
                        
                        # --- IMPLEMENT DYNAMIC SIDEBAR FILTERING CHECKS ---
                        if flat_return_annual < min_yield_filter:
                            continue
                        if moneyness_filter == "Only OTM (Out-of-the-Money)" and is_itm:
                            continue
                        if moneyness_filter == "Only ITM (In-the-Money)" and not is_itm:
                            continue
                        if valuation_filter and not is_overvalued:
                            continue
                        if delta < delta_range[0] or delta > delta_range[1]:
                            continue
                        if market_iv_pct < iv_range[0] or market_iv_pct > iv_range[1]:
                            continue
                        if theta < max_theta_decay: # E.g., if contract decays slower than slider limit
                            continue
                            
                        all_calls_analyzed.append({
                            "Expiration": exp_date,
                            "Days": days_to_expiry,
                            "Moneyness": moneyness_state,
                            "Strike": K,
                            "Market Price": f"${market_premium:.2f}",
                            "Fair Price (HV)": f"${fair_price:.2f}",
                            "Variance": f"{round(variance * 100, 1)}%",
                            "Annualized Yield": f"{round(flat_return_annual, 1)}%",
                            "Market IV": f"{round(market_iv_pct, 1)}%",
                            "Delta": round(delta, 2),
                            "Gamma": round(gamma, 4),
                            "Theta (Daily)": round(theta, 3),
                            "Valuation Status": status
                        })
                
                # --- RENDER CONDITIONAL MATRIX DATA ---
                if all_calls_analyzed:
                    df_results = pd.DataFrame(all_calls_analyzed)
                    st.success(f"Successfully located {len(df_results)} contracts matching your precise strategic filters.")
                    st.dataframe(df_results, width='stretch')
                else:
                    st.info("No matching options contracts fit the selected parameters. Try loosening your risk sliders or checking during market operational hours.")
                    
    except Exception as e:
        st.error(f"Data stream exception raised: {e}")
