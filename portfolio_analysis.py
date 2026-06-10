from __future__ import annotations
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


def build_feature_frame(stock_ind: pd.DataFrame, macro_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = stock_ind.copy().sort_values("Date")
    if macro_df is not None and not macro_df.empty:
        df = pd.merge(df, macro_df, on="Date", how="left").sort_values("Date").ffill()
    for col in ["benchmark", "vix", "yield", "crude", "currency", "gold"]:
        if col in df.columns:
            df[f"{col}_ret_21d"] = df[col].pct_change(21)
            df[f"{col}_ret_63d"] = df[col].pct_change(63)
    df["price_vs_sma20"] = df["Close"] / df["SMA_20"] - 1
    df["price_vs_sma50"] = df["Close"] / df["SMA_50"] - 1
    df["price_vs_sma200"] = df["Close"] / df["SMA_200"] - 1
    df["vol_chg"] = df["Volume_Ratio"].replace([np.inf, -np.inf], np.nan)
    features = [
        "Return_21D", "Return_63D", "RSI", "MACD_Hist", "Volatility_21D", "Volume_Ratio",
        "price_vs_sma20", "price_vs_sma50", "price_vs_sma200",
        "benchmark_ret_21d", "benchmark_ret_63d", "vix_ret_21d", "yield_ret_63d",
        "crude_ret_63d", "currency_ret_63d", "gold_ret_63d"
    ]
    for f in features:
        if f not in df.columns:
            df[f] = 0
    return df[["Date", "Close"] + features].replace([np.inf, -np.inf], np.nan).dropna()


def run_adaptive_backtest(stock_ind: pd.DataFrame, macro_df: pd.DataFrame | None = None, horizon_days: int = 63, step_days: int = 21, min_train_days: int = 756) -> tuple[pd.DataFrame, dict]:
    ff = build_feature_frame(stock_ind, macro_df)
    features = [c for c in ff.columns if c not in ["Date", "Close"]]
    ff["Future_Close"] = ff["Close"].shift(-horizon_days)
    ff["Future_Return"] = ff["Future_Close"] / ff["Close"] - 1
    ff["Target"] = np.where(ff["Future_Return"] > 0.025, 1, np.where(ff["Future_Return"] < -0.025, -1, 0))
    ff = ff.dropna(subset=["Future_Close", "Target"])
    rows = []
    if len(ff) < min_train_days + horizon_days + 10:
        return pd.DataFrame(), {"message": "Not enough data for adaptive walk-forward backtest."}
    idxs = list(range(min_train_days, len(ff) - horizon_days, step_days))[-36:]
    for i in idxs:
        train = ff.iloc[:i]
        test = ff.iloc[[i]]
        X_train, y_train = train[features], train["Target"]
        X_test = test[features]
        model = Pipeline([
            ("scaler", StandardScaler()),
            ("rf", RandomForestClassifier(n_estimators=250, max_depth=5, min_samples_leaf=10, random_state=42, class_weight="balanced"))
        ])
        model.fit(X_train, y_train)
        proba = model.predict_proba(X_test)[0]
        classes = list(model.named_steps["rf"].classes_)
        probs = {int(c): float(p) for c, p in zip(classes, proba)}
        up_p = probs.get(1, 0.0); down_p = probs.get(-1, 0.0); flat_p = probs.get(0, 0.0)
        if up_p >= max(down_p, flat_p) and up_p > 0.40:
            rec = "Buy"
        elif down_p >= max(up_p, flat_p) and down_p > 0.40:
            rec = "Sell"
        else:
            rec = "Hold"
        actual_ret = float(test["Future_Return"].iloc[0])
        if rec == "Buy": correct = actual_ret > 0
        elif rec == "Sell": correct = actual_ret < 0
        else: correct = abs(actual_ret) <= 0.04
        rows.append({
            "Date": test["Date"].iloc[0].date().isoformat(),
            "Recommendation": rec,
            "Model Up Probability": round(up_p, 2),
            "Model Down Probability": round(down_p, 2),
            "Price Then": round(float(test["Close"].iloc[0]), 2),
            "Actual Future Price": round(float(test["Future_Close"].iloc[0]), 2),
            "Actual Return %": round(actual_ret * 100, 2),
            "Direction Correct": "Yes" if correct else "No",
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out, {"message":"No backtest rows generated."}
    accuracy = round((out["Direction Correct"] == "Yes").mean() * 100, 2)
    avg_return_buy = round(out.loc[out["Recommendation"] == "Buy", "Actual Return %"].mean(), 2) if (out["Recommendation"] == "Buy").any() else None
    stats = {
        "Directional Accuracy %": accuracy,
        "Rows Tested": len(out),
        "Average Actual Return after Buy %": avg_return_buy,
        "False Buy Count": int(((out["Recommendation"] == "Buy") & (out["Actual Return %"] < 0)).sum()),
        "False Sell Count": int(((out["Recommendation"] == "Sell") & (out["Actual Return %"] > 0)).sum()),
        "Important Note": "This is a walk-forward adaptive model using only data available before each test date. 95% accuracy cannot be guaranteed in real markets."
    }
    return out, stats
