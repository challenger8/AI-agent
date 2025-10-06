"""
services/deal_service.py
------------------------
Deal management and analysis service
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from services.base_service import BaseService
from config.settings import AnalysisSettings
from utils.exceptions import ServiceError

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
                    "date": deal['created_date'],
                    "type": "deal_created",
                    "description": f"Deal created: {deal.get('customer_name', 'Unknown customer')}",
                    "milestone": True
                })
            
            # Activities
            for activity in activities:
                timeline.append({
                    "date": activity.registerdate.isoformat() if activity.registerdate else None,
                    "type": "activity",
                    "activity_type": activity.activity_type.value,
                    "description": activity.activity_description,
                    "created_by": activity.created_by,
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
    
    def _calculate_deal_duration(self, deal: Dict[str, Any]) -> Optional[int]:
        """Calculate deal duration in days"""
        try:
            if hasattr(deal, 'RegisterTime'):
                created_date = deal.RegisterTime
                close_date = deal.LastUpdateTime or deal.ChangeToWonTime or deal.ChangeToLossTime
            else:
                created_date = deal.get('RegisterTime') or deal.get('register_time')
                close_date = (deal.get('LastUpdateTime') or deal.get('last_update_time') or 
                            deal.get('ChangeToWonTime') or deal.get('change_to_won_time'))
            
            if not created_date:
                return None
            
            start = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
            end = datetime.fromisoformat(close_date.replace('Z', '+00:00')) if close_date else datetime.now()
            
            return (end - start).days
            
        except Exception:
            return None
