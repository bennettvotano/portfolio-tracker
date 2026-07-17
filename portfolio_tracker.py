import yfinance as yf
import numpy as np
from datetime import datetime

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

SPY_BUY_PRICE = 745.76  # SPY price on your entry date - update if needed
LOOKBACK_PERIOD = "1y"  # window used for beta/volatility (industry standard)

print("=" * 70)
print(f"PAPER PORTFOLIO TRACKER - {datetime.today().strftime('%B %d, %Y')}")
print("=" * 70)

# ------------------------------------------------------------
# Step 1: Pull risk-free rate (13-week T-bill, ticker ^IRX)
# ------------------------------------------------------------
irx = yf.Ticker("^IRX")
risk_free_rate = irx.fast_info["last_price"] / 100  # ^IRX quotes as e.g. 5.25 -> 5.25%

# ------------------------------------------------------------
# Step 2: Pull 1-year daily history for SPY (market benchmark)
# ------------------------------------------------------------
spy_hist = yf.Ticker("SPY").history(period=LOOKBACK_PERIOD)
spy_returns = spy_hist["Close"].pct_change().dropna()
market_annual_return = spy_returns.mean() * 252
market_variance = spy_returns.var()

total_invested = 0
total_current = 0
weighted_beta = 0
position_daily_returns = {}  # store each stock's daily return series for portfolio-level calc
weights = {}

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

    # --- 1-year daily history for beta / volatility ---
    hist = stock.history(period=LOOKBACK_PERIOD)
    daily_returns = hist["Close"].pct_change().dropna()
    position_daily_returns[ticker] = daily_returns

    # Beta = covariance(stock, market) / variance(market)
    covariance = daily_returns.cov(spy_returns)
    beta = covariance / market_variance

    # Annualized volatility = daily std dev * sqrt(252 trading days)
    annual_volatility = daily_returns.std() * np.sqrt(252)

    # Annualized return (trailing 1y, used for Sharpe - not the same as since-purchase %)
    annual_return = daily_returns.mean() * 252

    # Sharpe ratio = (return - risk free rate) / volatility
    sharpe = (annual_return - risk_free_rate) / annual_volatility

    print(f"\n{info['name']} ({ticker})")
    print(f"  Buy Date:          {info['buy_date']}")
    print(f"  Buy Price:         ${buy_price:.2f}")
    print(f"  Current Price:     ${current_price:.2f}")
    print(f"  Since Purchase:    ${gain_loss:.2f} ({pct_change:.2f}%)")
    print(f"  Beta (1y):         {beta:.2f}")
    print(f"  Volatility (1y):   {annual_volatility * 100:.2f}%  (annualized)")
    print(f"  Sharpe Ratio (1y): {sharpe:.2f}")

    weights[ticker] = invested  # store dollar amount for now, convert to % after loop

# ------------------------------------------------------------
# Portfolio-level totals
# ------------------------------------------------------------
total_gain_loss = total_current - total_invested
total_pct = ((total_current - total_invested) / total_invested) * 100

# Convert dollar weights to portfolio percentage weights
for ticker in weights:
    weights[ticker] = weights[ticker] / total_invested

# Portfolio beta = weighted average of individual betas
portfolio_beta = 0
for ticker, info in portfolio.items():
    daily_returns = position_daily_returns[ticker]
    covariance = daily_returns.cov(spy_returns)
    beta = covariance / market_variance
    portfolio_beta += weights[ticker] * beta

# Portfolio daily return series = weighted sum of each position's daily returns
combined = None
for ticker in portfolio:
    weighted_series = position_daily_returns[ticker] * weights[ticker]
    combined = weighted_series if combined is None else combined.add(weighted_series, fill_value=0)

portfolio_annual_return = combined.mean() * 252
portfolio_annual_volatility = combined.std() * np.sqrt(252)
portfolio_sharpe = (portfolio_annual_return - risk_free_rate) / portfolio_annual_volatility

print("\n" + "=" * 70)
print("TOTAL PORTFOLIO")
print(f"  Invested:           ${total_invested:.2f}")
print(f"  Current Value:      ${total_current:.2f}")
print(f"  Since Purchase G/L: ${total_gain_loss:.2f} ({total_pct:.2f}%)")
print(f"  Portfolio Beta:     {portfolio_beta:.2f}")
print(f"  Portfolio Vol (1y): {portfolio_annual_volatility * 100:.2f}%")
print(f"  Portfolio Sharpe:   {portfolio_sharpe:.2f}")
print(f"  Risk-Free Rate:     {risk_free_rate * 100:.2f}%  (13-week T-bill)")

# ------------------------------------------------------------
# S&P 500 benchmark comparison
# ------------------------------------------------------------
spy_current = yf.Ticker("SPY").fast_info["last_price"]
spy_pct = ((spy_current - SPY_BUY_PRICE) / SPY_BUY_PRICE) * 100
spy_sharpe = (market_annual_return - risk_free_rate) / (spy_returns.std() * np.sqrt(252))

print("\nS&P 500 BENCHMARK (SPY)")
print(f"  Buy Price:     ${SPY_BUY_PRICE:.2f}")
print(f"  Current Price: ${spy_current:.2f}")
print(f"  Return:        {spy_pct:.2f}%")
print(f"  Sharpe (1y):   {spy_sharpe:.2f}")

print("\n" + "=" * 70)
print("VS BENCHMARK")
print(f"  Your Portfolio: {total_pct:.2f}%  |  Sharpe: {portfolio_sharpe:.2f}  |  Beta: {portfolio_beta:.2f}")
print(f"  S&P 500:        {spy_pct:.2f}%  |  Sharpe: {spy_sharpe:.2f}  |  Beta: 1.00")
if total_pct > spy_pct:
    print(f"  You are BEATING the market by {total_pct - spy_pct:.2f} percentage points")
else:
    print(f"  You are LAGGING the market by {spy_pct - total_pct:.2f} percentage points")
print("=" * 70)
