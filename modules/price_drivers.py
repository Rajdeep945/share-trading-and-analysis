from __future__ import annotations
import pandas as pd


def compile_price_drivers(*factor_lists) -> pd.DataFrame:
    rows = []
    for fl in factor_lists:
        rows.extend(fl or [])
    if not rows:
        return pd.DataFrame(columns=["Factor", "Impact", "Direction", "Prominence", "Explanation"])
    df = pd.DataFrame(rows)
    if "Impact" not in df.columns:
        df["Impact"] = 0
    df["AbsImpact"] = df["Impact"].abs()
    def prominence(x):
        if x >= 10: return "Very Prominent"
        if x >= 6: return "Prominent"
        if x >= 3: return "Moderate"
        return "Low"
    df["Prominence"] = df["AbsImpact"].apply(prominence)
    df = df.sort_values("AbsImpact", ascending=False).drop(columns=["AbsImpact"])
    return df[["Factor", "Impact", "Direction", "Prominence", "Explanation"]]


def prominent_driver_sentence(drivers: pd.DataFrame) -> str:
    if drivers is None or drivers.empty:
        return "No dominant driver was identified due to limited data."
    top = drivers.iloc[0]
    return f"Most prominent driver: {top['Factor']} ({top['Direction']}). {top['Explanation']}"
