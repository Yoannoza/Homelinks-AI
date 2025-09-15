import google.generativeai as genai
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
        # Configuration de Gemini
        genai.configure(api_key=genai_key)
        
        print(f"Uploading audio file: {file_path}")
        
        # Upload du fichier audio vers Gemini
        myfile = genai.upload_file(path=file_path, display_name="audio_transcription")
        
        print(f"File uploaded successfully: {myfile.uri}")
        
        # Prompt pour la transcription en français
        prompt = """
        Transcris exactement le contenu audio en français. 
        Ne fais que retourner la transcription textuelle, sans commentaires ni explications.
        Si l'audio contient des commandes pour une maison connectée (lumières, portes, etc.), 
        retourne la transcription exacte telle qu'elle a été prononcée.
        """
        
        # Génération de la transcription
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content([prompt, myfile])
        
        transcription = response.text.strip()
        print(f"\n\nTranscription: {transcription}")
        
        # Suppression du fichier uploadé pour économiser l'espace
        genai.delete_file(myfile.name)
        
        return transcription

    except Exception as e:
        print(f"Error in transcribing audio: {e}")
        raise e
