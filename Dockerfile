# Dockerfile simple pour Homelinks-AI
FROM python:3.11-slim

# Variables d'environnement
ENV PYTHONUNBUFFERED=1

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libasound2-dev \
    portaudio19-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Répertoire de travail
WORKDIR /app

# Copie et installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code
COPY . .

# Port
EXPOSE 5000

# Commande de démarrage (on démarre depuis le dossier core)
WORKDIR /app/core
CMD ["python", "-m", "uvicorn", "main:socket_app", "--host", "0.0.0.0", "--port", "5000"]
