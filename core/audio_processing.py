import tempfile
import os

def save_temp_file(file_data, file_extension="webm"):
    """Sauvegarde un fichier temporaire et retourne son chemin"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}")
    temp_file.write(file_data)
    temp_file.close()
    return temp_file.name

def clean_temp_file(file_path):
    """Nettoie les fichiers temporaires après usage"""
    if os.path.exists(file_path):
        os.remove(file_path)
