import os
from playwright.sync_api import sync_playwright
import pandas as pd
import time

class RapthorScraper:
    def __init__(self):
        # Récupération des secrets depuis les variables d'environnement Render
        self.username = os.environ.get("auchan_username")
        self.password = os.environ.get("auchan_password")
        self.base_url = "https://auchan.atgpedi.net/index.php"

    def fetch_orders(self):
        """
        Se connecte au portail et récupère le tableau des commandes.
        """
        data = []
        
        with sync_playwright() as p:
            # Lancement du navigateur (headless=True pour Render)
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                # 1. Connexion
                page.goto(self.base_url)
                # Sélecteurs basés sur ta vidéo (à ajuster si besoin avec l'inspecteur)
                # On suppose ici que les champs ont des attributs 'name' standards ou des ID
                page.fill('input[name="login"]', self.username) # Exemple de sélecteur
                page.fill('input[name="pass"]', self.password)  # Exemple de sélecteur
                page.click('button[type="submit"]') # Ou le bouton "S'identifier"
                
                # Attendre le chargement du dashboard
                page.wait_for_load_state('networkidle')

                # 2. Navigation vers la liste des commandes
                # (Si l'URL change après le clic sur "Commandes", on peut y aller direct)
                # page.goto("URL_DE_LA_LISTE_DES_COMMANDES") 
                
                # Simulation de récupération des données (Pour l'exemple, car je ne peux pas me connecter)
                # Dans la réalité, on utiliserait page.eval_on_selector_all pour lire le tableau HTML
                
                # --- MOCK DATA (Pour que tu puisses tester l'interface tout de suite) ---
                data = [
                    {"Numéro": "40484892", "Client": "Auchan France", "Lieu": "AUCHAN CATTE-SEM", "Date Commande": "26/11/2025", "Date Livraison": "03/12/2025", "Montant": 1779.00, "Statut": "Nouveau"},
                    {"Numéro": "40483812", "Client": "Auchan Super", "Lieu": "AUCHAN PETITE-FORET", "Date Commande": "25/11/2025", "Date Livraison": "01/12/2025", "Montant": 540.50, "Statut": "Accepté"},
                    {"Numéro": "40491001", "Client": "Auchan Hyper", "Lieu": "AUCHAN VÉLIZY", "Date Commande": "26/11/2025", "Date Livraison": "28/11/2025", "Montant": 2300.00, "Statut": "Expédié"},
                ]
                # ----------------------------------------------------------------------

            except Exception as e:
                print(f"Erreur lors du scraping: {e}")
                return None
            finally:
                browser.close()
        
        return pd.DataFrame(data)

# Fonction simple pour tester localement
if __name__ == "__main__":
    scraper = RapthorScraper()
    print(scraper.fetch_orders())
