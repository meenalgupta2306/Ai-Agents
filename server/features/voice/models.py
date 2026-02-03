"""Voice feature models"""
from pydantic import BaseModel, Field
from typing import Optional


class VoiceSampleUploadRequest(BaseModel):
    """Request model for voice sample upload"""
    user_id: str = Field(..., description="User ID")


class VoiceSampleUploadResponse(BaseModel):
    """Response model for voice sample upload"""
    status: str
    message: str
    duration_seconds: Optional[float] = None
    sample_path: Optional[str] = None


class VoiceSampleCheckResponse(BaseModel):
    """Response model for checking if user has voice sample"""
    has_sample: bool
    message: str
    metadata: Optional[dict] = None


class GenerateSpeechRequest(BaseModel):
    """Request model for speech generation"""
    text: str = Field(..., description="Text to convert to speech", min_length=1, max_length=5000)
    user_id: str = Field(..., description="User ID")


class GenerateSpeechResponse(BaseModel):
    """Response model for speech generation"""
    status: str
    message: str
    audio_filename: Optional[str] = None
    audio_url: Optional[str] = None
    text: Optional[str] = None
