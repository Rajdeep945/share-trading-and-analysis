from __future__ import annotations
import pandas as pd
import numpy as np

from modules.data_fetcher import fetch_stock_data, fetch_company_profile, fetch_market_macro_data, fetch_news
from modules.technical_analysis import calculate_indicators, latest_technical_score
from modules.fundamental_analysis import score_fundamentals
from modules.market_macro_analysis import latest_market_macro_score
from modules.sentiment_analysis import score_news_sentiment
from modules.recommendation_engine import final_recommendation
from modules.price_drivers import compile_price_drivers, prominent_driver_sentence

REQUIRED_COLUMNS = ["Ticker", "Quantity", "Average_Buy_Price"]

def normalize_portfolio_upload(df: pd.DataFrame) -> pd.DataFrame:
    data = df.copy()
    data.columns = [str(c).strip() for c in data.columns]
    aliases = {
        "ticker": "Ticker", "symbol": "Ticker", "stock": "Ticker", "stock_symbol": "Ticker",
        "qty": "Quantity", "quantity": "Quantity", "shares": "Quantity", "units": "Quantity",
        "avg_price": "Average_Buy_Price", "average_price": "Average_Buy_Price",
        "average_buy_price": "Average_Buy_Price", "buy_price": "Average_Buy_Price",
        "purchase_price": "Average_Buy_Price", "cost_price": "Average_Buy_Price"
    }
    rename = {}
    for c in data.columns:
        key = c.strip().lower().replace(" ", "_").replace("-", "_")
        if key in aliases:
            rename[c] = aliases[key]
    data = data.rename(columns=rename)
    missing = [c for c in REQUIRED_COLUMNS if c not in data.columns]
    if missing:
        raise ValueError(f"Portfolio file must contain columns: {REQUIRED_COLUMNS}. Missing: {missing}")
    data = data[REQUIRED_COLUMNS].copy()
    data["Ticker"] = data["Ticker"].astype(str).str.strip().str.upper()
    data["Quantity"] = pd.to_numeric(data["Quantity"], errors="coerce")
    data["Average_Buy_Price"] = pd.to_numeric(data["Average_Buy_Price"], errors="coerce")
    data = data.dropna(subset=["Ticker", "Quantity", "Average_Buy_Price"])
    data = data[(data["Ticker"] != "") & (data["Quantity"] > 0) & (data["Average_Buy_Price"] > 0)]
    if data.empty:
        raise ValueError("No valid portfolio rows found after cleaning.")
    return data.groupby("Ticker", as_index=False).agg({"Quantity": "sum", "Average_Buy_Price": "mean"})


def analyze_single_holding(ticker: str, quantity: float, avg_buy_price: float, years: int = 10) -> dict:
    price_df = fetch_stock_data(ticker, years)
    ind_df = calculate_indicators(price_df)
    profile = fetch_company_profile(ticker)
    macro_df = fetch_market_macro_data(ticker, years)
    news = fetch_news(ticker)

    tech_score, tech_factors = latest_technical_score(ind_df)
    fund_score, fund_factors = score_fundamentals(profile)
    macro_score, macro_factors = latest_market_macro_score(ind_df, macro_df)
    sentiment_score, sentiment_factors = score_news_sentiment(news)

    latest_vol = ind_df["Volatility_21D"].dropna().iloc[-1] if ind_df["Volatility_21D"].notna().any() else 0.25
    beta = profile.get("beta") or 1
    risk_penalty = int(max(0, (float(latest_vol) - 0.25) * 40 + max(0, float(beta or 1) - 1.2) * 10))
    rec = final_recommendation(tech_score, fund_score, macro_score, sentiment_score, risk_penalty)
    drivers = compile_price_drivers(tech_factors, fund_factors, macro_factors, sentiment_factors)
    prominent = prominent_driver_sentence(drivers)

    current_price = float(ind_df["Close"].dropna().iloc[-1])
    invested_value = float(quantity) * float(avg_buy_price)
    current_value = float(quantity) * current_price
    pnl = current_value - invested_value
    pnl_pct = (current_price / float(avg_buy_price) - 1) * 100

    # Portfolio action refines recommendation based on current gain/loss and risk.
    base_rec = rec["Recommendation"]
    if base_rec in ["Strong Buy", "Buy"] and pnl_pct < -15 and rec["Final Score"] < 70:
        action = "Hold / Review"
    elif base_rec in ["Strong Buy", "Buy"]:
        action = "Buy More / Accumulate"
    elif base_rec == "Hold":
        action = "Hold"
    elif base_rec == "Sell" and pnl_pct > 20:
        action = "Book Profit / Reduce"
    elif base_rec in ["Sell", "Strong Sell"]:
        action = "Reduce / Exit"
    else:
        action = base_rec

    risk_level = "Low"
    if float(latest_vol) > 0.35 or float(beta or 1) > 1.4 or rec["Final Score"] < 45:
        risk_level = "High"
    elif float(latest_vol) > 0.25 or float(beta or 1) > 1.15 or rec["Final Score"] < 60:
        risk_level = "Medium"

    return {
        "Ticker": ticker,
        "Company": profile.get("longName") or ticker,
        "Sector": profile.get("sector") or "Unknown",
        "Industry": profile.get("industry") or "Unknown",
        "Quantity": quantity,
        "Average Buy Price": round(float(avg_buy_price), 2),
        "Current Price": round(current_price, 2),
        "Invested Value": round(invested_value, 2),
        "Current Value": round(current_value, 2),
        "P&L": round(pnl, 2),
        "P&L %": round(pnl_pct, 2),
        "Recommendation": base_rec,
        "Portfolio Action": action,
        "Final Score": rec["Final Score"],
        "Confidence %": rec["Confidence"],
        "Technical Score": tech_score,
        "Fundamental Score": fund_score,
        "Market/Macro Score": macro_score,
        "Sentiment Score": sentiment_score,
        "Risk Level": risk_level,
        "Volatility": round(float(latest_vol), 4),
        "Beta": beta,
        "Most Prominent Driver": drivers.iloc[0]["Factor"] if not drivers.empty else "N/A",
        "Driver Summary": prominent,
        "drivers_df": drivers,
        "recommendation_context": rec,
    }


def analyze_portfolio(portfolio_df: pd.DataFrame, years: int = 10) -> tuple[pd.DataFrame, dict, dict]:
    holdings = normalize_portfolio_upload(portfolio_df)
    rows = []
    errors = {}
    details = {}
    for _, r in holdings.iterrows():
        ticker = r["Ticker"]
        try:
            result = analyze_single_holding(ticker, r["Quantity"], r["Average_Buy_Price"], years)
            details[ticker] = result
            clean = {k: v for k, v in result.items() if k not in ["drivers_df", "recommendation_context"]}
            rows.append(clean)
        except Exception as e:
            errors[ticker] = str(e)
    if not rows:
        raise ValueError(f"No holdings could be analyzed. Errors: {errors}")
    result_df = pd.DataFrame(rows)
    total_invested = float(result_df["Invested Value"].sum())
    total_current = float(result_df["Current Value"].sum())
    total_pnl = total_current - total_invested
    result_df["Portfolio Weight %"] = (result_df["Current Value"] / total_current * 100).round(2)
    result_df["Weighted Score Contribution"] = (result_df["Portfolio Weight %"] * result_df["Final Score"] / 100).round(2)
    summary = {
        "Total Invested": round(total_invested, 2),
        "Current Value": round(total_current, 2),
        "Total P&L": round(total_pnl, 2),
        "Total P&L %": round((total_current / total_invested - 1) * 100, 2) if total_invested else 0,
        "Portfolio Score": round(result_df["Weighted Score Contribution"].sum(), 2),
        "Holdings Analyzed": len(result_df),
        "High Risk Holdings": int((result_df["Risk Level"] == "High").sum()),
        "Reduce/Exit Flags": int(result_df["Portfolio Action"].str.contains("Reduce|Exit", case=False, regex=True).sum()),
        "Top Concentration %": round(float(result_df["Portfolio Weight %"].max()), 2),
        "Errors": errors,
    }
    return result_df, summary, details


def portfolio_chat_answer(question: str, portfolio_table: pd.DataFrame, summary: dict) -> str:
    q = (question or "").lower()
    if portfolio_table is None or portfolio_table.empty:
        return "Please upload and analyze your portfolio first."
    top_weight = portfolio_table.sort_values("Portfolio Weight %", ascending=False).head(3)
    worst = portfolio_table.sort_values("P&L %").head(3)
    best = portfolio_table.sort_values("P&L %", ascending=False).head(3)
    risky = portfolio_table[portfolio_table["Risk Level"].isin(["High", "Medium"])].sort_values(["Risk Level", "Portfolio Weight %"], ascending=[True, False]).head(5)
    reduce = portfolio_table[portfolio_table["Portfolio Action"].str.contains("Reduce|Exit|Book", case=False, regex=True, na=False)]
    buy = portfolio_table[portfolio_table["Portfolio Action"].str.contains("Buy More|Accumulate", case=False, regex=True, na=False)]

    if any(w in q for w in ["summary", "overall", "portfolio"]):
        return (f"Portfolio value is {summary.get('Current Value')}, total P&L is {summary.get('Total P&L')} "
                f"({summary.get('Total P&L %')}%). Portfolio score is {summary.get('Portfolio Score')}. "
                f"There are {summary.get('High Risk Holdings')} high-risk holdings and {summary.get('Reduce/Exit Flags')} reduce/exit flags.")
    if any(w in q for w in ["risk", "risky", "concentration"]):
        return "Top concentration / risk view:\n" + top_weight[["Ticker", "Portfolio Weight %", "Risk Level", "Final Score", "Portfolio Action"]].to_string(index=False)
    if any(w in q for w in ["sell", "exit", "reduce", "book"]):
        if reduce.empty:
            return "No holdings are currently flagged as Reduce/Exit/Book Profit by the model."
        return "Holdings flagged for reduction/profit booking:\n" + reduce[["Ticker", "Portfolio Action", "Final Score", "P&L %", "Most Prominent Driver"]].to_string(index=False)
    if any(w in q for w in ["buy", "add", "accumulate"]):
        if buy.empty:
            return "No holdings are currently flagged as Buy More / Accumulate."
        return "Holdings flagged for accumulation:\n" + buy[["Ticker", "Portfolio Action", "Final Score", "P&L %", "Most Prominent Driver"]].to_string(index=False)
    if any(w in q for w in ["loss", "worst", "underperform"]):
        return "Worst performers:\n" + worst[["Ticker", "P&L %", "Final Score", "Portfolio Action", "Most Prominent Driver"]].to_string(index=False)
    if any(w in q for w in ["best", "profit", "winner"]):
        return "Best performers:\n" + best[["Ticker", "P&L %", "Final Score", "Portfolio Action", "Most Prominent Driver"]].to_string(index=False)
    return "You can ask: portfolio summary, biggest risk, what should I reduce, what should I buy more, worst performers, best performers, or concentration risk."
