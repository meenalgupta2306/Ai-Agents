"""Voice generation tool for MCP"""
import os
import json
import base64
import httpx
from pathlib import Path


def voice_tool(text: str, user_email: str = "test@example.com"):
    """
    Generates speech in the user's cloned voice using XTTS.
    
    Args:
        text: The text to convert to speech
        user_email: Email of the user (defaults to test@example.com)
        
    Returns:
        Dict with status, message, and base64 encoded audio data
    """
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DOCUMENTS_DIR = BASE_DIR / 'documents'
    VOICE_SERVICE_URL = os.getenv('VOICE_SERVICE_URL', 'http://localhost:5002')
    
    # For now, use email as user_id (in production, you'd look up user_id from email)
    user_id = user_email.replace('@', '_').replace('.', '_')
    
    # Check if user has a voice sample
    # Check if user has any voice samples
    user_samples_dir = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}'
    has_samples = any(user_samples_dir.glob('*.wav')) if user_samples_dir.exists() else False
    
    if not has_samples:
        return {
            "status": "ERROR",
            "message": "No voice sample found. Please upload a voice sample first by visiting the Voice Setup page in your profile settings.",
            "requires_sample": True
        }
    
    try:
        # Call voice service to generate speech
        response = httpx.post(
            f"{VOICE_SERVICE_URL}/generate-speech",
            json={
                'user_id': user_id,
                'text': text
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Get the generated audio file path
            audio_filename = result.get('audio_filename')
            if audio_filename:
                # Check the new standardized location first
                audio_file_path = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}' / 'generated' / audio_filename
                
                # Fallback to legacy location
                if not audio_file_path.exists():
                    audio_file_path = DOCUMENTS_DIR / 'generated_audio' / f'user_{user_id}' / audio_filename
                
                # Read and encode audio file as base64
                if audio_file_path.exists():
                    with open(audio_file_path, 'rb') as f:
                        audio_data = f.read()
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    # Copy to artifacts directory for persistent storage
                    artifacts_dir = DOCUMENTS_DIR / 'artifacts' / 'audio'
                    artifacts_dir.mkdir(parents=True, exist_ok=True)
                    artifact_filename = f"speech_{audio_filename}"
                    artifact_path = artifacts_dir / artifact_filename
                    
                    import shutil
                    shutil.copy2(audio_file_path, artifact_path)
                    
                    # Return format that artifact extractor can parse
                    artifact_location = f"documents/artifacts/audio/{artifact_filename}"
                    
                    return {
                        "status": "SUCCESS",
                        "message": f"Speech generated successfully! ({len(text)} characters)\nLOCATION: {artifact_location}",
                        "audio_filename": audio_filename,
                        "audio_data": audio_base64,
                        "audio_format": "wav",
                        "artifact_path": artifact_location,
                        "text": text
                    }
                else:
                    return {
                        "status": "ERROR",
                        "message": f"Audio file was generated but not found at expected path: {audio_file_path}"
                    }
            else:
                return {
                    "status": "ERROR",
                    "message": "Speech generation completed but no audio file was returned"
                }
        else:
            error_data = response.json()
            return {
                "status": "ERROR",
                "message": error_data.get('error', 'Speech generation failed'),
                "details": error_data
            }
    
    except httpx.TimeoutException:
        return {
            "status": "ERROR",
            "message": "Speech generation timed out. The text might be too long or the voice service is not responding."
        }
    except httpx.ConnectError:
        return {
            "status": "ERROR",
            "message": "Could not connect to voice service. Please ensure the voice service is running on port 5002."
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Speech generation failed: {str(e)}"
        }
