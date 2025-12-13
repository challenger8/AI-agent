"""
services/deal_service.py
------------------------
Deal management and analysis service.
REFACTORED: Uses centralized utilities for DRY compliance.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from services.base_service import BaseService
from config.settings import AnalysisSettings
from utils.exceptions import ServiceError
from utils.deal_status_detector import DealStatusDetector
from utils.activity_utils import ActivityUtils
from utils.date_utils import DateUtils

class DealService(BaseService):
    """Service for deal management and basic analysis"""
    
    def get_deal(self, deal_id: int) -> Optional[Dict[str, Any]]:
        """
        Get deal by ID
        
        Args:
            deal_id: Deal identifier
            
        Returns:
            Deal data or None if not found
        """
        try:
            with self.repositories as uow:
                deal = uow.deals.get_deal_by_id(deal_id)
                return deal.to_dict() if deal else None
        except Exception as e:
            self.logger.error(f"Error getting deal {deal_id}: {e}")
            raise ServiceError(f"Failed to get deal: {e}")
    
    def get_deals_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        Get deals filtered by status
        
        Args:
            status: Deal status to filter by
            
        Returns:
            List of deals
        """
        try:
            with self.repositories as uow:
                deals = uow.deals.get_deals_by_status(status)
                return [deal.to_dict() for deal in deals]
        except Exception as e:
            self.logger.error(f"Error getting deals by status {status}: {e}")
            raise ServiceError(f"Failed to get deals: {e}")
    
    def get_all_deals(self) -> List[Dict[str, Any]]:
        """
        Get all deals
        
        Returns:
            List of all deals
        """
        try:
            with self.repositories as uow:
                deals = uow.deals.get_all_deals()
                return [deal.to_dict() for deal in deals]
        except Exception as e:
            self.logger.error(f"Error getting all deals: {e}")
            raise ServiceError(f"Failed to get deals: {e}")
    
    def get_deals_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get deals summary statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Summary statistics
        """
        try:
            deals = self.get_all_deals()
            
            if not deals:
                return {"error": "No deals found"}
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Basic counts
            total_deals = len(deals)
            active_deals = len([d for d in deals if d.get('deal_status') == 'در حال پیگیری'])
            closed_deals = len([d for d in deals if d.get('deal_status') == 'بسته شده'])
            
            # Recent deals
            recent_deals = [
                d for d in deals 
                if d.get('created_date') and 
                datetime.fromisoformat(d['created_date'].replace('Z', '+00:00')) >= cutoff_date
            ]
            
            # Value analysis
            total_value = sum(d.get('deal_value', 0) for d in deals if d.get('deal_value'))
            avg_deal_value = total_value / len(deals) if deals else 0
            
            return {
                "period_days": days,
                "total_deals": total_deals,
                "active_deals": active_deals,
                "closed_deals": closed_deals,
                "recent_deals": len(recent_deals),
                "total_value": total_value,
                "average_deal_value": round(avg_deal_value, 2),
                "summary": {
                    "conversion_rate": round((closed_deals / total_deals) * 100, 1) if total_deals > 0 else 0,
                    "activity_rate": round((len(recent_deals) / total_deals) * 100, 1) if total_deals > 0 else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating deals summary: {e}")
            raise ServiceError(f"Failed to generate summary: {e}")
    def get_deal_with_activities(self, deal_id: str) -> Optional[Dict[str, Any]]:
        """
        Get deal with all its activities (one-stop data access)
        
        This is the recommended way to fetch deal data for analysis.
        Ensures consistent data access pattern across services.
        
        Args:
            deal_id: Deal identifier
            
        Returns:
            Dictionary with 'deal' and 'activities' keys, or None if deal not found
            
        Example:
            data = deal_service.get_deal_with_activities('123')
            if data:
                deal = data['deal']
                activities = data['activities']
        """
        try:
            # Get deal
            deal = self.get_deal(deal_id)
            if not deal:
                return None
            
            # Get activities
            with self.repositories as uow:
                activities = uow.activities.get_activities_by_deal(deal_id)
            
            return {
                'deal': deal,
                'activities': activities,
                'activity_count': len(activities)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting deal with activities {deal_id}: {e}")
            raise ServiceError(f"Failed to get deal data: {e}")
    def get_deal_timeline(self, deal_id: int) -> Dict[str, Any]:
        """
        Get deal timeline with key milestones
        
        Args:
            deal_id: Deal identifier
            
        Returns:
            Deal timeline data
        """
        try:
            deal = self.get_deal(deal_id)
            if not deal:
                return {"error": f"Deal {deal_id} not found"}
            
            with self.repositories as uow:
                activities = uow.activities.get_activities_by_deal(deal_id)
                
            timeline = []
            
            # Deal creation
            if deal.get('RegisterTime') or deal.get('register_time'):
                timeline.append({
                    "date": deal.get('RegisterTime') or deal.get('register_time'),
                    "type": "deal_created",
                    "description": f"Deal created: {deal.get('customer_name', 'Unknown customer')}",
                    "milestone": True
                })
            
            # Activities
            for activity in activities:
                timeline.append({
                    "date": activity.registerdate.isoformat() if activity.registerdate else None,
                    "type": "activity",
                    "activity_type": activity.activitytypeid,
                    "description": activity.note or activity.resultnote or "",
                    "created_by": activity.creatorid or "",
                    "milestone": False
                })
            
            # Deal closure
            if deal.get('close_date'):
                timeline.append({
                    "date": deal['close_date'],
                    "type": "deal_closed",
                    "description": f"Deal closed with status: {deal.get('deal_status')}",
                    "milestone": True
                })
            
            # Sort by date
            timeline.sort(key=lambda x: x['date'] or '1900-01-01')
            
            return {
                "deal_id": deal_id,
                "timeline": timeline,
                "total_events": len(timeline),
                "duration_days": self._calculate_deal_duration(deal)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating timeline for deal {deal_id}: {e}")
            raise ServiceError(f"Failed to generate timeline: {e}")
    def detect_deal_status(self, deal: Dict[str, Any]) -> str:
        """
        Detect deal status from deal object.

        Delegates to centralized DealStatusDetector utility.

        Args:
            deal: Deal dictionary

        Returns:
            One of: 'won', 'lost', 'open', 'unknown'
        """
        return DealStatusDetector.detect_string(deal)

    def get_status_change_date(self, deal: Dict[str, Any]) -> Optional[datetime]:
        """
        Get when deal status changed (to won or lost).

        Delegates to centralized DealStatusDetector utility.

        Args:
            deal: Deal dictionary

        Returns:
            Datetime of status change, or None if not applicable
        """
        return DealStatusDetector.get_status_change_date(deal)

    def get_days_since_status_change(self, deal: Dict[str, Any]) -> Optional[int]:
        """
        Get days since deal status changed (for closed deals).

        Delegates to centralized DealStatusDetector utility.

        Args:
            deal: Deal dictionary

        Returns:
            Days since change, or None if deal is still open
        """
        return DealStatusDetector.get_days_since_status_change(deal)

    def is_deal_won(self, deal: Dict[str, Any]) -> bool:
        """Check if deal is won"""
        return DealStatusDetector.is_won(deal)

    def is_deal_lost(self, deal: Dict[str, Any]) -> bool:
        """Check if deal is lost"""
        return DealStatusDetector.is_lost(deal)

    def is_deal_open(self, deal: Dict[str, Any]) -> bool:
        """Check if deal is still open"""
        return DealStatusDetector.is_open(deal)

    def get_days_since_last_activity(self, activities: List[Any]) -> int:
        """
        Calculate days since last activity.

        Delegates to centralized ActivityUtils utility.

        Args:
            activities: List of activities

        Returns:
            Days since last activity, or 999 if no activities
        """
        return ActivityUtils.days_since_last_activity(activities)

    def get_deal_age_days(self, deal: Dict[str, Any]) -> int:
        """
        Calculate deal age in days (from creation to now or to close date).

        Delegates to centralized DealStatusDetector utility.

        Args:
            deal: Deal dictionary

        Returns:
            Deal age in days, or 999 if no creation date
        """
        return DealStatusDetector.get_deal_age_days(deal)

    def has_recent_followup(self, activities: List[Any], days: int = 30) -> bool:
        """
        Check if there's recent followup activity.

        Delegates to centralized ActivityUtils utility.

        Args:
            activities: List of activities
            days: Days to check back

        Returns:
            True if activity within days, False otherwise
        """
        return ActivityUtils.has_recent_activity(activities, days)
    def _calculate_deal_duration(self, deal: Dict[str, Any]) -> Optional[int]:
        """
        Calculate deal duration in days.

        Uses centralized DateUtils for date parsing.
        """
        try:
            if hasattr(deal, 'RegisterTime'):
                created_date = deal.RegisterTime
                close_date = deal.LastUpdateTime or deal.ChangeToWonTime or deal.ChangeToLossTime
            else:
                created_date = deal.get('RegisterTime') or deal.get('register_time')
                close_date = (deal.get('LastUpdateTime') or deal.get('last_update_time') or
                            deal.get('ChangeToWonTime') or deal.get('change_to_won_time'))

            start = DateUtils.parse_iso_date(created_date)
            if not start:
                return None

            end = DateUtils.parse_iso_date(close_date) or datetime.now()
            return DateUtils.days_between(start, end)

        except Exception:
            return None
