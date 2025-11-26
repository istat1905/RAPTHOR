import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st

# Récupérer les identifiants depuis les variables d'environnement de Render
LOGIN = os.getenv("AUCHAN_USERNAME")
PASSWORD = os.getenv("AUCHAN_PASSWORD")
URL_LOGIN = os.getenv("URL_LOGIN", "https://auchan.atgpedi.net/login")  # URL par défaut
URL_TABLEAU = os.getenv("URL_TABLEAU", "https://auchan.atgpedi.net/gui.php?page=documents_commandes_liste")

# Initialiser une session pour gérer les cookies
session = requests.Session()

def login():
    """Se connecter au site avec les identifiants."""
    try:
        # Récupérer la page de login pour obtenir le token CSRF si nécessaire
        response = session.get(URL_LOGIN)
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find("input", {"name": "csrf_token"})
        csrf_token = csrf_token["value"] if csrf_token else None

        # Préparer les données de login
        login_data = {
            "login": LOGIN,  # Adapte selon le nom du champ dans le formulaire
            "password": PASSWORD,
        }
        if csrf_token:
            login_data["csrf_token"] = csrf_token

        # Envoyer les identifiants
        response = session.post(URL_LOGIN, data=login_data)

        # Vérifier si la connexion a réussi (à adapter)
        return response.url == URL_TABLEAU or "Bienvenue" in response.text

    except Exception as e:
        st.error(f"Erreur lors de la connexion : {e}")
        return False

def get_tableau():
    """Récupérer le tableau des commandes."""
    try:
        # Récupérer la page du tableau
        response = session.get(URL_TABLEAU)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Trouver le tableau (adapte le sélecteur)
        table = soup.find("table")
        if not table:
            st.error("Tableau non trouvé sur la page.")
            return pd.DataFrame()

        # Extraire les données du tableau
        rows = table.find_all("tr")
        data = []
        for row in rows:
            cols = row.find_all(["th", "td"])
            cols = [col.text.strip() for col in cols]
            data.append(cols)

        # Créer un DataFrame
        df = pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame()
        return df

    except Exception as e:
        st.error(f"Erreur lors de la récupération du tableau : {e}")
        return pd.DataFrame()

# Interface Streamlit
st.title("Liste des commandes Auchan")

if st.button("Se connecter et récupérer les commandes"):
    with st.spinner("Connexion en cours..."):
        if login():
            st.success("Connexion réussie ! Récupération du tableau...")
            df = get_tableau()
            if not df.empty:
                st.write("Liste des commandes :")
                st.dataframe(df)
                # Option pour télécharger le tableau en CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Télécharger en CSV",
                    data=csv,
                    file_name='commandes_auchans.csv',
                    mime='text/csv',
                )
            else:
                st.error("Aucune donnée trouvée.")
        else:
            st.error("Échec de la connexion. Vérifiez vos identifiants ou l'URL.")
