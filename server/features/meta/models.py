"""Meta Marketing API data models"""
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class MetaAdAccount:
    """Represents a Meta Ad Account"""
    id: str
    name: str
    account_id: str
    currency: Optional[str] = None


@dataclass
class MetaCampaign:
    """Represents a Meta Campaign"""
    id: str
    name: str
    objective: str
    status: str
    account_id: str
    created_time: Optional[str] = None
    updated_time: Optional[str] = None


@dataclass
class MetaAdSet:
    """Represents a Meta Ad Set"""
    id: str
    name: str
    campaign_id: str
    status: str
    billing_event: Optional[str] = None
    optimization_goal: Optional[str] = None
    bid_amount: Optional[int] = None


@dataclass
class MetaAd:
    """Represents a Meta Ad"""
    id: str
    name: str
    adset_id: str
    status: str
    creative: Optional[dict] = None
