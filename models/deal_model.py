"""
Deal, Deal Activity, and CRM Agent Models
Updated to match actual CSV data structure
REFACTORED: Using SerializableMixin for DRY principle
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
import json

from models.base_model import SerializableMixin


@dataclass
class Deal(SerializableMixin):
    """Deal model representing a business deal from Deals.csv"""
    
    # Primary fields (using UUID strings)
    Id: Optional[str] = None
    Title: str = ""
    Description: str = ""
    RegisterTime: Optional[datetime] = None
    Price: Optional[Decimal] = None
    Status: str = ""
    
    # Pipeline and stage information
    PipelineStageId: Optional[str] = None
    PipelineId: Optional[str] = None
    
    # Time tracking fields
    ChangeToWonTime: Optional[datetime] = None
    ChangeToLossTime: Optional[datetime] = None
    LastTrackingTime: Optional[datetime] = None
    NextTrackingTime: Optional[datetime] = None
    ExpectedCloseDate: Optional[datetime] = None
    LastActivityUpdateTime: Optional[datetime] = None
    LastUpdateTime: Optional[datetime] = None
    
    # Deal metrics
    Probability: Optional[float] = None
    
    # Relationships (UUID references)
    ContactId: Optional[str] = None
    OwnerId: Optional[str] = None
    CreatorId: Optional[str] = None
    LabelId: Optional[str] = None
    LostReasonId: Optional[str] = None
    
    # Additional fields
    Pin: Optional[bool] = None
    LostReasonNote: str = ""
    LostReasonOther: str = ""
    Feedback: str = ""
    
    # Status flags
    IsIdle: Optional[bool] = None
    IsRotten: Optional[bool] = None
    IsRottenInStage: Optional[bool] = None
    
    # JSON fields (stored as strings in DB)
    Fields: Optional[str] = None
    Items: Optional[str] = None
    
    # Contact info
    MobilePhone: str = ""
    
    # Custom helper methods (keep these)
    def get_fields_as_dict(self) -> Dict[str, Any]:
        """Parse Fields JSON string to dictionary"""
        if self.Fields:
            try:
                return json.loads(self.Fields)
            except:
                return {}
        return {}
    
    def get_items_as_list(self) -> List[Dict[str, Any]]:
        """Parse Items JSON string to list"""
        if self.Items:
            try:
                return json.loads(self.Items)
            except:
                return []
        return []


@dataclass
class DealActivity(SerializableMixin):
    """Deal activity model representing actions/notes on deals from activities.csv"""
    
    # Primary fields
    id: Optional[str] = None
    title: str = ""
    note: str = ""
    resultnote: str = ""
    activitytypeid: Optional[str] = None
    
    # Status flags
    isprivate: Optional[bool] = None
    isdone: Optional[bool] = None
    ispinned: Optional[bool] = None
    
    # Date fields
    duedate: Optional[datetime] = None
    finishdate: Optional[datetime] = None
    donedate: Optional[datetime] = None
    registerdate: Optional[datetime] = None
    lastupdatetime: Optional[datetime] = None
    
    # Relationships (UUID references)
    dealid: Optional[str] = None
    creatorid: Optional[str] = None
    ownerid: Optional[str] = None
    updaterid: Optional[str] = None
    
    # Sentiment analysis fields
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    
    # Custom helper method (keep this)
    def get_combined_text(self) -> str:
        """Get combined text for sentiment analysis"""
        texts = []
        if self.title:
            texts.append(self.title)
        if self.note:
            texts.append(self.note)
        if self.resultnote:
            texts.append(self.resultnote)
        return " ".join(texts)


@dataclass
class CRMAgent(SerializableMixin):
    """CRM Agent/User model from crmteam.csv"""
    
    id: Optional[str] = None
    groupowner: str = ""
    ownername: str = ""
    adminid: Optional[str] = None
    role: str = ""
    phone: str = ""
    mobilephone: str = ""
    personalid: str = ""
    groupphone: str = ""
    
    # Custom helper methods (keep these)
    def get_display_name(self) -> str:
        """Get display name for the agent"""
        if self.ownername:
            return self.ownername
        elif self.groupowner:
            return self.groupowner
        else:
            return self.id or "Unknown"
    
    def get_contact_number(self) -> str:
        """Get primary contact number"""
        return self.mobilephone or self.phone or self.groupphone or ""