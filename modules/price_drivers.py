from __future__ import annotations

from typing import Dict, List


def identify_price_drivers(fundamental: Dict, technical: Dict, recommendation: Dict) -> Dict:
    rows: List[Dict] = []

    tech_score = technical.get("score", 50)
    fund_score = fundamental.get("score", 50)
    rsi = technical.get("rsi")

    if tech_score >= 70:
        rows.append({"Driver": "Technical momentum", "Impact": "High", "Direction": "Positive", "Prominence": "Very prominent", "Explanation": "Moving averages, MACD and momentum indicators are supportive."})
    elif tech_score < 45:
        rows.append({"Driver": "Weak technical trend", "Impact": "High", "Direction": "Negative", "Prominence": "Very prominent", "Explanation": "Price trend and momentum indicators are weak."})
    else:
        rows.append({"Driver": "Sideways technical trend", "Impact": "Medium", "Direction": "Neutral", "Prominence": "Moderate", "Explanation": "Technical indicators are mixed."})

    if fund_score >= 70:
        rows.append({"Driver": "Fundamental strength", "Impact": "High", "Direction": "Positive", "Prominence": "Prominent", "Explanation": "Available valuation, profitability, growth and leverage metrics are supportive."})
    elif fund_score < 50:
        rows.append({"Driver": "Fundamental weakness or incomplete data", "Impact": "Medium", "Direction": "Negative", "Prominence": "Prominent", "Explanation": "Available fundamental indicators are weak or incomplete."})
    else:
        rows.append({"Driver": "Moderate fundamentals", "Impact": "Medium", "Direction": "Neutral", "Prominence": "Moderate", "Explanation": "Fundamental score is neither strongly positive nor strongly negative."})

    if rsi is not None and rsi > 70:
        rows.append({"Driver": "Overbought RSI", "Impact": "Medium", "Direction": "Negative", "Prominence": "Watchlist", "Explanation": "RSI above 70 can indicate short-term overheating."})
    elif rsi is not None and rsi < 30:
        rows.append({"Driver": "Oversold RSI", "Impact": "Medium", "Direction": "Positive", "Prominence": "Watchlist", "Explanation": "RSI below 30 can indicate a possible rebound zone."})

    risk = recommendation.get("risk", {})
    if risk.get("rating") == "High":
        rows.append({"Driver": "Elevated risk profile", "Impact": "High", "Direction": "Negative", "Prominence": "Prominent", "Explanation": "Volatility, beta or valuation risk is elevated."})

    order = {"Very prominent": 4, "Prominent": 3, "Moderate": 2, "Watchlist": 1}
    rows = sorted(rows, key=lambda x: order.get(x["Prominence"], 0), reverse=True)
    top = rows[0] if rows else None
    return {"drivers": rows, "most_prominent": top}
