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
            # Lancer le navigateur (headless=False pour voir ce qui se passe)
            browser = p.firefox.launch(headless=False)
            page = browser.new_page()
            
            try:
                # 1. Aller sur la page d'accueil
                print(f"Connexion à {self.base_url}/gui.php?page=accueil")
                page.goto(f"{self.base_url}/gui.php?page=accueil", timeout=30000)
                
                # 2. Se connecter
                print("Connexion avec identifiants...")
                page.fill('input[name="login"]', self.username)
                page.fill('input[name="password"]', self.password)
                page.click('button[type="submit"]')
                
                # Attendre que la connexion soit effective
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                
                # 3. Cliquer sur Commandes
                print("Navigation vers Commandes...")
                page.click('a[href="gui.php?page=documents_commandes_liste"]')
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                
                # 4. Saisir la date
                print(f"Saisie de la date: {date_str}")
                date_input = page.locator('input[name="doDateHeureDemandee"]')
                date_input.fill(date_str)
                date_input.press('Enter')
                
                # Attendre le chargement des résultats
                page.wait_for_load_state('networkidle')
                time.sleep(3)
                
                # 5. Extraire les données du tableau
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
                
            finally:
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
                        "desadv": "DESADV à faire" in row.inner_text() if len(cells) > 4 else False
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
