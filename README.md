# 🏠 Homelinks-AI


**API intelligente de contrôle vocal pour maison connectée**

Homelinks-AI est une API REST moderne qui permet de contrôler votre maison connectée par commandes vocales. Elle utilise Google Gemini AI pour la transcription vocale, l'intelligence artificielle et la synthèse vocale.

---

## 📖 À propos du projet

**Homelinks-AI** est un serveur développé par l'équipe **Homelinks** dans le cadre du projet de **mini maison connectée** du **Club IA de l'IFRI** (Institut de Formation et de Recherche en Informatique).

Ce projet vise à créer une solution complète de domotique vocale, permettant aux utilisateurs de contrôler leur environnement domestique par des commandes naturelles en français. Le serveur agit comme l'intelligence centrale de la maison connectée, traitant les commandes vocales et orchestrant les différents appareils IoT.

**🎯 Objectif :** Démontrer les capacités de l'IA moderne dans l'IoT et la domotique, en créant une interface vocale intuitive pour le contrôle d'une maison connectée.

---

## 👥 Équipe Homelinks

L'équipe **Homelinks** est composée d'étudiants passionnés par l'intelligence artificielle et l'IoT, travaillant ensemble au sein du Club IA de l'IFRI pour développer des solutions innovantes en domotique.

**Contact :** yoannoza25@gmail.com

---

## ✨ Fonctionnalités

- 🎤 **Transcription vocale** : Convertit vos fichiers audio en texte français avec Gemini AI
- 🧠 **Intelligence artificielle** : Comprend et traite vos commandes naturellement
- 🏠 **Contrôle maison connectée** : Lumières, portes, capteurs de fumée et présence
- 🔊 **Synthèse vocale** : Génère des réponses audio naturelles
- ⚡ **WebSocket temps réel** : Notifications instantanées via Socket.IO
- 📚 **Documentation interactive** : API Swagger intégrée

---

## 🚀 Démarrage rapide

### Prérequis

- Docker installé sur votre machine
- Clés API Google Gemini AI : [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)

### Installation en 3 étapes

```bash
# 1. Cloner le repository
git clone https://github.com/Yoannoza/Homelinks-AI.git
cd Homelinks-AI

# 2. Configurer les variables d'environnement
cp .env.example .env
nano .env  # Ajoutez vos clés API

# 3. Déployer avec Docker
chmod +x deploy.sh
./deploy.sh
```

✅ L'API sera accessible sur **http://localhost:5000**

---

## 🔑 Configuration

Créez un fichier `.env` à la racine du projet :

```bash
# Clés API Google Gemini (obligatoires)
GENAI_API_KEY=votre_clé_gemini_api_principale
GEMINI_API_KEY=votre_clé_gemini_api_secondaire

# Configuration serveur (optionnel)
PORT=5000
ALLOWED_ORIGINS=http://localhost:3000,https://localhost:3000,https://homelinks.yoann-oza.me
```

**Obtenir les clés API :**
- **Google Gemini AI** : https://makersuite.google.com/app/apikey
- *Note : Vous pouvez utiliser la même clé pour les deux variables ou des clés différentes*

**Modèles Gemini utilisés :**
- **Transcription** : `gemini-2.5-flash-lite` (optimisé pour la vitesse)
- **IA/Processing** : `gemini-2.5-flash-lite` (équilibre performance/coût)
- **TTS** : `gemini-2.5-flash-preview-tts` (spécialisé synthèse vocale)

---

## 📚 API Endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/transcribe` | POST | Transcription audio → texte (utilise GENAI_API_KEY) |
| `/process` | POST | Traitement des commandes vocales (utilise GEMINI_API_KEY) |
| `/audio` | GET | Récupération audio généré (utilise GEMINI_API_KEY) |
| `/health` | GET | Health check |

📖 **Documentation interactive** : http://localhost:5000/docs

### Exemples d'utilisation

#### 1. Transcription audio
```bash
curl -X POST http://localhost:5000/transcribe \
  -F "audio=@commande.wav"
```

#### 2. Traiter une commande
```bash
curl -X POST http://localhost:5000/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "allume les lumières du salon",
    "all_state": "\"salon\": false, \"cuisine\": false, ..."
  }'
```

#### 3. Récupérer l'audio
```bash
curl http://localhost:5000/audio --output response.mp3
```

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Client Web     │
└────────┬────────┘
         │ HTTP/WebSocket
         ▼
┌─────────────────┐
│  FastAPI        │ ◄── Transcription (gemini-2.5-flash-lite)
│  + Socket.IO    │ ◄── IA Processing (gemini-2.5-flash-lite)
└────────┬────────┘ ◄── TTS (gemini-2.5-flash-preview-tts)
         │
         ▼
┌─────────────────┐
│  Maison         │
│  Connectée      │
└─────────────────┘
```

**Stack technologique :**
- Framework : FastAPI 0.104+
- Server : Uvicorn avec support asyncio
- **Transcription** : Google Gemini AI `gemini-2.5-flash-lite` (GENAI_API_KEY)
- **Intelligence** : Google Gemini AI `gemini-2.5-flash-lite` (GEMINI_API_KEY)
- **Text-to-Speech** : Google Gemini AI `gemini-2.5-flash-preview-tts` (GEMINI_API_KEY)
- WebSocket : Socket.IO
- Déploiement : Docker + GitHub Actions

---

## 🛠️ Développement local

### Option 1 : Sans Docker

```bash
# Installation des dépendances
pip install -r requirements.txt

# Configuration
cp .env.example .env
nano .env  # Ajoutez vos clés API

# Lancement
cd core
python main.py
```

### Option 2 : Avec Docker

```bash
# Build
docker build -t homelinks-ai .

# Run
docker run -d \
  --name homelinks-api \
  -p 5000:5000 \
  --env-file .env \
  homelinks-ai
```

---

## 🎮 Contrôles disponibles

| Élément | Type | Valeurs |
|---------|------|---------|
| Lumières | boolean | salon, cuisine, chambre, extérieur, garage |
| Portes | string | door1 (salon), door2 (garage) : "on" / "off" |
| Sécurité | boolean | smoke (fumée), presence, auth |

**Exemples de commandes vocales :**
- "Allume les lumières du salon"
- "Éteins toutes les lumières"
- "Ouvre la porte du garage"
- "Quelle est la température ?"

---

## 🚢 Déploiement production

### Déploiement automatique (GitHub Actions)

Le projet inclut un workflow qui déploie automatiquement sur votre VM à chaque push sur `main`.

**Configuration :**
1. Ajoutez ces secrets dans GitHub (Settings > Secrets) :
   - `VM_HOST` : Adresse IP de votre VM
   - `VM_USER` : Utilisateur SSH
   - `VM_SSH_KEY` : Clé privée SSH

2. Modifiez le chemin dans `.github/workflows/deploy.yml`

Plus de détails : [GITHUB_SECRETS.md](GITHUB_SECRETS.md)

### Configuration du domaine

Le serveur est configuré pour accepter les requêtes depuis le domaine **homelinks.yoann-oza.me** ainsi que les origines de développement locales.

**Origines autorisées :**
- `http://localhost:3000` (développement local)
- `https://localhost:3000` (développement local HTTPS)  
- `https://homelinks.yoann-oza.me` (production)

**Configuration CORS :**
- Méthodes autorisées : `GET`, `POST`
- Headers autorisés : tous (`*`)
- Credentials : autorisés

### Déploiement manuel

```bash
# Sur votre VM
git clone https://github.com/Yoannoza/Homelinks-AI.git
cd Homelinks-AI
cp .env.example .env
nano .env  # Configurez vos clés
./deploy.sh
```

---

## 📊 Monitoring

```bash
# Logs en temps réel
docker logs -f homelinks-container

# Statistiques
docker stats homelinks-container

# Accès au conteneur
docker exec -it homelinks-container bash
```

---

## 🔐 Sécurité

- ✅ Validation des entrées avec Pydantic
- ✅ Gestion sécurisée des sessions
- ✅ CORS configuré
- ✅ Variables d'environnement pour les secrets
- ✅ Health check intégré

---

## 📞 Support


- 📧 Email : yoannoza25@gmail.com
- 🐛 Issues : [GitHub Issues](https://github.com/Yoannoza/Homelinks-AI/issues)
- 📚 Documentation complète : [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

---

**Fait avec ❤️ par l'équipe Homelinks**  
*Projet du Club IA - IFRI (Institut de Formation et de Recherche en Informatique)*