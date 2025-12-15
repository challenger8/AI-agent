"""
Corrected Repository pattern implementation for actual database schema
Updated to match your snake_case column names
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging
import json

from .deal_model import Deal, DealActivity, CRMAgent
from .sentiment_model import SentimentAnalysis
from .base_repository import BaseRepository

class DealRepository(BaseRepository[Deal]):
    """Repository for Deal operations"""
    
    @property
    def table_name(self) -> str:
        return "deals"
    
    def _map_row_to_model(self, row: dict) -> Deal:
        """Convert DB row to Deal model"""
        return Deal(
            Id=row.get('id', ''),
            Title=row.get('title', ''),
            Description=row.get('description', ''),
            RegisterTime=row.get('register_time'),
            Price=row.get('price', 0),
            Status=row.get('status', ''),
            # ... rest of mapping
        )
    
    # NOW THESE BECOME ONE-LINERS using generic create!
    def create_deal(self, deal: Deal) -> Optional[str]:
        """Create new deal using generic create method"""
        # Set default timestamps if not provided
        if not deal.RegisterTime:
            deal.RegisterTime = datetime.now()
        if not deal.LastUpdateTime:
            deal.LastUpdateTime = datetime.now()
        return self.create_generic(deal)
    def get_all_deals(self) -> List[Deal]:
        return self.get_all(order_by="register_time DESC")
    
    def get_deal_by_id(self, deal_id: str) -> Optional[Deal]:
        return self.get_by_id(deal_id)
    
    def get_deals_by_status(self, status: str) -> List[Deal]:
        return self.get_by_field("status", status)
    
    # Only CUSTOM queries need implementation:
    def get_deals_in_date_range(self, start: datetime, end: datetime) -> List[Deal]:
        query = """
            SELECT * FROM deals 
            WHERE register_time BETWEEN %s AND %s
            ORDER BY register_time DESC
        """
        return self._execute_query_list(
            query, 
            (start, end),
            error_context="fetching deals in date range"
        )

class DealActivityRepository(BaseRepository[DealActivity]):
    """Repository for Activity operations"""
    
    @property
    def table_name(self) -> str:
        return "deal_activities"
    
    def _map_row_to_model(self, row: dict) -> DealActivity:
        return DealActivity(
            id=row.get('id', ''),
            title=row.get('title', ''),
            # ... rest of mapping
        )
    def create_activity(self, activity: DealActivity) -> Optional[str]:
        """Create new activity using generic create method"""
        # Set default timestamps if not provided
        if not activity.registerdate:
            activity.registerdate = datetime.now()
        if not activity.lastupdatetime:
            activity.lastupdatetime = datetime.now()
        return self.create_generic(activity)
    def update_activity_sentiment(self, activity_id: str, sentiment_score: float, sentiment_label: str) -> bool:
        """Update activity with sentiment analysis results"""
        try:
            query = """
            UPDATE deal_activities 
            SET sentiment_score = %s, sentiment_label = %s, last_update_time = %s
            WHERE id = %s
            """
            from datetime import datetime
            rows_affected = self.db.execute_update(
                query, 
                (sentiment_score, sentiment_label, datetime.now(), activity_id)
            )
            return rows_affected > 0
        except Exception as e:
            self.logger.error(f"Error updating activity sentiment {activity_id}: {e}")
            return False
    # ONE-LINERS!
    
    def get_activities_by_deal(self, deal_id: str) -> List[DealActivity]:
        return self.get_by_field("deal_id", deal_id, order_by="register_date DESC")
    
    def get_activity_by_id(self, activity_id: str) -> Optional[DealActivity]:
        return self.get_by_id(activity_id)


class CRMAgentRepository(BaseRepository[CRMAgent]):
    """Repository for CRM Agent operations - updated for crm_agents table"""
    
    @property
    def table_name(self) -> str:
        return "crm_agents"
    
    def _map_row_to_model(self, row: Dict[str, Any]) -> CRMAgent:
        """Map database row to CRMAgent object"""
        return CRMAgent(
            id=row.get('id', ''),
            groupowner=row.get('group_owner', ''),
            ownername=row.get('owner_name', ''),
            adminid=row.get('admin_id', ''),
            role=row.get('role', ''),
            phone=row.get('phone', ''),
            mobilephone=row.get('mobile_phone', ''),
            personalid=row.get('personal_id', ''),
            groupphone=row.get('group_phone', '')
        )
    
    # =========================================
    # NOW THESE BECOME ONE-LINERS!
    # =========================================
    
    def get_all_agents(self) -> List[CRMAgent]:
        """Get all CRM agents"""
        return self.get_all(order_by="owner_name")
    
    def get_agent_by_id(self, agent_id: str) -> Optional[CRMAgent]:
        """Get agent by ID"""
        return self.get_by_id(agent_id)
    
    def get_agents_by_role(self, role: str) -> List[CRMAgent]:
        """Get agents by role"""
        return self.get_by_field("role", role, order_by="owner_name")
    
    # =========================================
    # Only CUSTOM methods need implementation
    # =========================================
    
    def create_agent(self, agent: CRMAgent) -> Optional[str]:
        """Create new agent using generic create method"""
        return self.create_generic(agent)
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for an agent (custom query)"""
        try:
            performance = {}
            
            # Get deals by contact
            deals_query = 'SELECT COUNT(*) as total, status FROM deals WHERE contact_id = %s GROUP BY status'
            deals_results = self.db.execute_query(deals_query, (agent_id,))
            
            performance['deals_by_status'] = {
                row['status']: row['total'] for row in deals_results
            }
            performance['total_deals'] = sum(performance['deals_by_status'].values())
            
            # Get total deal value
            value_query = 'SELECT SUM(price) as total_value FROM deals WHERE contact_id = %s AND status = %s'
            won_value = self.db.execute_query(value_query, (agent_id, 'Won'))
            performance['won_deals_value'] = won_value[0]['total_value'] if won_value else 0
            
            # Get activities count
            activities_query = 'SELECT COUNT(*) as total FROM deal_activities WHERE owner_id = %s'
            activities_result = self.db.execute_query(activities_query, (agent_id,))
            performance['total_activities'] = activities_result[0]['total'] if activities_result else 0
            
            return performance
        except Exception as e:
            self.logger.error(f"Error getting agent performance {agent_id}: {e}")
            return {}

class SentimentRepository(BaseRepository[SentimentAnalysis]):
    """
    Repository for Sentiment Analysis operations.

    REFACTORED: Now inherits from BaseRepository for LSP compliance.
    """

    @property
    def table_name(self) -> str:
        return "sentiment_analysis"

    def _map_row_to_model(self, row: dict) -> SentimentAnalysis:
        """Convert database row to SentimentAnalysis model"""
        return SentimentAnalysis.from_dict(dict(row))

    def save_sentiment(self, sentiment: SentimentAnalysis) -> Optional[int]:
        """Save sentiment analysis result using generic create method"""
        # Set default timestamp if not provided
        if not sentiment.processed_at:
            sentiment.processed_at = datetime.now()
        return self.create_generic(sentiment)

    def get_sentiment_by_activity(self, activity_id: str) -> Optional[SentimentAnalysis]:
        """Get sentiment analysis for an activity"""
        return self._execute_query_single(
            'SELECT * FROM sentiment_analysis WHERE activity_id = %s',
            (activity_id,),
            error_context=f"fetching sentiment for activity {activity_id}"
        )

    def get_sentiments_by_deal(self, deal_id: str) -> List[SentimentAnalysis]:
        """Get all sentiment analyses for a deal"""
        return self._execute_query_list(
            'SELECT * FROM sentiment_analysis WHERE deal_id = %s ORDER BY processed_at DESC',
            (deal_id,),
            error_context=f"fetching sentiments for deal {deal_id}"
        )

    def get_sentiment_statistics(self) -> Dict[str, Any]:
        """Get sentiment analysis statistics"""
        try:
            stats = {}

            # Overall sentiment distribution
            dist_query = 'SELECT label, COUNT(*) as count FROM sentiment_analysis GROUP BY label'
            dist_results = self.db.execute_query(dist_query)
            stats['sentiment_distribution'] = {row['label']: row['count'] for row in dist_results}

            # Average scores
            avg_query = 'SELECT AVG(score) as avg_score, AVG(polarity) as avg_polarity FROM sentiment_analysis'
            avg_result = self.db.execute_query(avg_query)
            if avg_result:
                stats['average_score'] = avg_result[0]['avg_score']
                stats['average_polarity'] = avg_result[0]['avg_polarity']

            return stats
        except Exception as e:
            self.logger.error(f"Error getting sentiment statistics: {e}")
            return {}


class RepositoryManager:
    """Manager for all repositories"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.deals = DealRepository(db_manager)
        self.activities = DealActivityRepository(db_manager)
        self.agents = CRMAgentRepository(db_manager)
        self.sentiment = SentimentRepository(db_manager)
    
    # ADD THESE TWO METHODS:
    def __enter__(self):
        """Enter context manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager"""
        # Don't close database connection here - it's managed elsewhere
        return False
    
    def get_deal_with_details(self, deal_id: str) -> Dict[str, Any]:
        """Get deal with all related information"""
        try:
            deal = self.deals.get_deal_by_id(deal_id)
            if not deal:
                return None
            
            result = {
                'deal': deal.to_dict(),
                'activities': [],
                'owner': None,
                'creator': None
            }
            
            # Get activities
            activities = self.activities.get_activities_by_deal(deal_id)
            result['activities'] = [activity.to_dict() for activity in activities]
            
            # Note: Owner and Creator info would need to be implemented based on your schema
            
            return result
        except Exception as e:
            logging.error(f"Error getting deal with details {deal_id}: {e}")
            return None


def create_repositories(db_manager) -> RepositoryManager:
    """Factory function to create repository manager"""
    return RepositoryManager(db_manager)