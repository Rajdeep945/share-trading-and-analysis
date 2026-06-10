from __future__ import annotations
import numpy as np
import pandas as pd


def merge_stock_macro(stock_df: pd.DataFrame, macro_df: pd.DataFrame) -> pd.DataFrame:
    stock = stock_df[["Date", "Close", "Volume"]].copy()
    data = pd.merge(stock, macro_df, on="Date", how="left").sort_values("Date").ffill()
    for col in [c for c in data.columns if c not in ["Date"]]:
        data[f"{col}_ret_21d"] = data[col].pct_change(21)
        data[f"{col}_ret_63d"] = data[col].pct_change(63)
    return data


def latest_market_macro_score(stock_df: pd.DataFrame, macro_df: pd.DataFrame) -> tuple[int, list[dict]]:
    if macro_df is None or macro_df.empty:
        return 50, [{"Factor":"Macro data unavailable","Impact":0,"Direction":"Neutral","Explanation":"External market/macro proxy data was unavailable."}]
    data = merge_stock_macro(stock_df, macro_df).dropna(subset=["Close"])
    row = data.iloc[-1]
    score = 50
    factors = []

    def add(name, impact, direction, explanation):
        factors.append({"Factor": name, "Impact": impact, "Direction": direction, "Explanation": explanation})

    bench_21 = row.get("benchmark_ret_21d")
    bench_63 = row.get("benchmark_ret_63d")
    stock_21 = row.get("Close_ret_21d")
    if pd.notna(bench_21):
        if bench_21 > 0.03:
            score += 9; add("Market index momentum", 9, "Positive", "Benchmark index has positive 1-month momentum.")
        elif bench_21 < -0.03:
            score -= 9; add("Market index weakness", -9, "Negative", "Benchmark index has negative 1-month momentum.")
    if pd.notna(stock_21) and pd.notna(bench_21):
        rel = stock_21 - bench_21
        if rel > 0.04:
            score += 8; add("Relative strength", 8, "Positive", "Stock is outperforming the benchmark.")
        elif rel < -0.04:
            score -= 8; add("Relative weakness", -8, "Negative", "Stock is underperforming the benchmark.")
    vix_21 = row.get("vix_ret_21d")
    if pd.notna(vix_21):
        if vix_21 > 0.12:
            score -= 8; add("Volatility spike", -8, "Negative", "Market volatility proxy has increased sharply.")
        elif vix_21 < -0.08:
            score += 5; add("Volatility cooling", 5, "Positive", "Market volatility proxy is cooling.")
    yld_63 = row.get("yield_ret_63d")
    if pd.notna(yld_63):
        if yld_63 > 0.08:
            score -= 5; add("Rising yields", -5, "Negative", "Rising bond yields can pressure equity valuations.")
        elif yld_63 < -0.06:
            score += 4; add("Falling yields", 4, "Positive", "Falling yields can support equity valuation multiples.")
    crude_63 = row.get("crude_ret_63d")
    if pd.notna(crude_63):
        if crude_63 > 0.15:
            score -= 3; add("Crude oil rise", -3, "Negative", "Rising crude can affect inflation and input costs.")
        elif crude_63 < -0.12:
            score += 3; add("Crude oil decline", 3, "Positive", "Lower crude can ease inflation/input cost pressure.")
    curr_63 = row.get("currency_ret_63d")
    if pd.notna(curr_63):
        if abs(curr_63) > 0.05:
            impact = -3 if curr_63 > 0 else 2
            score += impact
            add("Currency movement", impact, "Negative" if impact < 0 else "Positive", "Currency proxy moved materially, which can affect foreign flows and imported costs.")

    return int(max(0, min(100, score))), factors
