from flask import Flask, request, jsonify, send_from_directory
import speech_recognition as sr
import requests
from flask_cors import CORS
from pydub import AudioSegment
import os
import google.generativeai as genai
from tts import speech
import json
from dotenv import load_dotenv  # Pour charger les clés API depuis .env

# Charger les variables d'environnement
load_dotenv()

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
XI_API_KEY = os.getenv("XI_API_KEY")

# Configurer l'API Google Generative AI
genai.configure(api_key=GENAI_API_KEY)

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)

# Initialiser l'état global et le modèle
state = "none"
model = genai.GenerativeModel('gemini-1.5-pro')

# Répertoires pour les fichiers temporaires
TEMP_AUDIO_PATH = "/tmp/audio.webm"
TEMP_WAV_PATH = "/tmp/audio.wav"

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    try:
        file = request.files['audio']
        file.save(TEMP_AUDIO_PATH)

        # Convertir WebM/Opus en WAV
        audio = AudioSegment.from_file(TEMP_AUDIO_PATH, format="webm")
        audio.export(TEMP_WAV_PATH, format="wav")

        # Reconnaissance vocale
        recognizer = sr.Recognizer()
        with sr.AudioFile(TEMP_WAV_PATH) as source:
            audio_data = recognizer.record(source)
        transcription = recognizer.recognize_google(audio_data, language='fr-FR')

        print(f"Transcription: {transcription}")  # Log dans le terminal

        # Nettoyage des fichiers temporaires
        os.remove(TEMP_AUDIO_PATH)
        os.remove(TEMP_WAV_PATH)

        return jsonify(transcription=transcription)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/audio')
def get_recording():
    return send_from_directory('.', 'output.mp3') 

@app.route('/process', methods=['POST'])
def process_transcription():
    try:
        data = request.json
        text = data.get('text', '')
        state = data.get('state', '')
        all_state = data.get('all_state', '')
        

        commands = "{" + all_state

        # Identifier si une commande ou une réponse est attendue
        wanted_str = model.generate_content(
            f"""Retourne moi uniquement (sans commentaire) ce json ("command":false, "response":false) mis à jour en fonction de si le texte ci dessous attends qu'on execute une commande ou si il attends une réponse: {text}."""
        ).text

        wanted = json.loads(wanted_str)
        print(f"Interprétation du modèle: {wanted}")

        # Traiter les commandes ou les réponses
        if wanted['command']:
            exec_prompt = f"""Retourne-moi uniquement (sans commentaire) ce JSON ({state}) mis à jour avec les commandes issues de ce texte {text}. Voici une description pour que tu interprètes mieux les commandes : 
            'salon' - "État de la lampe dans le salon (allumée ou éteinte)",
            ...
            """
            commands = model.generate_content(exec_prompt).text
            print(f"Commandes générées: \n{commands}")

        if wanted['response']:
            res_prompt = f"""Base-toi sur cet état de la maison ({all_state}) et sur la demande de l'utilisateur {text} pour produire une réponse très précise."""
            response = model.generate_content(res_prompt).text
            speech(response)
            commands += ""","audio":true}"""
            print(f"Réponse générée: \n{response}")

        return jsonify(commands=commands)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
