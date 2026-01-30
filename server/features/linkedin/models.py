"""LinkedIn data models"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class LinkedInProfile:
    urn: str
    id: str
    name: str
    firstName: Optional[str] = None
    lastName: Optional[str] = None

@dataclass
class LinkedInOrganization:
    urn: str
    id: str
    name: str
    vanityName: Optional[str] = None
    logoUrl: Optional[str] = None
