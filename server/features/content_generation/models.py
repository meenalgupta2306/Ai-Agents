"""
Data models for content generation
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Literal
from enum import Enum


class SceneType(str, Enum):
    """Types of scenes in the video"""
    INTRO = "intro"
    ACTION = "action"
    CONCLUSION = "conclusion"


@dataclass
class ActionDetails:
    """Details for an action scene"""
    type: str  # "drag"
    item_id: str
    zone_id: str


@dataclass
class SceneTiming:
    """Timing details for a scene"""
    pre_action: float = 0  # seconds before action
    action: float = 0  # seconds during action
    post_action: float = 0  # seconds after action


@dataclass
class Scene:
    """Represents a single scene in the video"""
    id: str
    type: SceneType
    duration: float
    focus: str
    teaching_strategy: str
    action: Optional[ActionDetails] = None
    timing: Optional[SceneTiming] = None


@dataclass
class SceneStructure:
    """Complete scene structure for a video"""
    question_type: str
    total_duration: float
    scenes: List[Scene]


@dataclass
class SceneScript:
    """Script for a single scene"""
    scene_id: str
    script: str
    word_count: int
    estimated_duration: float


@dataclass
class AudioFile:
    """Audio file metadata"""
    scene_id: str
    file_path: str
    duration: float


@dataclass
class FrameSequence:
    """Frame sequence for a scene"""
    scene_id: str
    frame_dir: str
    frame_count: int
    duration: float
    fps: int = 10


@dataclass
class GenerationProgress:
    """Progress tracking for content generation"""
    session_id: str
    status: Literal["started", "processing", "completed", "failed"]
    current_phase: str
    progress_percentage: int
    phases: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class GenerationResult:
    """Final result of content generation"""
    session_id: str
    status: str
    video_path: Optional[str]
    duration: float
    scenes_count: int
    artifacts: Dict[str, str] = field(default_factory=dict)
