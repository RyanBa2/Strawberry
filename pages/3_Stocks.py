# pages/3_Stocks.py

import streamlit as st
import pandas as pd
import yfinance as yf
from utils import load_assets, save_assets

def main():
    st.title("Stocks")

    # 1) Load data
    assets = load_assets()
    stocks_data = assets.get("stocks", {})

    # ----------------------------------------------------
    # 2) Compute overall KRW/USD total (예수금 + 주식 실시간 평가)
    # ----------------------------------------------------
    grand_krw_total = 0.0
    grand_usd_total = 0.0

    # 각 계좌별 합계를 저장하기 위한 dict
    account_totals = {}

    # stocks_data에는 total_krw, total_usd가 이미 있을 수 있으나,
    # 이번에는 "실시간 주가 기반의" 총합을 다시 계산해보겠습니다.
    # => deposit + actual stock valuation
    for account_name, holdings in stocks_data.items():
        if account_name in ["total_krw", "total_usd"]:
            continue
        if not isinstance(holdings, list):
            continue
        acc_krw, acc_usd = compute_account_totals(holdings)
        account_totals[account_name] = (acc_krw, acc_usd)
        grand_krw_total += acc_krw
        grand_usd_total += acc_usd

    # 3) Summary: 보여줄 값(실시간 주가 기반 합)
    st.subheader("Summary of Stocks (Real-time Valuation)")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Stocks (KRW)", f"₩ {grand_krw_total:,.0f}")
    with col2:
        st.metric("Stocks (USD)", f"$ {grand_usd_total:,.2f}")

    st.write("---")

    # 4) Display each stock account
    st.subheader("Stock Accounts")
    for account_name, holdings in stocks_data.items():
        if account_name in ["total_krw", "total_usd"]:
            continue
        if not isinstance(holdings, list):
            continue

        st.markdown(f"### {account_name}")

        # 해당 계좌의 KRW/USD 실시간 총합
        acc_krw, acc_usd = account_totals.get(account_name, (0,0))

        # 작은 표시
        st.write(f"**Account Total**: ₩ {acc_krw:,.0f} / $ {acc_usd:,.2f}")

        with st.expander(f"{account_name} Details", expanded=False):
            if not holdings:
                st.write("No holdings yet in this account.")
            else:
                df = build_stock_dataframe(holdings)
                st.dataframe(df, use_container_width=True)

    st.write("---")
    st.subheader("Operations")

    # 탭 순서: Buy Stock, Sell Stock, Deposit, Withdraw, Exchange,
    #         Remove Zero Stocks, Add Stock Account, Delete Stock Account
    (tab_buy, tab_sell, tab_dep, tab_wd, tab_ex,
     tab_rmz, tab_add, tab_del) = st.tabs([
         "Buy Stock", "Sell Stock", "Deposit", "Withdraw",
         "Exchange", "Remove Zero Stocks",
         "Add Stock Account", "Delete Stock Account"
     ])

    # ---------------------------------------------------------
    # (A) Buy Stock
    # ---------------------------------------------------------
    with tab_buy:
        st.write("Buy (or add to) a stock holding in a chosen account.")
        buy_acc_list = [k for k in stocks_data.keys() if isinstance(stocks_data[k], list)]
        buy_acc_list = [acc for acc in buy_acc_list if acc not in ["total_krw", "total_usd"]]

        if not buy_acc_list:
            st.info("No stock accounts available.")
        else:
            selected_buy_acc = st.selectbox("Select Account", buy_acc_list, key="buy_acc")

            holdings = stocks_data[selected_buy_acc]
            existing_symbols = []
            for item in holdings:
                if item.get("name") in ("원화 예수금", "달러 예수금"):
                    continue
                existing_symbols.append(item["symbol"])

            all_symbol_options = ["[New Stock]"] + existing_symbols
            chosen_symbol = st.selectbox(
                "Choose a symbol (or 'New Stock')",
                all_symbol_options,
                key="choose_symbol_buy"
            )

            currency = "KRW"
            ticker = ""
            tags = ["#Investment Assets"]

            if chosen_symbol != "[New Stock]" and chosen_symbol in existing_symbols:
                stock_item = next((x for x in holdings if x.get("symbol") == chosen_symbol), None)
                if stock_item:
                    currency = stock_item.get("currency", "USD")
                    ticker = stock_item.get("ticker", "")
                    tags = stock_item.get("tags", [])
                    st.write(f"Symbol: **{chosen_symbol}** (existing)")
                    st.write(f"Ticker: **{ticker}** (existing)")
                    st.write(f"Currency: **{currency}** (existing)")
                    st.write(f"Tags: {tags} (existing)")
                else:
                    st.error("Could not find chosen symbol data.")
            else:
                # New
                user_symbol = st.text_input("Symbol (name) (e.g. Apple, 삼성전자)",
                                            value="", key="newstock_symbol_buy")
                user_ticker = st.text_input("Ticker (e.g. AAPL, 005930.KS)",
                                            value="", key="newstock_ticker_buy")
                currency = st.selectbox("Currency for this new stock", ["KRW", "USD"], key="newstock_cur_buy")
                possible_tags = [
                    "#Checking Account",
                    "#Receivables and Deposits",
                    "#Safe Assets",
                    "#Investment Assets"
                ]
                tags = st.multiselect("Tags", possible_tags, default=["#Investment Assets"], key="newstock_tags_buy")
                chosen_symbol = user_symbol.strip()
                ticker = user_ticker.strip()

            buy_price = st.number_input("Per share price (for your reference, not stored)",
                                        min_value=0.0, format="%g", value=0.0, step=1.0,
                                        key="buy_price")
            buy_qty = st.number_input("Quantity (shares)", min_value=0.0, format="%g",
                                      value=0.0, step=1.0, key="buy_qty")

            if st.button("Confirm Buy"):
                if chosen_symbol == "[New Stock]":
                    st.warning("Please enter a valid symbol name for the new stock.")
                elif buy_qty <= 0:
                    st.warning("Quantity must be > 0.")
                else:
                    deposit_item = None
                    cost_amount = buy_price * buy_qty
                    if currency == "KRW":
                        deposit_item = next((x for x in holdings if x.get("name") == "원화 예수금"), None)
                        if not deposit_item:
                            st.error("No KRW deposit found.")
                            return
                        if deposit_item["amount_krw"] < cost_amount:
                            st.error("Insufficient deposit in KRW.")
                            return
                        deposit_item["amount_krw"] -= cost_amount
                        stocks_data["total_krw"] -= cost_amount
                    else:
                        deposit_item = next((x for x in holdings if x.get("name") == "달러 예수금"), None)
                        if not deposit_item:
                            st.error("No USD deposit found.")
                            return
                        if deposit_item["amount_usd"] < cost_amount:
                            st.error("Insufficient deposit in USD.")
                            return
                        deposit_item["amount_usd"] -= cost_amount
                        stocks_data["total_usd"] -= cost_amount

                    if chosen_symbol in existing_symbols:
                        for it in holdings:
                            if it["symbol"] == chosen_symbol:
                                it["quantity"] += buy_qty
                                st.success(f"Added {buy_qty} shares to [{chosen_symbol}]. Deposit updated.")
                                break
                    else:
                        new_item = {
                            "symbol": chosen_symbol,
                            "ticker": ticker,
                            "currency": currency,
                            "quantity": buy_qty,
                            "tags": tags
                        }
                        holdings.append(new_item)
                        st.success(f"New symbol [{chosen_symbol}] with {buy_qty} shares added. Deposit updated.")

                    save_assets(assets)

    # ---------------------------------------------------------
    # (B) Sell Stock
    # ---------------------------------------------------------
    with tab_sell:
        st.write("Sell from a stock holding in a chosen account.")
        sell_acc_list = [k for k in stocks_data.keys() if isinstance(stocks_data[k], list)]
        sell_acc_list = [acc for acc in sell_acc_list if acc not in ["total_krw", "total_usd"]]

        if not sell_acc_list:
            st.info("No stock accounts available.")
        else:
            selected_sell_acc = st.selectbox("Select Account", sell_acc_list, key="sell_acc")
            holdings = stocks_data[selected_sell_acc]

            hold_symbols = []
            for item in holdings:
                if item.get("name") in ("원화 예수금", "달러 예수금"):
                    continue
                hold_symbols.append(item["symbol"])

            if not hold_symbols:
                st.info("No stock holdings to sell.")
            else:
                chosen_sell_symbol = st.selectbox("Choose a stock to sell", hold_symbols, key="choose_symbol_sell")
                stock_item = next((x for x in holdings if x.get("symbol") == chosen_sell_symbol), None)
                if stock_item:
                    st.write(f"Symbol: **{stock_item['symbol']}**")
                    st.write(f"Ticker: **{stock_item['ticker']}**")
                    st.write(f"Currency: **{stock_item['currency']}**")
                    st.write(f"Tags: {stock_item.get('tags', [])}")
                    st.write(f"Current shares: {stock_item['quantity']}")

                    sell_price = st.number_input("Sell share price", min_value=0.0, format="%g",
                                                 value=0.0, step=1.0, key="sell_price")
                    sell_qty = st.number_input("Quantity to sell", min_value=0.0, format="%g",
                                               value=0.0, step=1.0, key="sell_qty")

                    if st.button("Confirm Sell"):
                        if sell_qty <= 0:
                            st.warning("Quantity must be > 0.")
                        elif sell_qty > stock_item["quantity"]:
                            st.error(f"Not enough shares. You have {stock_item['quantity']}.")
                        else:
                            stock_item["quantity"] -= sell_qty
                            proceed = sell_price * sell_qty

                            if stock_item["currency"] == "KRW":
                                depo = next((x for x in holdings if x.get("name") == "원화 예수금"), None)
                                if not depo:
                                    st.error("Could not find 원화 예수금.")
                                    return
                                depo["amount_krw"] += proceed
                                stocks_data["total_krw"] += proceed
                            else:
                                depo = next((x for x in holdings if x.get("name") == "달러 예수금"), None)
                                if not depo:
                                    st.error("Could not find 달러 예수금.")
                                    return
                                depo["amount_usd"] += proceed
                                stocks_data["total_usd"] += proceed

                            st.success(f"Sold {sell_qty} shares of [{stock_item['symbol']}] for {proceed:,.0f}. Deposit updated.")
                            save_assets(assets)
                else:
                    st.error("Could not find that stock item.")

    # ---------------------------------------------------------
    # (C) Deposit
    # ---------------------------------------------------------
    with tab_dep:
        st.write("Deposit money into the chosen stock account (KRW or USD).")
        dep_acc_list = [k for k in stocks_data.keys() if isinstance(stocks_data[k], list)]
        dep_acc_list = [acc for acc in dep_acc_list if acc not in ["total_krw", "total_usd"]]

        if dep_acc_list:
            selected_acc = st.selectbox("Select Account", dep_acc_list, key="dep_acc")
            currency_type = st.selectbox("Currency", ["KRW", "USD"], key="dep_cur")
            dep_amount = st.number_input("Deposit Amount", min_value=0.0, format="%g",
                                         value=0.0, step=1000.0, key="dep_amount")

            if st.button("Deposit Now"):
                if dep_amount > 0:
                    success = deposit_stock_account(assets, selected_acc, currency_type, dep_amount)
                    if success:
                        save_assets(assets)
                        st.success(f"Deposited {dep_amount:,.0f} {currency_type} into [{selected_acc}].")
                    else:
                        st.error("Deposit failed: could not find the deposit item.")
                else:
                    st.warning("Please enter a valid deposit amount > 0.")
        else:
            st.info("No stock accounts available to deposit into.")

    # ---------------------------------------------------------
    # (D) Withdraw
    # ---------------------------------------------------------
    with tab_wd:
        st.write("Withdraw money from the chosen stock account (KRW or USD).")
        wd_acc_list = [k for k in stocks_data.keys() if isinstance(stocks_data[k], list)]
        wd_acc_list = [acc for acc in wd_acc_list if acc not in ["total_krw", "total_usd"]]

        if wd_acc_list:
            selected_acc = st.selectbox("Select Account", wd_acc_list, key="wd_acc")
            currency_type = st.selectbox("Currency", ["KRW", "USD"], key="wd_cur")
            wd_amount = st.number_input("Withdraw Amount", min_value=0.0, format="%g",
                                        value=0.0, step=1000.0, key="wd_amount")

            if st.button("Withdraw Now"):
                if wd_amount > 0:
                    result = withdraw_stock_account(assets, selected_acc, currency_type, wd_amount)
                    if result == "ok":
                        st.success(f"Withdrew {wd_amount:,.0f} {currency_type} from [{selected_acc}].")
                        save_assets(assets)
                    elif result == "insufficient":
                        st.error("Withdraw failed: insufficient balance.")
                    else:
                        st.error("Withdraw failed: deposit item not found or unknown error.")
                else:
                    st.warning("Please enter a valid withdraw amount > 0.")
        else:
            st.info("No stock accounts available to withdraw from.")

    # ---------------------------------------------------------
    # (E) Exchange
    # ---------------------------------------------------------
    with tab_ex:
        st.write("Exchange currency within a chosen account (KRW ↔ USD).")
        ex_acc_list = [k for k in stocks_data.keys() if isinstance(stocks_data[k], list)]
        ex_acc_list = [acc for acc in ex_acc_list if acc not in ["total_krw", "total_usd"]]

        if ex_acc_list:
            selected_acc = st.selectbox("Select Account", ex_acc_list, key="ex_acc")
            from_currency = st.selectbox("From Currency", ["KRW", "USD"], key="from_cur")
            to_currency = "KRW" if from_currency == "USD" else "USD"
            st.write(f"To Currency: **{to_currency}**")

            from_amount = st.number_input(f"How much {from_currency} to exchange?", min_value=0.0,
                                          format="%g", value=0.0, step=1000.0, key="from_amount")
            to_amount = st.number_input(f"Resulting {to_currency} amount (input manually)", min_value=0.0,
                                        format="%g", value=0.0, step=1000.0, key="to_amount")

            if st.button("Exchange Now"):
                if from_amount <= 0 or to_amount <= 0:
                    st.warning("Both from_amount and to_amount must be > 0.")
                else:
                    success = exchange_currency(assets, selected_acc, from_currency, to_currency, from_amount, to_amount)
                    if success == "ok":
                        save_assets(assets)
                        st.success(f"Exchanged {from_amount:,.0f} {from_currency} → {to_amount:,.0f} {to_currency}.")
                    elif success == "insufficient":
                        st.error("Insufficient balance in from_currency deposit.")
                    else:
                        st.error("Exchange failed. Possibly deposit item not found.")
        else:
            st.info("No stock accounts available for exchange.")

    # ---------------------------------------------------------
    # (F) Remove Zero Stocks
    # ---------------------------------------------------------
    with tab_rmz:
        st.write("Remove stocks with 0 quantity from a chosen account.")
        rmz_acc_list = [k for k in stocks_data.keys() if isinstance(stocks_data[k], list)]
        rmz_acc_list = [acc for acc in rmz_acc_list if acc not in ["total_krw", "total_usd"]]

        if rmz_acc_list:
            selected_rmz_acc = st.selectbox("Select Account", rmz_acc_list, key="rmz_acc")
            holdings_rmz = stocks_data[selected_rmz_acc]
            zero_stocks = [it["symbol"] for it in holdings_rmz
                           if it.get("name") not in ("원화 예수금", "달러 예수금")
                           and it.get("quantity", 0) == 0]
            if zero_stocks:
                chosen_zero_sym = st.selectbox("Select a 0-quantity stock to remove", zero_stocks, key="zero_sym")
                if st.button("Remove This 0-Quantity Stock"):
                    idx = None
                    for i, it in enumerate(holdings_rmz):
                        if it.get("symbol") == chosen_zero_sym and it.get("quantity", 0) == 0:
                            idx = i
                            break
                    if idx is not None:
                        del holdings_rmz[idx]
                        save_assets(assets)
                        st.success(f"Removed [{chosen_zero_sym}] which had 0 quantity.")
                    else:
                        st.error("Could not find or item is not zero quantity anymore.")
            else:
                st.info("No zero-quantity stocks in this account.")
        else:
            st.info("No stock accounts available.")

    # ---------------------------------------------------------
    # (G) Add Stock Account
    # ---------------------------------------------------------
    with tab_add:
        st.write("Create a new stock account.")
        new_account_name = st.text_input("New Stock Account Name", value="", key="add_stock_account_below")
        if st.button("Add Stock Account (below)"):
            acc_name_strip = new_account_name.strip()
            if acc_name_strip:
                if acc_name_strip in stocks_data:
                    st.warning(f"Account '{acc_name_strip}' already exists.")
                else:
                    stocks_data[acc_name_strip] = [
                        {
                            "name": "원화 예수금",
                            "amount_krw": 0,
                            "tags": ["#Investment Assets"]
                        },
                        {
                            "name": "달러 예수금",
                            "amount_usd": 0.0,
                            "tags": ["#Investment Assets"]
                        }
                    ]
                    save_assets(assets)
                    st.success(f"Stock account '{acc_name_strip}' created.")
            else:
                st.warning("Please enter a valid account name.")

    # ---------------------------------------------------------
    # (H) Delete Stock Account
    # ---------------------------------------------------------
    with tab_del:
        st.write("Delete an existing stock account (including its holdings).")
        existing_accounts = [k for k in stocks_data.keys() if isinstance(stocks_data[k], list)]
        existing_accounts = [acc for acc in existing_accounts if acc not in ("total_krw","total_usd")]
        if existing_accounts:
            del_acc = st.selectbox("Select an account to delete", existing_accounts, key="del_stock_account_below")
            if st.button("Delete Account (below)"):
                if del_acc in stocks_data:
                    del_holdings = stocks_data[del_acc]
                    # subtract deposit from total
                    krw_deposit = next((x for x in del_holdings if x.get("name") == "원화 예수금"), None)
                    if krw_deposit:
                        amt_krw = krw_deposit.get("amount_krw", 0)
                        stocks_data["total_krw"] -= amt_krw

                    usd_deposit = next((x for x in del_holdings if x.get("name") == "달러 예수금"), None)
                    if usd_deposit:
                        amt_usd = usd_deposit.get("amount_usd", 0)
                        stocks_data["total_usd"] -= amt_usd

                    del stocks_data[del_acc]
                    save_assets(assets)
                    st.success(f"Stock account '{del_acc}' has been deleted.")
                else:
                    st.error("Account not found or already deleted.")
        else:
            st.info("No stock accounts to delete.")

# ------------------------------------------------------------------------------
# HELPER FUNCTIONS
# ------------------------------------------------------------------------------

def compute_account_totals(holdings: list):
    """
    계좌 내 예수금 + 주식실시간가치 합산 (원화, 달러 분리)
    returns (acc_krw, acc_usd)
    """
    acc_krw = 0.0
    acc_usd = 0.0

    for item in holdings:
        # 예수금
        if item.get("name") == "원화 예수금":
            acc_krw += item.get("amount_krw", 0.0)
        elif item.get("name") == "달러 예수금":
            acc_usd += item.get("amount_usd", 0.0)
        else:
            # 주식
            cur = item.get("currency", "USD")
            qty = item.get("quantity", 0.0)
            ticker = item.get("ticker", "")
            if cur == "KRW":
                # 한국 종목 => fetch_live_price_KRW
                if ticker.endswith(".KS") or ticker.endswith(".KQ"):
                    live_krw = fetch_live_price_KRW(ticker)
                else:
                    # 기타 -> fetch USD + 환율
                    live_usd = fetch_live_price_USD(ticker)
                    exch_rate = 1350
                    live_krw = live_usd * exch_rate
                acc_krw += live_krw * qty
            else:
                # USD 주식
                live_usd = fetch_live_price_USD(ticker)
                acc_usd += live_usd * qty

    return acc_krw, acc_usd


def build_stock_dataframe(holdings: list) -> pd.DataFrame:
    rows = []
    for item in holdings:
        if item.get("name") in ("원화 예수금", "달러 예수금"):
            # deposit
            if "amount_krw" in item:
                sym = item["name"]
                amount = item["amount_krw"]
                row = {
                    "symbol": sym,
                    "KRW Price": "-",
                    "USD Price": "-",
                    "Quantity": f"{amount:,.0f}",
                    "KRW Value": amount,
                    "USD Value": "-",
                    "ticker": "(Deposit)",
                    "tags": item.get("tags", [])
                }
                rows.append(row)
            elif "amount_usd" in item:
                sym = item["name"]
                amount = item["amount_usd"]
                row = {
                    "symbol": sym,
                    "KRW Price": "-",
                    "USD Price": "-",
                    "Quantity": f"{amount:,.2f}",
                    "KRW Value": "-",
                    "USD Value": amount,
                    "ticker": "(Deposit)",
                    "tags": item.get("tags", [])
                }
                rows.append(row)
            continue

        symbol = item.get("symbol", "")
        ticker = item.get("ticker", "")
        currency = item.get("currency", "USD")
        quantity = item.get("quantity", 0.0)
        tags = item.get("tags", [])

        krw_price_str, usd_price_str = "-", "-"
        krw_value_str, usd_value_str = "-", "-"

        if currency == "KRW":
            # 한국 종목 => fetch_live_price_KRW(ticker)
            if ticker.endswith(".KS") or ticker.endswith(".KQ"):
                price_in_krw = fetch_live_price_KRW(ticker)
                krw_price_str = f"{price_in_krw:,.0f}"
                krw_value_str = f"{price_in_krw * quantity:,.0f}"
            else:
                # 기타 -> usd + 환율
                price_in_usd = fetch_live_price_USD(ticker) if ticker else 0.0
                exch_rate = 1350
                price_in_krw = price_in_usd * exch_rate
                krw_price_str = f"{price_in_krw:,.0f}"
                krw_value_str = f"{price_in_krw * quantity:,.0f}"

        else:
            price_in_usd = fetch_live_price_USD(ticker) if ticker else 0.0
            usd_price_str = f"{price_in_usd:,.2f}"
            usd_value_str = f"{price_in_usd * quantity:,.2f}"

        row = {
            "symbol": symbol,
            "KRW Price": krw_price_str,
            "USD Price": usd_price_str,
            "Quantity": f"{quantity:,.2f}",
            "KRW Value": krw_value_str,
            "USD Value": usd_value_str,
            "ticker": ticker,
            "tags": tags
        }
        rows.append(row)

    df = pd.DataFrame(rows, columns=[
        "symbol", "KRW Price", "USD Price", "Quantity",
        "KRW Value", "USD Value", "ticker", "tags"
    ])
    return df


def fetch_live_price_KRW(ticker: str) -> float:
    """Fetch recent price for Korean ticker from yfinance in KRW. If fail, return 0."""
    if not ticker:
        return 0.0
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d")
        if not hist.empty:
            return float(hist["Close"][-1])
        else:
            return 0.0
    except:
        return 0.0

def fetch_live_price_USD(ticker: str) -> float:
    """Fetch recent price in USD from yfinance. Return 0 if fail/no data."""
    if not ticker:
        return 0.0
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d")
        if not hist.empty:
            return float(hist["Close"][-1])
        else:
            return 0.0
    except:
        return 0.0

def deposit_stock_account(assets: dict, account_name: str, currency: str, amount: float) -> bool:
    stocks_data = assets["stocks"]
    if account_name not in stocks_data:
        return False
    holdings = stocks_data[account_name]
    if currency == "KRW":
        for item in holdings:
            if item.get("name") == "원화 예수금":
                item["amount_krw"] += amount
                stocks_data["total_krw"] += amount
                return True
        return False
    else:
        for item in holdings:
            if item.get("name") == "달러 예수금":
                item["amount_usd"] += amount
                stocks_data["total_usd"] += amount
                return True
        return False

def withdraw_stock_account(assets: dict, account_name: str, currency: str, amount: float):
    stocks_data = assets["stocks"]
    if account_name not in stocks_data:
        return False
    holdings = stocks_data[account_name]

    if currency == "KRW":
        for item in holdings:
            if item["name"] == "원화 예수금":
                if item["amount_krw"] < amount:
                    return "insufficient"
                item["amount_krw"] -= amount
                stocks_data["total_krw"] -= amount
                return "ok"
        return False
    else:  # USD
        for item in holdings:
            if item["name"] == "달러 예수금":
                if item["amount_usd"] < amount:
                    return "insufficient"
                item["amount_usd"] -= amount
                stocks_data["total_usd"] -= amount
                return "ok"
        return False

def exchange_currency(assets: dict, account_name: str, from_cur: str, to_cur: str, from_amt: float, to_amt: float):
    """
    환전 로직:
    - from_cur 예수금 -= from_amt
    - to_cur 예수금 += to_amt
    """
    stocks_data = assets["stocks"]
    if account_name not in stocks_data:
        return False
    holdings = stocks_data[account_name]

    if from_cur not in ["KRW", "USD"] or to_cur not in ["KRW", "USD"]:
        return False
    if from_cur == to_cur:
        return False

    # from
    if from_cur == "KRW":
        from_item = next((x for x in holdings if x.get("name") == "원화 예수금"), None)
        if not from_item:
            return False
        if from_item["amount_krw"] < from_amt:
            return "insufficient"
        from_item["amount_krw"] -= from_amt
        stocks_data["total_krw"] -= from_amt
    else:
        from_item = next((x for x in holdings if x.get("name") == "달러 예수금"), None)
        if not from_item:
            return False
        if from_item["amount_usd"] < from_amt:
            return "insufficient"
        from_item["amount_usd"] -= from_amt
        stocks_data["total_usd"] -= from_amt

    # to
    if to_cur == "KRW":
        to_item = next((x for x in holdings if x.get("name") == "원화 예수금"), None)
        if not to_item:
            return False
        to_item["amount_krw"] += to_amt
        stocks_data["total_krw"] += to_amt
    else:
        to_item = next((x for x in holdings if x.get("name") == "달러 예수금"), None)
        if not to_item:
            return False
        to_item["amount_usd"] += to_amt
        stocks_data["total_usd"] += to_amt

    return "ok"


if __name__ == "__main__":
    main()