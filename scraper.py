# scraper.py
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from datetime import datetime, timedelta
import time

def fetch_desadv_auchan(username, password):
    """
    Récupère les DESADV Auchan pour la date de demain,
    filtre les montants >= 850€, et regroupe par client.
    """
    # Config Firefox
    options = Options()
    options.add_argument("--headless")  # mode invisible, retirer si tu veux voir le navigateur
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")

    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

    try:
        # Aller sur la page login
        driver.get("https://auchan.atgpedi.net/gui.php?page=accueil")
        time.sleep(2)

        # Connexion
        driver.find_element(By.ID, "loginField").send_keys(username)
        driver.find_element(By.ID, "passwordField").send_keys(password)
        driver.find_element(By.ID, "passwordField").send_keys(Keys.ENTER)
        time.sleep(3)

        # Cliquer sur Commandes
        driver.find_element(By.LINK_TEXT, "Commandes").click()
        time.sleep(3)

        # Saisir la date de demain
        date_tomorrow = (datetime.today() + timedelta(days=1)).strftime("%d/%m/%Y")
        date_input = driver.find_element(By.ID, "doDateHeureDemandee")
        date_input.clear()
        date_input.send_keys(date_tomorrow)
        date_input.send_keys(Keys.ENTER)
        time.sleep(3)

        # Récupérer les lignes du tableau
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 5:  # vérifier selon la structure du tableau
                desadv = cols[0].text.strip()
                client = cols[1].text.strip()
                montant_text = cols[4].text.strip().replace("€","").replace(" ","").replace(",",".")
                try:
                    montant = float(montant_text)
                except:
                    montant = 0
                if montant >= 850:
                    data.append({"DESADV": desadv, "Client": client, "Montant": montant})

        # Regrouper par client et sommer les montants
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.groupby("Client", as_index=False).agg({
                "DESADV": lambda x: ", ".join(x),
                "Montant": "sum"
            })

        return df

    except Exception as e:
        print("Erreur Selenium:", e)
        return pd.DataFrame()

    finally:
        driver.quit()
