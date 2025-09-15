import os
import uuid
import time
import glob
import wave
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Charger les variables d'environnement
load_dotenv()

def cleanup_old_audio_files(max_age_hours=24):
    """Nettoie les fichiers audio de plus de 24h"""
    try:
        current_time = time.time()
        pattern = "audio_*.wav"  # Changé en .wav pour Gemini
        for file_path in glob.glob(pattern):
            file_age = current_time - os.path.getctime(file_path)
            if file_age > (max_age_hours * 3600):
                os.remove(file_path)
    except Exception as e:
        print(f"Warning: Could not cleanup old audio files: {e}")

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
    """Sauvegarde les données PCM dans un fichier WAV"""
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(rate)
        wf.writeframes(pcm)

def speech(text, session_id=None, voice_name='Kore'):
    """Génère de la parole à partir d'un texte et sauvegarde le fichier audio avec Gemini TTS"""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in environment variables")
    
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    # Nettoyage automatique des anciens fichiers
    cleanup_old_audio_files()
    
    # Génération d'un nom de fichier unique
    unique_id = session_id or str(uuid.uuid4())[:8]
    OUTPUT_PATH = f"audio_{unique_id}.wav"  # Changé en .wav
    
    try:
        # Configuration du client Gemini
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        # Génération du contenu audio avec Gemini TTS
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text[:5000],  # Limite de longueur du texte
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name,
                        )
                    )
                ),
            )
        )
        
        # Extraction des données audio
        audio_data = response.candidates[0].content.parts[0].inline_data.data
        
        # Sauvegarde du fichier audio
        wave_file(OUTPUT_PATH, audio_data)
        
        print(f"Audio stream saved successfully to {OUTPUT_PATH}")
        return OUTPUT_PATH  # Retourner le chemin du fichier créé
        
    except Exception as e:
        if "API_KEY" in str(e):
            raise Exception(f"Gemini API authentication error: {str(e)}")
        elif "quota" in str(e).lower() or "limit" in str(e).lower():
            raise Exception(f"Gemini API quota/limit error: {str(e)}")
        else:
            raise Exception(f"Gemini TTS request failed: {str(e)}")

# Fonction utilitaire pour lister les voix disponibles (optionnelle)
def get_available_voices():
    """Retourne la liste des voix disponibles pour Gemini TTS"""
    # Voix couramment disponibles pour Gemini TTS
    return [
        'Kore',
        'Charon', 
        'Fenrir',
        'Aoede',
        # Ajouter d'autres voix selon la documentation Gemini
    ]