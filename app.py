# app.py
import streamlit as st
from scraper import fetch_desadv_auchan
import pandas as pd

st.set_page_config(page_title="RAPTHOR - Auchan", layout="wide")
st.title("🖥 RAPTHOR - Auchan Automation")

st.sidebar.header("Actions disponibles")

# Récupérer ID / MDP depuis Secrets Streamlit
# Créer dans Streamlit Cloud :
# [auchan]
# username = "ton_id"
# password = "ton_mdp"
username = st.secrets["auchan"]["username"]
password = st.secrets["auchan"]["password"]

if st.sidebar.button("Récupérer DESADV"):
    st.info("Connexion et récupération des DESADV en cours...")
    df = fetch_desadv_auchan(username, password)

    if not df.empty:
        st.success("Récupération terminée !")
        st.dataframe(df)

        st.download_button(
            label="📥 Télécharger le rapport Excel",
            data=df.to_excel(index=False, engine='openpyxl'),
            file_name=f"RAPTHOR_DESADV_{pd.Timestamp.today().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("Aucune DESADV trouvée.")
