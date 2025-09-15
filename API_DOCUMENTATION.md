# API Documentation - Homelinks-AI

## Vue d'ensemble

Homelinks-AI est une API de contrôle vocal pour maison connectée utilisant FastAPI. L'API permet de transcrire de l'audio en texte, traiter les commandes vocales pour contrôler des appareils domestiques, et générer des réponses audio.

**Base URL:** `http://localhost:5000`  
**Protocol:** HTTP/HTTPS  
**WebSocket Support:** Oui (Socket.IO)

## Architecture

- **Framework:** FastAPI avec Socket.IO
- **Transcription:** Google Gemini AI (GENAI_API_KEY)
- **Intelligence Artificielle:** DeepSeek-V3 via Hyperbolic API
- **Text-to-Speech:** Google Gemini TTS
- **Sessions:** Gestion de sessions utilisateur avec IDs uniques

## Variables d'environnement requises

```bash
GENAI_API_KEY=your_gemini_api_key_here
GEMINI_API_KEY=your_alternative_gemini_key_here
HYPERBOLIC_API_KEY=your_hyperbolic_api_key_here
```

## Endpoints de l'API

### 1. POST /transcribe

Transcrit un fichier audio en texte français.

**Paramètres:**
- `audio` (file, required): Fichier audio à transcrire
  - Formats supportés: MP3, WAV, WEBM, M4A, OGG
  - Taille max: 25 MB

**Réponse:**
```json
{
  "transcription": "éteindre les lumières du salon"
}
```

**Codes d'erreur:**
- `400`: Fichier audio invalide ou vide
- `500`: Erreur de transcription

**Exemple cURL:**
```bash
curl -X POST "http://localhost:5000/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "audio=@command.wav"
```

---

### 2. POST /process

Traite une commande textuelle et contrôle les appareils de la maison connectée.

**Corps de la requête:**
```json
{
  "text": "allumer les lumières du salon",
  "state": "", 
  "all_state": "\"salon\": false, \"cuisine\": true, \"chambre\": false, \"exterieur\": false, \"garage\": false, \"smoke\": false, \"presence\": true, \"auth\": true, \"door1\": \"off\", \"door2\": \"off\", \"time\": \"14:30:25---15Sep2025\""
}
```

**Paramètres:**
- `text` (string, required): Commande vocale transcrite (1-1000 caractères)
- `state` (string, optional): État actuel des appareils (legacy)
- `all_state` (string, optional): État complet de la maison au format JSON

**Réponse:**
```json
{
  "salon": true,
  "cuisine": true,
  "chambre": false,
  "exterieur": false,
  "garage": false,
  "smoke": false,
  "presence": true,
  "auth": true,
  "door1": "off",
  "door2": "off",
  "time": "14:32:15---15Sep2025",
  "assistant_response": "J'ai allumé les lumières du salon comme demandé !"
}
```

**Schéma de l'état de la maison:**

| Champ | Type | Description |
|-------|------|-------------|
| `salon` | boolean | Lumières du salon (true=allumées, false=éteintes) |
| `cuisine` | boolean | Lumières de la cuisine |
| `chambre` | boolean | Lumières de la chambre |
| `exterieur` | boolean | Lumières extérieures |
| `garage` | boolean | Lumières du garage |
| `smoke` | boolean | Détection de fumée (true=fumée détectée) |
| `presence` | boolean | Détection de présence |
| `auth` | boolean | État d'authentification |
| `door1` | string | Porte du salon ("on"=ouverte, "off"=fermée) |
| `door2` | string | Porte du garage ("on"=ouverte, "off"=fermée) |
| `time` | string | Horodatage format "HH:MM:SS---JourMoisAnnee" |
| `assistant_response` | string | Réponse textuelle de l'assistant |

**Codes d'erreur:**
- `400`: Données de requête invalides
- `500`: Erreur de traitement IA
- `502`: Réponse IA malformée

**Exemple cURL:**
```bash
curl -X POST "http://localhost:5000/process" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "allumer toutes les lumières",
    "all_state": "\"salon\": false, \"cuisine\": false, \"chambre\": false, \"exterieur\": false, \"garage\": false, \"smoke\": false, \"presence\": true, \"auth\": true, \"door1\": \"off\", \"door2\": \"off\", \"time\": \"14:30:25---15Sep2025\""
  }'
```

---

### 3. GET /audio

Récupère le fichier audio généré pour la session utilisateur.

**Paramètres:** Aucun (utilise les cookies de session)

**Réponse:** 
- **Content-Type:** `audio/mpeg`
- **Body:** Flux audio MP3

**Codes d'erreur:**
- `404`: Fichier audio introuvable
- `500`: Erreur de récupération

**Exemple cURL:**
```bash
curl -X GET "http://localhost:5000/audio" \
  -H "Cookie: session=your_session_cookie" \
  --output response.mp3
```

---

## WebSocket Events (Socket.IO)

### Connection
```javascript
const socket = io('http://localhost:5000');
```

### Events

#### `connect`
Événement émis lors de la connexion client.

#### `disconnect` 
Événement émis lors de la déconnexion client.

#### `audio_ready`
Événement émis quand l'audio est prêt à être téléchargé.

**Payload:**
```json
{
  "url": "/audio",
  "session_id": "unique_session_id"
}
```

**Exemple JavaScript:**
```javascript
socket.on('audio_ready', (data) => {
  console.log('Audio ready at:', data.url);
  // Télécharger l'audio
  window.location.href = data.url;
});
```

---

## Flow d'utilisation typique

### 1. Transcription vocale complète
```bash
# 1. Transcrire l'audio
curl -X POST "http://localhost:5000/transcribe" \
  -F "audio=@command.wav"

# 2. Traiter la commande
curl -X POST "http://localhost:5000/process" \
  -H "Content-Type: application/json" \
  -d '{"text": "allumer le salon", "all_state": "..."}'

# 3. Récupérer la réponse audio
curl -X GET "http://localhost:5000/audio" --output response.mp3
```

### 2. Intégration WebSocket
```javascript
const socket = io('http://localhost:5000');

// Écouter quand l'audio est prêt
socket.on('audio_ready', (data) => {
  fetch(data.url)
    .then(response => response.blob())
    .then(audioBlob => {
      const audio = new Audio(URL.createObjectURL(audioBlob));
      audio.play();
    });
});

// Envoyer une commande
fetch('/process', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    text: "éteindre toutes les lumières",
    all_state: "..."
  })
});
```

---

## Validation et sécurité

### Validation des fichiers audio
- **Formats acceptés:** mp3, wav, webm, m4a, ogg
- **Taille maximale:** 25 MB
- **Validation MIME type:** Oui

### Sécurité
- **CORS:** Configuré pour domaines autorisés
- **Sanitisation:** Nettoyage automatique du texte d'entrée
- **Rate limiting:** Gestion des sessions utilisateur
- **Cleanup automatique:** Suppression des fichiers temporaires

### Sessions
- **Gestion:** Automatic session ID generation
- **Storage:** In-memory session storage
- **Cleanup:** Background cleanup of old temporary files

---

## Gestion d'erreurs

### Codes d'état HTTP
- `200`: Succès
- `400`: Requête malformée
- `404`: Ressource introuvable  
- `500`: Erreur serveur interne
- `502`: Erreur de passerelle (IA indisponible)
- `503`: Service indisponible

### Format des erreurs
```json
{
  "detail": "Description de l'erreur"
}
```

---

## Configuration CORS

Domaines autorisés par défaut:
- `https://homelinks.vercel.app`
- `http://localhost:3000`
- `http://127.0.0.1:3000`

---

## Déploiement

### Développement
```bash
cd core
python main.py
```

### Production
```bash
uvicorn main:socket_app --host 0.0.0.0 --port 5000
```

---

## Modèles de données Pydantic

### ProcessRequest
```python
{
  "text": str,           # 1-1000 caractères, requis
  "state": str,         # optionnel, legacy
  "all_state": str      # optionnel, état JSON complet
}
```

### TranscriptionResponse  
```python
{
  "transcription": str  # Texte transcrit
}
```

### ProcessResponse
```python
{
  "salon": bool,
  "cuisine": bool, 
  "chambre": bool,
  "exterieur": bool,
  "garage": bool,
  "smoke": bool,
  "presence": bool,
  "auth": bool,
  "door1": str,
  "door2": str,
  "time": str,
  "assistant_response": str
}
```

---

## Logs et monitoring

Les logs incluent:
- Requêtes entrantes
- Taille des fichiers audio
- Statut de transcription  
- Génération de réponses IA
- Génération d'audio
- Erreurs et exceptions

**Format de log:**
```
2025-09-15 14:30:25 - main - INFO - Process transcription request received
```
