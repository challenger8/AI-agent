"""
mcp/handlers/tool_handlers.py
-----------------------------
Tool handlers for MCP server
"""

import json
from datetime import datetime
from typing import Dict, Any, List

from mcp.types import Tool, TextContent
from config.settings import get_sentiment_available
from mcp_spec.schemas.tool_schemas import get_tool_schemas
from utils.logging_config import get_logger
from utils.exceptions import ServiceError

logger = get_logger("tool_handlers")

class ToolHandlers:
    """Handles MCP tool calls"""
    
    def __init__(self, analytics_service, sentiment_service=None):
        """
        Initialize tool handlers
        
        Args:
            analytics_service: Analytics service instance
            sentiment_service: Optional sentiment service instance
        """
        self.analytics_service = analytics_service
        self.sentiment_service = sentiment_service
        self.schemas = get_tool_schemas()
    
    def get_tools(self) -> List[Tool]:
        """Get list of available tools"""
        tools = [
            Tool(
                name="analyze_deal",
                description="Comprehensive deal analysis including activities and sentiment",
                inputSchema=self.schemas["analyze_deal"]
            ),
            Tool(
                name="analyze_deals_overview",
                description="Portfolio analysis with activity patterns and sentiment insights",
                inputSchema=self.schemas["analyze_deals_overview"]
            ),
            Tool(
                name="get_deal_activities_with_sentiment",
                description="Get deal activities with individual sentiment analysis",
                inputSchema=self.schemas["get_deal_activities_with_sentiment"]
            ),
            Tool(
                name="analyze_portfolio_health",
                description="Analyze overall portfolio health metrics",
                inputSchema=self.schemas["analyze_portfolio_health"]
            )
        ]
        
        # Add sentiment-specific tools if available
        if get_sentiment_available() and self.sentiment_service:
            tools.extend([
                Tool(
                    name="analyze_text_sentiment",
                    description="Analyze sentiment of Persian text",
                    inputSchema=self.schemas["analyze_text_sentiment"]
                ),
                Tool(
                    name="get_sentiment_trends",
                    description="Get sentiment trends for a deal over time",
                    inputSchema=self.schemas["get_sentiment_trends"]
                )
            ])
        
        return tools
    
    async def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """
        Handle tool call and return response
        
        Args:
            name: Tool name
            arguments: Tool arguments
            
        Returns:
            List of text content responses
        """
        try:
            # Load sentiment model if needed
            if self._is_sentiment_tool(name) and self.sentiment_service:
                await self._ensure_sentiment_model_loaded()
            
            # Route to appropriate handler
            if name == "analyze_deal":
                result = await self._handle_analyze_deal(arguments)
            elif name == "analyze_deals_overview":
                result = await self._handle_analyze_deals_overview(arguments)
            elif name == "get_deal_activities_with_sentiment":
                result = await self._handle_get_deal_activities(arguments)
            elif name == "analyze_portfolio_health":
                result = await self._handle_analyze_portfolio_health(arguments)
            elif name == "analyze_text_sentiment":
                result = await self._handle_analyze_text_sentiment(arguments)
            elif name == "get_sentiment_trends":
                result = await self._handle_get_sentiment_trends(arguments)
            else:
                result = {"error": f"Unknown tool: {name}"}
            
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2, default=str)
            )]
            
        except ServiceError as e:
            logger.error(f"Service error in tool {name}: {e}")
            error_result = {"error": f"Service error: {str(e)}"}
            return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]
        
        except Exception as e:
            logger.error(f"Unexpected error in tool {name}: {e}")
            error_result = {"error": f"Unexpected error: {str(e)}"}
            return [TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False))]
    
    async def _handle_analyze_deal(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle comprehensive deal analysis"""
        deal_id = arguments["deal_id"]
        logger.info(f"Analyzing deal {deal_id}")
        
        result = self.analytics_service.analyze_deal_comprehensive(deal_id)
        result["tool"] = "analyze_deal"
        return result
    
    async def _handle_analyze_deals_overview(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle portfolio overview analysis"""
        status = arguments.get("status")
        days = arguments.get("days", 30)
        
        logger.info(f"Analyzing deals overview: status={status}, days={days}")
        
        result = self.analytics_service.analyze_portfolio_overview(status, days)
        result["tool"] = "analyze_deals_overview"
        return result
    
    async def _handle_get_deal_activities(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get deal activities with sentiment"""
        deal_id = arguments["deal_id"]
        logger.info(f"Getting activities for deal {deal_id}")
        
        # Get deal and activities
        deal = self.analytics_service.deal_service.get_deal(deal_id)
        if not deal:
            return {"error": f"Deal {deal_id} not found"}
        
        with self.analytics_service.repositories as uow:
            activities = uow.activities.get_by_deal_id(deal_id)
        
        # Build response with activities
        activities_data = []
        for activity in activities:
            activity_dict = activity.to_dict()
            
            # Add sentiment if available
            if (self.sentiment_service and 
                self.sentiment_service.model_loaded and 
                activity.activity_description and 
                len(activity.activity_description.strip()) >= 5):
                
                sentiment = self.sentiment_service.analyze_text(activity.activity_description)
                activity_dict["sentiment"] = sentiment
            
            activities_data.append(activity_dict)
        
        result = {
            "deal": deal,
            "activities": activities_data,
            "timeline": self.analytics_service._create_activity_timeline(activities),
            "total_activities": len(activities),
            "tool": "get_deal_activities_with_sentiment"
        }
        
        return result
    
    async def _handle_analyze_portfolio_health(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle portfolio health analysis"""
        status_filter = arguments.get("status_filter")
        days = arguments.get("days", 30)
        
        logger.info(f"Analyzing portfolio health: status={status_filter}, days={days}")
        
        result = self.analytics_service.analyze_portfolio_overview(status_filter, days)
        result["tool"] = "analyze_portfolio_health"
        return result
    
    async def _handle_analyze_text_sentiment(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle text sentiment analysis"""
        text = arguments["text"]
        
        if not self.sentiment_service or not self.sentiment_service.model_loaded:
            return {"error": "Sentiment model not available"}
        
        logger.info("Analyzing text sentiment")
        
        result = self.sentiment_service.analyze_text(text)
        result.update({
            "analyzed_at": datetime.now().isoformat(),
            "tool": "analyze_text_sentiment"
        })
        
        return result
    
    async def _handle_get_sentiment_trends(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle sentiment trends analysis"""
        deal_id = arguments["deal_id"]
        days = arguments.get("days", 7)
        
        if not self.sentiment_service or not self.sentiment_service.model_loaded:
            return {"error": "Sentiment model not available"}
        
        logger.info(f"Getting sentiment trends for deal {deal_id}")
        
        # Get activities for the deal
        with self.analytics_service.repositories as uow:
            activities = uow.activities.get_by_deal_id(deal_id)
        
        if not activities:
            return {"error": f"No activities found for deal {deal_id}"}
        
        result = self.sentiment_service.get_sentiment_trends(activities, days)
        result.update({
            "deal_id": deal_id,
            "tool": "get_sentiment_trends"
        })
        
        return result
    
    def _is_sentiment_tool(self, tool_name: str) -> bool:
        """Check if tool requires sentiment analysis"""
        sentiment_tools = {
            "analyze_deal", 
            "analyze_deals_overview", 
            "get_deal_activities_with_sentiment",
            "analyze_text_sentiment", 
            "get_sentiment_trends"
        }
        return tool_name in sentiment_tools
    
    async def _ensure_sentiment_model_loaded(self):
        """Ensure sentiment model is loaded"""
        if self.sentiment_service and not self.sentiment_service.model_loaded:
            logger.info("Loading sentiment model for analysis...")
            await self.sentiment_service.initialize()
