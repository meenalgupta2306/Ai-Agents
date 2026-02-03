"""Voice Cloning Feature - Models for sample sets and generation history"""
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class VoiceSample:
    """Represents a single voice sample file"""
    filename: str
    uploaded_at: str
    duration_seconds: float
    file_size_bytes: int


@dataclass
class SampleSet:
    """Represents a set of voice samples"""
    set_id: str
    set_type: str  # 'profile' or 'demo'
    user_id: Optional[str]
    samples: List[VoiceSample]
    created_at: str
    total_samples: int


@dataclass
class GenerationRecord:
    """Represents a generated audio record"""
    audio_filename: str
    text: str
    set_id: str
    generated_at: str
    reference_clips_used: int
    config: dict
    source: str = 'web'


@dataclass
class GenerateSpeechRequest:
    """Request model for speech generation"""
    text: str
    set_id: str
    temperature: float = 0.85
    speed: float = 1.0
    repetition_penalty: float = 2.0


@dataclass
class UploadSampleRequest:
    """Request model for uploading voice samples"""
    set_id: Optional[str]  # If None, create new set
    user_id: Optional[str]  # For profile sets
