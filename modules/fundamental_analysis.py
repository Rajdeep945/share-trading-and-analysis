from __future__ import annotations

from typing import Dict, Any, List


def _score_range(value, good_low=None, good_high=None, lower_is_better=False, neutral=50):
    if value is None:
        return neutral
    try:
        value = float(value)
    except Exception:
        return neutral
    if lower_is_better:
        if good_high is not None and value <= good_high:
            return 75
        if good_high is not None and value <= good_high * 1.5:
            return 60
        return 40
    if good_low is not None and value >= good_low:
        return 75
    return 45


def fundamental_score(info: Dict[str, Any]) -> Dict[str, Any]:
    pe = info.get("trailingPE")
    fpe = info.get("forwardPE")
    pb = info.get("priceToBook")
    roe = info.get("returnOnEquity")
    margin = info.get("profitMargins")
    debt_to_equity = info.get("debtToEquity")
    revenue_growth = info.get("revenueGrowth")
    earnings_growth = info.get("earningsGrowth")
    beta = info.get("beta")

    scores = {
        "valuation_pe": _score_range(pe, good_high=25, lower_is_better=True),
        "forward_pe": _score_range(fpe, good_high=22, lower_is_better=True),
        "price_to_book": _score_range(pb, good_high=4, lower_is_better=True),
        "roe": _score_range(roe, good_low=0.12),
        "profit_margin": _score_range(margin, good_low=0.10),
        "debt_to_equity": _score_range(debt_to_equity, good_high=120, lower_is_better=True),
        "revenue_growth": _score_range(revenue_growth, good_low=0.06),
        "earnings_growth": _score_range(earnings_growth, good_low=0.06),
    }
    score = round(sum(scores.values()) / len(scores), 1)

    strengths: List[str] = []
    weaknesses: List[str] = []

    if revenue_growth is not None and revenue_growth > 0.06:
        strengths.append("Revenue growth appears positive")
    elif revenue_growth is not None:
        weaknesses.append("Revenue growth appears muted")

    if earnings_growth is not None and earnings_growth > 0.06:
        strengths.append("Earnings growth appears supportive")
    elif earnings_growth is not None:
        weaknesses.append("Earnings growth appears weak or negative")

    if roe is not None and roe > 0.12:
        strengths.append("Return on equity appears healthy")
    elif roe is not None:
        weaknesses.append("Return on equity appears below preferred level")

    if pe is not None and pe < 25:
        strengths.append("P/E valuation is not excessively stretched versus the default threshold")
    elif pe is not None:
        weaknesses.append("P/E valuation appears stretched versus the default threshold")

    if debt_to_equity is not None and debt_to_equity < 120:
        strengths.append("Leverage appears manageable")
    elif debt_to_equity is not None:
        weaknesses.append("Debt-to-equity appears elevated")

    if not strengths:
        strengths.append("Limited fundamental positives available from free data source")
    if not weaknesses:
        weaknesses.append("No major fundamental weakness detected from available free data")

    if score >= 70:
        view = "Strong fundamentals"
    elif score >= 55:
        view = "Moderate fundamentals"
    else:
        view = "Weak or incomplete fundamentals"

    return {
        "score": score,
        "view": view,
        "component_scores": scores,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "metrics": {
            "trailing_pe": pe,
            "forward_pe": fpe,
            "price_to_book": pb,
            "return_on_equity": roe,
            "profit_margin": margin,
            "debt_to_equity": debt_to_equity,
            "revenue_growth": revenue_growth,
            "earnings_growth": earnings_growth,
            "beta": beta,
        },
    }
