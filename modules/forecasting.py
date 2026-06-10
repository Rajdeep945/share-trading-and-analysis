from __future__ import annotations

from typing import Dict
import numpy as np
import pandas as pd


def simple_forecast(df: pd.DataFrame) -> Dict:
    close = df["Close"].dropna()
    current = float(close.iloc[-1])
    returns = close.pct_change().dropna()
    if len(returns) < 252:
        avg_daily = returns.mean() if not returns.empty else 0
        vol_daily = returns.std() if not returns.empty else 0.02
    else:
        avg_daily = returns.tail(252).mean()
        vol_daily = returns.tail(252).std()

    horizons = {"1 Month": 21, "3 Months": 63, "6 Months": 126, "12 Months": 252}
    rows = []
    for label, days in horizons.items():
        expected = current * ((1 + avg_daily) ** days)
        sigma = vol_daily * np.sqrt(days)
        bear = expected * (1 - sigma)
        bull = expected * (1 + sigma)
        rows.append({
            "Time Horizon": label,
            "Bear Case": round(float(bear), 2),
            "Base Case": round(float(expected), 2),
            "Bull Case": round(float(bull), 2),
            "Expected Upside/Downside %": round(((expected - current) / current) * 100, 2),
        })
    return {"current_price": round(current, 2), "forecast_rows": rows, "method": "Historical return and volatility based probabilistic scenario model"}
