"""
services/moe/experts/activity_expert.py
---------------------------------------
Expert for activity summarization and trends.
REFACTORED: Uses centralized utilities for DRY code.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..base_expert import BaseExpert, ExpertResult, require_repositories
from config.moe_settings import MoESettings
from utils.activity_utils import ActivityUtils
from utils.date_utils import DateUtils


class ActivityExpert(BaseExpert):
    """Expert specializing in activity analysis and trends"""

    @property
    def expert_type(self) -> str:
        return 'activity'

    @property
    def description(self) -> str:
        return "Analyzes activity patterns, timelines, and trends"

    @property
    def supported_query_types(self) -> list:
        return ['activity', 'timeline', 'history', 'trend']

    def can_handle(self, query: str, context: Dict[str, Any] = None) -> float:
        """
        Determine if this expert can handle the query.

        Uses centralized KeywordMatcher for consistent scoring.
        """
        matcher = self._get_keyword_matcher()
        return matcher.calculate_score(query, context)

    async def analyze(self, query: str, context: Dict[str, Any] = None) -> ExpertResult:
        """Perform activity analysis"""
        context = context or {}

        try:
            # Get deal ID if available
            deal_id = self._extract_deal_id(query, context)

            if deal_id:
                # Get activities for specific deal
                result = await self._analyze_deal_activities(deal_id)
            else:
                # Get overall activity summary
                result = await self._analyze_all_activities(context)

            if 'error' in result:
                return ExpertResult(
                    expert_type=self.expert_type,
                    success=False,
                    data=result,
                    confidence=0.0,
                    reasoning=f"Activity analysis failed: {result['error']}"
                )

            confidence = self.calculate_confidence(query, result)

            return ExpertResult(
                expert_type=self.expert_type,
                success=True,
                data=result,
                confidence=confidence,
                reasoning=f"Analyzed {result.get('total_activities', 0)} activities"
            )

        except Exception as e:
            self.logger.error(f"Activity analysis error: {e}")
            return ExpertResult.error_result(self.expert_type, str(e))

    @require_repositories
    async def _analyze_deal_activities(self, deal_id: str) -> Dict[str, Any]:
        """Analyze activities for a specific deal"""
        try:
            with self.repositories as uow:
                activities = uow.activities.get_activities_by_deal(deal_id)

            if not activities:
                return {
                    'deal_id': deal_id,
                    'total_activities': 0,
                    'message': 'No activities found for this deal'
                }

            # Create timeline
            timeline = []
            for activity in activities:
                activity_dict = activity.to_dict() if hasattr(activity, 'to_dict') else activity
                timeline.append({
                    'id': activity_dict.get('id'),
                    'title': activity_dict.get('title', 'Unknown'),
                    'note': activity_dict.get('note', ''),
                    'created_at': activity_dict.get('add_time', '')
                })

            # Calculate activity frequency
            frequency = self._calculate_frequency(activities)

            # Get recent activities
            recent = timeline[:5]

            return {
                'deal_id': deal_id,
                'total_activities': len(activities),
                'timeline': timeline,
                'recent_activities': recent,
                'frequency': frequency,
                'activity_types': self._count_activity_types(activities)
            }

        except Exception as e:
            return {'error': str(e)}

    @require_repositories
    async def _analyze_all_activities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all activities (overview)"""
        try:
            # Get days from context or default
            days = context.get('days', 30)
            cutoff_date = DateUtils.get_cutoff_date(days)

            with self.repositories as uow:
                # Get recent activities
                all_activities = uow.activities.get_all()

            if not all_activities:
                return {
                    'total_activities': 0,
                    'period_days': days,
                    'message': 'No activities found'
                }

            # Filter by date using DateUtils
            recent_activities = []
            for activity in all_activities:
                activity_date = ActivityUtils.get_activity_date(activity)
                if activity_date and activity_date >= cutoff_date:
                    recent_activities.append(activity)

            # Calculate summary using ActivityUtils
            activity_types = ActivityUtils.count_by_type(recent_activities)
            frequency = ActivityUtils.calculate_frequency(recent_activities)

            return {
                'total_activities': len(recent_activities),
                'period_days': days,
                'activity_types': activity_types,
                'frequency': frequency,
                'daily_average': len(recent_activities) / days if days > 0 else 0
            }

        except Exception as e:
            return {'error': str(e)}

    def _calculate_frequency(self, activities: List) -> Dict[str, Any]:
        """
        Calculate activity frequency.

        Uses centralized ActivityUtils for consistent calculation.
        """
        return ActivityUtils.calculate_frequency(activities)

    def _count_activity_types(self, activities: List) -> Dict[str, int]:
        """
        Count activities by type.

        Uses centralized ActivityUtils for consistent counting.
        """
        return ActivityUtils.count_by_type(activities)

    @property
    def confidence_boost_keys(self) -> List[str]:
        return ['total_activities', 'timeline', 'frequency']

    
