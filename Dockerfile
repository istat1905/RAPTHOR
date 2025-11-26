# Dockerfile corrigé pour Render avec Streamlit
FROM python:3.11-slim

WORKDIR /app

# Installer dépendances système pour Playwright
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

# Installer les dépendances Python
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Installer Playwright Chromium
RUN python -m playwright install --with-deps chromium

# Copier le reste des fichiers
COPY . .

# Exposer le port (facultatif)
ENV PORT 8501

# Commande pour lancer Streamlit avec expansion de variable
CMD sh -c "streamlit run app.py --server.port \$PORT --server.address 0.0.0.0"
