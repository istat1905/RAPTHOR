# Utiliser une image avec Playwright pré-installé
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installer Firefox explicitement
RUN playwright install firefox

# Copier le reste des fichiers de l'application
COPY . .

# Exposer le port 8501 (port par défaut de Streamlit)
EXPOSE 8501

# Commande pour lancer l'application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
