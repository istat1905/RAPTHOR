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
        
        # Vérifier et corriger le format de la date (jj/mm/aaaa)
        try:
            # Parser la date pour s'assurer qu'elle est valide
            date_obj = datetime.strptime(date_str, "%d/%m/%Y")
            # Reformater pour garantir jj/mm/aaaa (avec zéros devant si nécessaire)
            date_str = date_obj.strftime("%d/%m/%Y")
            print(f"📅 Date formatée: {date_str}")
        except ValueError:
            # Si le format est incorrect, essayer d'autres formats
            try:
                # Essayer avec l'année sur 2 chiffres
                date_obj = datetime.strptime(date_str, "%d/%m/%y")
                date_str = date_obj.strftime("%d/%m/%Y")
                print(f"📅 Date convertie: {date_str}")
            except:
                print(f"⚠️ Format de date invalide: {date_str}")
                raise Exception(f"Format de date invalide. Utilisez jj/mm/aaaa (ex: 25/11/2025)")
        
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
                        
                        # Cliquer et focus sur le champ
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
                        
                        # Appuyer sur Enter pour valider la recherche
                        print("  → Validation avec Enter")
                        page.keyboard.press('Enter')
                        time.sleep(3)
                        
                        print(f"✅ Filtre appliqué")
                        
                    except Exception as e:
                        print(f"⚠️ Erreur lors de la saisie: {e}")
                        # Fallback sur l'URL directe
                        search_url = f"{self.base_url}/gui.php?page=documents_commandes_liste&doDateHeureDemandee={date_str}"
                        print(f"  → Utilisation de l'URL: {search_url}")
                        page.goto(search_url, timeout=60000)
                        page.wait_for_load_state('networkidle', timeout=30000)
                        time.sleep(5)
                
                # Attendre le chargement des résultats
                print("Attente des résultats...")
                page.wait_for_load_state('networkidle', timeout=30000)
                time.sleep(3)
                
                # Prendre une capture d'écran après recherche
                try:
                    page.screenshot(path="/tmp/after_search.png", full_page=True)
                    print("📸 Capture après recherche: /tmp/after_search.png")
                except:
                    pass
                
                # 8. Debug: Vérifier la structure de la page
                print("\n=== DEBUG: Analyse de la page ===")
                
                # Compter les tableaux
                tables_count = page.locator('table').count()
                print(f"Nombre de tableaux: {tables_count}")
                
                # Chercher spécifiquement les tbody tr
                tbody_tr_count = page.locator('tbody tr').count()
                print(f"Nombre de lignes tbody tr: {tbody_tr_count}")
                
                # Chercher les lignes avec la classe spécifique si visible dans les images
                all_tr_count = page.locator('tr').count()
                print(f"Nombre total de tr: {all_tr_count}")
                
                # Afficher le HTML du tableau pour comprendre la structure
                if tables_count > 0:
                    try:
                        table_html = page.locator('table').first.inner_html()
                        print(f"\nHTML du premier tableau (premiers 500 caractères):")
                        print(table_html[:500])
                    except:
                        pass
                
                # Vérifier s'il y a un message "Aucun résultat"
                page_text = page.inner_text('body')
                if 'aucun' in page_text.lower() or 'no result' in page_text.lower():
                    print("⚠️ Message 'aucun résultat' détecté dans la page")
                
                print("=== FIN DEBUG ===\n")
                
                # 9. Extraire les données du tableau
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
            print("\n=== Début extraction ===")
            
            # Stratégie 1: Chercher tbody tr
            rows = page.locator('tbody tr').all()
            print(f"Stratégie 1 - Lignes tbody tr trouvées: {len(rows)}")
            
            # Stratégie 2: Si pas de résultats, chercher toutes les lignes tr
            if len(rows) == 0:
                print("Aucune ligne tbody tr, recherche de toutes les tr...")
                all_rows = page.locator('tr').all()
                print(f"Stratégie 2 - Total de lignes tr: {len(all_rows)}")
                
                # Filtrer pour exclure les en-têtes (thead) et lignes de recherche
                rows = []
                for row in all_rows:
                    try:
                        # Vérifier si la ligne contient des td (pas des th)
                        if row.locator('td').count() > 0:
                            rows.append(row)
                    except:
                        continue
                print(f"Lignes avec des td: {len(rows)}")
            
            if len(rows) == 0:
                print("❌ Aucune ligne trouvée dans le tableau")
                return commandes
            
            print(f"\n📊 Traitement de {len(rows)} lignes...")
            
            for i, row in enumerate(rows):
                try:
                    cells = row.locator('td').all()
                    nb_cells = len(cells)
                    
                    print(f"\n  Ligne {i+1}: {nb_cells} cellules")
                    
                    if nb_cells < 3:  # Ligne trop courte, probablement pas une commande
                        print(f"    ⚠️ Ligne ignorée (pas assez de cellules)")
                        continue
                    
                    # Debug: afficher le contenu des premières cellules
                    if i < 3:  # Afficher le détail des 3 premières lignes
                        for j, cell in enumerate(cells[:8]):
                            try:
                                text = cell.inner_text().strip()
                                print(f"    Cellule {j}: '{text[:50]}'")
                            except:
                                pass
                    
                    # Extraire les données (ajuster les indices selon le HTML réel)
                    # D'après vos captures: Numéro, Client, Livrer à, Création le, Livrer le, GLN, Montant, Statut
                    try:
                        # Chercher la cellule avec le numéro de commande (commence souvent par des chiffres)
                        numero = ""
                        client = ""
                        
                        for idx, cell in enumerate(cells):
                            text = cell.inner_text().strip()
                            # Le numéro de commande ressemble à "03134140" ou "03129921"
                            if text.isdigit() and len(text) >= 6:
                                numero = text
                                # Le client est généralement la cellule suivante
                                if idx + 1 < len(cells):
                                    client = cells[idx + 1].inner_text().strip()
                                break
                        
                        if not numero:
                            print(f"    ⚠️ Pas de numéro de commande trouvé")
                            continue
                        
                        # Extraire les autres infos si disponibles
                        livrer_a = cells[2].inner_text().strip() if len(cells) > 2 else ""
                        creation = cells[3].inner_text().strip() if len(cells) > 3 else ""
                        livraison = cells[4].inner_text().strip() if len(cells) > 4 else ""
                        gln = cells[5].inner_text().strip() if len(cells) > 5 else ""
                        montant_str = cells[6].inner_text().strip() if len(cells) > 6 else "0"
                        statut = cells[7].inner_text().strip() if len(cells) > 7 else ""
                        
                        # Parser le montant
                        montant = self._parse_montant(montant_str)
                        
                        # Vérifier si DESADV nécessaire
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
                        print(f"    ✅ Commande extraite: {numero} - {client} - {montant}€")
                        
                    except Exception as e:
                        print(f"    ❌ Erreur extraction données: {e}")
                        continue
                        
                except Exception as e:
                    print(f"  ❌ Erreur ligne {i+1}: {e}")
                    continue
            
            print(f"\n=== Fin extraction: {len(commandes)} commandes ===\n")
        
        except Exception as e:
            print(f"❌ Erreur extraction tableau: {e}")
            import traceback
            traceback.print_exc()
        
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
