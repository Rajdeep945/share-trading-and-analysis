from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd
import yfinance as yf


@dataclass
class StockDataBundle:
    ticker: str
    info: Dict[str, Any]
    history: pd.DataFrame
    financials: Optional[pd.DataFrame]
    balance_sheet: Optional[pd.DataFrame]
    cashflow: Optional[pd.DataFrame]


def _clean_history(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    if "Date" not in df.columns and "Datetime" in df.columns:
        df = df.rename(columns={"Datetime": "Date"})
    df["Date"] = pd.to_datetime(df["Date"]).dt.tz_localize(None)
    required = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
    for col in required:
        if col not in df.columns:
            df[col] = pd.NA
    df = df[["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]].dropna(subset=["Close"])
    df = df.sort_values("Date").reset_index(drop=True)
    return df


@pd.api.extensions.register_dataframe_accessor("safe")
class SafeAccessor:
    def __init__(self, pandas_obj):
        self._obj = pandas_obj

    def latest_value(self, row_name: str):
        if self._obj is None or self._obj.empty:
            return None
        if row_name not in self._obj.index:
            return None
        series = self._obj.loc[row_name].dropna()
        if series.empty:
            return None
        return series.iloc[0]


def fetch_stock_bundle(ticker: str, period: str = "10y") -> StockDataBundle:
    ticker = ticker.strip().upper()
    if not ticker:
        raise ValueError("Please enter a valid ticker symbol.")

    stock = yf.Ticker(ticker)
    hist = _clean_history(stock.history(period=period, auto_adjust=False))
    if hist.empty:
        raise ValueError(f"No historical data found for ticker '{ticker}'. Try exchange suffixes such as .NS, .BO, .L, .TO etc.")

    try:
        info = stock.info or {}
    except Exception:
        info = {}

    def safe_frame(fetcher):
        try:
            df = fetcher()
            return df if isinstance(df, pd.DataFrame) and not df.empty else None
        except Exception:
            return None

    return StockDataBundle(
        ticker=ticker,
        info=info,
        history=hist,
        financials=safe_frame(lambda: stock.financials),
        balance_sheet=safe_frame(lambda: stock.balance_sheet),
        cashflow=safe_frame(lambda: stock.cashflow),
    )


def get_company_snapshot(bundle: StockDataBundle) -> Dict[str, Any]:
    info = bundle.info or {}
    hist = bundle.history
    last = hist.iloc[-1]
    prev_close = hist.iloc[-2]["Close"] if len(hist) > 1 else last["Close"]
    day_change = ((last["Close"] - prev_close) / prev_close) * 100 if prev_close else 0
    return {
        "ticker": bundle.ticker,
        "name": info.get("longName") or info.get("shortName") or bundle.ticker,
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "currency": info.get("currency", ""),
        "current_price": float(last["Close"]),
        "day_change_pct": float(day_change),
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "forward_pe": info.get("forwardPE"),
        "price_to_book": info.get("priceToBook"),
        "dividend_yield": info.get("dividendYield"),
        "beta": info.get("beta"),
        "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
        "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
        "analysis_date": datetime.utcnow().strftime("%Y-%m-%d"),
    }
