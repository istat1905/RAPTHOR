import streamlit as st
import os
from scraper import scraper_auchan


st.title("📦 Scraper Auchan – Commandes")


# Récupération des identifiants depuis Render
default_username = os.getenv("auchan_username", "")
default_password = os.getenv("auchan_password", "")


username = st.text_input("Identifiant Auchan @GP", value=default_username)
password = st.text_input("Mot de passe", type="password", value=default_password)


if st.button("Scraper les commandes"):
if username and password:
st.info("Connexion à Auchan…")
df = scraper_auchan(username, password)


if not df.empty:
st.success("Commandes récupérées !")
st.dataframe(df)
st.download_button("Télécharger CSV", df.to_csv(index=False), "commandes.csv")
else:
st.warning("Aucune commande trouvée.")
else:
st.error("Veuillez entrer vos identifiants.")
