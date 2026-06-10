from __future__ import annotations


def answer_question(question: str, context: dict) -> str:
    q = (question or "").lower()
    rec = context.get("recommendation", {})
    scores = rec.get("Component Scores", {}) if isinstance(rec, dict) else {}
    prominent = context.get("prominent", "")
    forecast = context.get("forecast_text", "")
    risks = context.get("risks", "")
    drivers = context.get("drivers_text", "")

    if any(w in q for w in ["why", "driver", "driving", "reason"]):
        return f"The main price driver identified by the model is: {prominent}\n\nTop factor details:\n{drivers}"
    if any(w in q for w in ["buy", "hold", "sell", "recommend"]):
        return f"Current recommendation is {rec.get('Recommendation')} with final score {rec.get('Final Score')} and confidence {rec.get('Confidence')}%. Component scores: {scores}."
    if any(w in q for w in ["forecast", "future", "target", "price"]):
        return f"Tentative future value range based on current score, volatility and historical return distribution:\n{forecast}\n\nThis is probabilistic, not guaranteed."
    if any(w in q for w in ["risk", "downside", "stop"]):
        return f"Key risk view: {risks}"
    if any(w in q for w in ["macro", "market", "economic", "vix", "yield", "crude"]):
        return f"Market/macro score is {scores.get('Market/Macro')}. The model considers benchmark trend, stock relative strength, volatility proxy, yields, crude, currency and gold proxies. Top related drivers are included below:\n{drivers}"
    if any(w in q for w in ["technical", "rsi", "macd", "moving average"]):
        return f"Technical score is {scores.get('Technical')}. The model checks moving averages, RSI, MACD, volume confirmation, volatility, support and resistance."
    if any(w in q for w in ["fundamental", "pe", "roe", "valuation", "debt"]):
        return f"Fundamental score is {scores.get('Fundamental')}. The model checks available free-source metrics such as P/E, P/B, ROE, margins, leverage, growth and beta."
    return "I can answer questions such as: Why is the price moving? Should I buy/hold/sell? What is the forecast? What are the risks? What macro factors are affecting this stock?"
