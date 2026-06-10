from __future__ import annotations

from typing import Dict, Tuple
import numpy as np
import pandas as pd


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    close = data["Close"]

    for window in [20, 50, 100, 200]:
        data[f"SMA_{window}"] = close.rolling(window).mean()

    data["EMA_12"] = close.ewm(span=12, adjust=False).mean()
    data["EMA_26"] = close.ewm(span=26, adjust=False).mean()
    data["MACD"] = data["EMA_12"] - data["EMA_26"]
    data["MACD_SIGNAL"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_HIST"] = data["MACD"] - data["MACD_SIGNAL"]

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    data["RSI"] = 100 - (100 / (1 + rs))

    data["BB_MID"] = close.rolling(20).mean()
    data["BB_STD"] = close.rolling(20).std()
    data["BB_UPPER"] = data["BB_MID"] + 2 * data["BB_STD"]
    data["BB_LOWER"] = data["BB_MID"] - 2 * data["BB_STD"]

    data["DAILY_RETURN"] = close.pct_change()
    data["VOLATILITY_30D"] = data["DAILY_RETURN"].rolling(30).std() * np.sqrt(252)
    data["VOLUME_SMA_20"] = data["Volume"].rolling(20).mean()
    data["MOMENTUM_3M"] = close.pct_change(63)
    data["MOMENTUM_6M"] = close.pct_change(126)
    data["MOMENTUM_12M"] = close.pct_change(252)

    return data


def support_resistance(df: pd.DataFrame, lookback: int = 180) -> Tuple[float, float]:
    recent = df.tail(lookback)
    support = float(recent["Low"].quantile(0.10))
    resistance = float(recent["High"].quantile(0.90))
    return support, resistance


def technical_score(df: pd.DataFrame) -> Dict:
    data = add_indicators(df).dropna().copy()
    if data.empty:
        return {"score": 50, "trend": "Neutral", "signals": ["Insufficient indicator history"], "support": None, "resistance": None, "indicator_data": add_indicators(df)}

    latest = data.iloc[-1]
    score = 50
    signals = []

    price = latest["Close"]
    sma20 = latest["SMA_20"]
    sma50 = latest["SMA_50"]
    sma200 = latest["SMA_200"]
    rsi = latest["RSI"]
    macd = latest["MACD"]
    macd_signal = latest["MACD_SIGNAL"]
    vol = latest["Volume"]
    vol_sma = latest["VOLUME_SMA_20"]

    if price > sma20:
        score += 6; signals.append("Price is above 20-day moving average")
    else:
        score -= 6; signals.append("Price is below 20-day moving average")

    if price > sma50:
        score += 8; signals.append("Price is above 50-day moving average")
    else:
        score -= 8; signals.append("Price is below 50-day moving average")

    if price > sma200:
        score += 12; signals.append("Long-term trend is positive: price above 200-day moving average")
    else:
        score -= 12; signals.append("Long-term trend is weak: price below 200-day moving average")

    if sma50 > sma200:
        score += 8; signals.append("50-day average is above 200-day average")
    else:
        score -= 8; signals.append("50-day average is below 200-day average")

    if macd > macd_signal:
        score += 7; signals.append("MACD is bullish")
    else:
        score -= 7; signals.append("MACD is bearish")

    if rsi < 30:
        score += 5; signals.append("RSI is oversold, possible rebound zone")
    elif 30 <= rsi <= 70:
        score += 5; signals.append("RSI is in a healthy range")
    else:
        score -= 8; signals.append("RSI is overbought, short-term caution")

    if pd.notna(vol_sma) and vol > vol_sma:
        score += 4; signals.append("Volume is above 20-day average")
    else:
        score -= 2; signals.append("Volume confirmation is weak")

    for col, label in [("MOMENTUM_3M", "3-month"), ("MOMENTUM_6M", "6-month"), ("MOMENTUM_12M", "12-month")]:
        val = latest.get(col)
        if pd.notna(val) and val > 0:
            score += 4; signals.append(f"{label} momentum is positive")
        elif pd.notna(val):
            score -= 4; signals.append(f"{label} momentum is negative")

    score = max(0, min(100, round(score, 1)))
    if score >= 70:
        trend = "Bullish"
    elif score >= 45:
        trend = "Neutral / Sideways"
    else:
        trend = "Bearish"

    support, resistance = support_resistance(data)
    return {
        "score": score,
        "trend": trend,
        "signals": signals,
        "support": support,
        "resistance": resistance,
        "rsi": float(rsi),
        "macd": float(macd),
        "macd_signal": float(macd_signal),
        "volatility_30d": float(latest["VOLATILITY_30D"]) if pd.notna(latest["VOLATILITY_30D"]) else None,
        "indicator_data": add_indicators(df),
    }
