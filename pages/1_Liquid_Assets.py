# pages/1_Liquid_Assets.py

import streamlit as st
import pandas as pd
from utils import load_assets, save_assets

def main():
    # 간단한 CSS 삽입: 특정 요소 사이 간격을 조정
    custom_css = """
    <style>
    /* 전체 페이지 폰트 사이즈/라인 간격 조정 (선택사항) */
    /* .css-1fv8s86 {margin-top:0.5rem;}  */

    /* Total Liquid 부분 간격 줄이기 */
    .total-liquid-label {
        margin-bottom: 0px; /* label과 숫자 사이 공간 축소 */
    }
    .total-liquid-value {
        margin-top: -15px; /* 숫자 위 공간을 조금 당겨서 좁힘 */
        margin-bottom: 20px; /* 숫자 아래 공간 조금 */
    }

    /* Checking / Savings / Installment  사이 간격 늘리기 */
    .account-type-label {
        margin-top: 30px;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    st.title("Liquid Assets")

    # 1) Load data
    assets = load_assets()  # 예: "assets.json"
    liquid_assets = assets.get("liquid_assets", {})
    
    checking_data = liquid_assets.get("checking_account", {})
    savings_data = liquid_assets.get("savings_account", {})
    install_data = liquid_assets.get("installment_savings", {})

    # 2) Summary of Liquid Assets
    st.subheader("Summary of Liquid Assets")

    st.markdown("<p class='total-liquid-label'>Total Liquid</p>", unsafe_allow_html=True)
    total_str = f"₩ {liquid_assets.get('total_krw', 0):,}"
    st.markdown(f"<h2 class='total-liquid-value'>{total_str}</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<p class='account-type-label'>Checking Account</p>", unsafe_allow_html=True)
        check_str = f"₩ {checking_data.get('total_krw', 0):,}"
        st.markdown(f"### {check_str}")
    with col2:
        st.markdown("<p class='account-type-label'>Savings Account</p>", unsafe_allow_html=True)
        sav_str = f"₩ {savings_data.get('total_krw', 0):,}"
        st.markdown(f"### {sav_str}")
    with col3:
        st.markdown("<p class='account-type-label'>Installment Savings</p>", unsafe_allow_html=True)
        inst_str = f"₩ {install_data.get('total_krw', 0):,}"
        st.markdown(f"### {inst_str}")

    st.write("---")

    # 3) Checking Account - Expander
    st.markdown(f"#### Checking Account (₩ {checking_data.get('total_krw',0):,})")
    with st.expander("Detail of Checking Account", expanded=False):
        details_checking = checking_data.get("details", [])
        df_check = pd.DataFrame(details_checking)
        if not df_check.empty:
            df_check.rename(columns={
                "name": "Bank/Account",
                "amount_krw": "Balance (KRW)"
            }, inplace=True)
            df_check_styled = df_check.style.format({"Balance (KRW)": "{:,.0f}"})
            st.dataframe(df_check_styled, use_container_width=True)
        else:
            st.write("No Checking Account details.")

    # 4) Savings Account - Expander
    st.markdown(f"#### Savings Account (₩ {savings_data.get('total_krw',0):,})")
    with st.expander("Detail of Savings Account", expanded=False):
        details_savings = savings_data.get("details", [])
        df_sav = pd.DataFrame(details_savings)
        if not df_sav.empty:
            df_sav.rename(columns={
                "name": "Bank/Product",
                "amount_krw": "Balance (KRW)"
            }, inplace=True)
            df_sav_styled = df_sav.style.format({"Balance (KRW)": "{:,.0f}"})
            st.dataframe(df_sav_styled, use_container_width=True)
        else:
            st.write("No Savings Account details.")

    # 5) Installment Savings - Expander
    st.markdown(f"#### Installment Savings (₩ {install_data.get('total_krw',0):,})")
    with st.expander("Detail of Installment Savings", expanded=False):
        details_inst = install_data.get("details", [])
        df_inst = pd.DataFrame(details_inst)
        if not df_inst.empty:
            df_inst.rename(columns={
                "name": "Bank/Product",
                "amount_krw": "Balance (KRW)"
            }, inplace=True)
            df_inst_styled = df_inst.style.format({"Balance (KRW)": "{:,.0f}"})
            st.dataframe(df_inst_styled, use_container_width=True)
        else:
            st.write("No Installment Savings details.")

    st.write("---")
    st.subheader("Account Operations")

    # 6) Tabs for Deposit, Withdraw, Transfer, Add, Delete, Adjust
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Deposit", "Withdraw", "Transfer", "Add New Account", "Delete Existing Account", "Adjust"])

    # (A) Deposit
    with tab1:
        st.write("Deposit money into one of the existing accounts.")
        deposit_account_type = st.selectbox("Account Type", ["Checking", "Savings", "Installment"], key="dep_type")
        account_list = get_account_list(assets, deposit_account_type)
        deposit_account_name = st.selectbox("Select an account", account_list, key="dep_name")
        deposit_amount = st.number_input("Amount (KRW)", min_value=0, step=1000, key="dep_amt")

        if st.button("Deposit"):
            if deposit_amount > 0 and deposit_account_name:
                success = deposit_to_account(assets, deposit_account_type, deposit_account_name, deposit_amount)
                if success is True:
                    save_assets(assets)
                    st.success(f"Deposited ₩ {deposit_amount:,} to [{deposit_account_name}].")
                else:
                    st.error("Deposit failed. Account not found?")
            else:
                st.warning("Please enter a valid amount and select an account.")

    # (B) Withdraw
    with tab2:
        st.write("Withdraw money from an existing account.")
        withdraw_account_type = st.selectbox("Account Type", ["Checking", "Savings", "Installment"], key="wd_type")
        wd_account_list = get_account_list(assets, withdraw_account_type)
        withdraw_account_name = st.selectbox("Select an account", wd_account_list, key="wd_name")
        withdraw_amount = st.number_input("Amount (KRW)", min_value=0, step=1000, key="wd_amt")

        if st.button("Withdraw"):
            if withdraw_amount > 0 and withdraw_account_name:
                result = withdraw_from_account(assets, withdraw_account_type, withdraw_account_name, withdraw_amount)
                if result == "ok":
                    save_assets(assets)
                    st.success(f"Withdrew ₩ {withdraw_amount:,} from [{withdraw_account_name}].")
                elif result == "insufficient":
                    st.error("Withdrawal failed: amount exceeds balance. 금액을 다시 확인해주세요.")
                else:
                    st.error("Withdrawal failed. Account not found?")
            else:
                st.warning("Please enter a valid amount and select an account.")

    # (C) Transfer
    with tab3:
        st.write("Transfer money between accounts.")
        col_from, col_to = st.columns(2)
        with col_from:
            from_type = st.selectbox("From Account Type", ["Checking", "Savings", "Installment"], key="tf_from_type")
            from_list = get_account_list(assets, from_type)
            from_name = st.selectbox("From Account", from_list, key="tf_from_name")
        with col_to:
            to_type = st.selectbox("To Account Type", ["Checking", "Savings", "Installment"], key="tf_to_type")
            to_list = get_account_list(assets, to_type)
            to_name = st.selectbox("To Account", to_list, key="tf_to_name")

        transfer_amount = st.number_input("Amount (KRW)", min_value=0, step=1000, key="tf_amt")

        if st.button("Transfer"):
            if transfer_amount > 0 and from_name and to_name:
                if from_type == to_type and from_name == to_name:
                    st.error("Cannot transfer to the same account.")
                else:
                    result = transfer_between_accounts(assets, from_type, from_name, to_type, to_name, transfer_amount)
                    if result == "ok":
                        save_assets(assets)
                        st.success(f"Transferred ₩ {transfer_amount:,} from [{from_name}] to [{to_name}].")
                    elif result == "insufficient":
                        st.error("Transfer failed: amount exceeds balance. 금액을 다시 확인해주세요.")
                    else:
                        st.error("Transfer failed. Possibly account not found?")
            else:
                st.warning("Please enter a valid amount and select valid accounts.")

    # (D) Add new account
    with tab4:
        st.write("Add a new account under Checking / Savings / Installment.")
        new_type = st.selectbox("New Account Type", ["Checking", "Savings", "Installment"], key="new_type")
        new_name = st.text_input("Account/Bank Name", key="new_name")
        new_balance = st.number_input("Initial Balance (KRW)", min_value=0, step=1000, key="new_balance")

        # ▼▼▼ 추가된 부분: Tags 선택 multiselect ▼▼▼
        possible_tags = [
            "#Checking Account",
            "#Receivables and Deposits",
            "#Safe Assets",
            "#Investment Assets"
        ]
        selected_tags = st.multiselect("Select tags (optional)", possible_tags, key="new_tags")
        # ▲▲▲

        if st.button("Add New Account"):
            if new_name.strip():
                created_name = add_new_account_with_tags(assets, new_type, new_name, new_balance, selected_tags)
                if created_name:  # 반환값이 최종 생성된 계좌명
                    save_assets(assets)
                    st.success(f"New account [{created_name}] added with ₩ {new_balance:,}, Tags={selected_tags}.")
                else:
                    st.error("Failed to add new account.")
            else:
                st.warning("Please enter a valid account/bank name.")

    # (E) Delete account
    with tab5:
        st.write("Delete an existing account from Checking / Savings / Installment.")
        del_type = st.selectbox("Account Type to delete", ["Checking", "Savings", "Installment"], key="del_type")
        del_list = get_account_list(assets, del_type)
        del_name = st.selectbox("Which account to delete?", del_list, key="del_name")

        if st.button("Delete Account"):
            if del_name:
                success = delete_account(assets, del_type, del_name)
                if success:
                    save_assets(assets)
                    st.success(f"Account [{del_name}] has been deleted.")
                else:
                    st.error("Delete failed. Account not found?")
            else:
                st.warning("No account selected.")

    # (F) Adjust (잔액 직접 설정)
    with tab6:
        st.write("Adjust an account's balance to a new specific amount.")
        adj_type = st.selectbox("Account Type", ["Checking", "Savings", "Installment"], key="adj_type")
        adj_list = get_account_list(assets, adj_type)
        adj_name = st.selectbox("Select an account", adj_list, key="adj_name")
        adj_amount = st.number_input("New Balance (KRW)", min_value=0, step=1000, key="adj_amt")

        if st.button("Adjust Balance"):
            if adj_name:
                result = adjust_account_balance(assets, adj_type, adj_name, adj_amount)
                if result:
                    save_assets(assets)
                    st.success(f"Account [{adj_name}] balance has been set to ₩ {adj_amount:,}.")
                else:
                    st.error("Failed to adjust balance. Account not found?")
            else:
                st.warning("Please select an account to adjust.")

# ------------------------------------------------------------------------------
# 아래는 로직 함수들
# ------------------------------------------------------------------------------

def get_account_list(assets: dict, acct_type: str):
    if acct_type == "Checking":
        return [d["name"] for d in assets["liquid_assets"]["checking_account"]["details"]]
    elif acct_type == "Savings":
        return [d["name"] for d in assets["liquid_assets"]["savings_account"]["details"]]
    elif acct_type == "Installment":
        return [d["name"] for d in assets["liquid_assets"]["installment_savings"]["details"]]
    else:
        return []

def get_category_dict(assets: dict, acct_type: str):
    if acct_type == "Checking":
        return assets["liquid_assets"]["checking_account"]
    elif acct_type == "Savings":
        return assets["liquid_assets"]["savings_account"]
    elif acct_type == "Installment":
        return assets["liquid_assets"]["installment_savings"]
    return None

def deposit_to_account(assets: dict, acct_type: str, acct_name: str, amount: int):
    category = get_category_dict(assets, acct_type)
    if not category:
        return False
    for entry in category["details"]:
        if entry["name"] == acct_name:
            entry["amount_krw"] += amount
            category["total_krw"] += amount
            assets["liquid_assets"]["total_krw"] += amount
            assets["summary"]["liquid_assets_krw"] += amount
            assets["summary"]["converted_total_krw"] += amount
            return True
    return False

def withdraw_from_account(assets: dict, acct_type: str, acct_name: str, amount: int):
    category = get_category_dict(assets, acct_type)
    if not category:
        return False
    for entry in category["details"]:
        if entry["name"] == acct_name:
            if entry["amount_krw"] < amount:
                return "insufficient"
            entry["amount_krw"] -= amount
            category["total_krw"] -= amount
            assets["liquid_assets"]["total_krw"] -= amount
            assets["summary"]["liquid_assets_krw"] -= amount
            assets["summary"]["converted_total_krw"] -= amount
            return "ok"
    return False

def transfer_between_accounts(assets: dict, from_type: str, from_name: str,
                             to_type: str, to_name: str, amount: int):
    wd_result = withdraw_from_account(assets, from_type, from_name, amount)
    if wd_result == "insufficient":
        return "insufficient"
    elif wd_result is False:
        return False

    dp_result = deposit_to_account(assets, to_type, to_name, amount)
    if not dp_result:
        return False
    return "ok"

def add_new_account_with_tags(assets: dict, acct_type: str, acct_name: str, initial_balance: int, tags: list):
    """
    계좌를 새로 추가하되, 사용자가 multiselect로 선택한 tags도 함께 저장.
    """
    category = get_category_dict(assets, acct_type)
    if not category:
        return None

    existing_names = [e["name"] for e in category["details"]]
    new_name = acct_name.strip()
    if not new_name:
        return None

    original_name = new_name
    counter = 1
    while new_name in existing_names:
        new_name = f"{original_name} ({counter})"
        counter += 1

    # 선택된 태그가 없다면 빈 리스트
    if not tags:
        tags = []

    new_entry = {
        "name": new_name,
        "amount_krw": initial_balance,
        "tags": tags
    }
    category["details"].append(new_entry)

    # 금액 합계 반영
    category["total_krw"] += initial_balance
    assets["liquid_assets"]["total_krw"] += initial_balance
    assets["summary"]["liquid_assets_krw"] += initial_balance
    assets["summary"]["converted_total_krw"] += initial_balance

    return new_name

def delete_account(assets: dict, acct_type: str, acct_name: str):
    category = get_category_dict(assets, acct_type)
    if not category:
        return False

    for i, entry in enumerate(category["details"]):
        if entry["name"] == acct_name:
            balance = entry["amount_krw"]
            category["total_krw"] -= balance
            assets["liquid_assets"]["total_krw"] -= balance
            assets["summary"]["liquid_assets_krw"] -= balance
            assets["summary"]["converted_total_krw"] -= balance
            del category["details"][i]
            return True
    return False

def adjust_account_balance(assets: dict, acct_type: str, acct_name: str, new_balance: int):
    category = get_category_dict(assets, acct_type)
    if not category:
        return False

    for entry in category["details"]:
        if entry["name"] == acct_name:
            old_balance = entry["amount_krw"]
            diff = new_balance - old_balance
            entry["amount_krw"] = new_balance

            category["total_krw"] += diff
            assets["liquid_assets"]["total_krw"] += diff
            assets["summary"]["liquid_assets_krw"] += diff
            assets["summary"]["converted_total_krw"] += diff
            return True
    return False

if __name__ == "__main__":
    main()