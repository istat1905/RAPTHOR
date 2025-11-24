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
                page.goto(f"{self.base_url}/gui.php?page=documents_commandes_liste", timeout=60000)
                
                # Attendre plus longtemps le chargement complet
                print("Attente du chargement complet de la page...")
                page.wait_for_load_state('domcontentloaded')
                time.sleep(3)
                page.wait_for_load_state('networkidle', timeout=30000)
                time.sleep(5)  # Attente supplémentaire pour les scripts JS
                
                # Prendre une capture d'écran pour debug
                try:
                    page.screenshot(path="/tmp/page_after_load.png", full_page=True)
                    print("📸 Capture d'écran: /tmp/page_after_load.png")
                except:
                    pass
                
                # Debug: afficher l'URL actuelle et le titre
                print(f"URL actuelle: {page.url}")
                print(f"Titre de la page: {page.title()}")
                
                # 7. Chercher le champ de date avec plusieurs stratégies
                print(f"Recherche du champ de date pour: {date_str}")
                
                date_input = None
                
                # Stratégie 1: Attendre n'importe quel input dans la zone de recherche
                try:
                    print("Stratégie 1: Recherche par table...")
                    page.wait_for_selector('table', timeout=15000)
                    print("✅ Tableau trouvé")
                except Exception as e:
                    print(f"⚠️ Pas de tableau trouvé: {e}")
                
                # Stratégie 2: Lister tous les inputs disponibles
                print("Stratégie 2: Liste de tous les inputs...")
                all_inputs = page.locator('input[type="text"]').all()
                print(f"Nombre d'inputs text trouvés: {len(all_inputs)}")
                
                for i, inp in enumerate(all_inputs):
                    try:
                        name = inp.get_attribute('name')
                        id_attr = inp.get_attribute('id')
                        value = inp.get_attribute('value')
                        print(f"  Input {i}: id='{id_attr}', name='{name}', value='{value}'")
                        
                        # Si on trouve le bon champ
                        if name == 'doDateHeureDemandee' or id_attr == 'doDateHeureDemandee':
                            date_input = inp
                            print(f"✅ Champ de date trouvé à l'index {i}")
                            break
                    except Exception as e:
                        print(f"  Erreur input {i}: {e}")
                
                if not date_input:
                    # Stratégie 3: Utiliser l'URL directement avec paramètres
                    print("⚠️ Impossible de trouver le champ, utilisation de l'URL avec paramètres...")
                    
                    # Construire l'URL avec les paramètres de recherche
                    search_url = f"{self.base_url}/gui.php?page=documents_commandes_liste&doDateHeureDemandee={date_str}"
                    print(f"Navigation vers: {search_url}")
                    page.goto(search_url, timeout=60000)
                    page.wait_for_load_state('networkidle', timeout=30000)
                    time.sleep(5)
                    
                else:
                    # Remplir le champ trouvé
                    print(f"Remplissage du champ avec: {date_str}")
                    
                    try:
                        # Scroller jusqu'au champ
                        date_input.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        
                        # Cliquer et sélectionner
                        date_input.click()
                        time.sleep(0.5)
                        
                        # Sélectionner tout et effacer
                        page.keyboard.press('Control+A')
                        time.sleep(0.2)
                        page.keyboard.press('Backspace')
                        time.sleep(0.5)
                        
                        # Taper la date
                        date_input.type(date_str, delay=100)
                        time.sleep(1)
                        
                        print(f"✅ Date saisie: {date_str}")
                        
                        # Valider avec Enter
                        page.keyboard.press('Enter')
                        time.sleep(2)
                        
                    except Exception as e:
                        print(f"⚠️ Erreur lors de la saisie: {e}")
                        # Fallback sur l'URL
                        search_url = f"{self.base_url}/gui.php?page=documents_commandes_liste&doDateHeureDemandee={date_str}"
                        page.goto(search_url, timeout=60000)
                        page.wait_for_load_state('networkidle', timeout=30000)
                        time.sleep(5)
                
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
            # Attendre que le tableau soit présent
            page.wait_for_selector('table tbody tr', timeout=5000)
            
            # Extraire toutes les lignes du tableau (tbody tr)
            rows = page.locator('table tbody tr').all()
            
            print(f"Nombre de lignes trouvées: {len(rows)}")
            
            for i, row in enumerate(rows):
                try:
                    cells = row.locator('td').all()
                    
                    if len(cells) >= 7:  # D'après l'image 3, il y a plusieurs colonnes
                        # Colonnes visibles: Numéro, Client, Livrer à, Création le, Livrer le, GLN, Montant, Statut
                        numero = cells[0].inner_text().strip()
                        client = cells[1].inner_text().strip()
                        livrer_a = cells[2].inner_text().strip() if len(cells) > 2 else ""
                        creation = cells[3].inner_text().strip() if len(cells) > 3 else ""
                        livraison = cells[4].inner_text().strip() if len(cells) > 4 else ""
                        gln = cells[5].inner_text().strip() if len(cells) > 5 else ""
                        montant_str = cells[6].inner_text().strip() if len(cells) > 6 else "0"
                        statut = cells[7].inner_text().strip() if len(cells) > 7 else ""
                        
                        # Parser le montant
                        montant = self._parse_montant(montant_str)
                        
                        # Vérifier si DESADV nécessaire (chercher dans toute la ligne)
                        row_text = row.inner_text()
                        desadv = "desadv" in row_text.lower() or "DESADV" in row_text
                        
                        commande = {
                            "numero": numero,
                            "client": client,
                            "livrer_a": livrer_a,
                            "date_creation": creation,
                            "date_livraison": livraison,
                            "gln": gln,
                            "montant": montant,
                            "statut": statut,
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
