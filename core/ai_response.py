"""
Module de génération de réponses IA pour Homelinks-AI
Sépare la logique d'IA du contrôleur principal
Utilise l'API Gemini de Google
"""
import os
import json
import requests
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class AIResponseGenerator:
    """Générateur de réponses IA pour l'assistant Homelinks"""
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set in environment variables")
        
        self.model = "gemini-2.5-flash-lite"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        
    def generate_response(self, user_text, home_state=""):
        """
        Génère une réponse IA basée sur le texte utilisateur et l'état de la maison
        
        Args:
            user_text (str): Le texte de commande de l'utilisateur
            home_state (str): L'état actuel de la maison en JSON
            
        Returns:
            dict: Réponse JSON avec les commandes et assistant_response
        """
        
        # Construction du prompt système
        system_prompt = self._build_system_prompt(home_state)
        
        # Configuration de la requête API pour Gemini
        headers = {
            "Content-Type": "application/json",
        }
        
        # Format de données pour Gemini
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_prompt}\n\nUtilisateur: {user_text}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topP": 0.9,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json"
            }
        }
        
        # Ajouter la clé API à l'URL
        url_with_key = f"{self.api_url}?key={self.api_key}"
        
        try:
            response = requests.post(url_with_key, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            resp = response.json()
            
            if 'candidates' not in resp or not resp['candidates']:
                raise ValueError("Invalid API response: no candidates found")
                
            if 'content' not in resp['candidates'][0] or 'parts' not in resp['candidates'][0]['content']:
                raise ValueError("Invalid API response: no content parts found")
                
            content = resp['candidates'][0]['content']['parts'][0]['text']
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse JSON response: {e}")
                
        except requests.exceptions.Timeout:
            raise ValueError("API request timed out")
        except requests.exceptions.ConnectionError:
            raise ValueError("Failed to connect to API")
        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_json = e.response.json()
                if 'error' in error_json:
                    error_detail = f": {error_json['error'].get('message', 'Unknown error')}"
            except:
                error_detail = f": {e.response.text}"
            raise ValueError(f"API request failed with status {e.response.status_code}{error_detail}")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API request failed: {str(e)}")
    
    def _build_system_prompt(self, home_state):
        """Construit le prompt système pour l'IA"""
        
        commands = "{" + home_state + "}" if home_state else "{}"
        
        return f"""
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


# Instance globale pour réutilisation
ai_generator = None

def get_ai_generator():
    """Retourne l'instance du générateur d'IA (singleton)"""
    global ai_generator
    if ai_generator is None:
        ai_generator = AIResponseGenerator()
    return ai_generator

def generate_ai_response(user_text, home_state=""):
    """
    Fonction simplifiée pour générer une réponse IA
    
    Args:
        user_text (str): Texte de l'utilisateur
        home_state (str): État de la maison en JSON
        
    Returns:
        dict: Réponse de l'IA
    """
    generator = get_ai_generator()
    return generator.generate_response(user_text, home_state)