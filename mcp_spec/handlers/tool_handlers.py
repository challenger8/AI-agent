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
from services.stt_service import get_stt_service
from config.settings import STTSettings
from utils.decorators import requires_sentiment

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
        self.logger = logging.getLogger(self.__class__.__name__)
        self.schemas = get_tool_schemas()
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main dispatcher for tool calls.
        Routes tool_name to appropriate handler method.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
            
        Returns:
            Tool result dictionary
        """
        # Ensure sentiment model loaded for sentiment tools
        if self._is_sentiment_tool(tool_name):
            await self._ensure_sentiment_model_loaded()
        
        # Route to appropriate handler
        handlers = {
            'analyze_deal': self._handle_analyze_deal,
            'analyze_deals_overview': self._handle_analyze_deals_overview,
            'get_deal_activities': self._handle_get_deal_activities,
            'analyze_portfolio_health': self._handle_analyze_portfolio_health,
            'analyze_text_sentiment': self._handle_analyze_text_sentiment,
            'get_sentiment_trends': self._handle_get_sentiment_trends,
            'transcribe_audio': self._handle_transcribe_audio,
            'transcribe_batch': self._handle_transcribe_batch,
            'list_audio_files': self._handle_list_audio_files,
            'validate_audio': self._handle_validate_audio,
        }
        
        handler = handlers.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            return await handler(arguments)
        except Exception as e:
            self.logger.error(f"Error in tool {tool_name}: {e}")
            return {"error": str(e)}
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
            ),
            Tool(
            name="transcribe_audio",
            description="Transcribe Persian audio file to text using Whisper AI",
            inputSchema=self.schemas["transcribe_audio"]
        ),
        Tool(
            name="transcribe_batch",
            description="Transcribe multiple Persian audio files in batch",
            inputSchema=self.schemas["transcribe_batch"]
        ),
        Tool(
            name="list_audio_files",
            description="List all audio files available in the audio_files directory",
            inputSchema=self.schemas["list_audio_files"]
        ),
        Tool(
            name="validate_audio",
            description="Validate audio file format and compatibility",
            inputSchema=self.schemas["validate_audio"]
        ),
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
    
    @requires_sentiment({"error": "Sentiment model not available"})
    async def _handle_analyze_text_sentiment(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # No need to check anymore! Decorator handles it
        text = arguments["text"]
        result = self.sentiment_service.analyze_text(text)
        result.update({
            "analyzed_at": datetime.now().isoformat(),
            "tool": "analyze_text_sentiment"
        })
        return result
    
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
    
    @requires_sentiment({"error": "Sentiment model not available"})
    async def _handle_get_sentiment_trends(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        # Clean! No boilerplate!
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
    # ============================================
    # STT (Speech-to-Text) Tool Handlers - NEW
    # ============================================
    
    async def _handle_transcribe_audio(self, arguments: dict) -> str:
        """Handle transcribe_audio tool"""
        audio_file = arguments.get("audio_file")
        language = arguments.get("language", "fa")
        
        if not audio_file:
            return json.dumps({"error": "audio_file is required"}, ensure_ascii=False)
        
        try:
            stt_service = get_stt_service()
            
            if not stt_service.model_loaded:
                await stt_service.initialize()
            
            audio_path = STTSettings.AUDIO_DIR / audio_file
            
            if not audio_path.exists():
                return json.dumps({
                    "error": f"Audio file not found: {audio_file}",
                    "audio_directory": str(STTSettings.AUDIO_DIR)
                }, ensure_ascii=False, indent=2)
            
            logger.info(f"Transcribing: {audio_file}")
            result = await stt_service.transcribe_audio(audio_path, language)
            
            response = {
                "success": True,
                "audio_file": audio_file,
                "transcription": result["transcription"],
                "language": result["language"],
                "duration_seconds": result["duration_seconds"],
                "model": result["model"]
            }
            
            return json.dumps(response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    async def _handle_transcribe_batch(self, arguments: dict) -> str:
        """Handle transcribe_batch tool"""
        audio_files = arguments.get("audio_files", [])
        language = arguments.get("language", "fa")
        
        if not audio_files:
            return json.dumps({"error": "audio_files required"}, ensure_ascii=False)
        
        try:
            stt_service = get_stt_service()
            
            if not stt_service.model_loaded:
                await stt_service.initialize()
            
            audio_paths = [STTSettings.AUDIO_DIR / f for f in audio_files]
            results = await stt_service.transcribe_batch(audio_paths, language)
            
            response = {
                "success": True,
                "total_files": len(audio_files),
                "results": results
            }
            
            return json.dumps(response, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    async def _handle_list_audio_files(self, arguments: dict) -> str:
        """Handle list_audio_files tool"""
        try:
            audio_dir = STTSettings.AUDIO_DIR
            
            if not audio_dir.exists():
                return json.dumps({
                    "audio_directory": str(audio_dir),
                    "exists": False,
                    "files": []
                }, ensure_ascii=False, indent=2)
            
            audio_files = []
            for ext in STTSettings.SUPPORTED_FORMATS:
                audio_files.extend(audio_dir.glob(f"*{ext}"))
            
            files_info = [{
                "name": f.name,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "extension": f.suffix
            } for f in audio_files]
            
            files_info.sort(key=lambda x: x["name"])
            
            return json.dumps({
                "audio_directory": str(audio_dir),
                "total_files": len(files_info),
                "files": files_info,
                "supported_formats": STTSettings.SUPPORTED_FORMATS
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)
    
    async def _handle_validate_audio(self, arguments: dict) -> str:
        """Handle validate_audio tool"""
        audio_file = arguments.get("audio_file")
        
        if not audio_file:
            return json.dumps({"error": "audio_file required"}, ensure_ascii=False)
        
        try:
            stt_service = get_stt_service()
            audio_path = STTSettings.AUDIO_DIR / audio_file
            
            result = stt_service.validate_audio_file(audio_path)
            
            return json.dumps({
                "audio_file": audio_file,
                "valid": result["valid"],
                "errors": result["errors"],
                "warnings": result["warnings"],
                "details": result["details"]
            }, ensure_ascii=False, indent=2)
            
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)