"""
Repository pattern implementation for data access
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from .deal_model import Deal, DealActivity
from .sentiment_model import SentimentAnalysis

class DealRepository:
    """Repository for Deal operations"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_all_deals(self) -> List[Deal]:
        """Get all deals"""
        try:
            query = """
            SELECT * FROM deals 
            ORDER BY created_at DESC
            """
            results = self.db.execute_query(query)
            return [Deal.from_dict(dict(row)) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching deals: {e}")
            return []
    
    def get_deal_by_id(self, deal_id: int) -> Optional[Deal]:
        """Get deal by ID"""
        try:
            query = "SELECT * FROM deals WHERE id = ?"
            results = self.db.execute_query(query, (deal_id,))
            if results:
                return Deal.from_dict(dict(results[0]))
            return None
        except Exception as e:
            self.logger.error(f"Error fetching deal {deal_id}: {e}")
            return None
    
    def create_deal(self, deal: Deal) -> Optional[int]:
        """Create new deal"""
        try:
            query = """
            INSERT INTO deals (title, description, amount, currency, status, stage, 
                             probability, expected_close_date, client_name, client_company, 
                             client_email, source, priority, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            now = datetime.now()
            params = (
                deal.title, deal.description, deal.amount, deal.currency,
                deal.status, deal.stage, deal.probability, deal.expected_close_date,
                deal.client_name, deal.client_company, deal.client_email,
                deal.source, deal.priority, deal.tags, now, now
            )
            return self.db.execute_insert(query, params)
        except Exception as e:
            self.logger.error(f"Error creating deal: {e}")
            return None
    
    def update_deal(self, deal: Deal) -> bool:
        """Update existing deal"""
        try:
            query = """
            UPDATE deals SET title=?, description=?, amount=?, currency=?, status=?, 
                           stage=?, probability=?, expected_close_date=?, client_name=?, 
                           client_company=?, client_email=?, source=?, priority=?, 
                           tags=?, updated_at=?
            WHERE id=?
            """
            params = (
                deal.title, deal.description, deal.amount, deal.currency,
                deal.status, deal.stage, deal.probability, deal.expected_close_date,
                deal.client_name, deal.client_company, deal.client_email,
                deal.source, deal.priority, deal.tags, datetime.now(), deal.id
            )
            return self.db.execute_update(query, params) > 0
        except Exception as e:
            self.logger.error(f"Error updating deal {deal.id}: {e}")
            return False
    
    def get_deals_by_status(self, status: str) -> List[Deal]:
        """Get deals by status"""
        try:
            query = "SELECT * FROM deals WHERE status = ? ORDER BY created_at DESC"
            results = self.db.execute_query(query, (status,))
            return [Deal.from_dict(dict(row)) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching deals by status {status}: {e}")
            return []

class DealActivityRepository:
    """Repository for Deal Activity operations"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_activities_by_deal(self, deal_id: int) -> List[DealActivity]:
        """Get all activities for a deal"""
        try:
            query = """
            SELECT * FROM deal_activities 
            WHERE deal_id = ? 
            ORDER BY created_at DESC
            """
            results = self.db.execute_query(query, (deal_id,))
            return [DealActivity.from_dict(dict(row)) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching activities for deal {deal_id}: {e}")
            return []
    
    def create_activity(self, activity: DealActivity) -> Optional[int]:
        """Create new activity"""
        try:
            query = """
            INSERT INTO deal_activities (deal_id, activity_type, title, description, 
                                       created_at, created_by, duration_minutes, outcome, 
                                       next_action, sentiment_score, sentiment_label)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                activity.deal_id, activity.activity_type, activity.title,
                activity.description, activity.created_at or datetime.now(),
                activity.created_by, activity.duration_minutes, activity.outcome,
                activity.next_action, activity.sentiment_score, activity.sentiment_label
            )
            return self.db.execute_insert(query, params)
        except Exception as e:
            self.logger.error(f"Error creating activity: {e}")
            return None
    
    def update_activity_sentiment(self, activity_id: int, sentiment_score: float, sentiment_label: str) -> bool:
        """Update activity with sentiment analysis results"""
        try:
            query = """
            UPDATE deal_activities 
            SET sentiment_score = ?, sentiment_label = ?
            WHERE id = ?
            """
            return self.db.execute_update(query, (sentiment_score, sentiment_label, activity_id)) > 0
        except Exception as e:
            self.logger.error(f"Error updating activity sentiment {activity_id}: {e}")
            return False

class SentimentRepository:
    """Repository for Sentiment Analysis operations"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def save_sentiment(self, sentiment: SentimentAnalysis) -> Optional[int]:
        """Save sentiment analysis result"""
        try:
            query = """
            INSERT INTO sentiment_analysis (text, language, label, score, polarity, 
                                          subjectivity, model_name, model_version, 
                                          processed_at, deal_id, activity_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = (
                sentiment.text, sentiment.language, sentiment.label, sentiment.score,
                sentiment.polarity, sentiment.subjectivity, sentiment.model_name,
                sentiment.model_version, sentiment.processed_at or datetime.now(),
                sentiment.deal_id, sentiment.activity_id
            )
            return self.db.execute_insert(query, params)
        except Exception as e:
            self.logger.error(f"Error saving sentiment: {e}")
            return None
    
    def get_sentiment_by_activity(self, activity_id: int) -> Optional[SentimentAnalysis]:
        """Get sentiment analysis for an activity"""
        try:
            df = self.db.execute_query("SELECT * FROM sentiment_analysis WHERE activity_id = ?", (activity_id,))
            if not df.empty:
                return SentimentAnalysis.from_dict(df.iloc[0].to_dict())
            return None
        except Exception as e:
            self.logger.error(f"Error fetching sentiment for activity {activity_id}: {e}")
            return None

class RepositoryManager:
    """Manager for all repositories"""
    
    def __init__(self, db_manager):
        self.deals = DealRepository(db_manager)
        self.activities = DealActivityRepository(db_manager)
        self.sentiment = SentimentRepository(db_manager)

def create_repositories(db_manager) -> RepositoryManager:
    """Factory function to create repository manager"""
    return RepositoryManager(db_manager)