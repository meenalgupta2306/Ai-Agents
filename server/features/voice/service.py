"""Voice service - handles voice sample management and speech generation"""
import os
import json
import httpx
from pathlib import Path
from typing import Optional, Dict, Any
from werkzeug.datastructures import FileStorage
import logging

logger = logging.getLogger(__name__)

# Configuration
VOICE_SERVICE_URL = os.getenv('VOICE_SERVICE_URL', 'http://localhost:5002')
VOICE_SERVICE_ENABLED = os.getenv('VOICE_SERVICE_ENABLED', 'true').lower() == 'true'
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DOCUMENTS_DIR = BASE_DIR / 'documents'


class VoiceService:
    """Service for managing voice samples and speech generation"""
    
    def __init__(self):
        self.voice_service_url = VOICE_SERVICE_URL
        self.enabled = VOICE_SERVICE_ENABLED
    
    def check_service_health(self) -> bool:
        """Check if voice service is running"""
        try:
            import requests
            response = requests.get(f"{self.voice_service_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Voice service health check failed: {str(e)}")
            return False
    
    def has_voice_sample(self, user_id: str) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if user has uploaded a voice sample
        
        Returns:
            Tuple of (has_sample: bool, metadata: dict or None)
        """
        user_dir = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}'
        sample_path = user_dir / 'sample.wav'
        metadata_path = user_dir / 'metadata.json'
        
        # Check if any wav files exist
        has_files = any(user_dir.glob('*.wav')) if user_dir.exists() else False
        
        if not has_files and not sample_path.exists():
            return False, None
        
        # Load metadata if available
        metadata = None
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata: {str(e)}")
        
        # If no metadata but files exist, create basic metadata
        if not metadata and has_files:
            metadata = {'samples': []}
        
        return True, metadata

    def upload_voice_sample(self, user_id: str, audio_file: FileStorage) -> Dict[str, Any]:
        """
        Upload voice sample to voice service
        
        Args:
            user_id: User ID
            audio_file: Uploaded audio file (Werkzeug FileStorage)
            
        Returns:
            Response from voice service
        """
        if not self.enabled:
            return {
                'status': 'error',
                'message': 'Voice service is disabled'
            }
        
        try:
            import requests
            # Prepare multipart form data
            files = {
                'audio_file': (audio_file.filename, audio_file.read(), audio_file.content_type)
            }
            data = {
                'user_id': user_id
            }
            
            # Send to voice service
            response = requests.post(
                f"{self.voice_service_url}/upload-sample",
                files=files,
                data=data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json()
                return {
                    'status': 'error',
                    'message': error_data.get('error', 'Upload failed')
                }
        
        except Exception as e:
            logger.error(f"Voice sample upload failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Upload failed: {str(e)}'
            }
    
    def generate_speech(self, user_id: str, text: str, **kwargs) -> Dict[str, Any]:
        """
        Generate speech using user's voice sample
        
        Args:
            user_id: User ID
            text: Text to convert to speech
            **kwargs: Additional generation parameters (temperature, speed, etc.)
            
        Returns:
            Response with audio filename and path
        """
        if not self.enabled:
            return {
                'status': 'error',
                'message': 'Voice service is disabled'
            }
        
        # Check if user has voice sample
        has_sample, _ = self.has_voice_sample(user_id)
        if not has_sample:
            return {
                'status': 'error',
                'message': 'No voice sample found. Please upload a voice sample first.',
                'requires_sample': True
            }
        
        try:
            import requests
            
            # Construct payload
            payload = {
                'user_id': user_id,
                'text': text
            }
            # Add optional config params
            payload.update(kwargs)
            
            # Send generation request to voice service
            response = requests.post(
                f"{self.voice_service_url}/generate-speech",
                json=payload,
                timeout=60.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                error_data = response.json()
                return {
                    'status': 'error',
                    'message': error_data.get('error', 'Generation failed')
                }
        
        except Exception as e:
            logger.error(f"Speech generation failed: {str(e)}")
            return {
                'status': 'error',
                'message': f'Generation failed: {str(e)}'
            }
    
    def get_audio_file_path(self, user_id: str, filename: str) -> Optional[Path]:
        """
        Get full path to generated audio file
        
        Args:
            user_id: User ID
            filename: Audio filename
            
        Returns:
            Path to audio file or None if not found
        """
        generated_path = DOCUMENTS_DIR / 'generated_audio' / f'user_{user_id}' / filename
        
        if generated_path.exists():
            return generated_path
            
        # Also check for voice samples (allow any .wav file in the directory)
        if filename.endswith('.wav'):
            # Check root of voice_samples (legacy samples)
            sample_path = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}' / filename
            if sample_path.exists():
                return sample_path
                
            # Check generated subdirectory (new standardized location)
            generated_sample_path = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}' / 'generated' / filename
            if generated_sample_path.exists():
                return generated_sample_path
            
            # Check artifacts directory
            artifact_path = DOCUMENTS_DIR / 'artifacts' / 'audio' / filename
            if artifact_path.exists():
                return artifact_path
        
        return None
