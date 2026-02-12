"""
Video Assembler Service
Uses FFmpeg to create videos from frames and audio
"""

import os
import subprocess
from pathlib import Path
from typing import List
from ..models import SceneStructure, Scene, SceneType, FrameSequence, AudioFile


class VideoAssemblerService:
    """Assembles video from frames and audio using FFmpeg"""
    
    def __init__(self, documents_dir: str):
        """Initialize video assembler"""
        self.documents_dir = Path(documents_dir)
    
    def assemble_video(
        self,
        scene_structure: SceneStructure,
        frame_sequences: List[FrameSequence],
        audio_files: List[AudioFile],
        session_id: str
    ) -> str:
        """
        Assemble final video from all scenes
        
        Args:
            scene_structure: Scene structure
            frame_sequences: List of frame sequences per scene
            audio_files: List of audio files per scene
            session_id: Content generation session ID
            
        Returns:
            Path to final video file
        """
        session_dir = self.documents_dir / 'content_generation' / session_id
        video_dir = session_dir / 'videos'
        video_dir.mkdir(parents=True, exist_ok=True)
        
        # Create video for each scene
        scene_videos = []
        
        for scene, frame_seq, audio in zip(scene_structure.scenes, frame_sequences, audio_files):
            video_path = self._create_scene_video(scene, frame_seq, audio, video_dir)
            scene_videos.append(video_path)
        
        # Concatenate all scene videos
        final_video = self._concatenate_videos(scene_videos, video_dir)
        
        return str(final_video)
    
    def _create_scene_video(
        self,
        scene: Scene,
        frame_seq: FrameSequence,
        audio: AudioFile,
        output_dir: Path
    ) -> Path:
        """Create video for a single scene"""
        
        output_path = output_dir / f'{scene.id}.mp4'
        frame_dir = Path(frame_seq.frame_dir)
        
        if scene.type == SceneType.INTRO or scene.type == SceneType.CONCLUSION:
            # Static scene - single frame with audio
            frame_path = frame_dir / 'frame_000.png'
            
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', str(frame_path),
                '-i', audio.file_path,
                '-vf', "scale='trunc(iw/2)*2:trunc(ih/2)*2'",
                '-c:v', 'libx264',
                '-tune', 'stillimage',
                '-c:a', 'aac',
                '-b:a', '256k',
                '-ar', '44100',
                '-ac', '2',
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                '-pix_fmt', 'yuv420p',
                '-shortest',
                '-t', str(audio.duration),
                str(output_path)
            ]
            
        else:
            # Action scene - combine pre/drag/post frames with audio
            # Create a complex filter to handle different frame durations
            
            pre_frame = frame_dir / 'pre_action.png'
            post_frame = frame_dir / 'post_action.png'
            drag_pattern = frame_dir / 'drag_%03d.png'
            
            # Create concat file for frames
            concat_file = frame_dir / 'concat.txt'
            
            with open(concat_file, 'w') as f:
                # Pre-action frame (hold for pre_action duration)
                if scene.timing:
                    f.write(f"file '{pre_frame}'\n")
                    f.write(f"duration {scene.timing.pre_action}\n")
                    
                    # Drag frames (shown at 10 FPS)
                    num_drag_frames = frame_seq.frame_count - 2  # Exclude pre and post
                    for i in range(num_drag_frames):
                        drag_frame = frame_dir / f'drag_{i:03d}.png'
                        f.write(f"file '{drag_frame}'\n")
                        f.write(f"duration 0.1\n")  # 10 FPS = 0.1s per frame
                    
                    # Post-action frame (hold for post_action duration)
                    f.write(f"file '{post_frame}'\n")
                    f.write(f"duration {scene.timing.post_action}\n")
                    
                    # Repeat last frame to ensure proper duration
                    f.write(f"file '{post_frame}'\n")
            
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-i', audio.file_path,
                '-vf', "scale='trunc(iw/2)*2:trunc(ih/2)*2'",
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-b:a', '256k',
                '-ar', '44100',
                '-ac', '2',
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',
                '-pix_fmt', 'yuv420p',
                '-shortest',
                str(output_path)
            ]
        
        # Run FFmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed for {scene.id}: {result.stderr}")
        
        return output_path
    
    def _concatenate_videos(self, video_paths: List[Path], output_dir: Path) -> Path:
        """Concatenate all scene videos into final video"""
        
        final_output = output_dir / 'final_video.mp4'
        concat_file = output_dir / 'video_concat.txt'
        
        # Create concat file
        with open(concat_file, 'w') as f:
            for video_path in video_paths:
                f.write(f"file '{video_path}'\n")
        
        # Concatenate videos
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(final_output)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg concatenation failed: {result.stderr}")
        
        return final_output
