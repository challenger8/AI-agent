"""
services/analytics_service.py
-----------------------------
Advanced analytics and health metrics service
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

from services.base_service import BaseService
from services.deal_service import DealService
from services.sentiment_service import SentimentService
from config.settings import AnalysisSettings
from utils.exceptions import ServiceError

class AnalyticsService(BaseService):
    """Advanced analytics combining deals, activities, and sentiment"""
    
    def __init__(self, repositories=None, sentiment_service: Optional[SentimentService] = None):
        super().__init__(repositories)
        self.deal_service = DealService(repositories)
        self.sentiment_service = sentiment_service
    
    def analyze_deal_comprehensive(self, deal_id: str) -> Dict[str, Any]:
        """
        Comprehensive deal analysis including activities and sentiment
        
        Args:
            deal_id: Deal identifier
            
        Returns:
            Comprehensive analysis dictionary with deal data, activities, 
            sentiment, health score, risks, and recommendations
        """
        try:
            # Get deal data
            cache_key = self.cache_service.generate_key("deal_analysis", deal_id)
        
        # Try cache first
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                self.logger.debug(f"Deal analysis cache HIT for {deal_id}")
                return cached_result
            
            self.logger.debug(f"Deal analysis cache MISS for {deal_id} - calculating...")
            deal = self.deal_service.get_deal(deal_id)
            if not deal:
                return {"error": f"Deal {deal_id} not found"}
            
            # Get activities
            with self.repositories as uow:
                activities = uow.activities.get_activities_by_deal(deal_id)
            
            # Analyze sentiment for activities
            sentiment_summary = self._analyze_activities_sentiment(activities)
            
            # Calculate health score
            health_score = self._calculate_health_score(deal, activities, sentiment_summary)
            
            # Identify risk indicators
            risk_indicators = self._identify_risk_indicators(deal, activities, health_score)
            
            # Generate insights and recommendations
            insights = self._generate_insights(deal, activities, sentiment_summary, health_score, risk_indicators)
            
            # Create activity timeline
            timeline = self._create_activity_timeline(activities)
            
            result = {
            "deal": deal,
            "deal_id": deal_id,
            # ... all your other fields ...
            "analyzed_at": datetime.now().isoformat()
             }
        
        # Cache for 10 minutes (600 seconds)
            self.cache_service.set(cache_key, result, ttl=600)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive deal analysis for {deal_id}: {e}")
            raise ServiceError(f"Failed to analyze deal: {e}")
    
    def analyze_portfolio_overview(self, status: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """
        Portfolio-wide analytics with activity patterns and sentiment insights
        
        Args:
            status: Optional status filter
            days: Number of days to analyze
            
        Returns:
            Portfolio overview with statistics, activity breakdown, sentiment overview,
            health metrics, and insights
        """
        try:
            cache_key = self.cache_service.generate_key(
            "portfolio", 
            status or "all", 
            str(days)
        )
        
        # Try cache first
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                self.logger.debug("Portfolio overview cache HIT")
                return cached_result
            
            self.logger.debug("Portfolio overview cache MISS - calculating...")
            # Get deals
            if status:
                deals = self.deal_service.get_deals_by_status(status)
            else:
                deals = self.deal_service.get_all_deals()
            
            if not deals:
                return {
                    "summary": {"total_deals": 0},
                    "message": "No deals found"
                }
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Filter recent deals
            recent_deals = [
                d for d in deals 
                if d.get('register_time') and 
                self._parse_datetime(d['register_time']) >= cutoff_date
            ] if deals else []
            
            # Get all activities for analysis
            all_activities = []
            deal_activities_map = {}
            
            with self.repositories as uow:
                for deal in deals[:100]:  # Limit to prevent performance issues
                    deal_id = deal.get('id')
                    if deal_id:
                        activities = uow.activities.get_activities_by_deal(deal_id)
                        all_activities.extend(activities)
                        deal_activities_map[deal_id] = activities
            
            # Calculate summary statistics
            summary = self._calculate_portfolio_summary(deals, recent_deals, all_activities)
            
            # Activity breakdown
            activity_breakdown = self._calculate_activity_breakdown(all_activities, days)
            
            # Sentiment overview
            sentiment_overview = self._calculate_sentiment_overview(all_activities)
            
            # Health overview
            health_overview = self._calculate_health_overview(deals, deal_activities_map)
            
            # Generate portfolio insights
            portfolio_insights = self._generate_portfolio_insights(
                summary, activity_breakdown, sentiment_overview, health_overview
            )
            
            result = {
            "period_days": days,
            "status_filter": status,
            "summary": summary,
            "activity_breakdown": activity_breakdown,
            "sentiment_overview": sentiment_overview,
            "health_overview": health_overview,
            "insights": portfolio_insights,
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Cache for 5 minutes (300 seconds)
            self.cache_service.set(cache_key, result, ttl=300)
        
            return result
        except Exception as e:
            self.logger.error(f"Error in portfolio overview analysis: {e}")
            raise ServiceError(f"Failed to analyze portfolio: {e}")
    
    def _analyze_activities_sentiment(self, activities: List[Any]) -> Dict[str, Any]:
        """Analyze sentiment for all activities"""
        if not activities or not self.sentiment_service or not self.sentiment_service.model_loaded:
            return {
                "total_activities": len(activities) if activities else 0,
                "analyzed_activities": 0,
                "sentiment_available": False
            }
        
        sentiments = []
        analyzed_count = 0
        
        for activity in activities:
            # Get combined text from activity
            text = activity.get_combined_text() if hasattr(activity, 'get_combined_text') else ""
            
            if text and len(text.strip()) >= 5:
                sentiment_result = self.sentiment_service.analyze_text(text)
                if "error" not in sentiment_result:
                    sentiments.append({
                        "activity_id": activity.id,
                        "sentiment": sentiment_result.get("sentiment", "خنثی"),
                        "confidence": sentiment_result.get("confidence", 0.0),
                        "date": activity.registerdate
                    })
                    analyzed_count += 1
        
        # Calculate sentiment statistics
        if sentiments:
            sentiment_counts = defaultdict(int)
            for s in sentiments:
                sentiment_counts[s["sentiment"]] += 1
            
            # Determine dominant sentiment
            dominant = max(sentiment_counts.items(), key=lambda x: x[1])[0] if sentiment_counts else "خنثی"
            
            # Calculate average confidence
            avg_confidence = sum(s["confidence"] for s in sentiments) / len(sentiments)
            
            return {
                "total_activities": len(activities),
                "analyzed_activities": analyzed_count,
                "sentiment_available": True,
                "sentiment_distribution": dict(sentiment_counts),
                "dominant_sentiment": dominant,
                "average_confidence": round(avg_confidence, 3),
                "sentiment_details": sentiments[-10:]  # Last 10 for reference
            }
        
        return {
            "total_activities": len(activities),
            "analyzed_activities": 0,
            "sentiment_available": True,
            "sentiment_distribution": {},
            "dominant_sentiment": "خنثی"
        }
    
    def _calculate_health_score(self, deal: Dict[str, Any], activities: List[Any], 
                                sentiment_summary: Dict[str, Any]) -> int:
        """
        Calculate deal health score (0-100)
        
        Factors:
        - Activity recency
        - Activity frequency
        - Sentiment trends
        - Deal age
        - Status progression
        """
        score = AnalysisSettings.HEALTH_SCORE_BASE
        
        if not activities:
            return max(0, score - 30)  # Penalize deals with no activities
        
        now = datetime.now()
        
        # Factor 1: Activity Recency (max +15 points)
        last_activity_date = max(
            (a.registerdate for a in activities if a.registerdate),
            default=None
        )
        
        if last_activity_date:
            days_since_activity = (now - last_activity_date).days
            
            if days_since_activity <= 7:
                score += AnalysisSettings.RECENT_ACTIVITY_BONUS  # +15
            elif days_since_activity <= 14:
                score += 10
            elif days_since_activity <= 30:
                score += 5
            else:
                score -= 15  # Stale activity penalty
        
        # Factor 2: Activity Frequency (max +10 points)
        activity_count = len(activities)
        
        if activity_count >= 20:
            score += 10
        elif activity_count >= 10:
            score += 7
        elif activity_count >= 5:
            score += 5
        elif activity_count >= 2:
            score += 2
        
        # Factor 3: Activity Variety (max +8 points)
        activity_types = set()
        for activity in activities:
            if hasattr(activity, 'activitytypeid') and activity.activitytypeid:
                activity_types.add(activity.activitytypeid)
        
        variety_count = len(activity_types)
        if variety_count >= 5:
            score += AnalysisSettings.ACTIVITY_VARIETY_BONUS  # +8
        elif variety_count >= 3:
            score += 5
        elif variety_count >= 2:
            score += 2
        
        # Factor 4: Sentiment (max +15 or -15 points)
        if sentiment_summary.get("sentiment_available"):
            dominant = sentiment_summary.get("dominant_sentiment", "خنثی")
            
            if dominant == "مثبت":
                score += 15
            elif dominant == "منفی":
                score -= 15
            # Neutral = no change
        
        # Factor 5: Deal Age (penalty for old deals)
        register_time = deal.get('register_time')
        if register_time:
            deal_age_days = (now - self._parse_datetime(register_time)).days
            
            if deal_age_days > AnalysisSettings.AGING_DEAL_DAYS:  # 60 days
                score -= 10
            elif deal_age_days > 90:
                score -= 20
        
        # Factor 6: Deal Status
        status = deal.get('status', '').lower()
        
        if 'won' in status or 'بسته شده' in status:
            score += 10  # Closed deals are healthy
        elif 'lost' in status or 'لغو' in status:
            score -= 20  # Lost deals are unhealthy
        
        # Cap score between 0 and 100
        return max(0, min(AnalysisSettings.HEALTH_SCORE_MAX, score))
    
    def _identify_risk_indicators(self, deal: Dict[str, Any], activities: List[Any], 
                                  health_score: int) -> List[Dict[str, Any]]:
        """Identify risk indicators for the deal"""
        risks = []
        now = datetime.now()
        
        # Risk 1: Low Health Score
        if health_score < AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            risks.append({
                "type": "low_health_score",
                "severity": "high" if health_score < 30 else "medium",
                "description": f"امتیاز سلامت پایین: {health_score}/100",
                "recommendation": "بازبینی استراتژی معامله و افزایش تعامل با مشتری"
            })
        
        # Risk 2: Stale Activity
        if activities:
            last_activity_date = max(
                (a.registerdate for a in activities if a.registerdate),
                default=None
            )
            
            if last_activity_date:
                days_since_activity = (now - last_activity_date).days
                
                if days_since_activity >= AnalysisSettings.STALE_ACTIVITY_DAYS:
                    risks.append({
                        "type": "stale_activity",
                        "severity": "high" if days_since_activity > 30 else "medium",
                        "description": f"عدم فعالیت به مدت {days_since_activity} روز",
                        "recommendation": "پیگیری فوری و برنامه‌ریزی جلسه با مشتری"
                    })
        else:
            risks.append({
                "type": "no_activity",
                "severity": "critical",
                "description": "هیچ فعالیتی ثبت نشده است",
                "recommendation": "شروع فوری تعامل با مشتری"
            })
        
        # Risk 3: Aging Deal
        register_time = deal.get('register_time')
        if register_time:
            deal_age_days = (now - self._parse_datetime(register_time)).days
            
            if deal_age_days > AnalysisSettings.AGING_DEAL_DAYS:
                risks.append({
                    "type": "aging_deal",
                    "severity": "medium",
                    "description": f"معامله {deal_age_days} روز باز است",
                    "recommendation": "بررسی دلایل طولانی شدن و تعیین برنامه بستن"
                })
        
        # Risk 4: Negative Sentiment Trend
        # This would require sentiment history - simplified for now
        
        # Risk 5: No Recent Contact
        cold_threshold = AnalysisSettings.COLD_DEAL_DAYS
        if activities:
            last_activity_date = max(
                (a.registerdate for a in activities if a.registerdate),
                default=None
            )
            
            if last_activity_date:
                days_since = (now - last_activity_date).days
                if days_since > cold_threshold:
                    risks.append({
                        "type": "cold_deal",
                        "severity": "high",
                        "description": f"تماس آخر {days_since} روز پیش",
                        "recommendation": "احیای ارتباط با مشتری"
                    })
        
        return risks
    
    def _generate_insights(self, deal: Dict[str, Any], activities: List[Any],
                          sentiment_summary: Dict[str, Any], health_score: int,
                          risk_indicators: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable insights"""
        insights = []
        
        # Health-based insights
        if health_score >= AnalysisSettings.HEALTH_HIGH_THRESHOLD:
            insights.append(f"✅ معامله سالم با امتیاز {health_score}/100")
            insights.append("💡 فرصت مناسب برای بستن معامله")
        elif health_score >= AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            insights.append(f"⚠️ معامله در وضعیت متوسط با امتیاز {health_score}/100")
            insights.append("💡 نیاز به افزایش تعامل و پیگیری")
        else:
            insights.append(f"🔴 معامله در خطر با امتیاز {health_score}/100")
            insights.append("💡 بازبینی فوری استراتژی لازم است")
        
        # Activity insights
        if activities:
            activity_count = len(activities)
            if activity_count >= 10:
                insights.append(f"📈 تعامل خوب: {activity_count} فعالیت ثبت شده")
            elif activity_count < 3:
                insights.append(f"⚠️ تعامل کم: تنها {activity_count} فعالیت")
        
        # Sentiment insights
        if sentiment_summary.get("sentiment_available"):
            dominant = sentiment_summary.get("dominant_sentiment", "خنثی")
            
            if dominant == "مثبت":
                insights.append("😊 احساسات مثبت در تعاملات")
                insights.append("💡 فرصت خوب برای پیشنهاد بعدی")
            elif dominant == "منفی":
                insights.append("😟 احساسات منفی در تعاملات")
                insights.append("💡 شناسایی و رفع نگرانی‌های مشتری")
        
        # Risk-based insights
        if risk_indicators:
            high_risks = [r for r in risk_indicators if r["severity"] == "high"]
            if high_risks:
                insights.append(f"⚠️ {len(high_risks)} خطر با اولویت بالا شناسایی شد")
        
        return insights
    
    def _generate_recommendations(self, deal: Dict[str, Any], health_score: int,
                                 risk_indicators: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Priority recommendations from risks
        for risk in risk_indicators[:3]:  # Top 3 risks
            recommendations.append(risk.get("recommendation", ""))
        
        # Health-based recommendations
        if health_score < 40:
            recommendations.append("بررسی دلایل ضعف معامله و مشاوره با مدیر")
            recommendations.append("ارزیابی احتمال موفقیت و تصمیم‌گیری درباره ادامه")
        elif health_score < 70:
            recommendations.append("افزایش فرکانس تعامل با مشتری")
            recommendations.append("برنامه‌ریزی برای مراحل بعدی")
        
        # Remove duplicates and limit
        recommendations = list(dict.fromkeys(recommendations))
        return recommendations[:5]
    
    def _create_activity_timeline(self, activities: List[Any]) -> List[Dict[str, Any]]:
        """Create chronological timeline of activities"""
        if not activities:
            return []
        
        # Sort activities by date
        sorted_activities = sorted(
            [a for a in activities if hasattr(a, 'registerdate') and a.registerdate],
            key=lambda x: x.registerdate
        )
        
        timeline = []
        for activity in sorted_activities[-20:]:  # Last 20 activities
            timeline.append({
                "date": activity.registerdate.isoformat() if activity.registerdate else None,
                "title": activity.title if hasattr(activity, 'title') else "",
                "type": activity.activitytypeid if hasattr(activity, 'activitytypeid') else "",
                "is_done": activity.isdone if hasattr(activity, 'isdone') else False,
                "activity_id": activity.id
            })
        
        return timeline
    
    def _calculate_portfolio_summary(self, all_deals: List[Dict], recent_deals: List[Dict],
                                    all_activities: List[Any]) -> Dict[str, Any]:
        """Calculate portfolio summary statistics"""
        total_deals = len(all_deals)
        
        # Deal status breakdown
        status_counts = defaultdict(int)
        for deal in all_deals:
            status = deal.get('status', 'Unknown')
            status_counts[status] += 1
        
        # Calculate values
        total_value = sum(
            float(d.get('price', 0)) for d in all_deals 
            if d.get('price') is not None
        )
        
        avg_value = total_value / total_deals if total_deals > 0 else 0
        
        # Activity statistics
        total_activities = len(all_activities)
        avg_activities_per_deal = total_activities / total_deals if total_deals > 0 else 0
        
        # Deals with recent activity
        deals_with_activity = len([d for d in all_deals if any(
            a.dealid == d.get('id') for a in all_activities
        )])
        
        return {
            "total_deals": total_deals,
            "recent_deals": len(recent_deals),
            "status_breakdown": dict(status_counts),
            "total_value": round(total_value, 2),
            "average_deal_value": round(avg_value, 2),
            "total_activities": total_activities,
            "avg_activities_per_deal": round(avg_activities_per_deal, 2),
            "deals_with_activity": deals_with_activity,
            "activity_rate": round((deals_with_activity / total_deals * 100), 1) if total_deals > 0 else 0
        }
    
    def _calculate_activity_breakdown(self, activities: List[Any], days: int) -> Dict[str, Any]:
        """Calculate activity breakdown and patterns"""
        if not activities:
            return {"total": 0, "by_type": {}, "recent_count": 0}
        
        cutoff = datetime.now() - timedelta(days=days)
        
        # Activity type breakdown
        type_counts = defaultdict(int)
        recent_count = 0
        
        for activity in activities:
            # Count by type
            activity_type = activity.activitytypeid if hasattr(activity, 'activitytypeid') else "Unknown"
            type_counts[activity_type] += 1
            
            # Count recent activities
            if hasattr(activity, 'registerdate') and activity.registerdate:
                if activity.registerdate >= cutoff:
                    recent_count += 1
        
        return {
            "total": len(activities),
            "by_type": dict(type_counts),
            "recent_count": recent_count,
            "recent_percentage": round((recent_count / len(activities) * 100), 1) if activities else 0
        }
    
    def _calculate_sentiment_overview(self, activities: List[Any]) -> Dict[str, Any]:
        """Calculate sentiment overview across all activities"""
        if not self.sentiment_service or not self.sentiment_service.model_loaded:
            return {"sentiment_available": False}
        
        sentiment_result = self._analyze_activities_sentiment(activities)
        
        return {
            "sentiment_available": True,
            "analyzed_count": sentiment_result.get("analyzed_activities", 0),
            "distribution": sentiment_result.get("sentiment_distribution", {}),
            "dominant_sentiment": sentiment_result.get("dominant_sentiment", "خنثی"),
            "average_confidence": sentiment_result.get("average_confidence", 0.0)
        }
    
    def _calculate_health_overview(self, deals: List[Dict], 
                                   deal_activities_map: Dict[str, List[Any]]) -> Dict[str, Any]:
        """Calculate health overview across portfolio"""
        health_scores = []
        health_distribution = {"high": 0, "medium": 0, "low": 0}
        
        for deal in deals[:100]:  # Limit for performance
            deal_id = deal.get('id')
            if not deal_id:
                continue
            
            activities = deal_activities_map.get(deal_id, [])
            sentiment_summary = self._analyze_activities_sentiment(activities)
            health_score = self._calculate_health_score(deal, activities, sentiment_summary)
            
            health_scores.append(health_score)
            
            # Categorize
            if health_score >= AnalysisSettings.HEALTH_HIGH_THRESHOLD:
                health_distribution["high"] += 1
            elif health_score >= AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
                health_distribution["medium"] += 1
            else:
                health_distribution["low"] += 1
        
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
        
        return {
            "average_health_score": round(avg_health, 1),
            "distribution": health_distribution,
            "at_risk_count": health_distribution["low"],
            "healthy_count": health_distribution["high"]
        }
    
    def _generate_portfolio_insights(self, summary: Dict, activity_breakdown: Dict,
                                    sentiment_overview: Dict, health_overview: Dict) -> List[str]:
        """Generate portfolio-level insights"""
        insights = []
        
        # Summary insights
        total_deals = summary.get("total_deals", 0)
        if total_deals > 0:
            activity_rate = summary.get("activity_rate", 0)
            
            if activity_rate >= 70:
                insights.append(f"✅ نرخ فعالیت بالا: {activity_rate}% معاملات فعال")
            elif activity_rate < 40:
                insights.append(f"⚠️ نرخ فعالیت پایین: {activity_rate}% معاملات فعال")
        
        # Health insights
        avg_health = health_overview.get("average_health_score", 0)
        at_risk = health_overview.get("at_risk_count", 0)
        
        if avg_health >= 70:
            insights.append(f"💪 سلامت پورتفولیو خوب: میانگین {avg_health}/100")
        elif avg_health < 50:
            insights.append(f"⚠️ سلامت پورتفولیو نیاز به توجه: میانگین {avg_health}/100")
        
        if at_risk > 0:
            insights.append(f"🔴 {at_risk} معامله در خطر نیاز به توجه فوری")
        
        # Sentiment insights
        if sentiment_overview.get("sentiment_available"):
            dominant = sentiment_overview.get("dominant_sentiment", "خنثی")
            if dominant == "مثبت":
                insights.append("😊 احساسات کلی مثبت در پورتفولیو")
            elif dominant == "منفی":
                insights.append("😟 احساسات منفی در پورتفولیو - نیاز به بررسی")
        
        return insights
    
    def _get_health_category(self, score: int) -> str:
        """Get health category label"""
        if score >= AnalysisSettings.HEALTH_HIGH_THRESHOLD:
            return "سالم"
        elif score >= AnalysisSettings.HEALTH_MEDIUM_THRESHOLD:
            return "متوسط"
        else:
            return "در خطر"
    
    def _parse_datetime(self, date_value: Any) -> datetime:
        """Parse datetime from various formats"""
        if isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except:
                return datetime.now()
        else:
            return datetime.now()
    def invalidate_deal_cache(self, deal_id: str):
        """Invalidate cache for a specific deal"""
        cache_key = self.cache_service.generate_key("deal_analysis", deal_id)
        deleted = self.cache_service.delete(cache_key)
        
        # Also invalidate portfolio cache since deal affects portfolio
        self.cache_service.delete_pattern("portfolio:*")
        
        self.logger.info(f"Invalidated cache for deal {deal_id}")
        return deleted

    def clear_analytics_cache(self):
        """Clear all analytics caches"""
        deleted = self.cache_service.delete_pattern("deal_analysis:*")
        deleted += self.cache_service.delete_pattern("portfolio:*")
        
        self.logger.info(f"Cleared analytics cache: {deleted} keys deleted")
        return deleted