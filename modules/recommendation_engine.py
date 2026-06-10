from __future__ import annotations

from typing import Dict, Any, List


def risk_score_from_metrics(snapshot: Dict[str, Any], technical: Dict[str, Any]) -> Dict[str, Any]:
    score = 70
    risks: List[str] = []

    beta = snapshot.get("beta")
    vol = technical.get("volatility_30d")
    rsi = technical.get("rsi")

    if beta is not None:
        try:
            if beta > 1.3:
                score -= 12; risks.append("High beta indicates elevated market sensitivity")
            elif beta < 0.8:
                score += 5; risks.append("Lower beta indicates relatively defensive behavior")
        except Exception:
            pass

    if vol is not None:
        if vol > 0.45:
            score -= 15; risks.append("Recent annualized volatility is high")
        elif vol < 0.25:
            score += 5; risks.append("Recent volatility is relatively controlled")

    if rsi is not None and rsi > 70:
        score -= 8; risks.append("RSI is overbought, increasing short-term pullback risk")

    pe = snapshot.get("trailing_pe")
    try:
        if pe is not None and pe > 40:
            score -= 10; risks.append("High P/E increases valuation risk")
    except Exception:
        pass

    score = max(0, min(100, round(score, 1)))
    rating = "Low" if score >= 75 else "Medium" if score >= 50 else "High"
    if not risks:
        risks.append("No major risk flag identified from available MVP indicators")
    return {"score": score, "rating": rating, "risks": risks}


def final_recommendation(fundamental: Dict, technical: Dict, snapshot: Dict) -> Dict:
    risk = risk_score_from_metrics(snapshot, technical)
    market_score = 55  # MVP placeholder until benchmark/sector APIs are added
    macro_score = 50   # MVP placeholder until macro APIs are added
    sentiment_score = 50  # MVP placeholder until news sentiment is added

    weights = {
        "fundamentals": 0.30,
        "technicals": 0.30,
        "market_sector": 0.10,
        "macro": 0.10,
        "sentiment": 0.05,
        "risk": 0.15,
    }
    components = {
        "fundamentals": fundamental.get("score", 50),
        "technicals": technical.get("score", 50),
        "market_sector": market_score,
        "macro": macro_score,
        "sentiment": sentiment_score,
        "risk": risk.get("score", 50),
    }
    final_score = round(sum(components[k] * weights[k] for k in weights), 1)

    if final_score >= 80:
        recommendation = "Strong Buy"
    elif final_score >= 65:
        recommendation = "Buy"
    elif final_score >= 50:
        recommendation = "Hold"
    elif final_score >= 35:
        recommendation = "Sell"
    else:
        recommendation = "Strong Sell"

    confidence = round(min(90, max(35, abs(final_score - 50) * 1.4 + 45)), 1)

    explanation = []
    explanation.append(f"Fundamental score is {components['fundamentals']} and technical score is {components['technicals']}.")
    explanation.append(f"The MVP uses placeholder neutral scores for market, macro, and sentiment until premium/expanded data feeds are integrated.")
    explanation.append(f"Risk rating is {risk['rating']} based on volatility, beta, valuation and technical overheating checks.")

    return {
        "final_score": final_score,
        "recommendation": recommendation,
        "confidence": confidence,
        "components": components,
        "weights": weights,
        "risk": risk,
        "explanation": explanation,
    }
