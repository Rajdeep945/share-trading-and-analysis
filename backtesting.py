from __future__ import annotations


def final_recommendation(technical: int, fundamental: int, market_macro: int, sentiment: int, risk_penalty: int = 0) -> dict:
    weights = {
        "Technical": 0.25,
        "Fundamental": 0.30,
        "Market/Macro": 0.25,
        "News/Sentiment": 0.10,
        "Risk Adjustment": 0.10,
    }
    risk_score = max(0, min(100, 70 - risk_penalty))
    final = (
        technical * weights["Technical"] +
        fundamental * weights["Fundamental"] +
        market_macro * weights["Market/Macro"] +
        sentiment * weights["News/Sentiment"] +
        risk_score * weights["Risk Adjustment"]
    )
    if final >= 80:
        rec = "Strong Buy"
    elif final >= 65:
        rec = "Buy"
    elif final >= 50:
        rec = "Hold"
    elif final >= 35:
        rec = "Sell"
    else:
        rec = "Strong Sell"
    confidence = int(min(95, max(35, abs(final - 50) * 1.4 + 45)))
    return {
        "Recommendation": rec,
        "Final Score": round(final, 2),
        "Confidence": confidence,
        "Component Scores": {
            "Technical": technical,
            "Fundamental": fundamental,
            "Market/Macro": market_macro,
            "News/Sentiment": sentiment,
            "Risk Score": risk_score,
        },
        "Weights": weights,
    }


def recommendation_from_score(score: float) -> str:
    if score >= 80: return "Strong Buy"
    if score >= 65: return "Buy"
    if score >= 50: return "Hold"
    if score >= 35: return "Sell"
    return "Strong Sell"
