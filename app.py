import streamlit as st
from scraper import fetch_desadv_auchan
import pandas as pd

st.set_page_config(page_title="RAPTHOR Auchan", layout="wide")
st.title("🖥 RAPTHOR - Auchan Automation")

# Lire ID et MDP depuis les secrets Streamlit
username = st.secrets["auchan"]["username"]
password = st.secrets["auchan"]["password"]

st.sidebar.header("Actions disponibles")

if st.sidebar.button("Récupérer DESADV Auchan"):
    st.info("Connexion et analyse en cours...")
    df = fetch_desadv_auchan(username, password)

    if df is not None and not df.empty:
        st.success("Analyse terminée")
        st.dataframe(df)

        st.download_button(
            "📥 Télécharger Excel",
            data=df.to_excel(index=False, engine="openpyxl"),
            file_name="RAPTHOR_DESADV.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Aucun résultat trouvé.")
