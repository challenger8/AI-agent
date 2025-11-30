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
    
    # NOW THESE BECOME ONE-LINERS:
    
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
    
    # ONE-LINERS!
    def get_activities_by_deal(self, deal_id: str) -> List[DealActivity]:
        return self.get_by_field("deal_id", deal_id, order_by="register_date DESC")
    
    def get_activity_by_id(self, activity_id: str) -> Optional[DealActivity]:
        return self.get_by_id(activity_id)


class CRMAgentRepository:
    """Repository for CRM Agent operations - updated for crm_agents table"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_all_agents(self) -> List[CRMAgent]:
        """Get all CRM agents"""
        try:
            query = 'SELECT * FROM crm_agents ORDER BY owner_name'
            results = self.db.execute_query(query)
            return [self._map_db_to_agent(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching agents: {e}")
            return []
    
    def get_agent_by_id(self, agent_id: str) -> Optional[CRMAgent]:
        """Get agent by ID"""
        try:
            query = 'SELECT * FROM crm_agents WHERE id = %s'
            results = self.db.execute_query(query, (agent_id,))
            if results:
                return self._map_db_to_agent(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error fetching agent {agent_id}: {e}")
            return None
    
    def get_agents_by_role(self, role: str) -> List[CRMAgent]:
        """Get agents by role"""
        try:
            query = 'SELECT * FROM crm_agents WHERE role = %s ORDER BY owner_name'
            results = self.db.execute_query(query, (role,))
            return [self._map_db_to_agent(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching agents by role {role}: {e}")
            return []
    
    def create_agent(self, agent: CRMAgent) -> Optional[str]:
        """Create new agent"""
        try:
            query = """
            INSERT INTO crm_agents (id, group_owner, owner_name, admin_id, 
                               role, phone, mobile_phone, personal_id, group_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                agent.id, agent.groupowner, agent.ownername, agent.adminid,
                agent.role, agent.phone, agent.mobilephone, agent.personalid,
                agent.groupphone
            )
            self.db.execute_insert(query, params)
            return agent.id
        except Exception as e:
            self.logger.error(f"Error creating agent: {e}")
            return None
    
    def get_agent_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get performance metrics for an agent"""
        try:
            performance = {}
            
            # Get deals by contact (since no owner_id in deals table)
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
    
    def _map_db_to_agent(self, row: Dict[str, Any]) -> CRMAgent:
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


class SentimentRepository:
    """Repository for Sentiment Analysis operations"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def save_sentiment(self, sentiment: SentimentAnalysis) -> Optional[int]:
        """Save sentiment analysis result"""
        try:
            query = """
            INSERT INTO sentiment_analysis (id, text, language, label, score, polarity, 
                                        subjectivity, model_name, model_version, 
                                        processed_at, deal_id, activity_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                sentiment.id,sentiment.text, sentiment.language, sentiment.label, sentiment.score,
                sentiment.polarity, sentiment.subjectivity, sentiment.model_name,
                sentiment.model_version, sentiment.processed_at or datetime.now(),
                sentiment.deal_id, sentiment.activity_id
            )
            return self.db.execute_insert(query, params)
        except Exception as e:
            self.logger.error(f"Error saving sentiment: {e}")
            return None
    
    def get_sentiment_by_activity(self, activity_id: str) -> Optional[SentimentAnalysis]:
        """Get sentiment analysis for an activity"""
        try:
            query = 'SELECT * FROM sentiment_analysis WHERE activity_id = %s'
            results = self.db.execute_query(query, (activity_id,))
            if results:
                return SentimentAnalysis.from_dict(dict(results[0]))
            return None
        except Exception as e:
            self.logger.error(f"Error fetching sentiment for activity {activity_id}: {e}")
            return None
    
    def get_sentiments_by_deal(self, deal_id: str) -> List[SentimentAnalysis]:
        """Get all sentiment analyses for a deal"""
        try:
            query = 'SELECT * FROM sentiment_analysis WHERE deal_id = %s ORDER BY processed_at DESC'
            results = self.db.execute_query(query, (deal_id,))
            return [SentimentAnalysis.from_dict(dict(row)) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching sentiments for deal {deal_id}: {e}")
            return []
    
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