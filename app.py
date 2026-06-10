from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from modules.data_fetcher import fetch_stock_bundle, get_company_snapshot
from modules.technical_analysis import technical_score
from modules.fundamental_analysis import fundamental_score
from modules.recommendation_engine import final_recommendation
from modules.price_drivers import identify_price_drivers
from modules.forecasting import simple_forecast
from modules.backtesting import run_backtest


st.set_page_config(page_title="AI Share Trading Analysis Platform", page_icon="📈", layout="wide")

st.title("📈 AI Share Trading Analysis Platform")
st.caption("MVP for stock analysis, technical/fundamental scoring, price drivers, forecast scenarios and backtesting. Educational use only — not financial advice.")

with st.sidebar:
    st.header("Analyze Stock")
    ticker = st.text_input("Enter stock ticker", value="AAPL", help="Examples: AAPL, TSLA, MSFT, RELIANCE.NS, HDFCBANK.NS")
    horizon = st.selectbox("Backtest Horizon", options=[("1 Month", 21), ("3 Months", 63), ("6 Months", 126), ("12 Months", 252)], format_func=lambda x: x[0], index=1)
    analyze = st.button("Analyze Stock", type="primary")
    st.markdown("---")
    st.write("**Ticker tips**")
    st.write("Indian NSE tickers usually use `.NS`, e.g., `RELIANCE.NS`. BSE usually uses `.BO`.")


def money(value, currency=""):
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{currency} {float(value):,.2f}".strip()
    except Exception:
        return str(value)


def pct(value):
    if value is None or pd.isna(value):
        return "N/A"
    try:
        return f"{float(value):.2%}"
    except Exception:
        return str(value)


def plot_price(indicator_df: pd.DataFrame, ticker: str):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=indicator_df["Date"], y=indicator_df["Close"], mode="lines", name="Close"))
    for col in ["SMA_20", "SMA_50", "SMA_200"]:
        if col in indicator_df:
            fig.add_trace(go.Scatter(x=indicator_df["Date"], y=indicator_df[col], mode="lines", name=col))
    fig.update_layout(title=f"{ticker} Price & Moving Averages", height=460, xaxis_title="Date", yaxis_title="Price", legend_orientation="h")
    return fig


def plot_rsi(indicator_df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=indicator_df["Date"], y=indicator_df["RSI"], mode="lines", name="RSI"))
    fig.add_hline(y=70, line_dash="dash", annotation_text="Overbought")
    fig.add_hline(y=30, line_dash="dash", annotation_text="Oversold")
    fig.update_layout(title="RSI", height=300, xaxis_title="Date", yaxis_title="RSI")
    return fig


def plot_macd(indicator_df: pd.DataFrame):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=indicator_df["Date"], y=indicator_df["MACD"], mode="lines", name="MACD"))
    fig.add_trace(go.Scatter(x=indicator_df["Date"], y=indicator_df["MACD_SIGNAL"], mode="lines", name="Signal"))
    fig.update_layout(title="MACD", height=300, xaxis_title="Date", yaxis_title="MACD", legend_orientation="h")
    return fig


if analyze:
    try:
        with st.spinner("Fetching 10 years of stock data and generating analysis..."):
            bundle = fetch_stock_bundle(ticker, period="10y")
            snapshot = get_company_snapshot(bundle)
            fundamental = fundamental_score(bundle.info)
            technical = technical_score(bundle.history)
            recommendation = final_recommendation(fundamental, technical, snapshot)
            drivers = identify_price_drivers(fundamental, technical, recommendation)
            forecast = simple_forecast(bundle.history)
            backtest = run_backtest(bundle.history, horizon_days=horizon[1])
            indicator_df = technical["indicator_data"]

        st.subheader(f"{snapshot['name']} ({snapshot['ticker']})")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Current Price", money(snapshot["current_price"], snapshot["currency"]), f"{snapshot['day_change_pct']:.2f}%")
        c2.metric("Recommendation", recommendation["recommendation"])
        c3.metric("Confidence", f"{recommendation['confidence']}%")
        c4.metric("Final Score", recommendation["final_score"])
        c5.metric("Risk", recommendation["risk"]["rating"])

        tabs = st.tabs(["Overview", "Technicals", "Fundamentals", "Price Drivers", "Forecast", "Backtesting", "Raw Data"])

        with tabs[0]:
            st.markdown("### Executive Summary")
            st.write(" ".join(recommendation["explanation"]))
            if drivers["most_prominent"]:
                st.info(f"Most prominent price driver: **{drivers['most_prominent']['Driver']}** — {drivers['most_prominent']['Explanation']}")

            left, right = st.columns([2, 1])
            with left:
                st.plotly_chart(plot_price(indicator_df, snapshot["ticker"]), use_container_width=True, key="overview_price_chart")
            with right:
                st.markdown("### Company Snapshot")
                st.write(f"**Sector:** {snapshot['sector']}")
                st.write(f"**Industry:** {snapshot['industry']}")
                st.write(f"**Market Cap:** {money(snapshot['market_cap'], snapshot['currency'])}")
                st.write(f"**Trailing P/E:** {snapshot['trailing_pe']}")
                st.write(f"**Forward P/E:** {snapshot['forward_pe']}")
                st.write(f"**Price/Book:** {snapshot['price_to_book']}")
                st.write(f"**52W High:** {money(snapshot['fifty_two_week_high'], snapshot['currency'])}")
                st.write(f"**52W Low:** {money(snapshot['fifty_two_week_low'], snapshot['currency'])}")

            st.markdown("### Scoring Breakdown")
            score_df = pd.DataFrame([
                {"Component": k.replace("_", " ").title(), "Score": v, "Weight": recommendation["weights"][k]} for k, v in recommendation["components"].items()
            ])
            st.dataframe(score_df, use_container_width=True, hide_index=True)

        with tabs[1]:
            st.markdown("### Technical Analysis")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Technical Score", technical["score"])
            c2.metric("Trend", technical["trend"])
            c3.metric("Support", money(technical["support"], snapshot["currency"]))
            c4.metric("Resistance", money(technical["resistance"], snapshot["currency"]))
            st.plotly_chart(plot_price(indicator_df, snapshot["ticker"]), use_container_width=True, key="technical_price_chart")
            col1, col2 = st.columns(2)
            col1.plotly_chart(plot_rsi(indicator_df), use_container_width=True, key="technical_rsi_chart")
            col2.plotly_chart(plot_macd(indicator_df), use_container_width=True, key="technical_macd_chart")
            st.markdown("### Signals")
            for s in technical["signals"]:
                st.write(f"- {s}")

        with tabs[2]:
            st.markdown("### Fundamental Analysis")
            c1, c2 = st.columns(2)
            c1.metric("Fundamental Score", fundamental["score"])
            c2.metric("View", fundamental["view"])
            st.markdown("#### Strengths")
            for s in fundamental["strengths"]:
                st.write(f"- {s}")
            st.markdown("#### Weaknesses / Watchouts")
            for w in fundamental["weaknesses"]:
                st.write(f"- {w}")
            st.markdown("#### Key Metrics")
            metric_df = pd.DataFrame([{"Metric": k.replace("_", " ").title(), "Value": v} for k, v in fundamental["metrics"].items()])
            st.dataframe(metric_df, use_container_width=True, hide_index=True)

        with tabs[3]:
            st.markdown("### Price Driver Analysis")
            driver_df = pd.DataFrame(drivers["drivers"])
            st.dataframe(driver_df, use_container_width=True, hide_index=True)
            if drivers["most_prominent"]:
                st.success(f"Prominent factor: {drivers['most_prominent']['Driver']} — {drivers['most_prominent']['Explanation']}")

        with tabs[4]:
            st.markdown("### Tentative Future Value")
            st.caption(f"Method: {forecast['method']}. This is probabilistic and not guaranteed.")
            forecast_df = pd.DataFrame(forecast["forecast_rows"])
            st.dataframe(forecast_df, use_container_width=True, hide_index=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=forecast_df["Time Horizon"], y=forecast_df["Base Case"], mode="lines+markers", name="Base Case"))
            fig.add_trace(go.Scatter(x=forecast_df["Time Horizon"], y=forecast_df["Bull Case"], mode="lines+markers", name="Bull Case"))
            fig.add_trace(go.Scatter(x=forecast_df["Time Horizon"], y=forecast_df["Bear Case"], mode="lines+markers", name="Bear Case"))
            fig.update_layout(title="Forecast Scenario Range", height=420, yaxis_title="Price")
            st.plotly_chart(fig, use_container_width=True, key="forecast_scenario_chart")

        with tabs[5]:
            st.markdown("### Backtesting")
            st.caption("MVP backtest uses historical technical score snapshots and compares recommendation direction against actual future movement.")
            st.json(backtest["summary"])
            if backtest.get("rows"):
                st.dataframe(pd.DataFrame(backtest["rows"]), use_container_width=True, hide_index=True)

        with tabs[6]:
            st.markdown("### Historical Data")
            st.dataframe(bundle.history.tail(500), use_container_width=True, hide_index=True)

        st.warning("Disclaimer: This MVP is for research and educational analysis only. It is not registered financial advice. Predictions and recommendations may be wrong. Validate independently before making investment decisions.")

    except Exception as exc:
        st.error(str(exc))
else:
    st.info("Enter a ticker in the sidebar and click **Analyze Stock** to generate the report.")
    st.markdown("""
### What this MVP does
- Fetches 10 years of historical data automatically
- Calculates moving averages, RSI, MACD, volatility and momentum
- Applies basic fundamental scoring from available free data
- Produces Buy / Hold / Sell recommendation with confidence score
- Shows price drivers and most prominent factor
- Provides tentative future value range
- Runs simple historical backtesting

### Example tickers
`AAPL`, `MSFT`, `TSLA`, `NVDA`, `RELIANCE.NS`, `TCS.NS`, `HDFCBANK.NS`
""")
