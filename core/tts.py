import requests
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def speech(text):
    """Génère de la parole à partir d'un texte et sauvegarde le fichier audio"""
    XI_API_KEY = os.getenv("XI_API_KEY")
    
    if not XI_API_KEY:
        raise ValueError("XI_API_KEY is not set in environment variables")
    
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    VOICE_ID = "5Qfm4RqcAer0xoyWtoHC"
    OUTPUT_PATH = "output.mp3"
    CHUNK_SIZE = 1024

    # Construire l'URL de l'API TTS
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream"

    headers = {
        "Accept": "application/json",
        "xi-api-key": XI_API_KEY
    }

    data = {
        "text": text[:5000],  # Limit text length to prevent overly long requests
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        }
    }

    try:
        response = requests.post(tts_url, headers=headers, json=data, stream=True, timeout=30)
        response.raise_for_status()

        with open(OUTPUT_PATH, "wb") as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                f.write(chunk)

        print("Audio stream saved successfully.")
    except requests.exceptions.Timeout:
        raise Exception("TTS request timed out")
    except requests.exceptions.HTTPError as e:
        raise Exception(f"TTS API error: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"TTS request failed: {str(e)}")
    except IOError as e:
        raise Exception(f"Failed to save audio file: {str(e)}")
