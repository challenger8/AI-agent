"""
mcp/handlers/resource_handlers.py
---------------------------------
Resource handlers for MCP server
"""

import json
from datetime import datetime
from typing import List

from mcp.types import Resource
from config.settings import get_sentiment_available
from utils.logging_config import get_logger

logger = get_logger("resource_handlers")

class ResourceHandlers:
    """Handles MCP resource requests"""
    
    def __init__(self, analytics_service, sentiment_service=None):
        """
        Initialize resource handlers
        
        Args:
            analytics_service: Analytics service instance
            sentiment_service: Optional sentiment service instance
        """
        self.analytics_service = analytics_service
        self.sentiment_service = sentiment_service
    
    def get_resources(self) -> List[Resource]:
        """Get list of available resources"""
        resources = [
            Resource(
                uri="deals://dashboard",
                name="Deals Dashboard",
                description="Comprehensive deals analysis with activity and sentiment insights",
                mimeType="application/json"
            ),
            Resource(
                uri="deals://portfolio-health",
                name="Portfolio Health",
                description="Overall portfolio health metrics and risk indicators",
                mimeType="application/json"
            ),
            Resource(
                uri="deals://activity-summary",
                name="Activity Summary",
                description="Summary of all deal activities and engagement patterns",
                mimeType="application/json"
            )
        ]
        
        # Add sentiment-specific resources if available
        if get_sentiment_available() and self.sentiment_service:
            resources.extend([
                Resource(
                    uri="deals://sentiment-overview",
                    name="Sentiment Overview", 
                    description="Overall sentiment analysis across all activities",
                    mimeType="application/json"
                ),
                Resource(
                    uri="deals://sentiment-trends",
                    name="Sentiment Trends",
                    description="Time-based sentiment trends and patterns",
                    mimeType="application/json"
                )
            ])
        
        return resources
    
    async def handle_resource_request(self, uri: str) -> str:
        """
        Handle resource request and return JSON response
        
        Args:
            uri: Resource URI
            
        Returns:
            JSON string response
        """
        try:
            if uri == "deals://dashboard":
                return await self._handle_dashboard()
            elif uri == "deals://portfolio-health":
                return await self._handle_portfolio_health()
            elif uri == "deals://activity-summary":
                return await self._handle_activity_summary()
            elif uri == "deals://sentiment-overview":
                return await self._handle_sentiment_overview()
            elif uri == "deals://sentiment-trends":
                return await self._handle_sentiment_trends()
            else:
                error_data = {"error": f"Resource not found: {uri}"}
                return json.dumps(error_data, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"Error handling resource {uri}: {e}")
            error_data = {"error": str(e), "resource": uri}
            return json.dumps(error_data, ensure_ascii=False, indent=2)
    
    async def _handle_dashboard(self) -> str:
        """Handle dashboard resource request"""
        logger.info("Generating dashboard data")
        
        # Load sentiment model if needed
        if self.sentiment_service and not self.sentiment_service.model_loaded:
            await self.sentiment_service.initialize()
        
        # Get comprehensive overview
        data = self.analytics_service.analyze_portfolio_overview()
        data["resource"] = "dashboard"
        data["last_updated"] = datetime.now().isoformat()
        
        return json.dumps(data, ensure_ascii=False, indent=2, default=str)
    
    async def _handle_portfolio_health(self) -> str:
        """Handle portfolio health resource request"""
        logger.info("Generating portfolio health data")
        
        data = self.analytics_service.analyze_portfolio_overview()
        
        # Focus on health metrics
        health_data = {
            "health_overview": data.get("health_overview", {}),
            "summary": data.get("summary", {}),
            "activity_breakdown": data.get("activity_breakdown", {}),
            "insights": data.get("insights", {}),
            "resource": "portfolio-health",
            "generated_at": datetime.now().isoformat()
        }
        
        return json.dumps(health_data, ensure_ascii=False, indent=2, default=str)
    
    async def _handle_activity_summary(self) -> str:
        """Handle activity summary resource request"""
        logger.info("Generating activity summary data")
        
        data = self.analytics_service.analyze_portfolio_overview()
        
        # Focus on activity data
        activity_data = {
            "activity_breakdown": data.get("activity_breakdown", {}),
            "summary": {
                "total_activities": data.get("summary", {}).get("total_activities", 0),
                "deals_with_activity": data.get("summary", {}).get("deals_with_activity", 0),
                "avg_activities_per_deal": data.get("summary", {}).get("avg_activities_per_deal", 0)
            },
            "period_days": data.get("period_days", 30),
            "resource": "activity-summary",
            "generated_at": datetime.now().isoformat()
        }
        
        return json.dumps(activity_data, ensure_ascii=False, indent=2, default=str)
    
    async def _handle_sentiment_overview(self) -> str:
        """Handle sentiment overview resource request"""
        if not get_sentiment_available() or not self.sentiment_service:
            error_data = {"error": "Sentiment analysis not available"}
            return json.dumps(error_data, ensure_ascii=False, indent=2)
        
        logger.info("Generating sentiment overview data")
        
        # Ensure model is loaded
        if not self.sentiment_service.model_loaded:
            await self.sentiment_service.initialize()
        
        data = self.analytics_service.analyze_portfolio_overview()
        
        # Focus on sentiment data
        sentiment_data = {
            "sentiment_overview": data.get("sentiment_overview", {}),
            "insights": data.get("insights", {}),
            "period_days": data.get("period_days", 30),
            "resource": "sentiment-overview",
            "generated_at": datetime.now().isoformat()
        }
        
        return json.dumps(sentiment_data, ensure_ascii=False, indent=2, default=str)
    
    async def _handle_sentiment_trends(self) -> str:
        """Handle sentiment trends resource request"""
        if not get_sentiment_available() or not self.sentiment_service:
            error_data = {"error": "Sentiment analysis not available"}
            return json.dumps(error_data, ensure_ascii=False, indent=2)
        
        logger.info("Generating sentiment trends data")
        
        # Ensure model is loaded
        if not self.sentiment_service.model_loaded:
            await self.sentiment_service.initialize()
        
        # Get all recent activities
        deals = self.analytics_service.deal_service.get_all_deals()
        all_activities = []
        
        with self.analytics_service.repositories as uow:
            for deal in deals[:10]:  # Limit to recent deals for performance
                activities = uow.activities.get_by_deal_id(deal['deal_id'])
                all_activities.extend(activities)
        
        # Get sentiment trends
        trends = self.sentiment_service.get_sentiment_trends(all_activities, days=14)
        trends.update({
            "resource": "sentiment-trends",
            "generated_at": datetime.now().isoformat()
        })
        
        return json.dumps(trends, ensure_ascii=False, indent=2, default=str)