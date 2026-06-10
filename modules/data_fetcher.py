from __future__ import annotations
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df


def fetch_stock_data(ticker: str, years: int = 10) -> pd.DataFrame:
    ticker = ticker.strip().upper()
    end = datetime.today()
    start = end - timedelta(days=365 * years + 20)
    df = yf.download(ticker, start=start, end=end, auto_adjust=False, progress=False, threads=False)
    df = _flatten_columns(df)
    if df is None or df.empty:
        raise ValueError(f"No price data found for {ticker}. Check ticker symbol/exchange suffix.")
    df = df.reset_index()
    if "Date" not in df.columns:
        df.rename(columns={df.columns[0]: "Date"}, inplace=True)
    required = ["Open", "High", "Low", "Close", "Volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns from market data: {missing}")
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.dropna(subset=["Close"]).sort_values("Date").reset_index(drop=True)
    return df


def fetch_single_series(ticker: str, years: int = 10, name: str | None = None) -> pd.DataFrame:
    end = datetime.today()
    start = end - timedelta(days=365 * years + 20)
    df = yf.download(ticker, start=start, end=end, progress=False, threads=False, auto_adjust=False)
    df = _flatten_columns(df)
    if df is None or df.empty or "Close" not in df.columns:
        return pd.DataFrame(columns=["Date", name or ticker])
    out = df.reset_index()[["Date", "Close"]].dropna()
    out["Date"] = pd.to_datetime(out["Date"])
    out.rename(columns={"Close": name or ticker}, inplace=True)
    return out


def infer_market_universe(ticker: str) -> dict:
    t = ticker.upper()
    if t.endswith(".NS") or t.endswith(".BO"):
        return {
            "benchmark": "^NSEI",
            "benchmark_name": "NIFTY 50",
            "vix": "^INDIAVIX",
            "currency": "INR=X",
            "currency_name": "USD/INR",
            "yield": "^TNX",
            "yield_name": "US 10Y Yield",
            "crude": "CL=F",
            "crude_name": "Crude Oil",
            "gold": "GC=F",
            "gold_name": "Gold",
        }
    return {
        "benchmark": "^GSPC",
        "benchmark_name": "S&P 500",
        "vix": "^VIX",
        "currency": "DX-Y.NYB",
        "currency_name": "US Dollar Index",
        "yield": "^TNX",
        "yield_name": "US 10Y Yield",
        "crude": "CL=F",
        "crude_name": "Crude Oil",
        "gold": "GC=F",
        "gold_name": "Gold",
    }


def fetch_market_macro_data(ticker: str, years: int = 10) -> pd.DataFrame:
    uni = infer_market_universe(ticker)
    frames = []
    for key in ["benchmark", "vix", "currency", "yield", "crude", "gold"]:
        frames.append(fetch_single_series(uni[key], years=years, name=key))
    if not frames:
        return pd.DataFrame()
    base = frames[0]
    for f in frames[1:]:
        base = pd.merge(base, f, on="Date", how="outer")
    base = base.sort_values("Date").ffill().dropna(how="all")
    return base


def fetch_company_profile(ticker: str) -> dict:
    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
    except Exception:
        info = {}
    fields = [
        "longName", "sector", "industry", "marketCap", "trailingPE", "forwardPE",
        "priceToBook", "returnOnEquity", "debtToEquity", "profitMargins", "operatingMargins",
        "revenueGrowth", "earningsGrowth", "dividendYield", "beta", "currentPrice",
        "fiftyTwoWeekHigh", "fiftyTwoWeekLow", "averageVolume", "recommendationKey"
    ]
    return {k: info.get(k) for k in fields}


def fetch_news(ticker: str, limit: int = 10) -> list[dict]:
    try:
        news = yf.Ticker(ticker).news or []
    except Exception:
        news = []
    clean = []
    for item in news[:limit]:
        title = item.get("title") or item.get("content", {}).get("title") or ""
        publisher = item.get("publisher") or item.get("content", {}).get("provider", {}).get("displayName") or ""
        link = item.get("link") or item.get("content", {}).get("canonicalUrl", {}).get("url") or ""
        clean.append({"title": title, "publisher": publisher, "link": link})
    return clean
