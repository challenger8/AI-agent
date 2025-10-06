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

class DealRepository:
    """Repository for Deal operations - corrected for snake_case columns"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_all_deals(self) -> List[Deal]:
        """Get all deals"""
        try:
            query = """
            SELECT * FROM deals 
            ORDER BY register_time DESC
            """
            results = self.db.execute_query(query)
            return [self._map_db_to_deal(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching deals: {e}")
            return []
    
    def get_deal_by_id(self, deal_id: str) -> Optional[Deal]:
        """Get deal by ID"""
        try:
            query = 'SELECT * FROM deals WHERE id = %s'
            results = self.db.execute_query(query, (deal_id,))
            if results:
                return self._map_db_to_deal(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error fetching deal {deal_id}: {e}")
            return None
    
    def create_deal(self, deal: Deal) -> Optional[str]:
        """Create new deal"""
        try:
            query = """
            INSERT INTO deals (id, title, description, register_time, price, 
                             status, pipeline_stage_id, pipeline_id, change_to_won_time, 
                             change_to_loss_time, last_tracking_time, next_tracking_time, 
                             probability, contact_id, label_id, lost_reason_id, 
                             lost_reason_note, lost_reason_other, is_idle, is_rotten, 
                             is_rotten_in_stage, fields, last_update_time, items, mobile_phone)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            now = datetime.now()
            params = (
                deal.Id, deal.Title, deal.Description, deal.RegisterTime or now,
                deal.Price, deal.Status, deal.PipelineStageId, deal.PipelineId,
                deal.ChangeToWonTime, deal.ChangeToLossTime, deal.LastTrackingTime,
                deal.NextTrackingTime, deal.Probability, deal.ContactId, 
                deal.LabelId, deal.LostReasonId, deal.LostReasonNote, 
                deal.LostReasonOther, deal.IsIdle, deal.IsRotten, 
                deal.IsRottenInStage, deal.Fields, now, deal.Items, deal.MobilePhone
            )
            self.db.execute_insert(query, params)
            return deal.Id
        except Exception as e:
            self.logger.error(f"Error creating deal: {e}")
            return None
    
    def update_deal(self, deal: Deal) -> bool:
        """Update existing deal"""
        try:
            query = """
            UPDATE deals SET 
                title=%s, description=%s, price=%s, status=%s, 
                pipeline_stage_id=%s, pipeline_id=%s, change_to_won_time=%s, 
                change_to_loss_time=%s, last_tracking_time=%s, next_tracking_time=%s, 
                probability=%s, contact_id=%s, label_id=%s, lost_reason_id=%s, 
                lost_reason_note=%s, lost_reason_other=%s, is_idle=%s, is_rotten=%s, 
                is_rotten_in_stage=%s, fields=%s, last_update_time=%s, 
                items=%s, mobile_phone=%s
            WHERE id=%s
            """
            params = (
                deal.Title, deal.Description, deal.Price, deal.Status,
                deal.PipelineStageId, deal.PipelineId, deal.ChangeToWonTime,
                deal.ChangeToLossTime, deal.LastTrackingTime, deal.NextTrackingTime,
                deal.Probability, deal.ContactId, deal.LabelId, deal.LostReasonId,
                deal.LostReasonNote, deal.LostReasonOther, deal.IsIdle, deal.IsRotten,
                deal.IsRottenInStage, deal.Fields, datetime.now(),
                deal.Items, deal.MobilePhone, deal.Id
            )
            return self.db.execute_update(query, params) > 0
        except Exception as e:
            self.logger.error(f"Error updating deal {deal.Id}: {e}")
            return False
    
    def get_deals_by_status(self, status: str) -> List[Deal]:
        """Get deals by status"""
        try:
            query = 'SELECT * FROM deals WHERE status = %s ORDER BY register_time DESC'
            results = self.db.execute_query(query, (status,))
            return [self._map_db_to_deal(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching deals by status {status}: {e}")
            return []
    
    def get_deals_by_owner(self, owner_id: str) -> List[Deal]:
        """Get deals by owner ID"""
        try:
            # Note: owner_id column doesn't exist in your schema, using contact_id instead
            query = 'SELECT * FROM deals WHERE contact_id = %s ORDER BY register_time DESC'
            results = self.db.execute_query(query, (owner_id,))
            return [self._map_db_to_deal(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching deals by owner {owner_id}: {e}")
            return []
    
    def get_deals_statistics(self) -> Dict[str, Any]:
        """Get deals statistics"""
        try:
            stats = {}
            
            # Total deals count
            count_query = 'SELECT COUNT(*) as total FROM deals'
            result = self.db.execute_query(count_query)
            stats['total_deals'] = result[0]['total'] if result else 0
            
            # Deals by status
            status_query = 'SELECT status, COUNT(*) as count FROM deals GROUP BY status'
            results = self.db.execute_query(status_query)
            stats['by_status'] = {row['status']: row['count'] for row in results}
            
            # Total value
            value_query = 'SELECT SUM(price) as total_value FROM deals WHERE status = %s'
            won_result = self.db.execute_query(value_query, ('Won',))
            stats['total_won_value'] = won_result[0]['total_value'] if won_result else 0
            
            return stats
        except Exception as e:
            self.logger.error(f"Error getting deals statistics: {e}")
            return {}
    
    def _map_db_to_deal(self, row: Dict[str, Any]) -> Deal:
        """Map database row to Deal object"""
        return Deal(
            Id=row.get('id', ''),
            Title=row.get('title', ''),
            Description=row.get('description', ''),
            RegisterTime=row.get('register_time'),
            Price=row.get('price'),
            Status=row.get('status', ''),
            PipelineStageId=row.get('pipeline_stage_id', ''),
            PipelineId=row.get('pipeline_id', ''),
            ChangeToWonTime=row.get('change_to_won_time'),
            ChangeToLossTime=row.get('change_to_loss_time'),
            LastTrackingTime=row.get('last_tracking_time'),
            NextTrackingTime=row.get('next_tracking_time'),
            ExpectedCloseDate=None,  # Not in your schema
            LastActivityUpdateTime=row.get('last_activity_update_time'),
            LastUpdateTime=row.get('last_update_time'),
            Probability=row.get('probability'),
            ContactId=row.get('contact_id', ''),
            OwnerId='',  # Not in your schema
            CreatorId='',  # Not in your schema
            LabelId=row.get('label_id', ''),
            LostReasonId=row.get('lost_reason_id', ''),
            Pin=False,  # Not in your schema
            LostReasonNote=row.get('lost_reason_note', ''),
            LostReasonOther=row.get('lost_reason_other', ''),
            Feedback='',  # Not in your schema
            IsIdle=row.get('is_idle', False),
            IsRotten=row.get('is_rotten', False),
            IsRottenInStage=row.get('is_rotten_in_stage', False),
            Fields=row.get('fields', ''),
            Items=row.get('items', ''),
            MobilePhone=row.get('mobile_phone', '')
        )


class DealActivityRepository:
    """Repository for Deal Activity operations - corrected for actual database columns"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
    
    def get_activities_by_deal(self, deal_id: str) -> List[DealActivity]:
        """Get all activities for a deal"""
        try:
            query = """
            SELECT * FROM deal_activities 
            WHERE deal_id = %s 
            ORDER BY register_date DESC
            """
            results = self.db.execute_query(query, (deal_id,))
            return [self._map_db_to_activity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching activities for deal {deal_id}: {e}")
            return []
    
    def get_activity_by_id(self, activity_id: str) -> Optional[DealActivity]:
        """Get activity by ID"""
        try:
            query = 'SELECT * FROM deal_activities WHERE id = %s'
            results = self.db.execute_query(query, (activity_id,))
            if results:
                return self._map_db_to_activity(results[0])
            return None
        except Exception as e:
            self.logger.error(f"Error fetching activity {activity_id}: {e}")
            return None
    
    def create_activity(self, activity: DealActivity) -> Optional[str]:
        """Create new activity - updated for actual database columns"""
        try:
            query = """
            INSERT INTO deal_activities (id, title, note, result_note, 
                                        activity_type_id, is_done, 
                                        due_date, finish_date, done_date, 
                                        register_date, last_update_time, 
                                        deal_id, case_id, creator_id, owner_id, updater_id,
                                        contacts, sentiment_score, sentiment_label)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                activity.id, activity.title, activity.note, activity.resultnote,
                activity.activitytypeid, activity.isdone,
                activity.duedate, activity.finishdate, activity.donedate, 
                activity.registerdate or datetime.now(),
                activity.lastupdatetime or datetime.now(), activity.dealid,
                '', activity.creatorid, activity.ownerid, activity.updaterid,
                '', activity.sentiment_score, activity.sentiment_label
            )
            self.db.execute_insert(query, params)
            return activity.id
        except Exception as e:
            self.logger.error(f"Error creating activity: {e}")
            return None
    
    def update_activity_sentiment(self, activity_id: str, sentiment_score: float, sentiment_label: str) -> bool:
        """Update activity with sentiment analysis results"""
        try:
            query = """
            UPDATE deal_activities 
            SET sentiment_score = %s, sentiment_label = %s
            WHERE id = %s
            """
            return self.db.execute_update(query, (sentiment_score, sentiment_label, activity_id)) > 0
        except Exception as e:
            self.logger.error(f"Error updating activity sentiment {activity_id}: {e}")
            return False
    
    def get_activities_by_owner(self, owner_id: str) -> List[DealActivity]:
        """Get activities by owner"""
        try:
            query = """
            SELECT * FROM deal_activities 
            WHERE owner_id = %s 
            ORDER BY register_date DESC
            """
            results = self.db.execute_query(query, (owner_id,))
            return [self._map_db_to_activity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching activities by owner {owner_id}: {e}")
            return []
    
    def get_pending_activities(self) -> List[DealActivity]:
        """Get pending (not done) activities"""
        try:
            query = """
            SELECT * FROM deal_activities 
            WHERE is_done = false OR is_done IS NULL
            ORDER BY due_date ASC NULLS LAST
            """
            results = self.db.execute_query(query)
            return [self._map_db_to_activity(row) for row in results]
        except Exception as e:
            self.logger.error(f"Error fetching pending activities: {e}")
            return []
    
    def _map_db_to_activity(self, row: Dict[str, Any]) -> DealActivity:
        """Map database row to DealActivity object"""
        return DealActivity(
            id=row.get('id', ''),
            title=row.get('title', ''),
            note=row.get('note', ''),
            resultnote=row.get('result_note', ''),
            activitytypeid=row.get('activity_type_id', ''),
            isprivate=False,  # Not in your database
            isdone=row.get('is_done', False),
            ispinned=False,  # Not in your database
            duedate=row.get('due_date'),
            finishdate=row.get('finish_date'),
            donedate=row.get('done_date'),
            registerdate=row.get('register_date'),
            lastupdatetime=row.get('last_update_time'),
            dealid=row.get('deal_id', ''),
            creatorid=row.get('creator_id', ''),
            ownerid=row.get('owner_id', ''),
            updaterid=row.get('updater_id', ''),
            sentiment_score=row.get('sentiment_score'),
            sentiment_label=row.get('sentiment_label')
        )


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