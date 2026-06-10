from __future__ import annotations
import numpy as np
import pandas as pd


def future_value_range(df: pd.DataFrame, final_score: float, horizons=(21, 63, 126, 252)) -> pd.DataFrame:
    data = df.dropna(subset=["Close"]).copy()
    close = float(data["Close"].iloc[-1])
    daily_ret = data["Close"].pct_change().dropna()
    mu = daily_ret.tail(756).mean() if len(daily_ret) else 0
    sigma = daily_ret.tail(756).std() if len(daily_ret) else 0.02
    score_tilt = (final_score - 50) / 10000  # daily tilt
    rows = []
    for h in horizons:
        exp_ret = (mu + score_tilt) * h
        vol = sigma * np.sqrt(h)
        base = close * (1 + exp_ret)
        bear = close * (1 + exp_ret - vol)
        bull = close * (1 + exp_ret + vol)
        label = {21:"1 Month",63:"3 Months",126:"6 Months",252:"12 Months"}.get(h, f"{h} Days")
        rows.append({"Horizon": label, "Bear Case": round(bear,2), "Base Case": round(base,2), "Bull Case": round(bull,2), "Expected Return %": round((base/close-1)*100,2)})
    return pd.DataFrame(rows)
