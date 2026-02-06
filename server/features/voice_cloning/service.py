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
        
        # Provider Registry
        self.MODEL_PROVIDERS = {
            "coqui-xtts-v2": "coqui",
            "minimax-t2a": "minimax"
        }
        
    def _get_provider_for_model(self, model_id: str) -> str:
        """Get the provider key for a given model ID"""
        return self.MODEL_PROVIDERS.get(model_id, "coqui")  # Default to coqui if unknown
        
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
        source: str = 'web',
        model: str = 'coqui-xtts-v2'  # Default to existing model
    ) -> Tuple[bool, str, Optional[GenerationRecord]]:
        """
        Generate speech using samples from a set using the specified model provider
        """
        set_dir = self.voice_samples_dir / set_id
        
        if not set_dir.exists():
            return False, f"Sample set {set_id} not found", None

        # Determine provider
        provider = self._get_provider_for_model(model)
        
        try:
            # Dispatch to provider handler
            if provider == "coqui":
                return self._generate_coqui(set_id, text, temperature, speed, repetition_penalty, source, model)
            elif provider == "minimax":
                return self._generate_minimax(set_id, text, temperature, speed, repetition_penalty, source, model)
            else:
                return False, f"Unsupported provider for model {model}", None

        except Exception as e:
            return False, f"Error generating speech: {str(e)}", None

    def _generate_coqui(
        self, set_id, text, temperature, speed, repetition_penalty, source, model
    ) -> Tuple[bool, str, Optional[GenerationRecord]]:
        """Handle generation using local Coqui TTS service"""
        payload = {
            'user_id': set_id,
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
                
                record = GenerationRecord(
                    audio_filename=result['audio_filename'],
                    text=text,
                    set_id=set_id,
                    generated_at=datetime.now().isoformat(),
                    reference_clips_used=result.get('reference_clips_used', 0),
                    config=result.get('config', {}),
                    source=source,
                    model=model
                )
                
                self._log_generation(set_id, record)
                return True, "Speech generated successfully", record
            else:
                error_msg = response.json().get('error', 'Generation failed')
                return False, error_msg, None
                
        except Exception as e:
            raise e

    def _generate_minimax(
        self, set_id, text, temperature, speed, repetition_penalty, source, model
    ) -> Tuple[bool, str, Optional[GenerationRecord]]:
        """
        Handle generation using Minimax API
        API Docs: https://platform.minimax.io/docs/guides/speech-voice-clone
        """
        api_key = os.getenv("MINIMAX_API_KEY")
        print(f"[{datetime.now()}] Starting Minimax generation for set {set_id}")
        if not api_key:
            print(f"[{datetime.now()}] ERROR: MINIMAX_API_KEY missing")
            return False, "MINIMAX_API_KEY not set in environment", None

        # 1. Select Samples
        # We need at least 1 sample for 'source' (Identity)
        # We try to use a 2nd sample for 'prompt' (Style) if available
        set_dir = self.voice_samples_dir / set_id
        
        # Get all samples from metadata or disk
        samples_info = []
        metadata_path = set_dir / 'metadata.json'
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                data = json.load(f)
                samples_info = data.get('samples', [])
        
        # Sort by duration (prefer longer for source)
        # If no metadata, fall back to listing files
        if not samples_info:
            wav_files = list(set_dir.glob('*.wav'))
            if not wav_files:
                return False, "No samples found in set", None
            # Basic dummy info structure
            samples_info = [{'filename': f.name, 'duration_seconds': 10} for f in wav_files]

        # Sort samples by duration descending (longest first for source)
        try:
            sorted_samples = sorted(samples_info, key=lambda x: x.get('duration_seconds', 0), reverse=True)
        except:
             sorted_samples = samples_info # Fallback

        if not sorted_samples:
             return False, "No valid samples found", None

        source_sample = sorted_samples[0]
        prompt_sample = sorted_samples[1] if len(sorted_samples) > 1 else sorted_samples[0]
        
        source_path = set_dir / source_sample['filename']
        prompt_path = set_dir / prompt_sample['filename']
        
        print(f"[{datetime.now()}] Selected Source: {source_sample['filename']}, Prompt: {prompt_sample['filename']}")

        if not source_path.exists():
             return False, f"Source sample file missing: {source_sample['filename']}", None
        
        if not prompt_path.exists():
             # Fallback to source if prompt missing
             prompt_path = source_path


        try:
            # 2. Upload Files
            upload_url = "https://api.minimax.io/v1/files/upload"
            headers = {"Authorization": f"Bearer {api_key}"}

            # Upload Source Audio
            # with open(source_path, "rb") as f:
            #     files = {"file": (source_sample['filename'], f)}
            #     data = {"purpose": "voice_clone"}
            #     response = requests.post(upload_url, headers=headers, data=data, files=files, timeout=60)
            #     if response.status_code != 200:
            #         print(f"[{datetime.now()}] Upload Error (Source): {response.text}")
            #     response.raise_for_status()
            #     source_file_id = response.json()["file"]["file_id"]
            #     print(f"[{datetime.now()}] Uploaded Source ID: {source_file_id}")

            # Upload Prompt Audio (Example Audio)
            # with open(prompt_path, "rb") as f:
            #     files = {"file": (prompt_sample['filename'], f)}
            #     data = {"purpose": "prompt_audio"}
            #     response = requests.post(upload_url, headers=headers, data=data, files=files, timeout=60)
            #     if response.status_code != 200:
            #         print(f"[{datetime.now()}] Upload Error (Prompt): {response.text}")
            #     response.raise_for_status()
            #     prompt_file_id = response.json()["file"]["file_id"]
            #     print(f"[{datetime.now()}] Uploaded Prompt ID: {prompt_file_id}")

            # 3. Clone / Generate Voice
            clone_url = "https://api.minimax.io/v1/voice_clone"
            
            # Using set_id as unique voice_id per set
            # Minimax requires voice_id to be a string
            voice_id = f"voice_{set_id}" 
            
            payload = {
                "file_id": 363048810168600,
                "voice_id": voice_id,
                "clone_prompt": {
                    "prompt_audio": 363049912885641,
                    "prompt_text": "Please replicate the tone and style of this audio." # Generic prompt text since we don't have transcript
                },
                "text": text,
                "model": "speech-01-turbo" # Using turbo as requested/implied for speed/cost, or could use speech-01-hd
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            print(f"[{datetime.now()}] Sending voice_clone request...")
            response = requests.post(clone_url, headers=headers, json=payload, timeout=120)
            
            print(response.status_code,"-----------------")
            if response.status_code != 200:
                print(f"[{datetime.now()}] Generation Error: {response.text}")
                return False, f"Minimax API Error: {response.text}", None
                
            # Check Content-Type to ensure we got audio, not a JSON error
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                try:
                    error_data = response.json()
                    print(error_data)
                    base_resp = error_data.get('base_resp', {})
                    status_msg = base_resp.get('status_msg', 'Unknown Error')
                    print(base_resp,"+++++++++++++++")
                    print(f"[{datetime.now()}] Generation Failed (API Logic): {status_msg}")
                    return False, f"Minimax Error: {status_msg}", None
                except:
                     print(f"[{datetime.now()}] Generation Failed: {response.text}")
                     return False, f"Minimax Response Error: {response.text}", None
            
            print(f"[{datetime.now()}] Generation successful")
                
            # 4. Save Audio
            # Minimax response content type is audio/mpeg usually
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"minimax_{timestamp}.mp3" 
            
            # Save in generated subfolder
            output_dir = set_dir / 'generated'
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / output_filename
            
            with open(output_path, "wb") as f:
                f.write(response.content)

            # Create Record
            record = GenerationRecord(
                audio_filename=output_filename,
                text=text,
                set_id=set_id,
                generated_at=datetime.now().isoformat(),
                reference_clips_used=2,
                config={
                    'provider': 'minimax', 
                    'model': 'speech-01-turbo',
                    'source_file_id': source_file_id,
                    'prompt_file_id': prompt_file_id
                },
                source=source,
                model=model
            )
            
            self._log_generation(set_id, record)
            return True, "Minimax generation successful", record

        except Exception as e:
            print(f"[{datetime.now()}] EXCEPTION: {str(e)}")
            return False, f"Minimax Error: {str(e)}", None
    
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
            'config': record.config,
            'source': record.source,
            'model': record.model
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
            
        all_records = [GenerationRecord(**{**g, 'source': g.get('source', 'legacy'), 'model': g.get('model', 'coqui-xtts-v2')}) for g in log_data.get('generations', [])]
        
        # Filter for web sources only (exclude legacy/agent)
        return [r for r in all_records if r.source == 'web']
