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
    options = Options()
    options.add_argument("--headless")  # mode invisible
    options.add_argument("--width=1920")
    options.add_argument("--height=1080")

    driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=options)

    try:
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
            if len(cols) >= 5:
                desadv = cols[0].text.strip()
                client = cols[1].text.strip()
                montant_text = cols[4].text.strip().replace("€","").replace(" ","").replace(",",".")
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
        driver.quit()
