"""
TTS Service for Content Generation
Wraps existing voice cloning service for parallel audio generation
"""

import os
import asyncio
from typing import List
from pathlib import Path
from ..models import SceneScript, AudioFile
from ...voice_cloning.service import VoiceCloningService


class TTSService:
    """Text-to-Speech service for content generation"""
    
    def __init__(self, documents_dir: str, voice_service_url: str):
        """Initialize TTS service"""
        self.voice_service = VoiceCloningService(documents_dir, voice_service_url)
        self.documents_dir = Path(documents_dir)
    
    async def generate_audio(
        self, 
        script: SceneScript, 
        set_id: str,
        session_id: str,
        model: str = 'coqui-xtts-v2'
    ) -> AudioFile:
        """
        Generate audio for a single script
        
        Args:
            script: SceneScript object
            set_id: Voice sample set ID to use
            session_id: Content generation session ID
            model: TTS model to use
            
        Returns:
            AudioFile object
        """
        # Generate speech using voice cloning service
        success, message, record = self.voice_service.generate_speech(
            set_id=set_id,
            text=script.script,
            temperature=0.85,
            speed=1.0,
            repetition_penalty=2.0,
            source='content_generation',
            model=model
        )
        
        if not success or not record:
            raise Exception(f"TTS generation failed: {message}")
        
        # Get audio file path
        set_dir = self.documents_dir / 'voice_samples' / set_id / 'generated'
        audio_path = set_dir / record.audio_filename
        
        # Copy to content generation session folder
        session_audio_dir = self.documents_dir / 'content_generation' / session_id / 'audio'
        session_audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Rename to scene_id for clarity
        output_filename = f"{script.scene_id}.mp3"
        output_path = session_audio_dir / output_filename
        
        # Copy file
        import shutil
        shutil.copy(audio_path, output_path)
        
        # Get actual audio duration (for now, use estimated)
        # TODO: Use librosa or similar to get actual duration
        duration = script.estimated_duration
        
        return AudioFile(
            scene_id=script.scene_id,
            file_path=str(output_path),
            duration=duration
        )
    
    async def generate_all(
        self,
        scripts: List[SceneScript],
        set_id: str,
        session_id: str,
        model: str = 'coqui-xtts-v2'
    ) -> List[AudioFile]:
        """
        Generate audio for all scripts in parallel
        
        Args:
            scripts: List of SceneScript objects
            set_id: Voice sample set ID
            session_id: Content generation session ID
            model: TTS model to use
            
        Returns:
            List of AudioFile objects
        """
        # Create tasks for parallel execution
        tasks = [
            self.generate_audio(script, set_id, session_id, model)
            for script in scripts
        ]
        
        # Execute all tasks in parallel
        audio_files = await asyncio.gather(*tasks)
        
        return audio_files
