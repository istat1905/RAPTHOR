from playwright.sync_api import sync_playwright
import pandas as pd


def scraper_auchan(username, password):
with sync_playwright() as p:
browser = p.chromium.launch(headless=True)
page = browser.new_page()
page.goto("https://auchan.atgpedi.net/index.php")


# Connexion SSO @GP
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
