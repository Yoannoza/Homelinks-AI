import google.generativeai as genai
import os
import mimetypes
import base64
from dotenv import load_dotenv


def transcribe_audio(file_path):
    """Transcrire un fichier audio directement avec Gemini"""
    # Charger les variables d'environnement
    load_dotenv()
    
    genai_key = os.getenv("GENAI_API_KEY")
    if not genai_key:
        raise ValueError("GENAI_API_KEY is not set in environment variables")
    
    try:
        # Configuration de Gemini
        genai.configure(api_key=genai_key)
        
        print(f"Processing audio file: {file_path}")
        
        # Lire le fichier audio en base64
        with open(file_path, 'rb') as audio_file:
            audio_data = base64.b64encode(audio_file.read()).decode('utf-8')
        
        # Déterminer le type MIME du fichier
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            # Fallback pour les fichiers audio courants
            if file_path.endswith('.webm'):
                mime_type = 'audio/webm'
            elif file_path.endswith('.wav'):
                mime_type = 'audio/wav'
            elif file_path.endswith('.mp3'):
                mime_type = 'audio/mp3'
            else:
                mime_type = 'audio/webm'  # Par défaut
        
        print(f"Audio file type: {mime_type}")
        
        # Prompt pour la transcription en français
        prompt = """
        Transcris exactement le contenu audio en français. 
        Ne fais que retourner la transcription textuelle, sans commentaires ni explications.
        Si l'audio contient des commandes pour une maison connectée (lumières, portes, etc.), 
        retourne la transcription exacte telle qu'elle a été prononcée.
        """
        
        # Génération de la transcription avec inline_data
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        response = model.generate_content([
            prompt,
            {
                "mime_type": mime_type,
                "data": audio_data
            }
        ])
        
        transcription = response.text.strip()
        print(f"Transcription: {transcription}")
        
        return transcription

    except Exception as e:
        print(f"Error in transcribing audio: {e}")
        raise e
