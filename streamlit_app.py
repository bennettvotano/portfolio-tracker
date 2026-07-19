import streamlit as st
import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Paper Portfolio Tracker", page_icon="📈", layout="wide")

# ============================================================
# PAPER PORTFOLIO - $10,000 total, entered July 1, 2026
# ============================================================
portfolio = {
    "META": {"name": "Meta",         "buy_price": 612.91, "shares": 3,  "buy_date": "2026-07-01"},
    "WMT":  {"name": "Walmart",      "buy_price": 108.82, "shares": 15, "buy_date": "2026-07-01"},
    "JPM":  {"name": "JPMorgan",     "buy_price": 334.07, "shares": 5,  "buy_date": "2026-07-01"},
    "AAPL": {"name": "Apple",        "buy_price": 294.38, "shares": 6,  "buy_date": "2026-07-01"},
    "UNH":  {"name": "UnitedHealth", "buy_price": 426.54, "shares": 4,  "buy_date": "2026-07-01"},
    "SON":  {"name": "Sonoco",       "buy_price": 56.15,  "shares": 30, "buy_date": "2026-07-01"},
}

SPY_BUY_PRICE = 745.76
LOOKBACK_PERIOD = "1y"

st.title("📈 Paper Portfolio Tracker")
st.caption(f"Live data as of {datetime.today().strftime('%B %d, %Y')} — $10,000 paper portfolio vs. S&P 500")

with st.spinner("Pulling live market data..."):
    # Risk-free rate
    irx = yf.Ticker("^IRX")
    risk_free_rate = irx.fast_info["last_price"] / 100

    # SPY benchmark history
    spy_hist = yf.Ticker("SPY").history(period=LOOKBACK_PERIOD)
    spy_returns = spy_hist["Close"].pct_change().dropna()
    market_variance = spy_returns.var()

    total_invested = 0
    total_current = 0
    position_daily_returns = {}
    weights = {}
    rows = []

    for ticker, info in portfolio.items():
        stock = yf.Ticker(ticker)
        current_price = stock.fast_info["last_price"]
        buy_price = info["buy_price"]
        shares = info["shares"]

        invested = buy_price * shares
        current_value = current_price * shares
        gain_loss = current_value - invested
        pct_change = ((current_price - buy_price) / buy_price) * 100

        total_invested += invested
        total_current += current_value

        hist = stock.history(period=LOOKBACK_PERIOD)
        daily_returns = hist["Close"].pct_change().dropna()
        position_daily_returns[ticker] = daily_returns

        covariance = daily_returns.cov(spy_returns)
        beta = covariance / market_variance
        annual_volatility = daily_returns.std() * np.sqrt(252)
        annual_return = daily_returns.mean() * 252
        sharpe = (annual_return - risk_free_rate) / annual_volatility

        weights[ticker] = invested

        rows.append({
            "Ticker": ticker,
            "Name": info["name"],
            "Buy Date": info["buy_date"],
            "Buy Price": f"${buy_price:.2f}",
            "Current Price": f"${current_price:.2f}",
            "Gain/Loss": f"${gain_loss:.2f}",
            "Return %": f"{pct_change:.2f}%",
            "Beta": f"{beta:.2f}",
            "Volatility": f"{annual_volatility * 100:.2f}%",
            "Sharpe": f"{sharpe:.2f}",
        })

    total_gain_loss = total_current - total_invested
    total_pct = ((total_current - total_invested) / total_invested) * 100

    for ticker in weights:
        weights[ticker] = weights[ticker] / total_invested

    portfolio_beta = sum(
        weights[t] * (position_daily_returns[t].cov(spy_returns) / market_variance)
        for t in portfolio
    )

    combined = None
    for ticker in portfolio:
        weighted_series = position_daily_returns[ticker] * weights[ticker]
        combined = weighted_series if combined is None else combined.add(weighted_series, fill_value=0)

    portfolio_annual_return = combined.mean() * 252
    portfolio_annual_volatility = combined.std() * np.sqrt(252)
    portfolio_sharpe = (portfolio_annual_return - risk_free_rate) / portfolio_annual_volatility

    spy_current = yf.Ticker("SPY").fast_info["last_price"]
    spy_pct = ((spy_current - SPY_BUY_PRICE) / SPY_BUY_PRICE) * 100

# ------------------------------------------------------------
# Top-level metrics
# ------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Portfolio Value", f"${total_current:,.2f}", f"{total_pct:.2f}%")
col2.metric("Total Gain/Loss", f"${total_gain_loss:,.2f}")
col3.metric("Portfolio Beta", f"{portfolio_beta:.2f}")
col4.metric("Sharpe Ratio", f"{portfolio_sharpe:.2f}")

st.divider()

# ------------------------------------------------------------
# vs Benchmark
# ------------------------------------------------------------
st.subheader("vs. S&P 500 Benchmark")
bcol1, bcol2, bcol3 = st.columns(3)
bcol1.metric("Your Portfolio Return", f"{total_pct:.2f}%")
bcol2.metric("S&P 500 Return", f"{spy_pct:.2f}%")
diff = total_pct - spy_pct
bcol3.metric("Difference", f"{diff:+.2f} pts", delta_color="normal")

if total_pct > spy_pct:
    st.success(f"✅ Beating the market by {diff:.2f} percentage points")
else:
    st.warning(f"⚠️ Lagging the market by {abs(diff):.2f} percentage points")

st.divider()

# ------------------------------------------------------------
# Holdings table
# ------------------------------------------------------------
st.subheader("Holdings")
df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True)

st.caption(f"Risk-free rate (13-week T-bill): {risk_free_rate * 100:.2f}%  |  Beta/volatility/Sharpe calculated on 1-year trailing daily returns")
