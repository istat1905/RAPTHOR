# Utiliser Python 3.11
FROM python:3.11-slim

# Installer les dépendances système nécessaires pour Playwright
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libx11-xcb1 \
    libxcb1 \
    libxcursor1 \
    libxi6 \
    libxtst6 \
    libglib2.0-0 \
    libxss1 \
    && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements
COPY requirements.txt .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Installer Chromium et ses dépendances AVANT de copier les fichiers
RUN playwright install --with-deps chromium

# Copier le reste des fichiers de l'application APRES l'installation de Playwright
COPY . .

# Exposer le port 8501 (port par défaut de Streamlit)
EXPOSE 8501

# Commande pour lancer l'application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
