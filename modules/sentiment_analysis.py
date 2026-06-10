from __future__ import annotations

POSITIVE = ["beat", "beats", "growth", "surge", "rally", "upgrade", "profit", "strong", "record", "buy", "outperform", "raises", "gain", "wins", "expands"]
NEGATIVE = ["miss", "falls", "fall", "drop", "downgrade", "loss", "weak", "probe", "lawsuit", "sell", "underperform", "cuts", "decline", "concern", "warning"]


def score_news_sentiment(news: list[dict]) -> tuple[int, list[dict]]:
    if not news:
        return 50, [{"Factor":"News unavailable","Impact":0,"Direction":"Neutral","Explanation":"No recent news was available from the free data source."}]
    total = 0
    rows = []
    for item in news:
        title = (item.get("title") or "").lower()
        pos = sum(1 for w in POSITIVE if w in title)
        neg = sum(1 for w in NEGATIVE if w in title)
        raw = pos - neg
        total += raw
        if raw != 0:
            rows.append({
                "Factor": "News sentiment",
                "Impact": raw * 3,
                "Direction": "Positive" if raw > 0 else "Negative",
                "Explanation": item.get("title", "")[:180]
            })
    score = max(0, min(100, 50 + total * 5))
    if not rows:
        rows.append({"Factor":"News sentiment neutral","Impact":0,"Direction":"Neutral","Explanation":"Recent headlines did not contain strong positive or negative keywords."})
    return int(score), rows[:8]
