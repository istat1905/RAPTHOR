from playwright.sync_api import sync_playwright
from datetime import datetime, timedelta
import pandas as pd
import time
import logging
import os

# Configuration du logging pour le débug
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AuchanScraper:
    """
    Classe pour automatiser la connexion et l'extraction de données sur la plateforme Auchan EDI.
    Utilise Playwright en mode synchrone (pour simplicité avec Streamlit sans async).
    """
    
    BASE_URL = "https://auchan.atgpedi.net" # URL de base
    LOGIN_URL = "https://accounts.atgpedi.net/login" # URL de connexion spécifique
    
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def scraper_commandes(self):
        """
        Se connecte au site Auchan et récupère les commandes de la semaine en cours.
        """
        resultats = {
            "success": False,
            "message": "",
            "commandes": [],
            "desadv_a_faire": [],
            "commandes_sup_850": [],
            "total_par_client": {}
        }
        
        # Le mode synchrone est utilisé ici, mais l'asynchrone est souvent préférable avec Streamlit
        # Néanmoins, nous gardons votre choix initial.
        with sync_playwright() as p:
            # Lancer Firefox en mode headless (parfait pour Docker/Render)
            browser = p.firefox.launch(
                headless=True
            )
            context = browser.new_context()
            page = context.new_page()
            
            try:
                # 1. Aller directement sur la page de connexion @GP
                logging.info(f"📡 [1/7] Connexion à la page de login @GP...")
                page.goto(self.LOGIN_URL, timeout=30000)
                page.wait_for_load_state('networkidle')
                time.sleep(2)
                logging.info("✅ Page de login chargée")
                
                # 2. Remplir les champs de connexion
                logging.info("🔑 [2/7] Saisie des identifiants...")
                page.fill('input[name="_username"]', self.username)
                page.fill('input[name="_password"]', self.password)
                logging.info("✅ Identifiants saisis")
                
                # 3. Cliquer sur le bouton "Se connecter"
                logging.info("✅ [3/7] Validation de la connexion...")
                # Sélecteur plus précis: 'button:has-text("Se connecter")'
                page.click('button:has-text("Se connecter")', timeout=10000)
                
                # Attendre que la connexion soit effective
                page.wait_for_load_state('networkidle', timeout=30000)
                time.sleep(3)
                logging.info(f"✅ Redirection effectuée vers: {page.url}")
                
                # 4. Vérifier qu'on est bien connecté
                if "login" in page.url.lower():
                    # Tenter de voir si un message d'erreur est présent
                    error_message = page.locator('div[role="alert"]').inner_text() if page.locator('div[role="alert"]').is_visible() else "Réessayez plus tard."
                    raise Exception(f"Échec de connexion - Vérifiez vos identifiants. Message: {error_message}")
                
                logging.info("✅ [4/7] Connexion réussie!")
                
                # 5. Aller sur la page Commandes
                logging.info("📋 [5/7] Navigation vers la liste des commandes...")
                page.goto(f"{self.BASE_URL}/gui.php?page=documents_commandes_liste", timeout=30000)
                page.wait_for_load_state('networkidle', timeout=30000)
                time.sleep(3)
                logging.info("✅ Page commandes chargée")
                
                # 6. Vérifier s'il y a des filtres actifs et les effacer si nécessaire
                logging.info("🔍 [6/7] Vérification des filtres...")
                try:
                    # Chercher le bouton "Effacer" (gomme)
                    # S'assurer que le sélecteur '.fa.fa-eraser' est correct
                    eraser_button = page.locator('.fa.fa-eraser').first
                    if eraser_button.is_visible(timeout=2000):
                        logging.info("🧹 Filtres détectés, effacement en cours...")
                        eraser_button.click()
                        page.wait_for_load_state('networkidle', timeout=15000)
                        time.sleep(2)
                        logging.info("✅ Filtres effacés")
                    else:
                        logging.info("ℹ️ Pas de bouton effacer visible")
                except Exception as e:
                    logging.info(f"ℹ️ Pas de filtres actifs ou erreur lors de la vérification: {e}")
                
                # 7. Extraire les données du tableau (toutes les commandes visibles)
                logging.info("📊 [7/7] Extraction des commandes...")
                
                # DEBUG: Prendre une capture d'écran de la page
                try:
                    # Rendre le chemin dynamique et sûr pour Streamlit
                    screenshot_dir = os.path.join(os.getcwd(), "screenshots")
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = os.path.join(screenshot_dir, f"page_commandes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    page.screenshot(path=screenshot_path, full_page=True)
                    logging.info(f"📸 Capture d'écran sauvegardée: {screenshot_path}")
                except Exception as e:
                    logging.warning(f"⚠️ Impossible de prendre la capture: {e}")
                
                commandes = self._extraire_commandes(page)
                
                if commandes:
                    # Filtrer pour garder seulement la semaine en cours (24/11 au 30/11)
                    commandes_semaine = self._filtrer_semaine_courante(commandes)
                    
                    # Remplir le dictionnaire de résultats
                    resultats["commandes"] = commandes_semaine
                    resultats["desadv_a_faire"] = self._filtrer_desadv(commandes_semaine)
                    resultats["commandes_sup_850"] = self._filtrer_montant_sup_850(commandes_semaine)
                    resultats["total_par_client"] = self._calculer_total_par_client(commandes_semaine)
                    resultats["success"] = True
                    resultats["message"] = f"{len(commandes_semaine)} commandes trouvées pour la semaine du 24/11 au 30/11"
                    logging.info(f"✅ {len(commandes_semaine)} commandes extraites pour cette semaine")
                else:
                    resultats["message"] = "Aucune commande trouvée"
                    logging.warning("⚠️ Aucune commande trouvée")
                
            except Exception as e:
                resultats["message"] = f"Erreur critique de scraping: {str(e)}"
                logging.error(f"❌ Erreur durant le scraping: {e}")
                
                # Prendre une capture d'écran pour déboguer l'erreur
                try:
                    screenshot_dir = os.path.join(os.getcwd(), "screenshots")
                    os.makedirs(screenshot_dir, exist_ok=True)
                    screenshot_path = os.path.join(screenshot_dir, f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                    page.screenshot(path=screenshot_path)
                    logging.error(f"📸 Capture d'écran d'erreur sauvegardée: {screenshot_path}")
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
            # Attendre que le tableau soit présent (classe "VL" avec V et L majuscules!)
            logging.info("Attente du tableau...")
            page.wait_for_selector('table.VL tbody tr', timeout=10000)
            
            # Extraire toutes les lignes du tableau (tbody tr)
            rows = page.locator('table.VL tbody tr').all()
            
            logging.info(f"✓ Nombre de lignes trouvées dans le tableau: {len(rows)}")
            
            for i, row in enumerate(rows):
                try:
                    cells = row.locator('td').all()
                    
                    # Vérifier qu'on a assez de colonnes (7 colonnes de données + 1 colonne action)
                    if len(cells) < 7:
                        continue
                    
                    # Colonnes: 0: Numéro, 1: Client, 2: Livrer à, 3: Création le, 4: Livrer le, 5: GLN, 6: Montant, 7: Statut/Actions
                    numero = cells[0].inner_text().strip()
                    client = cells[1].inner_text().strip()
                    livrer_a = cells[2].inner_text().strip()
                    creation = cells[3].inner_text().strip()
                    livraison = cells[4].inner_text().strip()
                    gln = cells[5].inner_text().strip()
                    montant_str = cells[6].inner_text().strip()
                    
                    # Le statut est dans la 8ème cellule (index 7)
                    statut_cell = cells[7].inner_text().strip() if len(cells) > 7 else "N/A"
                    
                    # Parser le montant
                    montant = self._parse_montant(montant_str)
                    
                    # Vérifier si DESADV nécessaire: On cherche la présence d'un lien "Préparer DESADV" dans la cellule d'action (index 7)
                    # Ceci est plus fiable que de chercher dans tout le HTML de la ligne.
                    desadv_needed = cells[7].locator('a:has-text("Préparer DESADV")').is_visible()
                    
                    commande = {
                        "numero": numero,
                        "client": client,
                        "livrer_a": livrer_a,
                        "date_creation": creation,
                        "date_livraison": livraison,
                        "gln": gln,
                        "montant": montant,
                        "statut": statut_cell,
                        "desadv_necessaire": desadv_needed # Renommé pour plus de clarté
                    }
                    
                    commandes.append(commande)
                    
                except Exception as e:
                    logging.warning(f"  ⚠️ Erreur ligne {i+1}: {e}")
                    continue
        
        except Exception as e:
            logging.error(f"❌ Erreur extraction tableau: {e}")
        
        return commandes
    
    def _filtrer_semaine_courante(self, commandes):
        """Filtre les commandes pour garder seulement celles de la semaine du 24/11 au 30/11/2025 (basé sur date_livraison)."""
        commandes_semaine = []
        
        # Dates de la semaine courante (basé sur le texte dans app.py)
        debut_semaine = datetime(2025, 11, 24)
        fin_semaine = datetime(2025, 11, 30)
        
        for cmd in commandes:
            try:
                # Parser la date de livraison (format DD/MM/YYYY)
                date_liv_str = cmd["date_livraison"]
                date_liv = datetime.strptime(date_liv_str, "%d/%m/%Y")
                
                # Vérifier si la date est dans l'intervalle [début, fin]
                if debut_semaine <= date_liv <= fin_semaine:
                    commandes_semaine.append(cmd)
            except ValueError:
                # Si erreur de parsing de date, on l'ignore (ou on la garde selon la politique désirée, ici on ignore)
                logging.warning(f"Date de livraison non valide: {cmd['date_livraison']} pour commande {cmd['numero']}")
                continue
        
        logging.info(f"📅 {len(commandes_semaine)} commandes filtrées pour la semaine du 24/11 au 30/11")
        return commandes_semaine
    
    def _parse_montant(self, montant_str):
        """Convertit un montant string en float (gestion des formats français: , comme décimal)."""
        try:
            # Enlever les espaces, € et remplacer la virgule (décimale) par un point
            montant_clean = montant_str.replace('€', '').replace(' ', '').replace('.', '').replace(',', '.').strip()
            if not montant_clean:
                return 0.0
            return float(montant_clean)
        except Exception as e:
            logging.error(f"Erreur de parsing du montant '{montant_str}': {e}")
            return 0.0
    
    def _filtrer_desadv(self, commandes):
        """Filtre les commandes qui nécessitent un DESADV."""
        # On utilise le champ 'desadv_necessaire' calculé dans _extraire_commandes
        return [cmd for cmd in commandes if cmd.get("desadv_necessaire", False)]
    
    def _filtrer_montant_sup_850(self, commandes):
        """Filtre les commandes avec montant > 850€."""
        return [cmd for cmd in commandes if cmd["montant"] > 850]
    
    def _calculer_total_par_client(self, commandes):
        """Calcule le total des commandes par client."""
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
