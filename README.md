# Investing Club Portfolio Dashboard (Streamlit)

This is a lightweight dashboard to visualise the same Excel tracker you’re using today (Holdings vs S&P500 vs Anti-Portfolio).

## What it does
- Upload your existing Excel workbook (same format / sheet names)
- Shows:
  - Overview KPIs (cost, value, return)
  - Holdings table with filters
  - Benchmark cumulative returns by month
  - Club excess return vs benchmarks

Nothing is stored; the workbook is processed in-session.

## Required sheet names
- `Holdings`
- `S&P500`
- `Anti-Portfolio`

## Run locally
1. Install Python 3.10+
2. Install deps:
   ```
   pip install -r requirements.txt
   ```
3. Start:
   ```
   streamlit run app.py
   ```

## Host for free (recommended): Streamlit Community Cloud
1. Create a GitHub repo and upload:
   - `app.py`
   - `requirements.txt`
2. Go to Streamlit Community Cloud
3. Deploy the repo (select `app.py` as entrypoint)
4. Share the URL with your club

## Notes
- Today it reads values already in your Excel.
- If you want *automatic* live pricing & FX, we can add:
  - `yfinance` price pulls
  - FX from an API
  - scheduled refresh + hosted dataset
