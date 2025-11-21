import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
from datetime import datetime, timedelta

def fetch_desadv_auchan(username, password):
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Mode invisible
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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

        # Récupérer la liste des commandes
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 5:
                client = cols[1].text.strip()
                desadv = cols[0].text.strip()
                montant = float(cols[4].text.replace("€","").replace(",","."))  # montant en float
                if montant >= 850:
                    data.append({"DESADV": desadv, "Client": client, "Montant": montant})

        # Regrouper par client et sommer le montant si plusieurs commandes
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
