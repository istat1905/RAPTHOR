import streamlit as st
from playwright.sync_api import sync_playwright
import pandas as pd

def scraper_auchan(username, password):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://auchan.atgpedi.net/index.php")

        # Connexion SSO
        page.click("a[href='call.php?call=base_sso_openid_connect_authentifier']")
        page.wait_for_timeout(1500)
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")

        # Aller dans Commandes
        page.click("a[href='gui.php?page=documents_commandes_liste']")
        page.wait_for_selector("table.VL")

        # Extraction tableau
        rows = page.query_selector_all("table.VL tr")
        data = []
        for r in rows[1:]:
            cols = [c.inner_text().strip() for c in r.query_selector_all("td")]
            if cols:
                data.append(cols)

        browser.close()
        if data:
            return pd.DataFrame(data)
        return pd.DataFrame()

# Interface Streamlit
st.title("Scraper Auchan Commandes")

import os

# Récupération automatique depuis Render
def_env_username = os.getenv("auchan_username", "")
def_env_password = os.getenv("auchan_password", "")

username = st.text_input("Identifiant Auchan @GP", value=def_env_username)("Identifiant Auchan @GP")
password = st.text_input("Mot de passe", type="password", value=def_env_password)("Mot de passe", type="password")

if st.button("Scraper les commandes"):
    if username and password:
        df = scraper_auchan(username, password)
        if not df.empty:
            st.success("Commandes récupérées !")
            st.dataframe(df)
            st.download_button("Télécharger Excel", df.to_csv(index=False), "commandes.csv")
        else:
            st.warning("Aucune commande trouvée.")
    else:
        st.error("Veuillez entrer vos identifiants.")
