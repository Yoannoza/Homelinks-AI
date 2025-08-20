import eventlet
eventlet.monkey_patch()

import logging
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
import speech_recognition as sr
import google.generativeai as genai
from audio_processing import save_temp_file, clean_temp_file
from speech_to_text import transcribe_audio
from tts import speech

# Charger les variables d'environnement
load_dotenv()

# Validate environment variables
HYPERBOLIC_API_KEY = os.getenv("HYPERBOLIC_API_KEY")
GENAI_API_KEY = os.getenv("GENAI_API_KEY")
XI_API_KEY = os.getenv("XI_API_KEY")

def validate_environment():
    """Validate that required environment variables are set"""
    missing_vars = []
    if not HYPERBOLIC_API_KEY:
        missing_vars.append("HYPERBOLIC_API_KEY")
    if not XI_API_KEY:
        missing_vars.append("XI_API_KEY")
    
    if missing_vars:
        print(f"Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("Some features may not work properly without these variables.")
    
    return len(missing_vars) == 0

# Validate environment on startup
validate_environment()

Hyperbolic_api = HYPERBOLIC_API_KEY
def gen_response(sys_prompt, user_prompt):
    """Generate response from Hyperbolic API with proper error handling"""
    if not HYPERBOLIC_API_KEY:
        raise ValueError("HYPERBOLIC_API_KEY is not set in environment variables")
    
    url = "https://api.hyperbolic.xyz/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HYPERBOLIC_API_KEY}"
    }
    data = {
        "messages": [
            {
                "role": "system",
                "content": sys_prompt,
            },
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "model": "deepseek-ai/DeepSeek-V3",
        "max_tokens": 18917,
        "temperature": 0.1,
        "top_p": 0.9,
        "response_format": {'type': 'json_object'}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        resp = response.json()
        
        if 'choices' not in resp or not resp['choices']:
            raise ValueError("Invalid API response: no choices found")
            
        if 'message' not in resp['choices'][0] or 'content' not in resp['choices'][0]['message']:
            raise ValueError("Invalid API response: no message content found")
            
        content = resp['choices'][0]['message']['content']
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
            
    except requests.exceptions.Timeout:
        raise ValueError("API request timed out")
    except requests.exceptions.ConnectionError:
        raise ValueError("Failed to connect to API")
    except requests.exceptions.HTTPError as e:
        raise ValueError(f"API request failed with status {e.response.status_code}: {e.response.text}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"API request failed: {str(e)}")
    

    
# Configurer l'API Google Generative AI
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
else:
    print("Warning: GENAI_API_KEY not set - Google Generative AI features will not work")

# Initialisation de l'application Flask
app = Flask(__name__)

# CORS configuration - more flexible for development
allowed_origins = [
    "https://homelinks.vercel.app",
    "http://localhost:3000",  # For local development
    "http://127.0.0.1:3000",  # For local development
]

# Allow localhost for development if in debug mode
if app.debug:
    allowed_origins.extend([
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ])

CORS(app, origins=allowed_origins, methods=["GET", "POST"], allow_headers=["Content-Type"])
socketio = SocketIO(app, cors_allowed_origins=allowed_origins)

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialiser l'état global et le modèle
state = "none"
# model = genai.GenerativeModel('gemini-1.5-pro')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to monitor API status"""
    status = {
        "status": "healthy",
        "timestamp": json.dumps({"time": "placeholder"}),  # Will be replaced by actual implementation
        "services": {
            "hyperbolic_api": bool(HYPERBOLIC_API_KEY),
            "xi_api": bool(XI_API_KEY),
            "genai_api": bool(GENAI_API_KEY)
        }
    }
    
    # Check if audio file exists
    audio_file = 'output.mp3'
    status["audio_ready"] = os.path.exists(audio_file)
    
    return jsonify(status), 200


def validate_audio_file(file):
    """Validate uploaded audio file"""
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    # Check file size (max 10MB)
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Seek back to start
    
    if size > 10 * 1024 * 1024:
        return False, "File too large (max 10MB)"
    
    return True, "Valid file"

def validate_process_input(data):
    """Validate input data for process endpoint"""
    if not data:
        return False, "No data provided"
    
    text = data.get('text', '')
    if not text or not text.strip():
        return False, "Text is required and cannot be empty"
    
    if len(text) > 1000:
        return False, "Text too long (max 1000 characters)"
    
    return True, "Valid input"

@app.route('/transcribe', methods=['POST'])
def transcribe_audio_route():
    logger.info("Transcribe audio request received")
    try:
        # Validate file
        file = request.files.get('audio')
        is_valid, message = validate_audio_file(file)
        if not is_valid:
            logger.warning(f"Invalid audio file: {message}")
            return jsonify({"error": message}), 400
        
        # Recevoir et enregistrer le fichier audio
        temp_audio_path = save_temp_file(file.read(), file_extension="webm")
        logger.info(f"Audio file saved temporarily at {temp_audio_path}")

        # Convertir et transcrire l'audio
        transcription = transcribe_audio(temp_audio_path)
        logger.info("Audio transcription completed successfully")

        # Nettoyer les fichiers temporaires
        clean_temp_file(temp_audio_path)

        return jsonify({"transcription": transcription}), 200

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return jsonify({"error": f"Transcription failed: {str(e)}"}), 500

@app.route('/audio')
def get_recording():
    try:
        audio_file = 'output.mp3'
        if not os.path.exists(audio_file):
            return jsonify({"error": "Audio file not found"}), 404
        return send_from_directory('.', audio_file)
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve audio: {str(e)}"}), 500

@app.route('/process', methods=['POST'])
def process_transcription():
    logger.info("Process transcription request received")
    try:
        # Validate content type
        if not request.is_json:
            logger.warning("Request not JSON format")
            return jsonify({"error": "Content-Type must be application/json"}), 400
        
        data = request.json
        is_valid, message = validate_process_input(data)
        if not is_valid:
            logger.warning(f"Invalid input data: {message}")
            return jsonify({"error": message}), 400
        
        text = data.get('text', '').strip()
        state = data.get('state', '')
        all_state = data.get('all_state', '')
        
        logger.info(f"Processing text: {text[:50]}...")

        commands = "{" + all_state + "}"
        
        system = f"""
            Tu es Homelinks, l'assistant vocal de ma maison. Voici le JSON qui renseigne sur l'état actuel de la maison :
            {commands}
            
            Explication : 
            
            - **salon** (`boolean`): 
            - `true` : Lampes du salon allumés.
            - `false` : Lampes du salon éteints.

            - **cuisine** (`boolean`): 
            - `true` : Lampes de la cuisine allumés.
            - `false` : Lampes de la cuisine éteints.

            - **chambre** (`boolean`): 
            - `true` : Lampes de la chambre allumés.
            - `false` : Lampes de la chambre éteints.

            - **exterieur** (`boolean`): 
            - `true` : Lampes extérieurs allumés.
            - `false` : Lampes extérieurs éteints.

            - **garage** (`boolean`): 
            - `true` : Lampes du garage allumés.
            - `false` : Lampes du garage éteints.

            - **smoke** (`boolean`): 
            - `true` : Fumée détectée.
            - `false` : Pas de fumée détectée.

            - **presence** (`boolean`): 
            - `true` : Présence détectée.
            - `false` : Aucune présence détectée.

            - **auth** (`boolean`): 
            - `true` : Authentification verifiée.
            - `false` : Authentification non verifiée.

            - **door1** (`string`): 
            - `"on"` : Porte du salon ouverte.
            - `"off"` : Porte du salon fermée.

            - **door2** (`string`): 
            - `"on"` : Porte du garage ouverte.
            - `"off"` : Porte du garage fermée.

            - **time** (`string`): 
            - Heure actuelle sous le format `HH:MM:SS---JourMoisAnnee`.

            - **assistant_response** (`string`): 
            - Réponse textuelle de l'assistant vocal, à lire à haute voix.
            

            Tu devras mettre à jour ce JSON en fonction de mes demandes, en respectant le format attendu.

            Dans ce JSON, il y a une variable assistant_response. C'est dans cette variable que tu devras mettre ta réponse textuelle à mon message. Elle sera ensuite transcrite en audio par un autre outil.

            Tu dois analyser mes demandes pour savoir :

            Quels appareils allumer ou éteindre,
            Si je veux tout allumer ou tout éteindre,
            Me répondre si je pose des questions sur l'état de la maison,
            Mais aussi répondre à des questions diverses.
            Tu es un assistant chaleureux et responsable. Un membre à part entière de la famille. Au-delà de la gestion de la maison, ton rôle est aussi d'entretenir des discussions excitantes et fraternelles à travers la variable assistant_response.

            Tu es l'assistant savant, drole, sympathique, responsable et protecteur de la maison.

            ⚠️ N'oublie jamais : tu dois toujours me renvoyer le résultat sous forme de JSON. TOUJOURS. Et jamais de valeurs vides.

            Exemple :
            {commands}
        """
        user = text
        
        # Generate response with error handling
        try:
            logger.info("Generating AI response")
            response = gen_response(system, user)
            logger.info("AI response generated successfully")
        except ValueError as e:
            logger.error(f"AI response generation failed: {str(e)}")
            return jsonify({"error": f"AI response generation failed: {str(e)}"}), 503
        
        # Validate response structure
        if not isinstance(response, dict):
            logger.error("Invalid response format from AI")
            return jsonify({"error": "Invalid response format from AI"}), 502
            
        if "assistant_response" not in response:
            logger.error("Missing assistant_response in AI response")
            return jsonify({"error": "Missing assistant_response in AI response"}), 502
        
        # Generate speech with error handling
        try:
            logger.info("Generating speech audio")
            speech(response["assistant_response"])
            # Informer le front que l'audio est prêt
            socketio.emit('audio_ready', {'url': '/audio'})
            logger.info("Speech generated and audio ready signal sent")
        except Exception as e:
            logger.warning(f"Speech generation failed: {e}")
            # Continue without audio - don't fail the entire request
        
        logger.info(f"Process completed successfully: {response}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Process transcription error: {str(e)}")
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, host="0.0.0.0", port=5000)
