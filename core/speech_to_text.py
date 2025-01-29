import speech_recognition as sr
from pydub import AudioSegment
from openai import OpenAI
import os
from dotenv import load_dotenv


def transcribe_audio(file_path):
    """Convertir un fichier WebM en WAV puis le transcrire en texte"""
    # Charger les variables d'environnement
    load_dotenv()   
    try:
        temp_wav_path = file_path.replace(".webm", ".wav")
        
        FFMPEG_PATH = "../bin/ffmpeg"  # Change selon ton projet
        AudioSegment.converter = FFMPEG_PATH

        if not os.path.exists(FFMPEG_PATH):
            raise RuntimeError("FFmpeg introuvable, assure-toi qu'il est bien dans /app/bin/ffmpeg")

        # Convertir WebM/Opus en WAV
        audio = AudioSegment.from_file(file_path, format="webm")
        audio.export(temp_wav_path, format="wav")
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Reconnaissance vocale with whisper
        audio_file= open(temp_wav_path, "rb")
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file,
            response_format="text",
            language="fr"
        )


        # Reconnaissance vocale with speech_recognition
        # recognizer = sr.Recognizer()
        # with sr.AudioFile(temp_wav_path) as source:
        #     audio_data = recognizer.record(source)

        # transcription = recognizer.recognize_google(audio_data, language='fr-FR')
        print(f"\n\nTranscription: {transcription}")

        # Nettoyage des fichiers temporaires
        os.remove(temp_wav_path)

        return transcription

    except Exception as e:
        print(f"Error in transcribing audio: {e}")
        raise e
