# Share Trading Analysis Platform - Streamlit MVP

This is a beginner-friendly Streamlit app for educational stock analysis.

## Files required at the top level of GitHub repository

Your GitHub repository should look exactly like this:

```text
app.py
requirements.txt
README.md
modules/
```

Inside `modules/`, you should see Python files such as `data_fetcher.py`, `technical_analysis.py`, `recommendation_engine.py`, etc.

## Deploy on Streamlit Community Cloud

1. Upload all files to GitHub.
2. Go to Streamlit Community Cloud.
3. Click **Create app** / **New app**.
4. Select your GitHub repository.
5. Branch: `main`.
6. Main file path: `app.py`.
7. Open **Advanced settings** and select Python `3.11` or `3.12` if available.
8. Click **Deploy**.

## If you get "Server not responding"

1. Open your Streamlit app page.
2. Click **Manage app** in the lower-right corner.
3. Click **Logs**.
4. Check the latest red error message.
5. Common fixes:
   - Make sure `requirements.txt` is uploaded at the same level as `app.py`.
   - Make sure the `modules` folder is uploaded.
   - In Streamlit Advanced settings, select Python 3.11 or 3.12.
   - Reboot the app after changes.

## Example tickers

US stocks:

```text
AAPL
MSFT
TSLA
NVDA
```

Indian NSE stocks:

```text
RELIANCE.NS
TCS.NS
HDFCBANK.NS
INFY.NS
```

## Run locally, optional

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Disclaimer

This app is for educational and research use only. It is not financial advice. Stock market predictions can be wrong.
