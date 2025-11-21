# app.py
import streamlit as st
from scraper import fetch_desadv_auchan
import pandas as pd

st.set_page_config(page_title="RAPTHOR - Auchan", layout="wide")
st.title("🖥 RAPTHOR - Auchan Automation")

st.sidebar.header("Connexion Auchan")

# Saisie ID / MDP en local (pas de secrets GitHub)
username = st.sidebar.text_input("Identifiant Auchan", type="password")
password = st.sidebar.text_input("Mot de passe Auchan", type="password")

st.sidebar.header("Actions disponibles")

if st.sidebar.button("Récupérer DESADV"):
    if not username or not password:
        st.warning("Merci de remplir identifiant et mot de passe")
    else:
        st.info("Connexion et récupération des DESADV en cours...")
        df = fetch_desadv_auchan(username, password)

        if not df.empty:
            st.success("Récupération terminée !")
            st.dataframe(df)

            # Bouton téléchargement Excel
            st.download_button(
                label="📥 Télécharger le rapport Excel",
                data=df.to_excel(index=False, engine='openpyxl'),
                file_name=f"RAPTHOR_DESADV_{pd.Timestamp.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Aucune DESADV trouvée.")
