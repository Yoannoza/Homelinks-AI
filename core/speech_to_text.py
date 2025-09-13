import speech_recognition as sr
from pydub import AudioSegment
from openai import OpenAI
import os
from dotenv import load_dotenv


def transcribe_audio(file_path):
    """Convertir un fichier WebM en WAV puis le transcrire en texte"""
    # Charger les variables d'environnement
    load_dotenv()   
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY is not set in environment variables")
    
    try:
        temp_wav_path = file_path.replace(".webm", ".wav")
        
        # Try to find ffmpeg in multiple locations
        ffmpeg_paths = [
            "../bin/ffmpeg",
            "/usr/bin/ffmpeg", 
            "/usr/local/bin/ffmpeg",
            "ffmpeg"
        ]
        
        ffmpeg_path = None
        for path in ffmpeg_paths:
            if os.path.exists(path) or (path == "ffmpeg"):  # System PATH
                ffmpeg_path = path
                break
        
        if ffmpeg_path and ffmpeg_path != "ffmpeg":
            AudioSegment.converter = ffmpeg_path

        # Convertir WebM/Opus en WAV
        audio = AudioSegment.from_file(file_path, format="webm")
        audio.export(temp_wav_path, format="wav")
        
        client = OpenAI(api_key=openai_key)

        # Reconnaissance vocale with whisper
        with open(temp_wav_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="text",
                language="fr"
            )

        print(f"\n\nTranscription: {transcription}")

        # Nettoyage des fichiers temporaires
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

        return transcription

    except Exception as e:
        print(f"Error in transcribing audio: {e}")
        # Clean up temp files on error
        temp_wav_path = file_path.replace(".webm", ".wav")
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)
        raise e
