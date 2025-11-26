# Image officielle Playwright avec Chromium
FROM mcr.microsoft.com/playwright/python:1.38.0-focal

WORKDIR /app

# Copier requirements et installer
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste des fichiers
COPY . .

# Définir le port Streamlit
ENV PORT 8501

# Lancer Streamlit avec variable de port
CMD sh -c "streamlit run app.py --server.port \$PORT --server.address 0.0.0.0"
