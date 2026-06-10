# Share Trading Analysis Platform - MVP v3

This version expands the MVP from technical-only analysis to a multi-factor framework.

## What is included

- 10-year stock data fetch using yfinance
- Technical indicators: moving averages, RSI, MACD, volume, volatility, support/resistance
- Fundamental scoring using available yfinance company metrics
- Market/macro proxy scoring using benchmark index, VIX, yield, crude, currency, gold
- News sentiment proxy from recent yfinance headlines
- Weighted Buy/Hold/Sell recommendation
- Price driver table showing prominent positive/negative factors
- Future value range: 1M, 3M, 6M, 12M
- Adaptive walk-forward backtesting using Random Forest
- In-app chatbot to ask questions about the current analysis

## Deployment

Upload the contents of this folder to GitHub:

- app.py
- requirements.txt
- README.md
- modules folder

Then deploy on Streamlit Community Cloud with main file path:

app.py

## Important note on accuracy

The app includes a model that learns from historical technical and market/macro features and performs walk-forward testing. However, 95% accuracy cannot be guaranteed in real markets. The app reports actual achieved accuracy for the selected ticker and horizon.

## Example tickers

US: AAPL, MSFT, TSLA, NVDA
India: RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS

## Disclaimer

This tool is for education and analytical exploration only. It is not financial advice.
