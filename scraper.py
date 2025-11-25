from playwright.sync_api import sync_playwright
from datetime import datetime
import pandas as pd
import pytesseract
from PIL import Image
import io
import time

class AuchanScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = "https://auchan.atgpedi.net"

    def scraper_commandes(self):
        """
        Se connecte au site Auchan, prend une capture d'écran et lit le tableau via OCR
        """
        resultats = {
            "success": False,
            "message": "",
            "commandes": [],
            "desadv_a_faire": [],
            "commandes_sup_850": [],
            "total_par_client": {}
        }

        with sync_playwright() as p:
            # Lancer Chromium headless pour Render.com
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context()
            page = context.new_page()

            try:
                # 1️⃣ Connexion
                page.goto("https://accounts.atgpedi.net/login", timeout=30000)
                page.wait_for_load_state('networkidle')
                time.sleep(2)

                page.fill('input[name="_username"]', self.username)
                page.fill('input[name="_password"]', self.password)
                page.click('button:has-text("Se connecter")')
                page.wait_for_load_state('networkidle', timeout=30000)
                time.sleep(3)

                if "login" in page.url.lower():
                    raise Exception("Échec de connexion - Vérifiez vos identifiants")

                # 2️⃣ Aller sur la page commandes
                page.goto(f"{self.base_url}/gui.php?page=documents_commandes_liste", timeout=30000)
                page.wait_for_load_state('networkidle', timeout=30000)
                time.sleep(3)

                # 3️⃣ Prendre capture d'écran complète de la page
                screenshot_path = "/tmp/page_commandes.png"
                page.screenshot(path=screenshot_path, full_page=True)

                # 4️⃣ Lire l'image avec OCR
                commandes = self._extraire_commandes_ocr(screenshot_path)

                if commandes:
                    # Filtrer semaine, DESADV, montants > 850 et totaux par client
                    commandes_semaine = self._filtrer_semaine_courante(commandes)
                    resultats["commandes"] = commandes_semaine
                    resultats["desadv_a_faire"] = self._filtrer_desadv(commandes_semaine)
                    resultats["commandes_sup_850"] = self._filtrer_montant_sup_850(commandes_semaine)
                    resultats["total_par_client"] = self._calculer_total_par_client(commandes_semaine)
                    resultats["success"] = True
                    resultats["message"] = f"{len(commandes_semaine)} commandes extraites pour la semaine"
                else:
                    resultats["message"] = "Aucune commande détectée via OCR"

            except Exception as e:
                resultats["message"] = f"Erreur durant le scraping : {str(e)}"
            finally:
                context.close()
                browser.close()

        return resultats

    def _extraire_commandes_ocr(self, image_path):
        """
        Lit l'image et transforme le texte OCR en liste de commandes
        """
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang="fra")
            lignes = [l.strip() for l in text.split("\n") if l.strip()]

            commandes = []
            for l in lignes:
                # Ici on sépare par espaces multiples, à adapter si nécessaire
                cols = l.split()
                if len(cols) < 6:
                    continue

                # Exemple simplifié : ajuster selon le rendu OCR réel
                commande = {
                    "numero": cols[0],
                    "client": cols[1],
                    "livrer_a": cols[2],
                    "date_creation": cols[-5],
                    "date_livraison": cols[-4],
                    "gln": cols[-3],
                    "montant": self._parse_montant(cols[-2]),
                    "statut": cols[-1],
                    "desadv": "desadv" in l.lower()
                }
                commandes.append(commande)

            return commandes

        except Exception as e:
            print(f"❌ Erreur OCR : {e}")
            return []

    def _filtrer_semaine_courante(self, commandes):
        debut_semaine = datetime(2025, 11, 24)
        fin_semaine = datetime(2025, 11, 30)
        commandes_semaine = []

        for cmd in commandes:
            try:
                date_liv = datetime.strptime(cmd["date_livraison"], "%d/%m/%Y")
                if debut_semaine <= date_liv <= fin_semaine:
                    commandes_semaine.append(cmd)
            except:
                commandes_semaine.append(cmd)

        return commandes_semaine

    def _parse_montant(self, montant_str):
        try:
            montant_clean = montant_str.replace('€', '').replace(' ', '').replace(',', '.').strip()
            return float(montant_clean) if montant_clean else 0.0
        except:
            return 0.0

    def _filtrer_desadv(self, commandes):
        return [cmd for cmd in commandes if cmd.get("desadv", False)]

    def _filtrer_montant_sup_850(self, commandes):
        return [cmd for cmd in commandes if cmd["montant"] > 850]

    def _calculer_total_par_client(self, commandes):
        totaux = {}
        for cmd in commandes:
            client = cmd["client"]
            if client in totaux:
                totaux[client]["montant_total"] += cmd["montant"]
                totaux[client]["nb_commandes"] += 1
                totaux[client]["commandes"].append(cmd["numero"])
            else:
                totaux[client] = {
                    "montant_total": cmd["montant"],
                    "nb_commandes": 1,
                    "commandes": [cmd["numero"]]
                }
        return totaux
