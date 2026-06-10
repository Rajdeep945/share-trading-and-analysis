from __future__ import annotations

from typing import Dict
import pandas as pd

from .technical_analysis import technical_score


def _signal_from_score(score: float) -> str:
    if score >= 65:
        return "Buy"
    if score >= 50:
        return "Hold"
    return "Sell"


def run_backtest(df: pd.DataFrame, horizon_days: int = 63, sample_months: int = 24) -> Dict:
    data = df.copy().reset_index(drop=True)
    if len(data) < 260 + horizon_days:
        return {"summary": {"message": "Insufficient data for backtesting"}, "rows": []}

    rows = []
    step = 21
    start = max(220, len(data) - sample_months * step - horizon_days)
    for i in range(start, len(data) - horizon_days, step):
        hist = data.iloc[: i + 1]
        tech = technical_score(hist)
        rec = _signal_from_score(tech["score"])
        price_now = float(data.iloc[i]["Close"])
        future_price = float(data.iloc[i + horizon_days]["Close"])
        future_return = (future_price - price_now) / price_now
        predicted_direction = 1 if rec == "Buy" else -1 if rec == "Sell" else 0
        actual_direction = 1 if future_return > 0.02 else -1 if future_return < -0.02 else 0
        direction_correct = predicted_direction == actual_direction if rec != "Hold" else abs(future_return) <= 0.05
        rows.append({
            "Date": data.iloc[i]["Date"].strftime("%Y-%m-%d"),
            "Recommendation": rec,
            "Technical Score": tech["score"],
            "Price Then": round(price_now, 2),
            "Actual Future Price": round(future_price, 2),
            "Actual Return %": round(future_return * 100, 2),
            "Direction Correct": "Yes" if direction_correct else "No",
        })

    if not rows:
        return {"summary": {"message": "No backtest rows generated"}, "rows": []}
    accuracy = sum(1 for r in rows if r["Direction Correct"] == "Yes") / len(rows) * 100
    avg_return = sum(r["Actual Return %"] for r in rows) / len(rows)
    return {
        "summary": {
            "Directional Accuracy %": round(accuracy, 2),
            "Average Future Return %": round(avg_return, 2),
            "Samples": len(rows),
            "Horizon Days": horizon_days,
        },
        "rows": rows,
    }
