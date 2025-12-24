import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Investing Club Dashboard", layout="wide")

# -----------------------
# Helpers
# -----------------------
def to_month_key(x) -> str:
    if pd.isna(x):
        return ""
    try:
        d = pd.to_datetime(x)
        return f"{d.year:04d}-{d.month:02d}"
    except Exception:
        return str(x).strip()

def pct(x):
    if pd.isna(x):
        return np.nan
    return float(x)

def safe_num(s):
    return pd.to_numeric(s, errors="coerce")

@st.cache_data(show_spinner=False)
def load_workbook(file_bytes: bytes):
    # Read sheets
    xls = pd.ExcelFile(file_bytes)
    sheet_names = xls.sheet_names

    def read_sheet(name):
        if name not in sheet_names:
            return None
        df = pd.read_excel(xls, sheet_name=name)
        return df

    holdings = read_sheet("Holdings")
    sp = read_sheet("S&P500")
    anti = read_sheet("Anti-Portfolio")
    return holdings, sp, anti, sheet_names

def normalise_holdings(df: pd.DataFrame) -> pd.DataFrame:
    # Expect your file’s column names (works even if extra unnamed cols exist)
    # Keep only relevant columns if present.
    cols = [
        "Month","Stock","Ticker","Total Return","vs Anti-Portfolio","vs S&P500",
        "Stock Return","Currency Return","Dividend Return",
        "Current Value $A","Initial Investment $A","Overall Return $A (incl. Dividends)",
        "Qty","Dividends USD","Buy Price USD","Curent Price USD","Current Value USD",
        "QuoteCurrency","AUD/USD at Trade*","AUD/USD Now"
    ]
    have = [c for c in cols if c in df.columns]
    out = df[have].copy()

    # Drop empty rows (no ticker + no stock)
    key_cols = [c for c in ["Ticker","Stock"] if c in out.columns]
    if key_cols:
        out = out.dropna(subset=key_cols, how="all")

    # Month key
    if "Month" in out.columns:
        out["MonthKey"] = out["Month"].apply(to_month_key)

    # Numerics
    for c in [
        "Total Return","vs Anti-Portfolio","vs S&P500","Stock Return","Currency Return","Dividend Return",
        "Current Value $A","Initial Investment $A","Overall Return $A (incl. Dividends)",
        "Qty","Dividends USD","Buy Price USD","Curent Price USD","Current Value USD",
        "AUD/USD at Trade*","AUD/USD Now"
    ]:
        if c in out.columns:
            out[c] = safe_num(out[c])

    return out

def normalise_benchmark(df: pd.DataFrame, name: str) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["Month","MonthKey","Total Return","Benchmark"])
    out = df.copy()
    # Try to find the month column and total return column
    month_col = "Month" if "Month" in out.columns else out.columns[0]
    tr_col = "Total Return" if "Total Return" in out.columns else None
    if tr_col is None:
        # fallback: pick a column containing 'Return'
        for c in out.columns:
            if "return" in str(c).lower():
                tr_col = c
                break
    if tr_col is None:
        tr_col = out.columns[1] if len(out.columns) > 1 else out.columns[0]

    out = out[[month_col, tr_col]].copy()
    out.columns = ["Month","Total Return"]
    out["MonthKey"] = out["Month"].apply(to_month_key)
    out["Total Return"] = safe_num(out["Total Return"])
    out["Benchmark"] = name
    out = out.dropna(subset=["MonthKey"])
    return out

def make_line_chart(df: pd.DataFrame, x: str, y: str, label: str):
    fig, ax = plt.subplots()
    ax.plot(df[x], df[y], marker="o")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title(label)
    ax.grid(True, alpha=0.25)
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig, use_container_width=True)

def make_bar_chart(df: pd.DataFrame, x: str, y: str, label: str):
    fig, ax = plt.subplots()
    ax.bar(df[x], df[y])
    ax.set_title(label)
    ax.grid(True, axis="y", alpha=0.25)
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig, use_container_width=True)

# -----------------------
# UI: upload or use sample
# -----------------------
st.title("📈 Investing Club Portfolio Dashboard")

with st.sidebar:
    st.header("Data source")
    up = st.file_uploader("Upload your Excel (same format as your tracker)", type=["xlsx"])
    st.caption("Tip: keep the sheet names: Holdings, S&P500, Anti-Portfolio.")

    st.divider()
    st.header("Views")
    view = st.radio("Choose dashboard view", ["Overview", "Holdings", "Benchmarks", "Attribution"], index=0)

if up is None:
    st.info("Upload your Excel to begin. Nothing is stored — it runs in your browser session.")
    st.stop()

holdings_raw, sp_raw, anti_raw, sheet_names = load_workbook(up.getvalue())

if holdings_raw is None or holdings_raw.empty:
    st.error("Couldn't find a non-empty 'Holdings' sheet. Check your workbook tabs.")
    st.stop()

holdings = normalise_holdings(holdings_raw)
sp = normalise_benchmark(sp_raw, "S&P500")
anti = normalise_benchmark(anti_raw, "Anti-Portfolio")

# -----------------------
# Common derived metrics
# -----------------------
base_currency = "AUD"
as_at = dt.date.today().strftime("%d %b %Y")

# totals (latest snapshot)
total_cost = float(holdings["Initial Investment $A"].sum()) if "Initial Investment $A" in holdings.columns else np.nan
total_value = float(holdings["Current Value $A"].sum()) if "Current Value $A" in holdings.columns else np.nan
total_pl = float(holdings["Overall Return $A (incl. Dividends)"].sum()) if "Overall Return $A (incl. Dividends)" in holdings.columns else np.nan
total_ret = (total_pl / total_cost) if (not np.isnan(total_cost) and total_cost != 0) else np.nan

# weights
if "Current Value $A" in holdings.columns and total_value and not np.isnan(total_value) and total_value != 0:
    holdings["Weight"] = holdings["Current Value $A"] / total_value
else:
    holdings["Weight"] = np.nan

# -----------------------
# Overview
# -----------------------
if view == "Overview":
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("As at", as_at)
    c2.metric("Total cost (AUD)", f"{total_cost:,.0f}" if not np.isnan(total_cost) else "—")
    c3.metric("Current value (AUD)", f"{total_value:,.0f}" if not np.isnan(total_value) else "—")
    c4.metric("Total return", f"{total_ret*100:,.2f}%" if not np.isnan(total_ret) else "—")

    st.subheader("Top positions by weight")
    top = holdings.sort_values("Weight", ascending=False).head(10).copy()
    show_cols = [c for c in ["Ticker","Stock","Current Value $A","Weight","Total Return","vs S&P500","vs Anti-Portfolio"] if c in top.columns]
    if "Weight" in show_cols:
        top["Weight"] = (top["Weight"] * 100).round(2)
        top = top.rename(columns={"Weight":"Weight (%)"})
    st.dataframe(top[show_cols], use_container_width=True)

    st.subheader("Returns by position")
    chart_df = holdings.dropna(subset=["Total Return"]).copy() if "Total Return" in holdings.columns else holdings.copy()
    if "Ticker" in chart_df.columns and "Total Return" in chart_df.columns:
        tmp = chart_df.groupby("Ticker", as_index=False)["Total Return"].mean().sort_values("Total Return", ascending=False)
        make_bar_chart(tmp, "Ticker", "Total Return", "Average Total Return by Ticker")
    else:
        st.caption("Couldn’t find 'Ticker' and 'Total Return' columns to chart.")

# -----------------------
# Holdings table + filters
# -----------------------
elif view == "Holdings":
    st.subheader("Holdings")
    col1, col2, col3 = st.columns([2, 2, 2])
    tickers = sorted([t for t in holdings["Ticker"].dropna().astype(str).unique()]) if "Ticker" in holdings.columns else []
    months = sorted([m for m in holdings["MonthKey"].dropna().astype(str).unique()]) if "MonthKey" in holdings.columns else []

    with col1:
        sel_tickers = st.multiselect("Tickers", tickers, default=tickers)
    with col2:
        sel_months = st.multiselect("Months", months, default=months)
    with col3:
        sort_by = st.selectbox("Sort by", [c for c in ["Weight","Total Return","vs S&P500","vs Anti-Portfolio","Stock Return","Dividend Return"] if c in holdings.columns] or ["Ticker"])

    df = holdings.copy()
    if "Ticker" in df.columns and sel_tickers:
        df = df[df["Ticker"].astype(str).isin(sel_tickers)]
    if "MonthKey" in df.columns and sel_months:
        df = df[df["MonthKey"].astype(str).isin(sel_months)]
    if sort_by in df.columns:
        df = df.sort_values(sort_by, ascending=False)

    # format
    out = df.copy()
    if "Weight" in out.columns:
        out["Weight (%)"] = (out["Weight"] * 100).round(2)
    st.dataframe(out, use_container_width=True)

# -----------------------
# Benchmarks time series
# -----------------------
elif view == "Benchmarks":
    st.subheader("Benchmarks: Total Return by Month")
    bench = pd.concat([sp, anti], ignore_index=True)
    if bench.empty:
        st.caption("No benchmark data found.")
        st.stop()

    # Sort month keys and make cumulative if your sheet is per-month total return
    bench = bench.dropna(subset=["MonthKey","Total Return"]).copy()
    bench = bench.sort_values("MonthKey")

    # compute cumulative (compound) series per benchmark
    bench["MonthlyReturn"] = bench["Total Return"]
    bench["CumReturn"] = bench.groupby("Benchmark")["MonthlyReturn"].transform(lambda s: (1 + s).cumprod() - 1)

    # pivot for plot
    piv = bench.pivot_table(index="MonthKey", columns="Benchmark", values="CumReturn", aggfunc="last").reset_index()
    st.dataframe(piv, use_container_width=True)

    for b in [c for c in piv.columns if c != "MonthKey"]:
        tmp = piv[["MonthKey", b]].dropna()
        make_line_chart(tmp, "MonthKey", b, f"Cumulative Return: {b}")

# -----------------------
# Attribution: club vs benchmarks
# -----------------------
else:
    st.subheader("Attribution: Club vs Benchmarks (by Month)")
    if "MonthKey" not in holdings.columns or "Total Return" not in holdings.columns:
        st.caption("Need 'Month' and 'Total Return' in Holdings to compute month-level comparison.")
        st.stop()

    club = holdings.dropna(subset=["MonthKey","Total Return"]).copy()
    # average per month across positions (simple equal-weight proxy, matching your sheet’s per-line return approach)
    club_m = club.groupby("MonthKey", as_index=False)["Total Return"].mean()
    club_m = club_m.rename(columns={"Total Return":"Club Total Return"})

    sp_m = sp[["MonthKey","Total Return"]].rename(columns={"Total Return":"S&P500 Total Return"})
    anti_m = anti[["MonthKey","Total Return"]].rename(columns={"Total Return":"Anti Total Return"})

    comp = club_m.merge(sp_m, on="MonthKey", how="left").merge(anti_m, on="MonthKey", how="left")
    comp = comp.sort_values("MonthKey")
    comp["Club vs S&P500"] = comp["Club Total Return"] - comp["S&P500 Total Return"]
    comp["Club vs Anti"] = comp["Club Total Return"] - comp["Anti Total Return"]

    st.dataframe(comp, use_container_width=True)

    make_line_chart(comp, "MonthKey", "Club Total Return", "Club Total Return (Avg across positions)")
    if "Club vs S&P500" in comp.columns:
        make_line_chart(comp, "MonthKey", "Club vs S&P500", "Excess Return vs S&P500")
    if "Club vs Anti" in comp.columns:
        make_line_chart(comp, "MonthKey", "Club vs Anti", "Excess Return vs Anti-Portfolio")

st.caption("If you want this to auto-pull live prices & FX, we can add a nightly refresh script and redeploy.")