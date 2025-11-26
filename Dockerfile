# Utilise l'image Python officielle comme base
FROM python:3.11-slim

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Installe les dépendances nécessaires à Playwright et aux navigateurs headless
# Ces paquets sont souvent obligatoires pour le scraping robuste
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    libwebp-dev \
    # Dépendances nécessaires à Chromium/Playwright
    libnss3 \
    libfontconfig1 \
    libgconf-2-4 \
    --fix-missing && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copie le fichier des dépendances et installe-les
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Installe le navigateur Chromium pour Playwright
# Ceci est CRUCIAL pour que le scraping fonctionne
RUN playwright install chromium

# Copie le reste du code dans le conteneur
COPY . .

# Expose le port par défaut de Streamlit (8501)
EXPOSE 8501

# Commande pour lancer l'application Streamlit
# Le --server.port est nécessaire si Render utilise une variable d'environnement pour le port
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.enableCORS", "false"]
