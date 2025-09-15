import tempfile
import os
import time
import glob
import uuid

def save_temp_file(file_data, file_extension="webm", prefix="temp_audio"):
    """Sauvegarde un fichier temporaire et retourne son chemin"""
    try:
        # Créer un nom de fichier plus sécurisé
        unique_id = str(uuid.uuid4())[:8]
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=f".{file_extension}",
            prefix=f"{prefix}_{unique_id}_"
        )
        temp_file.write(file_data)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        raise Exception(f"Failed to save temporary file: {str(e)}")

def clean_temp_file(file_path):
    """Nettoie les fichiers temporaires après usage"""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        print(f"Warning: Could not remove temporary file {file_path}: {e}")

def cleanup_old_temp_files(max_age_minutes=60):
    """Nettoie les fichiers temporaires de plus de 60 minutes"""
    try:
        temp_dir = tempfile.gettempdir()
        current_time = time.time()
        
        # Patterns pour les fichiers temporaires de l'app
        patterns = [
            os.path.join(temp_dir, "temp_audio_*"),
            "temp_audio_*",  # Dans le répertoire courant aussi
        ]
        
        files_cleaned = 0
        for pattern in patterns:
            for file_path in glob.glob(pattern):
                try:
                    file_age = current_time - os.path.getctime(file_path)
                    if file_age > (max_age_minutes * 60):
                        os.remove(file_path)
                        files_cleaned += 1
                except Exception:
                    continue  # Ignore individual file errors
                    
        if files_cleaned > 0:
            print(f"Cleaned up {files_cleaned} old temporary audio files")
            
    except Exception as e:
        print(f"Warning: Could not cleanup old temporary files: {e}")

def get_file_size_mb(file_path):
    """Retourne la taille d'un fichier en MB"""
    try:
        if os.path.exists(file_path):
            return os.path.getsize(file_path) / (1024 * 1024)
        return 0
    except Exception:
        return 0
