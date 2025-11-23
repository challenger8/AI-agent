"""
services/moe/experts/activity_expert.py
---------------------------------------
Expert for activity summarization and trends
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List

from ..base_expert import BaseExpert, ExpertResult
from config.moe_settings import MoESettings


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
        """Determine if this expert can handle the query"""
        query_lower = query.lower()
        score = 0.0

        # Check for activity-related keywords
        activity_keywords = [
            'activity', 'فعالیت', 'timeline', 'جدول زمانی', 'history', 'تاریخچه',
            'recent', 'اخیر', 'last', 'آخرین', 'trend', 'روند', 'summary', 'خلاصه',
            'what happened', 'چه اتفاقی', 'updates', 'بروزرسانی'
        ]

        for keyword in activity_keywords:
            if keyword in query_lower:
                score += 0.15

        # Check for time-related patterns
        time_patterns = [
            r'\blast\s+\d+\s+days?\b',
            r'\brecent\b',
            r'\bthis\s+week\b',
            r'\bthis\s+month\b'
        ]

        for pattern in time_patterns:
            if re.search(pattern, query_lower):
                score += 0.1

        # Context boost
        if context and context.get('entity_type') == 'activity':
            score += 0.2

        return min(score, 1.0)

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

    async def _analyze_deal_activities(self, deal_id: str) -> Dict[str, Any]:
        """Analyze activities for a specific deal"""
        if not self.repositories:
            return {'error': 'Repositories not available'}

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

    async def _analyze_all_activities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze all activities (overview)"""
        if not self.repositories:
            return {'error': 'Repositories not available'}

        try:
            # Get days from context or default
            days = context.get('days', 30)
            cutoff_date = datetime.now() - timedelta(days=days)

            with self.repositories as uow:
                # Get recent activities
                all_activities = uow.activities.get_all()

            if not all_activities:
                return {
                    'total_activities': 0,
                    'period_days': days,
                    'message': 'No activities found'
                }

            # Filter by date
            recent_activities = []
            for activity in all_activities:
                activity_dict = activity.to_dict() if hasattr(activity, 'to_dict') else activity
                add_time = activity_dict.get('add_time')
                if add_time:
                    try:
                        if isinstance(add_time, str):
                            activity_date = datetime.fromisoformat(add_time.replace('Z', '+00:00'))
                        else:
                            activity_date = add_time
                        if activity_date >= cutoff_date:
                            recent_activities.append(activity)
                    except (ValueError, TypeError):
                        pass

            # Calculate summary
            activity_types = self._count_activity_types(recent_activities)
            frequency = self._calculate_frequency(recent_activities)

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
        """Calculate activity frequency"""
        if not activities:
            return {'status': 'no_data'}

        # Count by day
        daily_counts = {}
        for activity in activities:
            activity_dict = activity.to_dict() if hasattr(activity, 'to_dict') else activity
            add_time = activity_dict.get('add_time', '')
            if add_time:
                try:
                    if isinstance(add_time, str):
                        date_str = add_time[:10]
                    else:
                        date_str = add_time.strftime('%Y-%m-%d')
                    daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
                except (ValueError, AttributeError):
                    pass

        if not daily_counts:
            return {'status': 'no_dated_activities'}

        avg_per_day = sum(daily_counts.values()) / len(daily_counts)
        max_day = max(daily_counts.items(), key=lambda x: x[1]) if daily_counts else (None, 0)

        return {
            'average_per_day': round(avg_per_day, 2),
            'busiest_day': max_day[0],
            'busiest_day_count': max_day[1],
            'total_days_with_activity': len(daily_counts)
        }

    def _count_activity_types(self, activities: List) -> Dict[str, int]:
        """Count activities by type"""
        type_counts = {}
        for activity in activities:
            activity_dict = activity.to_dict() if hasattr(activity, 'to_dict') else activity
            activity_type = activity_dict.get('type', 'unknown')
            type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
        return type_counts

    def calculate_confidence(self, query: str, result: Dict[str, Any]) -> float:
        """Calculate confidence score for the result"""
        base_confidence = 0.7

        # Boost for data presence
        if result.get('total_activities', 0) > 0:
            base_confidence += 0.1

        # Boost for timeline
        if result.get('timeline'):
            base_confidence += 0.1

        # Boost for frequency data
        if result.get('frequency') and result['frequency'].get('average_per_day'):
            base_confidence += 0.05

        return min(base_confidence, 1.0)

    def _extract_deal_id(self, query: str, context: Dict[str, Any]) -> str:
        """Extract deal ID from query or context"""
        if context.get('deal_id'):
            return str(context['deal_id'])

        patterns = [
            r'\bdeal[\s_-]?(\d+)\b',
            r'\bدیل[\s_-]?(\d+)\b'
        ]

        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                return match.group(1)

        return None
