#!/usr/bin/env python3
"""
Rerun Video Assembly for a specific session
"""

import os
import json
import sys
from pathlib import Path
from typing import List

# Fix imports to allow running from root
sys.path.append(os.path.abspath('server'))

from features.content_generation.services.video_assembler import VideoAssemblerService
from features.content_generation.models import (
    SceneStructure, Scene, SceneType, SceneTiming, 
    ActionDetails, FrameSequence, AudioFile
)

def rerun_assembly(session_id: str):
    """Rerun video assembly for a session"""
    print(f"🎬 Rerunning Video Assembly for session: {session_id}")
    
    documents_dir = os.path.abspath('server/documents')
    session_dir = Path(documents_dir) / 'content_generation' / session_id
    
    if not session_dir.exists():
        print(f"❌ Session directory not found: {session_dir}")
        return

    # 1. Load Scene Structure
    structure_path = session_dir / 'scene_structure.json'
    with open(structure_path, 'r') as f:
        structure_data = json.load(f)
    
    scenes = []
    for s in structure_data['scenes']:
        timing = SceneTiming(**s['timing']) if 'timing' in s else None
        action = ActionDetails(**s['action']) if 'action' in s else None
        
        scene = Scene(
            id=s['id'],
            type=SceneType(s['type']),
            duration=s['duration'],
            focus=s['focus'],
            teaching_strategy=s['teaching_strategy'],
            action=action,
            timing=timing
        )
        scenes.append(scene)
    
    scene_structure = SceneStructure(
        question_type=structure_data['question_type'],
        total_duration=structure_data['total_duration'],
        scenes=scenes
    )

    # 2. Reconstruct Frame Sequences
    frame_sequences = []
    frames_dir = session_dir / 'frames'
    for scene in scenes:
        scene_frame_dir = frames_dir / scene.id
        frame_count = len(list(scene_frame_dir.glob('*.png')))
        
        seq = FrameSequence(
            scene_id=scene.id,
            frame_dir=str(scene_frame_dir),
            frame_count=frame_count,
            duration=scene.duration,
            fps=10
        )
        frame_sequences.append(seq)

    # 3. Load Audio durations from scripts.json
    scripts_path = session_dir / 'scripts.json'
    with open(scripts_path, 'r') as f:
        scripts_data = json.load(f)
    
    audio_durations = {s['scene_id']: s['estimated_duration'] for s in scripts_data}
    
    audio_files = []
    audio_dir = session_dir / 'audio'
    for scene in scenes:
        audio_path = audio_dir / f"{scene.id}.mp3"
        audio = AudioFile(
            scene_id=scene.id,
            file_path=str(audio_path),
            duration=audio_durations.get(scene.id, scene.duration)
        )
        audio_files.append(audio)

    # 4. Run Assembler
    assembler = VideoAssemblerService(documents_dir)
    try:
        final_video = assembler.assemble_video(
            scene_structure,
            frame_sequences,
            audio_files,
            session_id
        )
        print(f"\n✅ SUCCESS! Final video created at: {final_video}")
    except Exception as e:
        print(f"\n❌ FAILED: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        rerun_assembly(sys.argv[1])
    else:
        # Default to the session reported by user if no arg provided
        rerun_assembly("session_9d885155f1fb")
