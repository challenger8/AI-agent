"""
Deal, Deal Activity, and CRM Agent Models
Updated to match actual CSV data structure
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
import json

@dataclass
class Deal:
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
    OwnerId: Optional[str] = None  # References crmteam.id
    CreatorId: Optional[str] = None  # References crmteam.id
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
    Fields: Optional[str] = None  # Custom fields JSON
    Items: Optional[str] = None  # Deal items JSON
    
    # Contact info
    MobilePhone: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert deal to dictionary"""
        return {
            'Id': self.Id,
            'Title': self.Title,
            'Description': self.Description,
            'RegisterTime': self.RegisterTime.isoformat() if self.RegisterTime else None,
            'Price': float(self.Price) if self.Price else None,
            'Status': self.Status,
            'PipelineStageId': self.PipelineStageId,
            'PipelineId': self.PipelineId,
            'ChangeToWonTime': self.ChangeToWonTime.isoformat() if self.ChangeToWonTime else None,
            'ChangeToLossTime': self.ChangeToLossTime.isoformat() if self.ChangeToLossTime else None,
            'LastTrackingTime': self.LastTrackingTime.isoformat() if self.LastTrackingTime else None,
            'NextTrackingTime': self.NextTrackingTime.isoformat() if self.NextTrackingTime else None,
            'ExpectedCloseDate': self.ExpectedCloseDate.isoformat() if self.ExpectedCloseDate else None,
            'LastActivityUpdateTime': self.LastActivityUpdateTime.isoformat() if self.LastActivityUpdateTime else None,
            'LastUpdateTime': self.LastUpdateTime.isoformat() if self.LastUpdateTime else None,
            'Probability': self.Probability,
            'ContactId': self.ContactId,
            'OwnerId': self.OwnerId,
            'CreatorId': self.CreatorId,
            'LabelId': self.LabelId,
            'LostReasonId': self.LostReasonId,
            'Pin': self.Pin,
            'LostReasonNote': self.LostReasonNote,
            'LostReasonOther': self.LostReasonOther,
            'Feedback': self.Feedback,
            'IsIdle': self.IsIdle,
            'IsRotten': self.IsRotten,
            'IsRottenInStage': self.IsRottenInStage,
            'Fields': self.Fields,
            'Items': self.Items,
            'MobilePhone': self.MobilePhone
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Deal':
        """Create deal from dictionary"""
        deal = cls()
        for key, value in data.items():
            if hasattr(deal, key):
                # Handle datetime fields
                datetime_fields = [
                    'RegisterTime', 'ChangeToWonTime', 'ChangeToLossTime',
                    'LastTrackingTime', 'NextTrackingTime', 'ExpectedCloseDate',
                    'LastActivityUpdateTime', 'LastUpdateTime'
                ]
                if key in datetime_fields and value:
                    if isinstance(value, str):
                        try:
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            value = None
                # Handle decimal fields
                elif key == 'Price' and value is not None:
                    value = Decimal(str(value))
                # Handle boolean fields
                elif key in ['Pin', 'IsIdle', 'IsRotten', 'IsRottenInStage'] and value is not None:
                    if isinstance(value, str):
                        value = value.lower() in ['true', '1', 'yes']
                
                setattr(deal, key, value)
        return deal
    
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
class DealActivity:
    """Deal activity model representing actions/notes on deals from activities.csv"""
    
    # Primary fields
    id: Optional[str] = None  # UUID
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
    dealid: Optional[str] = None  # References Deal.Id
    creatorid: Optional[str] = None  # References crmteam.id
    ownerid: Optional[str] = None  # References crmteam.id
    updaterid: Optional[str] = None  # References crmteam.id
    
    # Sentiment analysis fields (to be added by analysis)
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'note': self.note,
            'resultnote': self.resultnote,
            'activitytypeid': self.activitytypeid,
            'isprivate': self.isprivate,
            'isdone': self.isdone,
            'ispinned': self.ispinned,
            'duedate': self.duedate.isoformat() if self.duedate else None,
            'finishdate': self.finishdate.isoformat() if self.finishdate else None,
            'donedate': self.donedate.isoformat() if self.donedate else None,
            'registerdate': self.registerdate.isoformat() if self.registerdate else None,
            'lastupdatetime': self.lastupdatetime.isoformat() if self.lastupdatetime else None,
            'dealid': self.dealid,
            'creatorid': self.creatorid,
            'ownerid': self.ownerid,
            'updaterid': self.updaterid,
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
                datetime_fields = [
                    'duedate', 'finishdate', 'donedate', 
                    'registerdate', 'lastupdatetime'
                ]
                if key in datetime_fields and value:
                    if isinstance(value, str):
                        try:
                            value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                        except:
                            value = None
                # Handle boolean fields
                elif key in ['isprivate', 'isdone', 'ispinned'] and value is not None:
                    if isinstance(value, str):
                        value = value.lower() in ['true', '1', 'yes']
                
                setattr(activity, key, value)
        return activity
    
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
class CRMAgent:
    """CRM Agent/User model from crmteam.csv"""
    
    id: Optional[str] = None  # UUID
    groupowner: str = ""
    ownername: str = ""
    adminid: Optional[str] = None
    role: str = ""
    phone: str = ""
    mobilephone: str = ""
    personalid: str = ""
    groupphone: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary"""
        return {
            'id': self.id,
            'groupowner': self.groupowner,
            'ownername': self.ownername,
            'adminid': self.adminid,
            'role': self.role,
            'phone': self.phone,
            'mobilephone': self.mobilephone,
            'personalid': self.personalid,
            'groupphone': self.groupphone
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CRMAgent':
        """Create agent from dictionary"""
        agent = cls()
        for key, value in data.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        return agent
    
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