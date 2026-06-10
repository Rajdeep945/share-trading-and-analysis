from __future__ import annotations
import math


def _score_range(value, good_low=None, good_high=None, inverse=False, neutral=50):
    if value is None:
        return neutral
    try:
        v = float(value)
        if math.isnan(v): return neutral
    except Exception:
        return neutral
    if good_low is not None and v < good_low:
        s = max(0, 50 - (good_low - v) * 10)
    elif good_high is not None and v > good_high:
        s = max(0, 80 - (v - good_high) * 3)
    else:
        s = 80
    return 100 - s if inverse else s


def score_fundamentals(profile: dict) -> tuple[int, list[dict]]:
    score = 50
    factors = []

    def add(name, impact, direction, explanation):
        factors.append({"Factor": name, "Impact": round(impact, 2), "Direction": direction, "Explanation": explanation})

    pe = profile.get("trailingPE") or profile.get("forwardPE")
    pb = profile.get("priceToBook")
    roe = profile.get("returnOnEquity")
    de = profile.get("debtToEquity")
    pm = profile.get("profitMargins")
    rg = profile.get("revenueGrowth")
    eg = profile.get("earningsGrowth")
    beta = profile.get("beta")

    if pe is not None:
        try:
            pe = float(pe)
            if 5 <= pe <= 30:
                score += 8; add("Valuation acceptable", 8, "Positive", f"P/E around {pe:.1f} is not extreme for many sectors.")
            elif pe > 45:
                score -= 10; add("High P/E valuation", -10, "Negative", f"P/E around {pe:.1f} indicates valuation risk.")
            elif pe <= 0:
                score -= 8; add("Negative/invalid P/E", -8, "Negative", "Negative earnings or unavailable profitability signal.")
        except Exception: pass
    if roe is not None:
        try:
            v = float(roe)
            if v > 0.15:
                score += 10; add("Strong ROE", 10, "Positive", f"ROE of {v:.1%} suggests strong return generation.")
            elif v < 0.05:
                score -= 8; add("Weak ROE", -8, "Negative", f"ROE of {v:.1%} is weak.")
        except Exception: pass
    if de is not None:
        try:
            v = float(de)
            if v > 150:
                score -= 8; add("High leverage", -8, "Negative", "Debt-to-equity appears elevated.")
            elif v < 75:
                score += 5; add("Manageable leverage", 5, "Positive", "Debt-to-equity appears manageable.")
        except Exception: pass
    if pm is not None:
        try:
            v = float(pm)
            if v > 0.10:
                score += 8; add("Healthy margins", 8, "Positive", f"Profit margin of {v:.1%} supports quality.")
            elif v < 0.02:
                score -= 6; add("Thin margins", -6, "Negative", "Low margins can increase earnings risk.")
        except Exception: pass
    if rg is not None:
        try:
            v = float(rg)
            if v > 0.08:
                score += 8; add("Revenue growth", 8, "Positive", f"Revenue growth of {v:.1%} is supportive.")
            elif v < -0.03:
                score -= 8; add("Revenue decline", -8, "Negative", f"Revenue growth of {v:.1%} is weak.")
        except Exception: pass
    if eg is not None:
        try:
            v = float(eg)
            if v > 0.08:
                score += 8; add("Earnings growth", 8, "Positive", f"Earnings growth of {v:.1%} supports upside.")
            elif v < -0.03:
                score -= 8; add("Earnings decline", -8, "Negative", f"Earnings growth of {v:.1%} pressures valuation.")
        except Exception: pass
    if beta is not None:
        try:
            v = float(beta)
            if v > 1.5:
                score -= 4; add("High beta risk", -4, "Negative", "High beta can amplify market sell-offs.")
        except Exception: pass

    return int(max(0, min(100, score))), factors
