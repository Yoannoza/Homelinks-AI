# 🏠 Homelinks-AI

API de contrôle vocal pour maison connectée utilisant Gemini AI et FastAPI.

## 🚀 Déploiement rapide

```bash
# 1. Cloner le repo
git clone https://github.com/Yoannoza/Homelinks-AI.git
cd Homelinks-AI

# 2. Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec vos clés API

# 3. Déployer avec Docker
./deploy.sh
```

## 🔑 Configuration

Créez un fichier `.env` avec :

```bash
GENAI_API_KEY=your_gemini_api_key
HYPERBOLIC_API_KEY=your_hyperbolic_api_key
```

## 📚 API Endpoints

- `POST /transcribe` - Transcription audio → texte
- `POST /process` - Traitement des commandes vocales  
- `GET /audio` - Récupération audio généré
- `GET /health` - Health check

Documentation complète : `http://localhost:5000/docs`

## 🏗️ Architecture

- **Transcription** : Google Gemini AI
- **IA** : DeepSeek-V3 via Hyperbolic
- **TTS** : Google Gemini
- **WebSocket** : Socket.IO pour notifications temps réel

## �️ Développement

```bash
# Installation
pip install -r requirements.txt

# Démarrage
cd core
python main.py
```