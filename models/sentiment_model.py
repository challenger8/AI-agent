"""
Sentiment Analysis Model
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

@dataclass
class SentimentAnalysis:
    """Sentiment analysis result model"""
    
    id: Optional[int] = None
    text: str = ""
    language: str = "fa"  # Persian by default
    
    # Sentiment results
    label: str = ""  # positive, negative, neutral
    score: float = 0.0  # confidence score 0-1
    
    # Additional sentiment metrics
    polarity: Optional[float] = None  # -1 to 1 (negative to positive)
    subjectivity: Optional[float] = None  # 0 to 1 (objective to subjective)
    
    # Metadata
    model_name: str = ""
    model_version: str = ""
    processed_at: Optional[datetime] = None
    
    # Optional linking to other entities
    deal_id: Optional[int] = None
    activity_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert sentiment analysis to dictionary"""
        return {
            'id': self.id,
            'text': self.text,
            'language': self.language,
            'label': self.label,
            'score': self.score,
            'polarity': self.polarity,
            'subjectivity': self.subjectivity,
            'model_name': self.model_name,
            'model_version': self.model_version,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'deal_id': self.deal_id,
            'activity_id': self.activity_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SentimentAnalysis':
        """Create sentiment analysis from dictionary"""
        sentiment = cls()
        for key, value in data.items():
            if hasattr(sentiment, key):
                # Handle datetime fields
                if key == 'processed_at' and value:
                    if isinstance(value, str):
                        value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                
                setattr(sentiment, key, value)
        return sentiment
    
    def is_positive(self) -> bool:
        """Check if sentiment is positive"""
        return self.label.lower() == 'positive' or self.score > 0.6
    
    def is_negative(self) -> bool:
        """Check if sentiment is negative"""
        return self.label.lower() == 'negative' or self.score < -0.6
    
    def is_neutral(self) -> bool:
        """Check if sentiment is neutral"""
        return not self.is_positive() and not self.is_negative()