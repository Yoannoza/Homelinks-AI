import asyncio
import logging
import os
import json
import uuid
import tempfile
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import aiofiles
import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field, validator
from starlette.middleware.sessions import SessionMiddleware
import socketio

from dotenv import load_dotenv
from audio_processing import save_temp_file, clean_temp_file, cleanup_old_temp_files, get_file_size_mb
from speech_to_text import transcribe_audio
from tts import speech
from ai_response import generate_ai_response
from config import Config

# Load environment variables
load_dotenv()

# Environment variables validation
def validate_environment():
    """Validate that required environment variables are set"""
    missing_vars = Config.validate_required_keys()
    if missing_vars:
        print(f"Warning: Missing required environment variables: {', '.join(missing_vars)}")
        print("Some core features will not work properly without these variables.")
        
    return len(missing_vars) == 0

# Pydantic models for request/response validation
class ProcessRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000, description="Voice command text")
    state: Optional[str] = Field("", description="Current device state")
    all_state: Optional[str] = Field("", description="Complete home state JSON")
    
    @validator('text')
    def sanitize_text(cls, v):
        import re
        # Remove potential harmful characters but keep French accents
        return re.sub(r'[^\w\s\-.,!?àáâäèéêëìíîïòóôöùúûüÿñç]', '', v.strip(), flags=re.IGNORECASE)

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    services: Dict[str, bool]
    audio_ready: bool
    session_id: str

class TranscriptionResponse(BaseModel):
    transcription: str

class ProcessResponse(BaseModel):
    salon: Optional[bool] = None
    cuisine: Optional[bool] = None
    chambre: Optional[bool] = None
    exterieur: Optional[bool] = None
    garage: Optional[bool] = None
    smoke: Optional[bool] = None
    presence: Optional[bool] = None
    auth: Optional[bool] = None
    door1: Optional[str] = None
    door2: Optional[str] = None
    time: Optional[str] = None
    assistant_response: str

# Global storage for user sessions and audio files
user_audio_files: Dict[str, str] = {}
user_sessions: Dict[str, str] = {}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Async HTTP client for API calls
async def get_http_client():
    return httpx.AsyncClient(timeout=30.0)

async def gen_response(sys_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """Generate response using the separated AI module"""
    try:
        # Extraire l'état de la maison du prompt système
        # Le prompt contient l'état entre les premiers { }
        import re
        state_match = re.search(r'\{([^}]+)\}', sys_prompt)
        home_state = state_match.group(1) if state_match else ""
        
        # Utiliser le module séparé
        response = generate_ai_response(user_prompt, home_state)
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI response generation failed: {str(e)}")

def get_user_session(request: Request) -> str:
    """Get or create a unique session ID for the user"""
    session_id = request.session.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())[:8]
        request.session['session_id'] = session_id
    return session_id

def validate_audio_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded audio file"""
    if not file:
        return False, "No file provided"
    
    if not file.filename:
        return False, "No file selected"
    
    # Check file size (max 10MB)
    if hasattr(file, 'size') and file.size:
        if file.size > 10 * 1024 * 1024:
            return False, "File too large (max 10MB)"
        if file.size == 0:
            return False, "Empty file not allowed"
    
    # Basic file type validation
    allowed_extensions = ['.webm', '.wav', '.mp3', '.m4a', '.ogg']
    file_ext = os.path.splitext(file.filename.lower())[1]
    if file_ext not in allowed_extensions:
        return False, f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
    
    return True, "Valid file"

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Homelinks AI Assistant API")
    validate_environment()
    yield
    # Shutdown
    logger.info("Shutting down Homelinks AI Assistant API")
    # Cleanup any remaining audio files
    for audio_file in user_audio_files.values():
        try:
            if os.path.exists(audio_file):
                os.remove(audio_file)
        except Exception:
            pass

# Create FastAPI app
app = FastAPI(
    title="Homelinks AI Assistant API",
    description="Voice assistant API for smart home control",
    version="2.0.0",
    lifespan=lifespan
)

# # CORS configuration
allowed_origins = Config.ALLOWED_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# SocketIO setup
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=allowed_origins
)
socket_app = socketio.ASGIApp(sio, app)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test basic functionality
        current_time = datetime.now().isoformat()
    
        
        # Check services availability (basic test)
        services_status = {
            "speech_to_text": True,  # Could add actual service test
            "tts": True,
            "ai_response": True
        }
        
        return {
            "status": "healthy",
            "timestamp": current_time,
            "services": services_status,
            "version": "1.0",
            "uptime": current_time
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio_route(
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...)
):
    """Transcribe audio file to text"""
    logger.info("Transcribe audio request received")
    
    # Cleanup old temporary files in background
    background_tasks.add_task(cleanup_old_temp_files)
    
    # Validate file
    is_valid, message = validate_audio_file(audio)
    if not is_valid:
        logger.warning(f"Invalid audio file: {message}")
        raise HTTPException(status_code=400, detail=message)
    
    try:
        # Read file content
        file_content = await audio.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Empty file content")
        
        # Save temporary file
        file_extension = os.path.splitext(audio.filename.lower())[1][1:] or "webm"
        temp_audio_path = save_temp_file(file_content, file_extension=file_extension)
        logger.info(f"Audio file saved temporarily at {temp_audio_path} ({get_file_size_mb(temp_audio_path):.2f} MB)")

        # Transcribe audio
        transcription = transcribe_audio(temp_audio_path)
        logger.info("Audio transcription completed successfully")

        # Clean up temporary file
        background_tasks.add_task(clean_temp_file, temp_audio_path)

        return TranscriptionResponse(transcription=transcription)

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.get("/audio")
async def get_recording(request: Request):
    """Download generated speech audio file"""
    try:
        session_id = get_user_session(request)
        audio_file = user_audio_files.get(session_id)
        
        if not audio_file or not os.path.exists(audio_file):
            # Fallback to legacy system
            fallback_file = 'output.mp3'
            if os.path.exists(fallback_file):
                return FileResponse(fallback_file)
            raise HTTPException(status_code=404, detail="Audio file not found")
            
        return FileResponse(audio_file)
    except Exception as e:
        logger.error(f"Audio retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve audio: {str(e)}")

@app.post("/process", response_model=ProcessResponse)
async def process_transcription(
    request: Request,
    background_tasks: BackgroundTasks,
    data: ProcessRequest
):
    """Process voice command and control smart home devices"""
    logger.info("Process transcription request received")
    
    try:
        text = data.text
        state = data.state or ""
        all_state = data.all_state or ""
        
        logger.info(f"Processing text: {text[:50]}...")

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
        
        # Generate response
        logger.info("Generating AI response")
        response = await gen_response(system, text)
        logger.info("AI response generated successfully")
        
        # Validate response structure
        if "assistant_response" not in response:
            logger.error("Missing assistant_response in AI response")
            raise HTTPException(status_code=502, detail="Missing assistant_response in AI response")
        
        # Generate speech in background
        session_id = get_user_session(request)
        background_tasks.add_task(
            generate_speech_background, 
            response["assistant_response"], 
            session_id
        )
        
        logger.info(f"Process completed successfully")
        return ProcessResponse(**response)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Process transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

async def generate_speech_background(text: str, session_id: str):
    """Background task to generate speech"""
    max_retries = 2
    audio_file_path = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Generating speech audio (attempt {attempt + 1}/{max_retries})")
            audio_file_path = speech(text, session_id)
            
            # Store the audio file path for this session
            user_audio_files[session_id] = audio_file_path
            
            # Emit audio ready signal via SocketIO
            await sio.emit('audio_ready', {'url': '/audio', 'session_id': session_id})
            logger.info("Speech generated and audio ready signal sent")
            break
            
        except Exception as e:
            logger.warning(f"Speech generation failed (attempt {attempt + 1}): {e}")
            if attempt == max_retries - 1:
                logger.error("All speech generation attempts failed")

# SocketIO event handlers
@sio.event
async def connect(sid, environ):
    logger.info(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    logger.info(f"Client disconnected: {sid}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(
        "main:socket_app",  # Use socket_app instead of app for SocketIO support
        host="0.0.0.0",
        port=5000,
        reload=False,  # Set to True for development
        log_level="info"
    )