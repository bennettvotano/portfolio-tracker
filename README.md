# Portfolio Tracker

A Python tool that tracks a $10,000 paper trading portfolio (META, WMT, JPM, AAPL, UNH, SON) against the S&P 500 benchmark using live market data.

## Features
- Pulls real-time stock prices via the `yfinance` API
- Calculates gain/loss and percentage return per position and portfolio-wide
- Computes beta, annualized volatility, and Sharpe ratio for each holding using 1-year trailing daily returns
- Benchmarks portfolio performance against SPY, including risk-adjusted comparison (Sharpe ratio)
- Pulls the current risk-free rate from the 13-week Treasury bill for accurate Sharpe calculations

## How to run
Run `run_tracker.command` (Mac) or execute `python3 portfolio_tracker.py` directly. Requires `yfinance` and `numpy`.
