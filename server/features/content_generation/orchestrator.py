"""
Content Generation Orchestrator
Coordinates the full pipeline from config to video
"""

import os
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from .services import (
    SceneGeneratorService, 
    ScriptGeneratorService, 
    TTSService,
    FrameCaptureService,
    VideoAssemblerService
)
from .models import GenerationProgress, GenerationResult


class ContentGenerationOrchestrator:
    """Main orchestrator for content generation pipeline"""
    
    def __init__(self, documents_dir: str, voice_service_url: str):
        """Initialize orchestrator with all services"""
        self.documents_dir = Path(documents_dir)
        self.voice_service_url = voice_service_url
        
        # Initialize services
        self.scene_generator = SceneGeneratorService()
        self.script_generator = ScriptGeneratorService()
        self.tts_service = TTSService(documents_dir, voice_service_url)
        self.frame_capture = FrameCaptureService(documents_dir)
        self.video_assembler = VideoAssemblerService(documents_dir)
        
        # Progress tracking
        self.progress_callbacks: Dict[str, Callable] = {}
    
    def set_progress_callback(self, session_id: str, callback: Callable):
        """Set progress callback for a session"""
        self.progress_callbacks[session_id] = callback
    
    async def _update_progress(
        self, 
        session_id: str, 
        phase: str, 
        status: str,
        progress: int,
        message: str = ""
    ):
        """Update progress for a session"""
        if session_id in self.progress_callbacks:
            await self.progress_callbacks[session_id]({
                "session_id": session_id,
                "current_phase": phase,
                "status": status,
                "progress_percentage": progress,
                "message": message
            })
    
    async def generate_content(
        self,
        session_id: str,
        config_path: str,
        voice_set_id: str,
        tts_model: str = 'coqui-xtts-v2',
        options: Optional[Dict[str, Any]] = None
    ) -> GenerationResult:
        """
        Full pipeline orchestration
        
        Args:
            session_id: Session ID for tracking
            config_path: Path to config.json
            voice_set_id: Voice sample set ID for TTS
            tts_model: TTS model to use
            options: Additional options (teacher_style, pace, etc.)
            
        Returns:
            GenerationResult object
        """
        # Use provided session_id
        session_dir = self.documents_dir / 'content_generation' / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Check if we should skip generation phases
            skip_generation = options.get('skip_generation', False) if options else False
            
            if not skip_generation:
                # Phase 1: Scene Generation
                await self._update_progress(
                    session_id, 
                    "scene_generation", 
                    "processing", 
                    10,
                    "Analyzing config and generating scene structure..."
                )
                
                scene_structure = await self.scene_generator.generate(config_path)
                
                # Save scene structure
                scene_structure_path = session_dir / 'scene_structure.json'
                self.scene_generator.save_scene_structure(scene_structure, str(scene_structure_path))
                
                await self._update_progress(
                    session_id,
                    "scene_generation",
                    "completed",
                    20,
                    f"Generated {len(scene_structure.scenes)} scenes"
                )
                
                # Phase 2: Script Generation (parallel)
                await self._update_progress(
                    session_id,
                    "script_generation",
                    "processing",
                    30,
                    "Generating teacher scripts for all scenes..."
                )
                
                scripts = await self.script_generator.generate_all(
                    scene_structure.scenes,
                    scene_structure.question_type
                )
                
                # Save scripts
                import json
                scripts_data = [
                    {
                        'scene_id': s.scene_id,
                        'script': s.script,
                        'word_count': s.word_count,
                        'estimated_duration': s.estimated_duration
                    }
                    for s in scripts
                ]
                scripts_path = session_dir / 'scripts.json'
                with open(scripts_path, 'w') as f:
                    json.dump(scripts_data, f, indent=2)
                
                await self._update_progress(
                    session_id,
                    "script_generation",
                    "completed",
                    50,
                    f"Generated scripts for {len(scripts)} scenes"
                )
                
                # Phase 3: Audio Generation (parallel)
                await self._update_progress(
                    session_id,
                    "audio_generation",
                    "processing",
                    60,
                    "Converting scripts to audio..."
                )
                
                audio_files = await self.tts_service.generate_all(
                    scripts,
                    voice_set_id,
                    session_id,
                    tts_model
                )
                
                await self._update_progress(
                    session_id,
                    "audio_generation",
                    "completed",
                    80,
                    f"Generated {len(audio_files)} audio files"
                )
            else:
                # Load existing data
                await self._update_progress(
                    session_id,
                    "loading",
                    "processing",
                    10,
                    "Loading existing session data..."
                )
                
                # Load scene structure
                from .models import SceneStructure, Scene, SceneType, ActionDetails, SceneTiming
                import json
                
                scene_structure_path = session_dir / 'scene_structure.json'
                if not scene_structure_path.exists():
                    raise FileNotFoundError(f"Scene structure not found for session {session_id}")
                
                with open(scene_structure_path, 'r') as f:
                    data = json.load(f)
                    scenes = []
                    for s_data in data['scenes']:
                        action = None
                        if s_data.get('action'):
                            action = ActionDetails(**s_data['action'])
                        
                        timing = None
                        if s_data.get('timing'):
                            timing = SceneTiming(**s_data['timing'])
                            
                        scenes.append(Scene(
                            id=s_data['id'],
                            type=SceneType(s_data['type']),
                            duration=s_data['duration'],
                            focus=s_data['focus'],
                            teaching_strategy=s_data['teaching_strategy'],
                            action=action,
                            timing=timing
                        ))
                    
                    scene_structure = SceneStructure(
                        question_type=data['question_type'],
                        total_duration=data['total_duration'],
                        scenes=scenes
                    )
                
                scripts_path = session_dir / 'scripts.json'
                audio_durations = {}
                if scripts_path.exists():
                    try:
                        with open(scripts_path, 'r') as f:
                            sd = json.load(f)
                            audio_durations = {s['scene_id']: s['estimated_duration'] for s in sd}
                    except:
                        pass
                
                # Load audio files
                from .models import AudioFile
                audio_dir = session_dir / 'audio'
                audio_files = []
                for scene in scenes:
                    audio_path = audio_dir / f"{scene.id}.mp3"
                    if audio_path.exists():
                        # Use duration from scripts or fallback to scene duration
                        duration = audio_durations.get(scene.id, scene.duration)
                        audio_files.append(AudioFile(
                            scene_id=scene.id,
                            file_path=str(audio_path),
                            duration=duration
                        ))
                
                await self._update_progress(
                    session_id,
                    "loading",
                    "completed",
                    60,
                    "Loaded existing session data"
                )
            
            # Phase 4: Frame Capture
            await self._update_progress(
                session_id,
                "frame_capture",
                "processing",
                70,
                "Capturing frames during automation..."
            )
            
            # Get URL from options or use default
            url = options.get('url') if options else None
            # URL is optional if using existing browser
            
            frame_sequences = await self.frame_capture.capture_automation_with_frames(
                scene_structure=scene_structure,
                session_id=session_id,
                url=url,
                use_existing_browser=options.get('use_existing_browser', True),
                cdp_url=options.get('cdp_url', 'http://localhost:9222')
            )
            
            await self._update_progress(
                session_id,
                "frame_capture",
                "completed",
                80,
                f"Captured frames for {len(frame_sequences)} scenes"
            )
            
            # Phase 5: Video Assembly
            await self._update_progress(
                session_id,
                "video_assembly",
                "processing",
                85,
                "Assembling video with FFmpeg..."
            )
            
            video_path = self.video_assembler.assemble_video(
                scene_structure=scene_structure,
                frame_sequences=frame_sequences,
                audio_files=audio_files,
                session_id=session_id
            )
            
            await self._update_progress(
                session_id,
                "video_assembly",
                "completed",
                95,
                "Video assembly complete"
            )
            
            # Complete result
            result = GenerationResult(
                session_id=session_id,
                status="completed",
                video_path=video_path,
                duration=scene_structure.total_duration,
                scenes_count=len(scene_structure.scenes),
                artifacts={
                    'scene_structure': str(scene_structure_path),
                    'scripts': str(scripts_path),
                    'audio_dir': str(session_dir / 'audio'),
                    'frames_dir': str(session_dir / 'frames'),
                    'video_path': video_path
                }
            )
            
            await self._update_progress(
                session_id,
                "completed",
                "completed",
                100,
                "Content generation completed successfully!"
            )
            
            return result
            
        except Exception as e:
            await self._update_progress(
                session_id,
                "error",
                "failed",
                0,
                f"Error: {str(e)}"
            )
            raise e
