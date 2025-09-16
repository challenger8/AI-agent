"""
Deal and Deal Activity Models
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from decimal import Decimal

@dataclass
class Deal:
    """Deal model representing a business deal"""
    
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    amount: Optional[Decimal] = None
    currency: str = "USD"
    status: str = "active"  # active, closed_won, closed_lost, pending
    stage: str = "qualification"  # qualification, proposal, negotiation, closing
    probability: Optional[float] = None
    expected_close_date: Optional[datetime] = None
    actual_close_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Client information
    client_name: str = ""
    client_company: str = ""
    client_email: str = ""
    
    # Additional metadata
    source: str = ""  # website, referral, cold_call, etc.
    priority: str = "medium"  # low, medium, high
    tags: Optional[str] = None  # JSON string of tags
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert deal to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'amount': float(self.amount) if self.amount else None,
            'currency': self.currency,
            'status': self.status,
            'stage': self.stage,
            'probability': self.probability,
            'expected_close_date': self.expected_close_date.isoformat() if self.expected_close_date else None,
            'actual_close_date': self.actual_close_date.isoformat() if self.actual_close_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'client_name': self.client_name,
            'client_company': self.client_company,
            'client_email': self.client_email,
            'source': self.source,
            'priority': self.priority,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Deal':
        """Create deal from dictionary"""
        deal = cls()
        for key, value in data.items():
            if hasattr(deal, key):
                # Handle datetime fields
                if key in ['expected_close_date', 'actual_close_date', 'created_at', 'updated_at'] and value:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                # Handle decimal fields
                elif key == 'amount' and value is not None:
                    value = Decimal(str(value))
                
                setattr(deal, key, value)
        return deal

@dataclass
class DealActivity:
    """Deal activity model representing actions/notes on deals"""
    
    id: Optional[int] = None
    deal_id: int = 0
    activity_type: str = "note"  # note, call, email, meeting, task
    title: str = ""
    description: str = ""
    created_at: Optional[datetime] = None
    created_by: str = ""
    
    # Activity specific fields
    duration_minutes: Optional[int] = None  # for calls, meetings
    outcome: str = ""  # positive, negative, neutral
    next_action: str = ""
    
    # Sentiment analysis will be added to this
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary"""
        return {
            'id': self.id,
            'deal_id': self.deal_id,
            'activity_type': self.activity_type,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by,
            'duration_minutes': self.duration_minutes,
            'outcome': self.outcome,
            'next_action': self.next_action,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DealActivity':
        """Create activity from dictionary"""
        activity = cls()
        for key, value in data.items():
            if hasattr(activity, key):
                # Handle datetime fields
                if key == 'created_at' and value:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                
                setattr(activity, key, value)
        return activity