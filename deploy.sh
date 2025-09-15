#!/bin/bash

# deploy.sh - Script de déploiement simple pour Homelinks-AI

set -e

APP_NAME="homelinks-ai"
IMAGE_NAME="homelinks-ai"
CONTAINER_NAME="homelinks-container"

echo "🚀 Déploiement de $APP_NAME..."

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

# Vérifier .env
if [ ! -f ".env" ]; then
    echo "❌ Fichier .env manquant"
    echo "💡 Copiez .env.example vers .env et configurez vos clés API"
    exit 1
fi

# Arrêter le conteneur existant
echo "🛑 Arrêt du conteneur existant..."
docker stop $CONTAINER_NAME 2>/dev/null || true
docker rm $CONTAINER_NAME 2>/dev/null || true

# Construire l'image
echo "🔨 Construction de l'image..."
docker build -t $IMAGE_NAME .

# Démarrer le conteneur
echo "▶️ Démarrage du conteneur..."
docker run -d \
  --name $CONTAINER_NAME \
  -p 5000:5000 \
  --env-file .env \
  --restart unless-stopped \
  $IMAGE_NAME

# Attendre que le service soit prêt
echo "⏳ Attente du démarrage..."
sleep 10

# Tester l'API
if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Déploiement réussi!"
    echo "📊 API accessible sur: http://localhost:5000"
    echo "📚 Documentation: http://localhost:5000/docs"
    echo "📋 Logs: docker logs -f $CONTAINER_NAME"
else
    echo "❌ Le service ne répond pas"
    echo "📋 Logs d'erreur:"
    docker logs $CONTAINER_NAME
    exit 1
fi
