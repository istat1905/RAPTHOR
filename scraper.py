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
        """
        Se connecte au site Auchan et récupère les commandes
        date_str: format "DD/MM/YYYY" ou None pour demain
        """
        resultats = {
            "success": False,
            "message": "",
            "commandes": [],
            "desadv_a_faire": [],
            "commandes_sup_850": [],
            "total_par_client": {}
        }
        
        # Si pas de date fournie, utiliser demain
        if not date_str:
            demain = datetime.now() + timedelta(days=1)
            date_str = demain.strftime("%d/%m/%Y")
        
        with sync_playwright() as p:
            # Lancer Chromium en mode headless pour Render.com
            browser = p.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
            )
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # 1. Aller sur la page d'accueil
                print(f"Connexion à {self.base_url}/index.php")
                page.goto(f"{self.base_url}/index.php", timeout=30000)
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                
                # 2. Cliquer sur "M'identifier avec mon compte @GP"
                print("Clic sur le bouton de connexion @GP...")
                page.click('a.btn-outline-atgp')
                
                # Attendre la redirection vers la page de connexion
                page.wait_for_load_state('networkidle')
                time.sleep(3)
                
                # 3. Remplir les champs de connexion (la structure peut varier)
                print("Saisie des identifiants...")
                
                # Essayer plusieurs sélecteurs possibles pour l'identifiant
                try:
                    page.fill('input[name="login"]', self.username)
                except:
                    try:
                        page.fill('input[type="text"]', self.username)
                    except:
                        page.fill('input#username', self.username)
                
                # Essayer plusieurs sélecteurs possibles pour le mot de passe
                try:
                    page.fill('input[name="password"]', self.password)
                except:
                    try:
                        page.fill('input[type="password"]', self.password)
                    except:
                        page.fill('input#password', self.password)
                
                # 4. Cliquer sur le bouton de connexion
                print("Validation de la connexion...")
                try:
                    page.click('button[type="submit"]')
                except:
                    try:
                        page.click('input[type="submit"]')
                    except:
                        page.press('input[type="password"]', 'Enter')
                
                # Attendre que la connexion soit effective
                page.wait_for_load_state('networkidle')
                time.sleep(3)
                
                # 5. Vérifier qu'on est bien connecté
                if "login" in page.url.lower() or "authentification" in page.url.lower():
                    raise Exception("Échec de connexion - Vérifiez vos identifiants")
                
                # 6. Aller sur la page Commandes
                print("Navigation vers Commandes...")
                page.goto(f"{self.base_url}/gui.php?page=documents_commandes_liste", timeout=30000)
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                
                # 7. Saisir la date
                print(f"Saisie de la date: {date_str}")
                date_input = page.locator('input[name="doDateHeureDemandee"]')
                date_input.click()
                date_input.fill('')  # Vider d'abord
                date_input.fill(date_str)
                date_input.press('Enter')
                
                # Attendre le chargement des résultats
                page.wait_for_load_state('networkidle')
                time.sleep(3)
                
                # 8. Extraire les données du tableau
                print("Extraction des commandes...")
                commandes = self._extraire_commandes(page)
                
                if commandes:
                    resultats["commandes"] = commandes
                    resultats["desadv_a_faire"] = self._filtrer_desadv(commandes)
                    resultats["commandes_sup_850"] = self._filtrer_montant_sup_850(commandes)
                    resultats["total_par_client"] = self._calculer_total_par_client(commandes)
                    resultats["success"] = True
                    resultats["message"] = f"{len(commandes)} commandes trouvées pour le {date_str}"
                else:
                    resultats["message"] = "Aucune commande trouvée"
                
            except Exception as e:
                resultats["message"] = f"Erreur: {str(e)}"
                print(f"Erreur durant le scraping: {e}")
                
                # Prendre une capture d'écran pour déboguer
                try:
                    page.screenshot(path="/tmp/error_screenshot.png")
                    print("Capture d'écran sauvegardée pour débogage")
                except:
                    pass
                
            finally:
                context.close()
                browser.close()
        
        return resultats
    
    def _extraire_commandes(self, page):
        """Extrait les données du tableau de commandes"""
        commandes = []
        
        try:
            # Attendre que le tableau soit présent
            page.wait_for_selector('table', timeout=5000)
            
            # Extraire toutes les lignes du tableau
            rows = page.locator('table tbody tr').all()
            
            for row in rows:
                cells = row.locator('td').all()
                if len(cells) >= 4:  # Ajuster selon la structure réelle
                    commande = {
                        "numero": cells[0].inner_text().strip(),
                        "client": cells[1].inner_text().strip(),
                        "montant": self._parse_montant(cells[2].inner_text().strip()),
                        "statut": cells[3].inner_text().strip() if len(cells) > 3 else "",
                        "desadv": "DESADV" in row.inner_text().upper() or "desadv" in row.inner_text().lower()
                    }
                    commandes.append(commande)
        
        except Exception as e:
            print(f"Erreur extraction: {e}")
        
        return commandes
    
    def _parse_montant(self, montant_str):
        """Convertit un montant string en float"""
        try:
            # Enlever les espaces, € et remplacer , par .
            montant_clean = montant_str.replace('€', '').replace(' ', '').replace(',', '.')
            return float(montant_clean)
        except:
            return 0.0
    
    def _filtrer_desadv(self, commandes):
        """Filtre les commandes qui nécessitent un DESADV"""
        return [cmd for cmd in commandes if cmd.get("desadv", False)]
    
    def _filtrer_montant_sup_850(self, commandes):
        """Filtre les commandes avec montant > 850€"""
        return [cmd for cmd in commandes if cmd["montant"] > 850]
    
    def _calculer_total_par_client(self, commandes):
        """Calcule le total des commandes par client"""
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
