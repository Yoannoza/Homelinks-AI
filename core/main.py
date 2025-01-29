import logging
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import eventlet
eventlet.monkey_patch()
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


Hyperbolic_api = os.getenv("HYPERBOLIC_API_KEY")
def gen_response(sys_prompt, user_prompt):
    url = "https://api.hyperbolic.xyz/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Hyperbolic_api}"
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
        "response_format" : {'type': 'json_object'}
    }
    
    response = requests.post(url, headers=headers, json=data)
    resp = response.json()
    return json.loads(resp['choices'][0]['message']['content'])
    

GENAI_API_KEY = os.getenv("GENAI_API_KEY")
XI_API_KEY = os.getenv("XI_API_KEY")

# Configurer l'API Google Generative AI
genai.configure(api_key=GENAI_API_KEY)

# Initialisation de l'application Flask
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")
# Configurer le logging
# logging.basicConfig(level=logging.DEBUG)

# Initialiser l'état global et le modèle
state = "none"
# model = genai.GenerativeModel('gemini-1.5-pro')


@app.route('/transcribe', methods=['POST'])
def transcribe_audio_route():
    try:
        # Recevoir et enregistrer le fichier audio
        file = request.files['audio']
        temp_audio_path = save_temp_file(file.read(), file_extension="webm")

        # Convertir et transcrire l'audio
        transcription = transcribe_audio(temp_audio_path)

        # Nettoyer les fichiers temporaires
        clean_temp_file(temp_audio_path)

        return jsonify(transcription=transcription)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/audio')
def get_recording():
    try:
        return send_from_directory('.', 'output.mp3')
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/process', methods=['POST'])
def process_transcription():
    try:
        data = request.json
        text = data.get('text', '')
        state = data.get('state', '')
        all_state = data.get('all_state', '')

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
        
        response = gen_response(system, user)
        
        
        speech(response["assistant_response"])
        
        # Informer le front que l'audio est prêt
        socketio.emit('audio_ready', {'url': '/audio'})
        
        print(f"Commandes générées: \n{response}")
        

        # # Identifier si une commande ou une réponse est attendue
        # wanted_str = model.generate_content(
        #     f""" Retourne moi uniquement (sans commentaire) ce json ("command":false, "response":false) mis à jour en fonction de si le texte ci dessous attends qu'on execute une commande ou si il attends une réponse: {text}."""
        # ).text
        

        # wanted = json.loads(wanted_str)
        # print(f"Interprétation du modèle: {wanted}")

        # # Traiter les commandes ou les réponses
        # if wanted['command']:
        #     exec_prompt = f"""Retourne-moi uniquement (sans commentaire) ce JSON ({state}) mis à jour avec les commandes issues de ce texte {text}. Voici une description pour que tu interprètes mieux les commandes : 
        #     'salon' - "État de la lampe dans le salon (allumée ou éteinte)", ..."""
        #     commands = model.generate_content(exec_prompt).text
        #     print(f"Commandes générées: \n{commands}")

        # if wanted['response']:
        #     res_prompt = f"""Base-toi sur cet état de la maison ({all_state}) et sur la demande de l'utilisateur {text} pour produire une réponse très précise."""
        #     response = model.generate_content(res_prompt).text
        #     speech(response)
        #     commands += ""","audio":true}"""
        #     print(f"Réponse générée: \n{response}")

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # app.run(debug=True)
    socketio.run(app, host="0.0.0.0", port=5000)
