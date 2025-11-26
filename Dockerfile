# Dockerfile pour Auchan Scraper

# Image Python 3.11 slim
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système pour Playwright
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Installer Playwright Chromium
RUN python -m playwright install --with-deps chromium

# Copier le reste des fichiers de l'application
COPY . .

# Définir le port pour Streamlit
ENV PORT 8501

# Commande pour lancer Streamlit
CMD ["streamlit", "run", "app.py", "--server.port", "${PORT}", "--server.address", "0.0.0.0"]
