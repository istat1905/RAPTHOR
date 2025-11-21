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
                time.sleep(2)
                
                # 7. Saisir la date dans le champ de recherche
                print(f"Saisie de la date: {date_str}")
                
                # Attendre que le tableau et les filtres soient complètement chargés
                print("Attente du chargement du tableau...")
                page.wait_for_selector('table.VL', timeout=30000)
                time.sleep(3)  # Attente supplémentaire pour le chargement complet
                
                # Utiliser l'ID du champ qui est plus fiable
                print("Recherche du champ de date de livraison...")
                
                # Essayer d'abord avec l'ID
                try:
                    date_input = page.locator('#doDateHeureDemandee')
                    date_input.wait_for(state="attached", timeout=30000)
                    print("✅ Champ trouvé avec l'ID")
                except:
                    # Fallback sur le name
                    date_input = page.locator('input[name="doDateHeureDemandee"]')
                    date_input.wait_for(state="attached", timeout=30000)
                    print("✅ Champ trouvé avec le name")
                
                # Attendre que le champ soit vraiment visible et interactif
                date_input.wait_for(state="visible", timeout=30000)
                time.sleep(1)
                
                # Scroller jusqu'au champ pour s'assurer qu'il est visible
                date_input.scroll_into_view_if_needed()
                time.sleep(0.5)
                
                # Effacer le contenu actuel et saisir la nouvelle date
                print(f"Remplissage avec: {date_str}")
                
                # Méthode 1: Triple-clic pour sélectionner puis taper
                date_input.click(click_count=3)
                time.sleep(0.3)
                page.keyboard.press('Backspace')
                time.sleep(0.3)
                
                # Taper la nouvelle date caractère par caractère
                for char in date_str:
                    page.keyboard.type(char)
                    time.sleep(0.05)
                
                time.sleep(1)
                print(f"✅ Date saisie: {date_str}")
                
                # Presser Enter pour lancer la recherche
                print("Validation de la recherche...")
                page.keyboard.press('Enter')
                time.sleep(0.5)
                
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
