from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import pandas as pd
import time

class AuchanScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.base_url = "https://auchan.atgpedi.net"

    def scraper_commandes(self, date_str=None):

        resultats = {
            "success": False,
            "message": "",
            "commandes": [],
            "desadv_a_faire": [],
            "commandes_sup_850": [],
            "total_par_client": {}
        }

        # Si aucune date → prendre demain
        if not date_str:
            demain = datetime.now() + timedelta(days=1)
            date_str = demain.strftime("%d/%m/%Y")

        # Vérification format date
        try:
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            date_str = date_obj.strftime("%d/%m/%Y")
        except:
            raise Exception("Format date invalide : utilisez JJ/MM/AAAA")

        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )

            context = browser.new_context()
            page = context.new_page()

            try:
                print("🔐 Connexion en cours…")
                page.goto("https://accounts.atgpedi.net/login", timeout=30000)
                page.wait_for_load_state("networkidle")
                time.sleep(1)

                page.fill('input[name="_username"]', self.username)
                page.fill('input[name="_password"]', self.password)
                page.click('button[type="submit"]')

                page.wait_for_load_state("networkidle")
                time.sleep(3)

                if "login" in page.url:
                    raise Exception("Identifiants invalides")

                print("✅ Connecté")

                # 🔥 Aller DIRECTEMENT avec le filtre en URL → 100% fiable
                search_url = (
                    f"{self.base_url}/gui.php?page=documents_commandes_liste"
                    f"&doDateHeureDemandee={date_str}"
                )

                print(f"📄 Chargement des commandes {date_str}…")
                page.goto(search_url, timeout=60000)
                page.wait_for_load_state("domcontentloaded")
                time.sleep(2)

                # 🔥 Attendre que les lignes du tableau soient chargées
                try:
                    page.wait_for_selector("table tr td", timeout=10000)
                except:
                    print("⚠ Aucun TD trouvé → peut-être 0 commande")
                    pass

                commandes = self._extraire_commandes(page)

                if commandes:
                    resultats["success"] = True
                    resultats["commandes"] = commandes
                    resultats["desadv_a_faire"] = self._filtrer_desadv(commandes)
                    resultats["commandes_sup_850"] = self._filtrer_montant_sup_850(commandes)
                    resultats["total_par_client"] = self._calculer_total_par_client(commandes)
                    resultats["message"] = f"{len(commandes)} commandes trouvées"
                else:
                    resultats["message"] = "Aucune commande trouvée pour cette date"

            except Exception as e:
                resultats["message"] = f"❌ Erreur: {str(e)}"
                try:
                    page.screenshot(path=f"/tmp/error_{int(time.time())}.png")
                except:
                    pass

            finally:
                context.close()
                browser.close()

        return resultats

    def _extraire_commandes(self, page):
        print("📦 Extraction des commandes…")

        commandes = []

        # 🔥 La méthode la plus fiable : toutes les lignes avec td
        rows = page.locator("table tr").filter(has="td").all()

        print(f"➡ Lignes détectées : {len(rows)}")

        for i, row in enumerate(rows):
            try:
                cells = [c.inner_text().strip() for c in row.locator("td").all()]

                if len(cells) < 6:
                    continue

                numero = cells[0]
                client = cells[1]
                livrer_a = cells[2]
                date_creation = cells[3]
                date_livraison = cells[4]
                gln = cells[5]

                montant = self._parse_montant(cells[6]) if len(cells) > 6 else 0
                statut = cells[7] if len(cells) > 7 else ""

                commandes.append({
                    "numero": numero,
                    "client": client,
                    "livrer_a": livrer_a,
                    "date_creation": date_creation,
                    "date_livraison": date_livraison,
                    "gln": gln,
                    "montant": montant,
                    "statut": statut,
                    "desadv": "DESADV" in statut.upper()
                })

            except Exception as e:
                print(f"⚠ Erreur ligne {i}: {e}")
                continue

        print(f"✅ {len(commandes)} commandes extraites")
        return commandes

    def _parse_montant(self, montant_str):
        try:
            montant = montant_str.replace("€", "").replace(" ", "").replace(",", ".")
            return float(montant)
        except:
            return 0.0

    def _filtrer_desadv(self, commandes):
        return [c for c in commandes if c.get("desadv")]

    def _filtrer_montant_sup_850(self, commandes):
        return [c for c in commandes if c["montant"] > 850]

    def _calculer_total_par_client(self, commandes):
        clients = {}

        for c in commandes:
            client = c["client"]
            if client not in clients:
                clients[client] = {
                    "montant_total": 0,
                    "nb_commandes": 0,
                    "commandes": []
                }

            clients[client]["montant_total"] += c["montant"]
            clients[client]["nb_commandes"] += 1
            clients[client]["commandes"].append(c["numero"])

        return clients
