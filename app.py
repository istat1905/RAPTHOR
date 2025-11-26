import streamlit as st
import os
from scraper import scraper_auchan
from traitement import appliquer_criteres

st.title("📦 Automatisation Auchan – Commandes")

# Récupérer identifiants depuis Render
username = os.getenv("auchan_username", "")
password = os.getenv("auchan_password", "")

if st.button("Récupérer et traiter commandes"):
    if username and password:
        try:
            st.info("Connexion et récupération des commandes…")
            df = scraper_auchan(username, password)
            st.success("Commandes récupérées !")
            st.dataframe(df)
            fichier_final = appliquer_criteres(df)
            st.success(f"Fichier final généré : {fichier_final}")
            st.download_button("Télécharger Excel", open(fichier_final, "rb"), file_name=fichier_final)
        except Exception as e:
            st.error("Erreur lors du scraping ou traitement !")
            st.exception(e)
    else:
        st.error("Veuillez définir vos identifiants Auchan dans Render.")
