import streamlit as st
import pandas as pd
import yfinance as yf
from utils import load_assets, save_assets

st.set_page_config(page_title="My Assets Overview", layout="wide")
st.title("My Assets (Home)")

# -----------------------------
# 환율 관련 함수 (yfinance 활용)
# -----------------------------
def fetch_exchange_rate() -> float:
    try:
        data = yf.Ticker("KRX=X")
        hist = data.history(period="1d")
        if not hist.empty:
            return float(hist["Close"][-1])
        else:
            return 1350.0
    except Exception:
        return 1350.0

# -----------------------------
# Stocks 관련 헬퍼 함수
# -----------------------------
def fetch_live_price_KRW(ticker: str) -> float:
    if not ticker:
        return 0.0
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d")
        if not hist.empty:
            return float(hist["Close"][-1])
        else:
            return 0.0
    except Exception:
        return 0.0

def fetch_live_price_USD(ticker: str) -> float:
    if not ticker:
        return 0.0
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d")
        if not hist.empty:
            return float(hist["Close"][-1])
        else:
            return 0.0
    except Exception:
        return 0.0

def compute_stock_totals(holdings: list, exch_rate: float):
    acc_krw = 0.0
    acc_usd = 0.0
    for item in holdings:
        if item.get("name") == "원화 예수금":
            acc_krw += item.get("amount_krw", 0.0)
        elif item.get("name") == "달러 예수금":
            acc_usd += item.get("amount_usd", 0.0)
        else:
            cur = item.get("currency", "USD")
            qty = item.get("quantity", 0.0)
            ticker = item.get("ticker", "")
            if cur == "KRW":
                if ticker.endswith(".KS") or ticker.endswith(".KQ"):
                    live_krw = fetch_live_price_KRW(ticker)
                else:
                    live_usd = fetch_live_price_USD(ticker)
                    live_krw = live_usd * exch_rate
                acc_krw += live_krw * qty
            else:
                live_usd = fetch_live_price_USD(ticker)
                acc_usd += live_usd * qty
    return acc_krw, acc_usd

def aggregate_stock_assets(stocks_data: dict, exch_rate: float):
    total_krw = 0.0
    total_usd = 0.0
    for account_name, holdings in stocks_data.items():
        if account_name in ["total_krw", "total_usd"]:
            continue
        if isinstance(holdings, list):
            acc_krw, acc_usd = compute_stock_totals(holdings, exch_rate)
            total_krw += acc_krw
            total_usd += acc_usd
    return total_krw, total_usd

# -----------------------------
# 각 자산 카테고리 집계 함수
# -----------------------------
def aggregate_liquid_assets(liquid_assets: dict):
    return liquid_assets.get("total_krw", 0)

def aggregate_receivables_deposits(rd: dict):
    return rd.get("total_krw", 0)

def aggregate_cryptocurrency(crypto: dict, exch_rate: float):
    crypto_usd = crypto.get("total_usd", 0)
    crypto_krw = crypto_usd * exch_rate
    return crypto_krw, crypto_usd

#################################
# 1) 전체 자산 요약 계산
#################################
assets = load_assets()
exch_rate = fetch_exchange_rate()

liquid_total = aggregate_liquid_assets(assets.get("liquid_assets", {}))
rd_total = aggregate_receivables_deposits(assets.get("receivables_and_deposits", {}))
stocks_krw, stocks_usd = aggregate_stock_assets(assets.get("stocks", {}), exch_rate)
crypto_krw, crypto_usd = aggregate_cryptocurrency(assets.get("cryptocurrency", {}), exch_rate)

# (A) KRW 자산 합
total_krw = liquid_total + rd_total + stocks_krw + crypto_krw
# (B) USD 자산 합
total_usd = stocks_usd + crypto_usd
# (C) Combined Total in KRW
combined_total_krw = total_krw + (total_usd * exch_rate)

#################################
# 2) 화면 배치
#################################

st.subheader("Combined Total in KRW")
st.markdown(f"## ₩ {int(combined_total_krw):,}")

# 여기서 폰트 크기를 subheader보다 작은 일반 텍스트 형태로 조정
st.write(
    f"**Total (KRW)**: ₩ {int(total_krw):,} &nbsp;/&nbsp; "
    f"**Total (USD)**: $ {total_usd:,.2f}"
)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Liquid Assets (₩)", f"₩ {liquid_total:,.0f}")
with col2:
    st.metric("Savings/Deposits (₩)", f"₩ {rd_total:,.0f}")
with col3:
    st.metric("Stocks (₩)", f"₩ {stocks_krw:,.0f}")
with col4:
    st.metric("Stocks (USD)", f"$ {stocks_usd:,.2f}")
with col5:
    st.metric("Cryptocurrency (₩)", f"₩ {crypto_krw:,.0f}")

st.write("---")
st.write("<br><br>", unsafe_allow_html=True)
st.info("Use the sidebar to navigate to other pages.")