"""OAuth data models"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class ConnectedAccount:
    platform: str
    type: str  # 'personal' or 'organization'
    name: str
    accountId: str
    accessToken: str
    email: Optional[str] = None
    vanityName: Optional[str] = None
    logoUrl: Optional[str] = None
    picture: Optional[str] = None
