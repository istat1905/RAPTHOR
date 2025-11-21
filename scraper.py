# scraper.py
import pandas as pd
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

def fetch_desadv_auchan(username, password):
    """
    Récupère les DESADV Auchan pour la date de demain,
    filtre les montants >= 850€, et regroupe par client.
    """
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)  # headless pour cloud
        page = browser.new_page()

        try:
            # Aller sur la page login
            page.goto("https://auchan.atgpedi.net/gui.php?page=accueil", timeout=60000)

            # Connexion
            page.fill("#loginField", username)
            page.fill("#passwordField", password)
            page.press("#passwordField", "Enter")
            page.wait_for_timeout(3000)

            # Cliquer sur Commandes
            page.click("text=Commandes")
            page.wait_for_timeout(3000)

            # Saisir la date de demain
            date_tomorrow = (datetime.today() + timedelta(days=1)).strftime("%d/%m/%Y")
            page.fill("#doDateHeureDemandee", date_tomorrow)
            page.press("#doDateHeureDemandee", "Enter")
            page.wait_for_timeout(3000)

            # Récupérer les lignes du tableau
            rows = page.query_selector_all("table tbody tr")
            data = []
            for row in rows:
                cols = row.query_selector_all("td")
                if len(cols) >= 5:
                    desadv = cols[0].inner_text().strip()
                    client = cols[1].inner_text().strip()
                    montant_text = cols[4].inner_text().strip().replace("€","").replace(" ","").replace(",",".")
                    try:
                        montant = float(montant_text)
                    except:
                        montant = 0
                    if montant >= 850:
                        data.append({"DESADV": desadv, "Client": client, "Montant": montant})

            df = pd.DataFrame(data)
            if not df.empty:
                df = df.groupby("Client", as_index=False).agg({
                    "DESADV": lambda x: ", ".join(x),
                    "Montant": "sum"
                })

            return df

        finally:
            browser.close()
