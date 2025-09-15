"""
Configuration centralisée pour l'application Homelinks-AI
"""
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration de l'application"""
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GENAI_API_KEY = os.getenv("GENAI_API_KEY")
    
    # CORS origins
    ALLOWED_ORIGINS = ["*"]


    @classmethod
    def validate_required_keys(cls):
        """Valide que les clés API requises sont présentes"""
        missing_keys = []
        
        if not cls.GEMINI_API_KEY:
            missing_keys.append("GEMINI_API_KEY")
        if not cls.GENAI_API_KEY:
            missing_keys.append("GENAI_API_KEY")
        return missing_keys
    