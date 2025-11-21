import streamlit as st
from scraper import fetch_desadv_auchan

st.set_page_config(page_title="RAPTHOR Auchan", layout="wide")
st.title("🖥 RAPTHOR - Auchan Automation")

st.sidebar.header("Connexion Auchan")

# Inputs sécurisés pour identifiant et mot de passe
username = st.sidebar.text_input("Identifiant", type="password")
password = st.sidebar.text_input("Mot de passe", type="password")

st.sidebar.header("Actions disponibles")
if st.sidebar.button("Récupérer DESADV Auchan"):
    if not username or not password:
        st.warning("Merci de remplir identifiant et mot de passe.")
    else:
        st.info("Récupération des DESADV en cours...")
        df = fetch_desadv_auchan(username, password)
        if df is not None and not df.empty:
            st.success("Récupération terminée !")
            st.dataframe(df)

            # Bouton pour exporter en Excel
            st.download_button(
                label="📥 Télécharger le rapport Excel",
                data=df.to_excel(index=False, engine='openpyxl'),
                file_name=f"RAPTHOR_DESADV_{pd.Timestamp.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("Aucune DESADV trouvée.")
