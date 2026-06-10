from __future__ import annotations
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from modules.data_fetcher import fetch_stock_data, fetch_company_profile, fetch_market_macro_data, fetch_news, infer_market_universe
from modules.technical_analysis import calculate_indicators, latest_technical_score
from modules.fundamental_analysis import score_fundamentals
from modules.market_macro_analysis import latest_market_macro_score
from modules.sentiment_analysis import score_news_sentiment
from modules.recommendation_engine import final_recommendation
from modules.price_drivers import compile_price_drivers, prominent_driver_sentence
from modules.forecasting import future_value_range
from modules.backtesting import run_adaptive_backtest
from modules.chatbot import answer_question

st.set_page_config(page_title="Share Trading Analysis Platform", layout="wide")

st.title("📈 Multi-Factor Share Trading Analysis Platform")
st.caption("MVP v3: technical + fundamental + market/macro proxy + news sentiment + adaptive backtesting + chatbot")

with st.sidebar:
    st.header("Analyze Stock")
    ticker = st.text_input("Enter ticker", value="AAPL", help="Examples: AAPL, TSLA, MSFT, RELIANCE.NS, TCS.NS, HDFCBANK.NS")
    years = st.slider("Historical years", 3, 10, 10)
    horizon_label = st.selectbox("Backtest horizon", ["1 Month", "3 Months", "6 Months", "12 Months"], index=1)
    horizon_map = {"1 Month": 21, "3 Months": 63, "6 Months": 126, "12 Months": 252}
    analyze = st.button("Analyze Stock", type="primary")

st.info("Important: This app provides analytical signals, not certified financial advice. Future prices and recommendations are probabilistic and can be wrong.")

@st.cache_data(ttl=3600, show_spinner=False)
def load_all(ticker: str, years: int):
    price = fetch_stock_data(ticker, years)
    ind = calculate_indicators(price)
    profile = fetch_company_profile(ticker)
    macro = fetch_market_macro_data(ticker, years)
    news = fetch_news(ticker)
    return price, ind, profile, macro, news

if analyze or ticker:
    try:
        with st.spinner("Fetching 10-year data and running multi-factor analysis..."):
            price_df, ind_df, profile, macro_df, news = load_all(ticker.strip(), years)
            tech_score, tech_factors = latest_technical_score(ind_df)
            fund_score, fund_factors = score_fundamentals(profile)
            macro_score, macro_factors = latest_market_macro_score(ind_df, macro_df)
            sentiment_score, sentiment_factors = score_news_sentiment(news)
            # Simple risk penalty from volatility and beta
            latest_vol = ind_df["Volatility_21D"].dropna().iloc[-1] if ind_df["Volatility_21D"].notna().any() else 0.25
            beta = profile.get("beta") or 1
            risk_penalty = int(max(0, (latest_vol - 0.25) * 40 + max(0, float(beta or 1) - 1.2) * 10))
            rec = final_recommendation(tech_score, fund_score, macro_score, sentiment_score, risk_penalty)
            drivers = compile_price_drivers(tech_factors, fund_factors, macro_factors, sentiment_factors)
            prominent = prominent_driver_sentence(drivers)
            forecast_df = future_value_range(ind_df, rec["Final Score"])
    except Exception as e:
        st.error(f"Could not analyze {ticker}. Error: {e}")
        st.stop()

    company = profile.get("longName") or ticker.upper()
    current_price = ind_df["Close"].dropna().iloc[-1]
    prev_price = ind_df["Close"].dropna().iloc[-2]
    day_change = (current_price / prev_price - 1) * 100

    st.subheader(f"{company} ({ticker.upper()})")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Current Price", f"{current_price:,.2f}", f"{day_change:.2f}%")
    c2.metric("Recommendation", rec["Recommendation"])
    c3.metric("Final Score", rec["Final Score"])
    c4.metric("Confidence", f"{rec['Confidence']}%")
    c5.metric("Most Prominent", drivers.iloc[0]["Factor"] if not drivers.empty else "N/A")

    st.markdown(f"**Price driver summary:** {prominent}")

    tabs = st.tabs(["Overview", "Charts", "Scores & Drivers", "Forecast", "Backtesting", "News", "Chatbot"])

    with tabs[0]:
        st.write("### Executive Summary")
        st.write(
            f"The model gives **{rec['Recommendation']}** based on a weighted score of **{rec['Final Score']}**. "
            f"It combines technical indicators, available fundamentals, market/macro proxies, news sentiment and risk adjustment. "
            f"The most prominent observed driver is: **{drivers.iloc[0]['Factor'] if not drivers.empty else 'N/A'}**."
        )
        st.write("### Company Snapshot")
        snap = {
            "Company": company,
            "Sector": profile.get("sector"),
            "Industry": profile.get("industry"),
            "Market Cap": profile.get("marketCap"),
            "P/E": profile.get("trailingPE") or profile.get("forwardPE"),
            "P/B": profile.get("priceToBook"),
            "ROE": profile.get("returnOnEquity"),
            "Debt to Equity": profile.get("debtToEquity"),
            "Profit Margin": profile.get("profitMargins"),
            "Revenue Growth": profile.get("revenueGrowth"),
            "Beta": profile.get("beta"),
        }
        st.dataframe(pd.DataFrame([snap]), use_container_width=True)
        st.write("### Market Universe Used")
        st.json(infer_market_universe(ticker))

    with tabs[1]:
        st.write("### 10-Year Price and Moving Averages")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=ind_df["Date"], y=ind_df["Close"], name="Close"))
        for ma in ["SMA_20", "SMA_50", "SMA_200"]:
            fig.add_trace(go.Scatter(x=ind_df["Date"], y=ind_df[ma], name=ma))
        fig.update_layout(height=520, xaxis_title="Date", yaxis_title="Price")
        st.plotly_chart(fig, use_container_width=True, key="price_ma_chart")

        st.write("### RSI")
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(x=ind_df["Date"], y=ind_df["RSI"], name="RSI"))
        fig_rsi.add_hline(y=70, line_dash="dash")
        fig_rsi.add_hline(y=30, line_dash="dash")
        fig_rsi.update_layout(height=330)
        st.plotly_chart(fig_rsi, use_container_width=True, key="rsi_chart")

        st.write("### MACD")
        fig_macd = go.Figure()
        fig_macd.add_trace(go.Scatter(x=ind_df["Date"], y=ind_df["MACD"], name="MACD"))
        fig_macd.add_trace(go.Scatter(x=ind_df["Date"], y=ind_df["MACD_Signal"], name="Signal"))
        fig_macd.update_layout(height=330)
        st.plotly_chart(fig_macd, use_container_width=True, key="macd_chart")

    with tabs[2]:
        st.write("### Component Scores")
        score_df = pd.DataFrame([{"Component": k, "Score": v} for k, v in rec["Component Scores"].items()])
        fig_scores = px.bar(score_df, x="Component", y="Score", text="Score", title="Multi-Factor Component Scores")
        st.plotly_chart(fig_scores, use_container_width=True, key="score_chart")
        st.dataframe(score_df, use_container_width=True)

        st.write("### What Is Driving the Share Price?")
        st.dataframe(drivers, use_container_width=True)
        st.caption("Prominence is based on absolute contribution. This is an explainability proxy, not a guarantee of true causation.")

    with tabs[3]:
        st.write("### Tentative Future Value")
        st.dataframe(forecast_df, use_container_width=True)
        fig_forecast = go.Figure()
        fig_forecast.add_trace(go.Scatter(x=forecast_df["Horizon"], y=forecast_df["Base Case"], name="Base Case"))
        fig_forecast.add_trace(go.Scatter(x=forecast_df["Horizon"], y=forecast_df["Bull Case"], name="Bull Case"))
        fig_forecast.add_trace(go.Scatter(x=forecast_df["Horizon"], y=forecast_df["Bear Case"], name="Bear Case"))
        fig_forecast.update_layout(height=420, yaxis_title="Tentative Price")
        st.plotly_chart(fig_forecast, use_container_width=True, key="forecast_chart")
        st.warning("Future value is a probability range based on historical behavior, current score and volatility. It is not guaranteed.")

    with tabs[4]:
        st.write("### Adaptive Multi-Factor Walk-Forward Backtesting")
        st.write(
            "This backtest trains only on data available before each historical test date, then checks whether the future direction was correct. "
            "It uses technical, market and macro proxy features. Fundamentals/news are included in current recommendation but not fully historical in this free-data MVP."
        )
        with st.spinner("Running adaptive backtest..."):
            bt, stats = run_adaptive_backtest(ind_df, macro_df, horizon_days=horizon_map[horizon_label])
        if bt.empty:
            st.warning(stats.get("message", "Backtest unavailable."))
        else:
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Directional Accuracy", f"{stats['Directional Accuracy %']}%")
            s2.metric("Rows Tested", stats["Rows Tested"])
            s3.metric("False Buy", stats["False Buy Count"])
            s4.metric("False Sell", stats["False Sell Count"])
            st.dataframe(bt, use_container_width=True)
            fig_bt = px.bar(bt, x="Date", y="Actual Return %", color="Direction Correct", title="Backtest Actual Returns by Historical Signal")
            st.plotly_chart(fig_bt, use_container_width=True, key="backtest_chart")
            st.info(stats["Important Note"])

    with tabs[5]:
        st.write("### Recent News Used for Sentiment Proxy")
        if news:
            for n in news:
                title = n.get("title") or "Untitled"
                link = n.get("link")
                pub = n.get("publisher") or ""
                if link:
                    st.markdown(f"- [{title}]({link}) — {pub}")
                else:
                    st.markdown(f"- {title} — {pub}")
        else:
            st.write("No recent news returned by the free data source.")

    with tabs[6]:
        st.write("### Ask the Analysis Chatbot")
        st.caption("Ask questions about the currently analyzed stock. This MVP chatbot uses the generated analysis context, not live broker advice.")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        for role, msg in st.session_state.chat_history:
            with st.chat_message(role):
                st.write(msg)
        q = st.chat_input("Ask: Why is it falling? Should I buy? What are the risks? What is the forecast?")
        if q:
            st.session_state.chat_history.append(("user", q))
            forecast_text = forecast_df.to_string(index=False)
            drivers_text = drivers.head(6).to_string(index=False) if not drivers.empty else "No drivers available."
            risk_text = f"Volatility: {latest_vol:.2%}; beta: {beta}; risk penalty: {risk_penalty}."
            context = {
                "recommendation": rec,
                "prominent": prominent,
                "forecast_text": forecast_text,
                "drivers_text": drivers_text,
                "risks": risk_text,
            }
            ans = answer_question(q, context)
            st.session_state.chat_history.append(("assistant", ans))
            st.rerun()
else:
    st.write("Enter a stock ticker and click Analyze Stock.")
