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
                # 1. Aller directement sur la page de connexion @GP
                print(f"Connexion à la page de login @GP...")
                page.goto("https://accounts.atgpedi.net/login", timeout=30000)
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                
                # 3. Remplir les champs de connexion
                print("Saisie des identifiants...")
                page.fill('input[name="_username"]', self.username)
                page.fill('input[name="_password"]', self.password)
                
                # 4. Cliquer sur le bouton "Se connecter"
                print("Validation de la connexion...")
                page.click('button:has-text("Se connecter")')
                
                # Attendre que la connexion soit effective
                page.wait_for_load_state('networkidle')
                time.sleep(3)
                
                # 5. Vérifier qu'on est bien connecté (on doit voir "Bonjour" ou être redirigé)
                if "login" in page.url.lower():
                    raise Exception("Échec de connexion - Vérifiez vos identifiants")
                
                print("✅ Connexion réussie!")
                
                # 6. Aller sur la page Commandes
                print("Navigation vers Commandes...")
                page.goto(f"{self.base_url}/gui.php?page=documents_commandes_liste", timeout=30000)
                page.wait_for_load_state('networkidle')
                time.sleep(3)
                
                # DEBUG: Prendre une capture d'écran pour voir l'état de la page
                try:
                    screenshot_path = f"/tmp/page_commandes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    page.screenshot(path=screenshot_path)
                    print(f"📸 Capture page commandes: {screenshot_path}")
                except:
                    pass
                
                # 7. Saisir la date dans le champ de recherche
                print(f"Recherche du champ de date...")
                
                # Attendre que la page soit complètement chargée
                page.wait_for_load_state('domcontentloaded')
                time.sleep(2)
                
                # Trouver le champ de date
                date_input = page.locator('input#doDateHeureDemandee')
                date_input.wait_for(state='visible', timeout=10000)
                
                print(f"✓ Champ de date trouvé, saisie de: {date_str}")
                date_input.click()
                time.sleep(0.5)
                
                # Vider le champ avec Ctrl+A puis Delete
                date_input.press('Control+A')
                date_input.press('Backspace')
                time.sleep(0.5)
                
                # Saisir la nouvelle date
                date_input.type(date_str, delay=50)
                time.sleep(0.5)
                
                # Appuyer sur Entrée pour valider
                date_input.press('Enter')
                
                # Attendre le chargement des résultats
                print("Attente des résultats...")
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
                    print(f"✅ {len(commandes)} commandes extraites")
                else:
                    resultats["message"] = "Aucune commande trouvée pour cette date"
                    print("⚠️ Aucune commande trouvée")
                
            except Exception as e:
                resultats["message"] = f"Erreur: {str(e)}"
                print(f"❌ Erreur durant le scraping: {e}")
                
                # Prendre une capture d'écran pour déboguer
                try:
                    screenshot_path = f"/tmp/error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    page.screenshot(path=screenshot_path)
                    print(f"📸 Capture d'écran sauvegardée: {screenshot_path}")
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
            # Attendre que le tableau soit présent (classe "vL" avec L minuscule!)
            page.wait_for_selector('table.vL tbody tr', timeout=10000)
            
            # Extraire toutes les lignes du tableau (tbody tr)
            rows = page.locator('table.vL tbody tr').all()
            
            print(f"Nombre de lignes trouvées: {len(rows)}")
            
            for i, row in enumerate(rows):
                try:
                    cells = row.locator('td').all()
                    
                    # Vérifier qu'on a assez de colonnes (ignorer les lignes vides ou de header)
                    if len(cells) < 8:
                        continue
                    
                    # Colonnes: Numéro, Client, Livrer à, Création le, Livrer le, GLN, Montant, Statut
                    numero = cells[0].inner_text().strip()
                    client = cells[1].inner_text().strip()
                    livrer_a = cells[2].inner_text().strip()
                    creation = cells[3].inner_text().strip()
                    livraison = cells[4].inner_text().strip()
                    gln = cells[5].inner_text().strip()
                    montant_str = cells[6].inner_text().strip()
                    
                    # Le statut et les icônes sont dans la dernière colonne
                    statut_cell = cells[7].inner_text().strip() if len(cells) > 7 else ""
                    
                    # Parser le montant
                    montant = self._parse_montant(montant_str)
                    
                    # Vérifier si DESADV nécessaire (chercher dans toute la ligne ou dans les attributs)
                    row_html = row.inner_html()
                    desadv = "desadv" in row_html.lower()
                    
                    commande = {
                        "numero": numero,
                        "client": client,
                        "livrer_a": livrer_a,
                        "date_creation": creation,
                        "date_livraison": livraison,
                        "gln": gln,
                        "montant": montant,
                        "statut": statut_cell,
                        "desadv": desadv
                    }
                    
                    commandes.append(commande)
                    print(f"  ✓ Commande {i+1}: {numero} - {client} - {montant}€")
                    
                except Exception as e:
                    print(f"  ⚠️ Erreur ligne {i+1}: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ Erreur extraction tableau: {e}")
        
        return commandes
    
    def _parse_montant(self, montant_str):
        """Convertit un montant string en float"""
        try:
            # Enlever les espaces, € et remplacer , par .
            montant_clean = montant_str.replace('€', '').replace(' ', '').replace(',', '.').strip()
            if not montant_clean:
                return 0.0
            return float(montant_clean)
        except Exception as e:
            print(f"  ⚠️ Erreur parsing montant '{montant_str}': {e}")
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
