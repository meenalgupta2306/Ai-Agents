"""Voice Cloning Feature - Service layer for sample set management and TTS generation"""
import os
import json
import uuid
import requests
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from werkzeug.datastructures import FileStorage

from .models import VoiceSample, SampleSet, GenerationRecord


class VoiceCloningService:
    """Service for managing voice sample sets and TTS generation"""
    
    def __init__(self, documents_dir: str, voice_service_url: str):
        self.documents_dir = Path(documents_dir)
        self.voice_samples_dir = self.documents_dir / 'voice_samples'
        self.voice_service_url = voice_service_url
        
    def create_sample_set(self, set_type: str = 'demo', user_id: Optional[str] = None) -> str:
        """
        Create a new sample set directory
        
        Args:
            set_type: 'profile' or 'demo'
            user_id: User ID for profile sets
            
        Returns:
            set_id: Unique identifier for the set
        """
        if set_type == 'profile' and user_id:
            set_id = f"user_{user_id}"
        else:
            set_id = f"set_{uuid.uuid4().hex[:8]}"
            
        set_dir = self.voice_samples_dir / set_id
        set_dir.mkdir(parents=True, exist_ok=True)
        
        # Create generated audio subdirectory for demo sets
        # Create generated audio subdirectory for all sets
        (set_dir / 'generated').mkdir(exist_ok=True)
            
        # Initialize metadata
        metadata = {
            'set_id': set_id,
            'set_type': set_type,
            'user_id': user_id,
            'samples': [],
            'created_at': datetime.now().isoformat(),
            'total_samples': 0
        }
        
        metadata_path = set_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        return set_id
    
    def get_sample_set(self, set_id: str) -> Optional[SampleSet]:
        """Get sample set metadata"""
        set_dir = self.voice_samples_dir / set_id
        metadata_path = set_dir / 'metadata.json'
        
        if not metadata_path.exists():
            return None
            
        with open(metadata_path, 'r') as f:
            data = json.load(f)
            
        samples = [VoiceSample(**s) for s in data.get('samples', [])]
        
        return SampleSet(
            set_id=data.get('set_id', set_id),
            set_type=data.get('set_type', 'profile'),
            user_id=data.get('user_id'),
            samples=samples,
            created_at=data.get('created_at', datetime.now().isoformat()),
            total_samples=len(samples)
        )
    
    def list_sample_sets(self, user_id: Optional[str] = None) -> List[SampleSet]:
        """List all available sample sets, optionally filtered by user"""
        sets = []
        
        if not self.voice_samples_dir.exists():
            return sets
            
        for set_dir in self.voice_samples_dir.iterdir():
            if set_dir.is_dir():
                sample_set = self.get_sample_set(set_dir.name)
                if sample_set:
                    if user_id is None or sample_set.user_id == user_id:
                        sets.append(sample_set)
                        
        return sets
    
    def upload_sample_to_set(self, set_id: str, audio_file: FileStorage) -> Tuple[bool, str, Optional[VoiceSample]]:
        """
        Upload a voice sample to an existing set
        
        Returns:
            (success, message, sample_info)
        """
        set_dir = self.voice_samples_dir / set_id
        
        if not set_dir.exists():
            return False, f"Sample set {set_id} not found", None
            
        # Forward to voice service for processing
        files = {'audio_file': (audio_file.filename, audio_file.stream, audio_file.content_type)}
        data = {'user_id': set_id}  # Use set_id as user_id for voice service
        
        try:
            response = requests.post(
                f"{self.voice_service_url}/upload-sample",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                sample_info = result.get('sample_info')
                
                if sample_info:
                    return True, "Sample uploaded successfully", VoiceSample(**sample_info)
                else:
                    return True, "Sample uploaded successfully", None
            else:
                error_msg = response.json().get('error', 'Upload failed')
                return False, error_msg, None
                
        except Exception as e:
            return False, f"Error uploading sample: {str(e)}", None
    
    def generate_speech(
        self,
        set_id: str,
        text: str,
        temperature: float = 0.85,
        speed: float = 1.0,
        repetition_penalty: float = 2.0,
        source: str = 'web'
    ) -> Tuple[bool, str, Optional[GenerationRecord]]:
        """
        Generate speech using samples from a set
        
        Returns:
            (success, message, generation_record)
        """
        set_dir = self.voice_samples_dir / set_id
        
        if not set_dir.exists():
            return False, f"Sample set {set_id} not found", None
            
        # Call voice service
        payload = {
            'user_id': set_id,  # Use set_id as user_id for voice service
            'text': text,
            'temperature': temperature,
            'speed': speed,
            'repetition_penalty': repetition_penalty
        }
        
        try:
            response = requests.post(
                f"{self.voice_service_url}/generate-speech",
                json=payload,
                timeout=300
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Create generation record
                record = GenerationRecord(
                    audio_filename=result['audio_filename'],
                    text=text,
                    set_id=set_id,
                    generated_at=datetime.now().isoformat(),
                    reference_clips_used=result.get('reference_clips_used', 0),
                    config=result.get('config', {}),
                    source=source
                )
                
                # Log generation to set's generation log
                self._log_generation(set_id, record)
                
                return True, "Speech generated successfully", record
            else:
                error_msg = response.json().get('error', 'Generation failed')
                return False, error_msg, None
                
        except Exception as e:
            return False, f"Error generating speech: {str(e)}", None
    
    def _log_generation(self, set_id: str, record: GenerationRecord):
        """Log a generation to the set's generation log"""
        set_dir = self.voice_samples_dir / set_id
        
        # For demo sets, log in the generated subdirectory
        # Log in the generated subdirectory for all sets
        log_path = set_dir / 'generated' / 'generation_log.json'
            
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing log
        log_data = {'generations': []}
        if log_path.exists():
            with open(log_path, 'r') as f:
                log_data = json.load(f)
                
        # Add new record
        log_data['generations'].append({
            'audio_filename': record.audio_filename,
            'text': record.text,
            'set_id': record.set_id,
            'generated_at': record.generated_at,
            'reference_clips_used': record.reference_clips_used,
            'config': record.config,
            'source': record.source
        })
        
        # Save log
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
    
    def get_generation_history(self, set_id: str) -> List[GenerationRecord]:
        """Get generation history for a sample set"""
        set_dir = self.voice_samples_dir / set_id
        
        # Log path is always in generated subdirectory
        log_path = set_dir / 'generated' / 'generation_log.json'
            
        if not log_path.exists():
            return []
            
        with open(log_path, 'r') as f:
            log_data = json.load(f)
            
        all_records = [GenerationRecord(**{**g, 'source': g.get('source', 'legacy')}) for g in log_data.get('generations', [])]
        
        # Filter for web sources only (exclude legacy/agent)
        return [r for r in all_records if r.source == 'web']
