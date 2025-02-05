# pages/2_Receivables_and_Deposits.py

import streamlit as st
import pandas as pd
from utils import load_assets, save_assets

def main():
    # 간단한 CSS로 간격/디자인 조정
    custom_css = """
    <style>
    .total-rd-label {
        margin-bottom: 0px;
    }
    .total-rd-value {
        margin-top: -15px; 
        margin-bottom: 20px;
    }
    .category-label {
        margin-top: 30px;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    st.title("Receivables & Deposits")

    # 1) 데이터 로드
    assets = load_assets()  
    r_d = assets.get("receivables_and_deposits", {})
    
    receivables_data = r_d.get("receivables", {})
    deposits_data = r_d.get("deposits", {})

    # 2) 요약 (상단)
    st.subheader("Summary of Receivables & Deposits")

    # -- 첫 줄: 전체 합 (Total) --
    st.markdown("<p class='total-rd-label'>Total (Receivables & Deposits)</p>", unsafe_allow_html=True)
    total_str = f"₩ {r_d.get('total_krw', 0):,}"
    st.markdown(f"<h2 class='total-rd-value'>{total_str}</h2>", unsafe_allow_html=True)

    # -- 두 번째 줄(2개 컬럼): Receivables / Deposits --
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<p class='category-label'>Receivables</p>", unsafe_allow_html=True)
        recv_str = f"₩ {receivables_data.get('total_krw', 0):,}"
        st.markdown(f"### {recv_str}")
    with col2:
        st.markdown("<p class='category-label'>Deposits</p>", unsafe_allow_html=True)
        deps_str = f"₩ {deposits_data.get('total_krw', 0):,}"
        st.markdown(f"### {deps_str}")

    st.write("---")

    # 3) Receivables - Expander
    st.markdown(f"#### Receivables (₩ {receivables_data.get('total_krw',0):,})")
    with st.expander("Detail of Receivables", expanded=False):
        details_recv = receivables_data.get("details", [])
        df_recv = pd.DataFrame(details_recv)
        if not df_recv.empty:
            df_recv.rename(columns={
                "name": "Counterparty",
                "amount_krw": "Balance (KRW)"
            }, inplace=True)
            df_recv_styled = df_recv.style.format({"Balance (KRW)": "{:,.0f}"})
            st.dataframe(df_recv_styled, use_container_width=True)
        else:
            st.write("No receivables recorded.")

    # 4) Deposits - Expander
    st.markdown(f"#### Deposits (₩ {deposits_data.get('total_krw',0):,})")
    with st.expander("Detail of Deposits", expanded=False):
        details_deps = deposits_data.get("details", [])
        df_deps = pd.DataFrame(details_deps)
        if not df_deps.empty:
            df_deps.rename(columns={
                "name": "Counterparty / Contract",
                "amount_krw": "Balance (KRW)"
            }, inplace=True)
            df_deps_styled = df_deps.style.format({"Balance (KRW)": "{:,.0f}"})
            st.dataframe(df_deps_styled, use_container_width=True)
        else:
            st.write("No deposits recorded.")

    st.write("---")
    st.subheader("Operations")

    # 5) Tabs: Loan out, Repaying, Settlement, Adjust
    tab1, tab2, tab3, tab4 = st.tabs(["Loan out", "Repaying", "Settlement", "Adjust"])

    # (A) Loan out (기존 Deposit + AddNew 통합)
    with tab1:
        st.write("Loan out money to Receivables or Deposits. If the name already exists, add to existing balance; otherwise create a new entry.")

        loan_type = st.selectbox("Type", ["Receivables", "Deposits"], key="rd_loan_type")
        loan_name = st.text_input("Counterparty / Contract Name", key="rd_loan_name")
        loan_amount = st.number_input("Amount (KRW)", min_value=0, step=1000, key="rd_loan_amt")

        # ▼▼▼ 추가: Tags 멀티셀렉트 ▼▼▼
        possible_tags = [
            "#Checking Account",
            "#Receivables and Deposits",
            "#Safe Assets",
            "#Investment Assets"
        ]
        selected_tags = st.multiselect("Select tags (only if creating new)", possible_tags, key="rd_loan_tags")
        # ▲▲▲

        if st.button("Loan out"):
            if loan_amount > 0 and loan_name.strip():
                # rd_loan_out에 tags도 인자로 넘김
                success_name = rd_loan_out(assets, loan_type, loan_name.strip(), loan_amount, selected_tags)
                if success_name:
                    save_assets(assets)
                    if success_name == loan_name.strip():
                        st.success(f"Loaned out ₩ {loan_amount:,} to **existing** [{success_name}]. Tags ignored for existing entry.")
                    else:
                        st.success(f"Created a new entry [{success_name}] with tags={selected_tags} and loaned out ₩ {loan_amount:,}.")
                else:
                    st.error("Loan out failed for unknown reason.")
            else:
                st.warning("Please enter a valid name and amount.")

    # (B) Repaying (기존 Withdraw)
    with tab2:
        st.write("Repaying: return money from existing Receivables or Deposits.")
        repay_type = st.selectbox("Type", ["Receivables", "Deposits"], key="rd_repay_type")
        repay_list = get_rd_list(assets, repay_type)
        repay_name = st.selectbox("Select a target", repay_list, key="rd_repay_name")
        repay_amount = st.number_input("Amount (KRW)", min_value=0, step=1000, key="rd_repay_amt")

        if st.button("Repaying"):
            if repay_amount > 0 and repay_name:
                result = rd_withdraw(assets, repay_type, repay_name, repay_amount)
                if result == "ok":
                    save_assets(assets)
                    st.success(f"Repaying ₩ {repay_amount:,} from [{repay_name}].")
                elif result == "insufficient":
                    st.error("Repaying failed: amount exceeds balance. 금액을 다시 확인해주세요.")
                else:
                    st.error("Repaying failed. Target not found?")
            else:
                st.warning("Please select a target and enter amount.")

    # (C) Settlement (기존 Delete)
    with tab3:
        st.write("Settlement: remove an existing entry from Receivables or Deposits completely.")
        settle_type = st.selectbox("Type", ["Receivables", "Deposits"], key="rd_settle_type")
        settle_list = get_rd_list(assets, settle_type)
        settle_name = st.selectbox("Which to settle?", settle_list, key="rd_settle_name")

        if st.button("Settle"):
            if settle_name:
                success = rd_delete(assets, settle_type, settle_name)
                if success:
                    save_assets(assets)
                    st.success(f"Settlement done. [{settle_name}] removed.")
                else:
                    st.error("Settlement failed. Target not found?")
            else:
                st.warning("No target selected.")

    # (D) Adjust
    with tab4:
        st.write("Adjust a balance directly.")
        adj_type = st.selectbox("Type to adjust", ["Receivables", "Deposits"], key="rd_adj_type")
        adj_list = get_rd_list(assets, adj_type)
        adj_name = st.selectbox("Which entry to adjust?", adj_list, key="rd_adj_name")
        adj_amount = st.number_input("New Balance (KRW)", min_value=0, step=1000, key="rd_adj_amt")

        if st.button("Adjust"):
            if adj_name:
                result = rd_adjust(assets, adj_type, adj_name, adj_amount)
                if result:
                    save_assets(assets)
                    st.success(f"[{adj_name}] balance adjusted to ₩ {adj_amount:,}.")
                else:
                    st.error("Adjust failed. Target not found?")
            else:
                st.warning("Please select an entry to adjust.")

# ------------------------------------------------------------------------------
# 아래는 Receivables & Deposits용 로직 함수들 (수정된 rd_loan_out 포함)
# ------------------------------------------------------------------------------

def get_rd_list(assets: dict, rd_type: str):
    """Return a list of names in 'receivables' or 'deposits'."""
    r_d = assets.get("receivables_and_deposits", {})
    if rd_type == "Receivables":
        return [d["name"] for d in r_d["receivables"]["details"]]
    else:
        return [d["name"] for d in r_d["deposits"]["details"]]

def get_rd_category(assets: dict, rd_type: str):
    """Helper: return the dict for 'receivables' or 'deposits'."""
    r_d = assets.get("receivables_and_deposits", {})
    if rd_type == "Receivables":
        return r_d["receivables"]
    else:
        return r_d["deposits"]

def rd_loan_out(assets: dict, rd_type: str, rd_name: str, amount: int, tags: list):
    """
    Loan out money:
    - If rd_name already exists, just add 'amount' to existing balance (ignore 'tags').
    - If not, create a new entry with that name + the provided 'tags' (if any).
      If the same name is also taken, attach (1), (2), etc. until unique.
    Return the final name if success, or None if fail.
    """
    category = get_rd_category(assets, rd_type)
    if not category:
        return None

    existing_names = [e["name"] for e in category["details"]]

    if rd_name in existing_names:
        # 이미 존재 -> 금액만 추가, tags는 무시
        for entry in category["details"]:
            if entry["name"] == rd_name:
                entry["amount_krw"] += amount
                category["total_krw"] += amount
                assets["receivables_and_deposits"]["total_krw"] += amount
                assets["summary"]["receivables_and_deposits_krw"] += amount
                assets["summary"]["converted_total_krw"] += amount
                return rd_name  # same name
    else:
        # 새 항목 -> tags 반영
        new_name = rd_name
        original = new_name
        counter = 1
        while new_name in existing_names:
            new_name = f"{original} ({counter})"
            counter += 1

        new_entry = {
            "name": new_name,
            "amount_krw": amount,
            "tags": tags if tags else []
        }
        category["details"].append(new_entry)
        category["total_krw"] += amount
        assets["receivables_and_deposits"]["total_krw"] += amount
        assets["summary"]["receivables_and_deposits_krw"] += amount
        assets["summary"]["converted_total_krw"] += amount

        return new_name

    return None

def rd_withdraw(assets: dict, rd_type: str, rd_name: str, amount: int):
    """
    Repaying: subtract amount from existing. 
    return "ok" | "insufficient" | False
    """
    category = get_rd_category(assets, rd_type)
    if not category:
        return False
    for entry in category["details"]:
        if entry["name"] == rd_name:
            if entry["amount_krw"] < amount:
                return "insufficient"
            entry["amount_krw"] -= amount
            category["total_krw"] -= amount
            assets["receivables_and_deposits"]["total_krw"] -= amount
            assets["summary"]["receivables_and_deposits_krw"] -= amount
            assets["summary"]["converted_total_krw"] -= amount
            return "ok"
    return False

def rd_delete(assets: dict, rd_type: str, rd_name: str):
    """
    Settlement: remove the entry entirely.
    Return True if success, False if not found.
    """
    category = get_rd_category(assets, rd_type)
    if not category:
        return False
    for i, entry in enumerate(category["details"]):
        if entry["name"] == rd_name:
            balance = entry["amount_krw"]
            category["total_krw"] -= balance
            assets["receivables_and_deposits"]["total_krw"] -= balance
            assets["summary"]["receivables_and_deposits_krw"] -= balance
            assets["summary"]["converted_total_krw"] -= balance
            del category["details"][i]
            return True
    return False

def rd_adjust(assets: dict, rd_type: str, rd_name: str, new_balance: int):
    """
    Adjust the entry to new_balance directly.
    Return True if success, False if not found.
    """
    category = get_rd_category(assets, rd_type)
    if not category:
        return False
    for entry in category["details"]:
        if entry["name"] == rd_name:
            old_balance = entry["amount_krw"]
            diff = new_balance - old_balance
            entry["amount_krw"] = new_balance
            category["total_krw"] += diff
            assets["receivables_and_deposits"]["total_krw"] += diff
            assets["summary"]["receivables_and_deposits_krw"] += diff
            assets["summary"]["converted_total_krw"] += diff
            return True
    return False

if __name__ == "__main__":
    main()