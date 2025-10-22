from google import genai
from google.genai import types
import os
from dotenv import load_dotenv


def transcribe_audio(file_path):
    """Transcrire un fichier audio directement avec Gemini"""
    # Charger les variables d'environnement
    load_dotenv()
    
    genai_key = os.getenv("GENAI_API_KEY")
    if not genai_key:
        raise ValueError("GENAI_API_KEY is not set in environment variables")
    
    try:
        print(f"Processing audio file: {file_path}")
        
        # Créer le client Gemini
        client = genai.Client(api_key=genai_key)
        
        # Lire le fichier audio
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()
        
        # Déterminer le type MIME du fichier
        mime_type = 'audio/webm'
        if file_path.endswith('.wav'):
            mime_type = 'audio/wav'
        elif file_path.endswith('.mp3'):
            mime_type = 'audio/mp3'
        elif file_path.endswith('.ogg'):
            mime_type = 'audio/ogg'
        elif file_path.endswith('.m4a'):
            mime_type = 'audio/aac'
        
        print(f"Audio file type: {mime_type}")
        
        # Prompt pour la transcription en français
        prompt = """Génère une transcription exacte de ce contenu audio en français. 
        Retourne uniquement la transcription textuelle, sans commentaires ni explications.
        Si l'audio contient des commandes pour une maison connectée (lumières, portes, etc.), 
        transcris exactement ce qui a été dit."""
        
        # Génération de la transcription avec inline audio
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type=mime_type,
                )
            ]
        )
        
        transcription = response.text.strip()
        print(f"Transcription: {transcription}")
        
        return transcription

    except Exception as e:
        print(f"Error in transcribing audio: {e}")
        raise e
