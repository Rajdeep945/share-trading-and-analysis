from __future__ import annotations
import numpy as np
import pandas as pd


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    close = data["Close"].astype(float)
    data["Return_1D"] = close.pct_change()
    data["Return_21D"] = close.pct_change(21)
    data["Return_63D"] = close.pct_change(63)
    data["SMA_20"] = close.rolling(20).mean()
    data["SMA_50"] = close.rolling(50).mean()
    data["SMA_100"] = close.rolling(100).mean()
    data["SMA_200"] = close.rolling(200).mean()
    data["EMA_12"] = close.ewm(span=12, adjust=False).mean()
    data["EMA_26"] = close.ewm(span=26, adjust=False).mean()
    data["MACD"] = data["EMA_12"] - data["EMA_26"]
    data["MACD_Signal"] = data["MACD"].ewm(span=9, adjust=False).mean()
    data["MACD_Hist"] = data["MACD"] - data["MACD_Signal"]
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    data["RSI"] = 100 - (100 / (1 + rs))
    ma20 = data["SMA_20"]
    std20 = close.rolling(20).std()
    data["BB_Upper"] = ma20 + 2 * std20
    data["BB_Lower"] = ma20 - 2 * std20
    data["Volatility_21D"] = data["Return_1D"].rolling(21).std() * np.sqrt(252)
    data["Volume_SMA_20"] = data["Volume"].rolling(20).mean()
    data["Volume_Ratio"] = data["Volume"] / data["Volume_SMA_20"]
    data["Support_60D"] = data["Low"].rolling(60).min()
    data["Resistance_60D"] = data["High"].rolling(60).max()
    return data


def latest_technical_score(data: pd.DataFrame) -> tuple[int, list[dict]]:
    row = data.dropna(subset=["Close"]).iloc[-1]
    score = 50
    factors = []

    def add(name, impact, direction, explanation):
        factors.append({"Factor": name, "Impact": impact, "Direction": direction, "Explanation": explanation})

    close = row["Close"]
    for ma, pts in [("SMA_20", 6), ("SMA_50", 8), ("SMA_100", 6), ("SMA_200", 10)]:
        val = row.get(ma)
        if pd.notna(val):
            if close > val:
                score += pts
                add(f"Price above {ma}", pts, "Positive", f"Close is above {ma}, indicating upward trend support.")
            else:
                score -= pts
                add(f"Price below {ma}", -pts, "Negative", f"Close is below {ma}, indicating trend weakness.")

    rsi = row.get("RSI")
    if pd.notna(rsi):
        if rsi < 30:
            score += 8; add("RSI oversold", 8, "Positive", "RSI below 30 can signal oversold rebound potential.")
        elif rsi > 70:
            score -= 8; add("RSI overbought", -8, "Negative", "RSI above 70 can signal short-term overheating.")
        elif 45 <= rsi <= 65:
            score += 5; add("RSI healthy", 5, "Positive", "RSI is in a constructive momentum zone.")

    if pd.notna(row.get("MACD")) and pd.notna(row.get("MACD_Signal")):
        if row["MACD"] > row["MACD_Signal"]:
            score += 9; add("MACD bullish", 9, "Positive", "MACD is above signal line.")
        else:
            score -= 9; add("MACD bearish", -9, "Negative", "MACD is below signal line.")

    if pd.notna(row.get("Volume_Ratio")):
        if row["Volume_Ratio"] > 1.3 and row.get("Return_21D", 0) > 0:
            score += 5; add("Volume confirms rise", 5, "Positive", "Rising price with above-average volume.")
        elif row["Volume_Ratio"] > 1.3 and row.get("Return_21D", 0) < 0:
            score -= 5; add("Volume confirms fall", -5, "Negative", "Falling price with above-average volume.")

    score = int(max(0, min(100, score)))
    return score, factors
