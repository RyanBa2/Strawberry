# pages/4_Cryptocurrency.py

import streamlit as st
import pandas as pd

from utils import load_assets, save_assets

def main():
    st.title("Cryptocurrency")

    # 1) Load crypto data from JSON
    assets = load_assets()
    crypto_data = assets.get("cryptocurrency", {})
    
    # 2) Get total_usd (optional, if you want an overall sum)
    total_usd = crypto_data.get("total_usd", 0.0)

    # 3) Summary
    st.subheader("Summary of Cryptocurrency")
    st.metric("Total Crypto (USD)", f"${total_usd:,.2f}")

    st.write("---")

    # 4) Display each Exchange as an expander
    for exchange_name, data_or_list in crypto_data.items():
        if exchange_name == "total_usd":
            continue  # skip
        if not isinstance(data_or_list, list):
            continue  # skip anything that's not a list
        st.markdown(f"### {exchange_name}")
        with st.expander(f"{exchange_name} Details", expanded=False):
            if not data_or_list:
                st.write("No coins in this exchange yet.")
            else:
                df = pd.DataFrame(data_or_list)
                if df.empty:
                    st.write("Empty details.")
                else:
                    st.dataframe(df, use_container_width=True)

    st.write("---")
    st.subheader("Operations")

    # --- TABS for Add / Delete Exchange ---
    tab_add, tab_del = st.tabs(["Add Exchange", "Delete Exchange"])

    # (A) Add Exchange
    with tab_add:
        st.write("Add a new Exchange. e.g. 'Coinbase', 'Binance'...")
        new_exch_name = st.text_input("Exchange Name", key="add_exchange_name")
        if st.button("Add Exchange"):
            name_stripped = new_exch_name.strip()
            if name_stripped:
                if name_stripped in crypto_data:
                    st.warning(f"Exchange '{name_stripped}' already exists.")
                else:
                    crypto_data[name_stripped] = []
                    save_assets(assets)
                    st.success(f"Exchange '{name_stripped}' created!")
            else:
                st.warning("Please enter a valid exchange name.")

    # (B) Delete Exchange
    with tab_del:
        st.write("Delete an existing Exchange.")
        existing_exchanges = [k for k in crypto_data.keys() if k != "total_usd"]
        if existing_exchanges:
            del_exch_name = st.selectbox("Select an Exchange to delete", existing_exchanges, key="del_exchange_name")
            if st.button("Delete Exchange"):
                if del_exch_name in crypto_data:
                    del crypto_data[del_exch_name]
                    save_assets(assets)
                    st.success(f"Exchange '{del_exch_name}' has been deleted.")
                else:
                    st.error("Exchange not found? Possibly already deleted.")
        else:
            st.info("No exchanges to delete.")

if __name__ == "__main__":
    main()