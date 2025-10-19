"""
Gradio client for Deal Activity Sentiment Analyzer MCP Server
"""
import asyncio
import json
from config.settings import STTSettings
from pathlib import Path
import shutil
import gradio as gr
import pandas as pd
from typing import Dict, List, Tuple, Any
import logging
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class RAGSearchManager:
    """Manages RAG search operations in Gradio"""
    
    def __init__(self):
        self.rag_service = None
        self.initialized = False
    
    async def initialize_rag(self):
        """Initialize RAG search service"""
        try:
            from services.rag_search_service import RAGSearchService
            from database.database import create_database_manager
            from models.repositories import create_repositories
            
            # Initialize database and repositories
            db_manager = create_database_manager()
            repositories = create_repositories(db_manager)
            
            # Initialize RAG service
            self.rag_service = RAGSearchService(repositories)
            await self.rag_service.initialize()
            
            # Index all data
            await self.rag_service.index_all_data()
            
            self.initialized = True
            logger.info("✅ RAG service initialized and indexed")
            return True
        except Exception as e:
            logger.error(f"❌ RAG initialization failed: {e}")
            return False
    
    def search(self, query: str, search_type: str = "all", n_results: int = 5) -> Dict[str, Any]:
        """
        Perform semantic search
        
        Args:
            query: Search query
            search_type: 'all', 'deals', 'activities', or 'agents'
            n_results: Number of results
            
        Returns:
            Search results
        """
        if not self.initialized or not self.rag_service:
            return {'error': 'RAG service not initialized'}
        
        try:
            if search_type == 'deals':
                results = self.rag_service.search_deals(query, n_results)
                return self._format_results(results, 'deals')
            elif search_type == 'activities':
                results = self.rag_service.search_activities(query, n_results)
                return self._format_results(results, 'activities')
            elif search_type == 'agents':
                results = self.rag_service.search_agents(query, n_results)
                return self._format_results(results, 'agents')
            else:  # all
                return self.rag_service.search(query, n_results)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {'error': str(e)}
    
    def _format_results(self, results: List[Dict], result_type: str) -> Dict[str, Any]:
        """Format results for display"""
        return {
            'status': 'success',
            'query': '',
            'results': {result_type: results},
            'total_matches': len(results)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get index statistics"""
        if not self.initialized or not self.rag_service:
            return {'error': 'RAG service not initialized'}
        
        try:
            return self.rag_service.get_index_stats()
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {'error': str(e)}


# Global RAG manager instance
rag_manager = RAGSearchManager()


def format_search_results(results: Dict[str, Any]) -> str:
    """Format search results for Gradio display"""
    
    if 'error' in results:
        return f"❌ **Error:** {results['error']}"
    
    if results.get('status') == 'error':
        return f"❌ **Search Error:** {results.get('error', 'Unknown error')}"
    
    output = f"### 🔍 Search Results\n\n"
    output += f"**Query:** {results.get('query', 'N/A')}\n"
    output += f"**Total Matches:** {results.get('total_matches', 0)}\n\n"
    
    results_data = results.get('results', {})
    
    for entity_type in ['deals', 'activities', 'agents']:
        matches = results_data.get(entity_type, [])
        
        if matches:
            output += f"## 📄 {entity_type.upper()} ({len(matches)} matches)\n\n"
            
            for i, match in enumerate(matches, 1):
                output += f"**{i}. {entity_type[:-1].title()}**\n"
                output += f"- **ID:** {match.get('id')}\n"
                output += f"- **Text:** {match.get('text', 'N/A')[:100]}...\n"
                output += f"- **Similarity Score:** {match.get('similarity_score', 0):.4f}\n"
                
                # Show metadata
                metadata = match.get('metadata', {})
                if metadata:
                    output += f"- **Details:** {', '.join(f'{k}: {v}' for k, v in list(metadata.items())[:3])}\n"
                
                output += "\n"
    
    return output


def format_stats(stats_result: Dict[str, Any]) -> str:
    """Format index statistics for display"""
    
    if 'error' in stats_result:
        return f"❌ **Error:** {stats_result['error']}"
    
    stats = stats_result.get('stats', {})
    
    output = "### 📊 Index Statistics\n\n"
    output += f"**Total Indexed Documents:** {stats.get('total_documents', 0)}\n\n"
    
    output += "#### Collections\n\n"
    
    for collection_name in ['deals', 'activities', 'agents']:
        collection_stats = stats.get(collection_name, {})
        count = collection_stats.get('document_count', 0)
        output += f"- **{collection_name.title()}:** {count} documents\n"
    
    return output


def rag_search_handler(query: str, search_type: str, n_results: int) -> Tuple[str, str]:
    """Handle RAG search from Gradio interface"""
    
    if not query or query.strip() == "":
        return "❌ **Error:** Please enter a search query", ""
    
    if not rag_manager.initialized:
        return "❌ **Error:** RAG service not initialized. Please initialize first.", ""
    
    # Perform search
    results = rag_manager.search(query, search_type, n_results)
    
    # Format results
    formatted_results = format_search_results(results)
    
    # Extract plain text for export
    plain_text = f"Search Query: {query}\n"
    plain_text += f"Search Type: {search_type}\n"
    plain_text += f"Results: {results.get('total_matches', 0)} matches\n\n"
    
    for entity_type in ['deals', 'activities', 'agents']:
        matches = results.get('results', {}).get(entity_type, [])
        if matches:
            plain_text += f"\n{entity_type.upper()}:\n"
            for match in matches:
                plain_text += f"- {match.get('text', 'N/A')}\n"
    
    return formatted_results, plain_text


def initialize_rag_handler() -> str:
    """Initialize RAG service"""
    try:
        # Run async initialization in event loop
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(rag_manager.initialize_rag())
    
    if success:
        return "✅ **RAG Service Initialized**\n\nData indexed and ready for semantic search."
    else:
        return "❌ **Initialization Failed**\n\nCould not initialize RAG service. Check logs for details."


def get_stats_handler() -> str:
    """Get and display index statistics"""
    stats = rag_manager.get_stats()
    return format_stats(stats)


def create_rag_search_tab() -> None:
    """
    Create RAG search tab in Gradio interface
    
    Add this to the gr.Blocks() in gradio_mcp_client.py
    """
    
    with gr.Tab("🔍 Semantic Search (RAG)"):
        gr.HTML("<h2>🔍 Semantic Search</h2>")
        gr.HTML("<p>Search through your CRM data using natural language. Find deals, activities, and agents semantically.</p>")
        
        # Initialization section
        with gr.Group(label="🚀 Initialization"):
            with gr.Row():
                init_status = gr.Markdown("ℹ️ RAG service not initialized yet")
                init_btn = gr.Button("Initialize RAG Service", variant="primary", size="lg")
            
            stats_output = gr.Markdown("Waiting for initialization...")
        
        # Search section
        with gr.Group(label="🔎 Search"):
            with gr.Row():
                search_query = gr.Textbox(
                    label="Search Query",
                    placeholder="e.g., 'pricing concerns', 'implementation timeline', 'Sarah Johnson'",
                    lines=2
                )
            
            with gr.Row():
                search_type = gr.Dropdown(
                    choices=[
                        ("All (Deals + Activities + Agents)", "all"),
                        ("Deals Only", "deals"),
                        ("Activities Only", "activities"),
                        ("Agents Only", "agents")
                    ],
                    value="all",
                    label="Search Type"
                )
                
                n_results = gr.Slider(
                    minimum=1,
                    maximum=20,
                    value=5,
                    step=1,
                    label="Number of Results"
                )
                
                search_btn = gr.Button("Search", variant="primary", size="lg")
            
            # Results section
            search_results = gr.Markdown(label="Search Results", value="Run a search to see results...")
            
            # Export section
            with gr.Accordion("📥 Export Results", open=False):
                export_text = gr.Textbox(
                    label="Export as Text",
                    lines=10,
                    max_lines=20,
                    interactive=False
                )
                download_btn = gr.Button("Download as TXT", variant="secondary")
        
        # Event handlers
        init_btn.click(
            initialize_rag_handler,
            outputs=[init_status]
        ).then(
            get_stats_handler,
            outputs=[stats_output]
        )
        
        search_btn.click(
            rag_search_handler,
            inputs=[search_query, search_type, n_results],
            outputs=[search_results, export_text]
        )
        
        # Auto-get stats on initialization
        init_btn.click(
            get_stats_handler,
            outputs=[stats_output]
        )

class MCPClient:
    """MCP Client for communicating with the deal activity sentiment analyzer server"""
    
    def __init__(self):
        self.server_status = {}
        self.connection_status = "Disconnected"
        self.server = None
        
    async def connect_to_server(self):
        """Connect to the MCP server - FINAL FIXED VERSION"""
        try:
            # Import your MCP server
            from mcp_spec.server import create_mcp_server
            
            logger.info("Creating MCP server instance...")
            self.server = create_mcp_server()
            
            # IMPORTANT FIX: initialize_services() is async - must await it!
            logger.info("Initializing MCP server services (this may take a while)...")
            try:
                initialization_result = await self.server.initialize_services()  # ← Added await!
                logger.info(f"Initialization result: {initialization_result}")
            except Exception as init_error:
                logger.error(f"Initialization error: {init_error}")
                # Continue anyway - some services might still work
                initialization_result = False
            
            # Wait additional time for models to fully load
            logger.info("Waiting for services to complete loading...")
            await asyncio.sleep(8)  # Give time for Persian BERT to load
            
            # Get server status
            self.server_status = self.server.get_server_status()
            self.connection_status = "Connected"
            
            logger.info(f"Final server status: {self.server_status}")
            
            # Check what's actually available
            services_available = []
            if self.server_status.get('database_connected', False):
                services_available.append("Database")
            if self.server_status.get('sentiment_available', False):
                services_available.append("Sentiment Analysis")
            if self.server_status.get('analytics_ready', False):
                services_available.append("Analytics")
            
            if services_available:
                message = f"Connected successfully! Available services: {', '.join(services_available)}"
            else:
                message = "Connected to server, but no services fully initialized. Check environment variables and logs."
            
            return True, message
            
        except Exception as e:
            logger.error(f"Connection failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.connection_status = "Connection Failed"
            return False, f"Failed to connect: {str(e)}"
    
    async def get_server_status(self):
        """Get current server status"""
        try:
            if self.server is not None:
                self.server_status = self.server.get_server_status()
                return self.server_status
            return {"error": "Server not connected"}
        except Exception as e:
            logger.error(f"Error getting server status: {e}")
            return {"error": str(e)}
    
    async def analyze_sentiment(self, text: str, language: str = "fa"):
        """Analyze sentiment - ENHANCED VERSION"""
        try:
            if self.server is None:
                return {"error": "Server not connected"}
            
            logger.info(f"Analyzing sentiment for text: {text[:50]}...")
            
            # Check if we have sentiment service
            if hasattr(self.server, 'sentiment_service') and self.server.sentiment_service:
                logger.info("Found sentiment_service, trying methods...")
                
                # Try common method names
                methods_to_try = [
                    ('analyze_sentiment', [text, language]),
                    ('analyze_sentiment', [text]),
                    ('analyze_text', [text]),
                    ('analyze', [text]),
                    ('predict', [text])
                ]
                
                for method_name, args in methods_to_try:
                    if hasattr(self.server.sentiment_service, method_name):
                        try:
                            method = getattr(self.server.sentiment_service, method_name)
                            logger.info(f"Trying {method_name} with args: {args}")
                            result = await self._call_async_safe(method, *args)
                            logger.info(f"Success! Result: {result}")
                            
                            # Normalize the result format
                            if isinstance(result, dict):
                                return result
                            elif isinstance(result, list) and result:
                                # Handle transformers pipeline format
                                return {"label": result[0].get('label', 'Unknown'), "score": result[0].get('score', 0)}
                            else:
                                return {"result": str(result)}
                                
                        except Exception as e:
                            logger.warning(f"Method {method_name} failed: {e}")
                            continue
                
                # Try accessing pipeline directly if available
                if hasattr(self.server.sentiment_service, 'pipeline'):
                    try:
                        logger.info("Trying pipeline directly")
                        result = self.server.sentiment_service.pipeline(text)
                        logger.info(f"Pipeline result: {result}")
                        return {"label": result[0]['label'], "score": result[0]['score']}
                    except Exception as e:
                        logger.warning(f"Direct pipeline access failed: {e}")
                
                return {"error": "Sentiment service found but no working methods available"}
            
            else:
                # If no sentiment_service, return helpful mock data
                logger.warning("No sentiment_service found, returning mock analysis")
                
                # Simple keyword-based mock sentiment for Persian text
                positive_words = ['عالی', 'خوب', 'بهترین', 'موفق', 'مناسب', 'قبول']
                negative_words = ['بد', 'ضعیف', 'نامناسب', 'رد', 'مشکل']
                
                text_lower = text.lower()
                pos_count = sum(1 for word in positive_words if word in text_lower)
                neg_count = sum(1 for word in negative_words if word in text_lower)
                
                if pos_count > neg_count:
                    sentiment = "POSITIVE"
                    score = 0.7 + (pos_count * 0.1)
                elif neg_count > pos_count:
                    sentiment = "NEGATIVE" 
                    score = 0.3 - (neg_count * 0.1)
                else:
                    sentiment = "NEUTRAL"
                    score = 0.5
                
                return {
                    "label": sentiment,
                    "score": min(max(score, 0.0), 1.0),
                    "note": "Mock analysis - sentiment service not fully initialized"
                }
                    
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Sentiment analysis failed: {str(e)}"}
    
    async def _call_async_safe(self, method, *args, **kwargs):
        """Safely call a method that might be async or sync"""
        try:
            # Try calling as async first
            if asyncio.iscoroutinefunction(method):
                return await method(*args, **kwargs)
            else:
                # Call synchronously
                return method(*args, **kwargs)
        except Exception as e:
            logger.error(f"Method call failed: {e}")
            raise
    
    async def get_deal_analytics(self, start_date: str = None, end_date: str = None):
        """Get deal analytics data"""
        try:
            if self.server is None:
                return {"error": "Server not connected"}
            
            logger.info(f"Getting deal analytics from {start_date} to {end_date}")
            
            # Check if server has analytics service
            if hasattr(self.server, 'analytics_service') and self.server.analytics_service:
                result = await self.server.analytics_service.get_deal_analytics(start_date, end_date)
                return result
            elif hasattr(self.server, 'get_deal_analytics'):
                result = await self.server.get_deal_analytics(start_date, end_date)
                return result
            else:
                # Return mock data for now
                return {
                    "total_deals": 150,
                    "average_sentiment": 0.65,
                    "daily_activity": [
                        {"date": "2025-09-10", "deal_count": 12},
                        {"date": "2025-09-11", "deal_count": 15},
                        {"date": "2025-09-12", "deal_count": 18},
                        {"date": "2025-09-13", "deal_count": 14},
                        {"date": "2025-09-14", "deal_count": 20},
                        {"date": "2025-09-15", "deal_count": 16},
                        {"date": "2025-09-16", "deal_count": 22}
                    ],
                    "sentiment_distribution": {
                        "positive": 60,
                        "neutral": 25,
                        "negative": 15
                    },
                    "top_keywords": {
                        "قرارداد": 45,
                        "خرید": 38,
                        "فروش": 32,
                        "تأیید": 28,
                        "موافقت": 25
                    }
                }
                
        except Exception as e:
            logger.error(f"Analytics error: {e}")
            return {"error": f"Analytics retrieval failed: {str(e)}"}
    
    async def get_sentiment_trends(self, period: str = "30d"):
        """Get sentiment trends over time"""
        try:
            if self.server is None:
                return {"error": "Server not connected"}
            
            logger.info(f"Getting sentiment trends for period: {period}")
            
            # Check if server has the method
            if hasattr(self.server, 'get_sentiment_trends'):
                result = await self.server.get_sentiment_trends(period)
                return result
            else:
                # Return mock trends data
                import random
                from datetime import datetime, timedelta
                
                days = int(period.rstrip('d'))
                dates = []
                trends = []
                
                for i in range(days):
                    date = datetime.now() - timedelta(days=days-i)
                    dates.append(date.strftime("%Y-%m-%d"))
                    
                    # Generate realistic trend data
                    base_positive = 0.6 + random.uniform(-0.1, 0.1)
                    base_neutral = 0.25 + random.uniform(-0.05, 0.05)
                    base_negative = 0.15 + random.uniform(-0.05, 0.05)
                    
                    trends.append({
                        "date": date.strftime("%Y-%m-%d"),
                        "positive": max(0, min(1, base_positive)),
                        "neutral": max(0, min(1, base_neutral)),
                        "negative": max(0, min(1, base_negative))
                    })
                
                return {
                    "trends": trends,
                    "summary": {
                        "average_positive": sum(t["positive"] for t in trends) / len(trends),
                        "average_negative": sum(t["negative"] for t in trends) / len(trends),
                        "trend_direction": "improving" if trends[-1]["positive"] > trends[0]["positive"] else "declining"
                    }
                }
                
        except Exception as e:
            logger.error(f"Trends error: {e}")
            return {"error": f"Trend analysis failed: {str(e)}"}
    async def transcribe_audio_file(self, audio_file_path: str, language: str = "fa"):
        """Transcribe audio file"""
        try:
            if not hasattr(self, 'server') or not self.server.tool_handlers:
                return {"error": "Server not connected"}
            
            # Get filename from path
            audio_file = Path(audio_file_path).name
            
            # Call transcribe tool via MCP
            result = await self.server.tool_handlers.handle_tool_call(
                'transcribe_audio',
                {'audio_file': audio_file, 'language': language}
            )
            
            if result and len(result) > 0:
                import json
                return json.loads(result[0].text)
            
            return {"error": "No response from server"}
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return {"error": str(e)}
    
    async def list_audio_files(self):
        """List available audio files"""
        try:
            if not hasattr(self, 'server') or not self.server.tool_handlers:
                return {"error": "Server not connected"}
            
            result = await self.server.tool_handlers.handle_tool_call(
                'list_audio_files',
                {}
            )
            
            if result and len(result) > 0:
                import json
                return json.loads(result[0].text)
            
            return {"error": "No response from server"}
            
        except Exception as e:
            logger.error(f"List files error: {e}")
            return {"error": str(e)}

# Global MCP client instance
mcp_client = MCPClient()

def create_status_display(status_info):
    """Create a formatted status display"""
    if isinstance(status_info, dict) and "error" not in status_info:
        status_text = "🟢 **Server Status: Online**\n\n"
        for key, value in status_info.items():
            emoji = "✅" if value else "❌"
            status_text += f"{emoji} {key.replace('_', ' ').title()}: {value}\n"
    else:
        status_text = "🔴 **Server Status: Offline**\n\n"
        if isinstance(status_info, dict) and "error" in status_info:
            status_text += f"Error: {status_info['error']}"
    
    return status_text

def connect_server():
    """Connect to MCP server - synchronous wrapper"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    success, message = loop.run_until_complete(mcp_client.connect_to_server())
    status = loop.run_until_complete(mcp_client.get_server_status())
    
    return create_status_display(status), message

def refresh_status():
    """Refresh server status - synchronous wrapper"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    status = loop.run_until_complete(mcp_client.get_server_status())
    return create_status_display(status)

def analyze_text_sentiment(text, language):
    """Analyze sentiment of input text - synchronous wrapper"""
    if not text.strip():
        return "Please enter text to analyze", None
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(mcp_client.analyze_sentiment(text, language))
    
    if "error" in result:
        return f"Error: {result['error']}", None
    
    # Create visualization
    if "sentiment_scores" in result:
        scores = result["sentiment_scores"]
        labels = list(scores.keys())
        values = list(scores.values())
        
        fig = px.bar(
            x=labels, 
            y=values,
            title="Sentiment Analysis Results",
            labels={"x": "Sentiment", "y": "Confidence Score"},
            color=values,
            color_continuous_scale="RdYlGn"
        )
        fig.update_layout(showlegend=False)
    elif "label" in result and "score" in result:
        # Handle different result format
        fig = px.bar(
            x=[result["label"]], 
            y=[result["score"]],
            title="Sentiment Analysis Results",
            labels={"x": "Sentiment", "y": "Confidence Score"}
        )
    else:
        fig = None
    
    # Format result text
    if "primary_sentiment" in result:
        result_text = f"**Primary Sentiment:** {result.get('primary_sentiment', 'Unknown')}\n"
        result_text += f"**Confidence:** {result.get('confidence', 0):.2%}\n\n"
    elif "label" in result:
        result_text = f"**Sentiment:** {result['label']}\n"
        result_text += f"**Score:** {result.get('score', 0):.3f}\n\n"
    else:
        result_text = f"**Result:** {result}\n"
    
    if "sentiment_scores" in result:
        result_text += "**Detailed Scores:**\n"
        for sentiment, score in result["sentiment_scores"].items():
            result_text += f"- {sentiment.title()}: {score:.3f}\n"
    
    return result_text, fig

def get_analytics_data(start_date, end_date):
    """Get analytics data and create visualizations - synchronous wrapper"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(mcp_client.get_deal_analytics(
        start_date.strftime("%Y-%m-%d") if start_date else None,
        end_date.strftime("%Y-%m-%d") if end_date else None
    ))
    
    if "error" in result:
        return f"Error: {result['error']}", None, None
    
    # Create deal activity chart
    if "daily_activity" in result:
        daily_data = result["daily_activity"]
        df_daily = pd.DataFrame(daily_data)
        
        fig_activity = px.line(
            df_daily, 
            x="date", 
            y="deal_count",
            title="Daily Deal Activity",
            labels={"date": "Date", "deal_count": "Number of Deals"}
        )
    else:
        fig_activity = None
    
    # Create sentiment distribution chart
    if "sentiment_distribution" in result:
        sentiment_data = result["sentiment_distribution"]
        
        fig_sentiment = px.pie(
            values=list(sentiment_data.values()),
            names=list(sentiment_data.keys()),
            title="Overall Sentiment Distribution"
        )
    else:
        fig_sentiment = None
    
    # Format summary text
    summary_text = "**Analytics Summary**\n\n"
    if "total_deals" in result:
        summary_text += f"Total Deals: {result['total_deals']}\n"
    if "average_sentiment" in result:
        summary_text += f"Average Sentiment Score: {result['average_sentiment']:.3f}\n"
    if "top_keywords" in result:
        summary_text += f"\n**Top Keywords:**\n"
        for keyword, count in result["top_keywords"].items():
            summary_text += f"- {keyword}: {count}\n"
    
    return summary_text, fig_activity, fig_sentiment

def get_trends_data(period):
    """Get sentiment trends data - synchronous wrapper"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(mcp_client.get_sentiment_trends(period))
    
    if "error" in result:
        return f"Error: {result['error']}", None
    
    if "trends" in result:
        trends_data = result["trends"]
        df_trends = pd.DataFrame(trends_data)
        
        fig = px.line(
            df_trends,
            x="date",
            y=["positive", "negative", "neutral"],
            title=f"Sentiment Trends - Last {period}",
            labels={"value": "Sentiment Score", "date": "Date"}
        )
        fig.update_layout(hovermode="x unified")
    else:
        fig = None
    
    # Format summary
    summary = "**Trends Summary**\n\n"
    if "summary" in result:
        for key, value in result["summary"].items():
            if isinstance(value, float):
                summary += f"{key.replace('_', ' ').title()}: {value:.3f}\n"
            else:
                summary += f"{key.replace('_', ' ').title()}: {value}\n"
    
    return summary, fig
def upload_audio_file(file):
    """Handle audio file upload"""
    if file is None:
        return "❌ No file uploaded", None
    
    try:
        # Copy file to audio_files directory
        audio_dir = STTSettings.AUDIO_DIR
        audio_dir.mkdir(exist_ok=True)
        
        # Get filename
        file_path = Path(file.name)
        dest_path = audio_dir / file_path.name
        
        # Copy file
        shutil.copy(file.name, dest_path)
        
        return f"✅ Uploaded: {file_path.name}", str(dest_path)
        
    except Exception as e:
        return f"❌ Upload failed: {str(e)}", None


def list_available_audio():
    """List available audio files"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(mcp_client.list_audio_files())
    
    if "error" in result:
        return f"❌ Error: {result['error']}"
    
    files = result.get('files', [])
    
    if not files:
        return "📭 No audio files found in audio_files/ directory"
    
    output = f"## 📂 Available Audio Files ({len(files)} total)\n\n"
    
    for file in files:
        output += f"- **{file['name']}** ({file['size_mb']}MB)\n"
    
    return output

def upload_audio_file(file):
    """Handle audio file upload"""
    if file is None:
        return "❌ No file uploaded", None
    
    try:
        # Copy file to audio_files directory
        audio_dir = STTSettings.AUDIO_DIR
        audio_dir.mkdir(exist_ok=True)
        
        # Get filename
        file_path = Path(file.name)
        dest_path = audio_dir / file_path.name
        
        # Copy file
        import shutil
        shutil.copy(file.name, dest_path)
        
        return f"✅ Uploaded: {file_path.name}", str(dest_path)
        
    except Exception as e:
        return f"❌ Upload failed: {str(e)}", None

def transcribe_audio(audio_file_path, language):
    """Transcribe audio file - synchronous wrapper"""
    if not audio_file_path:
        return "❌ No audio file selected", None
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        mcp_client.transcribe_audio_file(audio_file_path, language)
    )
    
    if "error" in result:
        return f"❌ Error: {result['error']}", None
    
    if result.get("success"):
        # Format output
        output = f"""
## ✅ Transcription Successful

**File:** {result.get('audio_file')}  
**Language:** {result.get('language')}  
**Duration:** {result.get('duration_seconds', 0):.2f} seconds  
**Model:** {result.get('model')}

### 📝 Transcription:

{result.get('transcription')}
"""
        return output, result.get('transcription')
    
    return "❌ Transcription failed", None

def list_available_audio():
    """List available audio files"""
    try:
        # Check if server is connected
        if not hasattr(mcp_client, 'server') or mcp_client.server is None:
            return "⚠️ **Server not connected**\n\nPlease connect to the server first in the 'Server Connection' tab."
        
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(mcp_client.list_audio_files())
    
    if "error" in result:
        return f"❌ Error: {result['error']}"
    
    files = result.get('files', [])
    
    if not files:
        return "📭 No audio files found in audio_files/ directory"
    
    output = f"## 📂 Available Audio Files ({len(files)} total)\n\n"
    
    for file in files:
        output += f"- **{file['name']}** ({file['size_mb']}MB)\n"
    
    return output
def list_audio_with_autoconnect():
    """List audio files, auto-connect if needed"""
    # Check if connected, if not try to connect
    if not hasattr(mcp_client, 'server') or mcp_client.server is None:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        success, message = loop.run_until_complete(mcp_client.connect_to_server())
        if not success:
            return f"⚠️ **Could not connect to server**\n\n{message}"
    
    return list_available_audio()
def transcribe_audio(audio_file_path, language):
    """Transcribe audio file - synchronous wrapper"""
    if not audio_file_path:
        return "❌ No audio file selected", None
    
    # Check if server is connected
    if not hasattr(mcp_client, 'server') or mcp_client.server is None:
        return "⚠️ **Server not connected**\n\nPlease connect to the server first in the 'Server Connection' tab.", None
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        mcp_client.transcribe_audio_file(audio_file_path, language)
    )
    
    if "error" in result:
        return f"❌ Error: {result['error']}", None
    
    if result.get("success"):
        # Format output
        output = f"""
## ✅ Transcription Successful

**File:** {result.get('audio_file')}  
**Language:** {result.get('language')}  
**Duration:** {result.get('duration_seconds', 0):.2f} seconds  
**Model:** {result.get('model')}

### 📝 Transcription:

{result.get('transcription')}
"""
        return output, result.get('transcription')
    
    return "❌ Transcription failed", None
# Create Gradio interface
with gr.Blocks(title="Deal Activity Sentiment Analyzer", theme=gr.themes.Soft()) as app:
    gr.HTML("<h1>🏢 Deal Activity Sentiment Analyzer</h1>")
    gr.HTML("<p>Analyze sentiment and activity patterns in deal-related communications</p>")
    
    with gr.Tab("🔌 Server Connection"):
        with gr.Row():
            with gr.Column(scale=2):
                server_status = gr.Markdown("🔴 **Server Status: Disconnected**")
                connection_msg = gr.Textbox(label="Connection Message", interactive=False)
            
            with gr.Column(scale=1):
                connect_btn = gr.Button("Connect to Server", variant="primary")
                refresh_btn = gr.Button("Refresh Status")
        
        # Event handlers
        connect_btn.click(connect_server, outputs=[server_status, connection_msg])
        refresh_btn.click(refresh_status, outputs=[server_status])
    
    with gr.Tab("📝 Sentiment Analysis"):
        with gr.Row():
            with gr.Column():
                text_input = gr.Textbox(
                    label="Text to Analyze",
                    placeholder="Enter text in Persian or English...",
                    lines=5
                )
                language_select = gr.Dropdown(
                    choices=[("Persian", "fa"), ("English", "en")],
                    value="fa",
                    label="Language"
                )
                analyze_btn = gr.Button("Analyze Sentiment", variant="primary")
            
            with gr.Column():
                sentiment_result = gr.Markdown(label="Analysis Result")
                sentiment_chart = gr.Plot(label="Sentiment Scores")
        
        # Event handler
        analyze_btn.click(
            analyze_text_sentiment,
            inputs=[text_input, language_select],
            outputs=[sentiment_result, sentiment_chart]
        )
    
    with gr.Tab("📊 Deal Analytics"):
        with gr.Row():
            start_date = gr.DateTime(
                label="Start Date",
                value=datetime.now() - timedelta(days=30)
            )
            end_date = gr.DateTime(
                label="End Date",
                value=datetime.now()
            )
            analytics_btn = gr.Button("Get Analytics", variant="primary")
        
        with gr.Row():
            analytics_summary = gr.Markdown(label="Summary")
        
        with gr.Row():
            activity_chart = gr.Plot(label="Deal Activity")
            sentiment_dist = gr.Plot(label="Sentiment Distribution")
        
        # Event handler
        analytics_btn.click(
            get_analytics_data,
            inputs=[start_date, end_date],
            outputs=[analytics_summary, activity_chart, sentiment_dist]
        )
    
    with gr.Tab("📈 Sentiment Trends"):
        with gr.Row():
            period_select = gr.Dropdown(
                choices=[
                    ("Last 7 days", "7d"),
                    ("Last 30 days", "30d"),
                    ("Last 90 days", "90d"),
                    ("Last 6 months", "180d")
                ],
                value="30d",
                label="Time Period"
            )
            trends_btn = gr.Button("Get Trends", variant="primary")
        
        with gr.Row():
            trends_summary = gr.Markdown(label="Trends Summary")
        
        with gr.Row():
            trends_chart = gr.Plot(label="Sentiment Trends Over Time")
        
        # Event handler
        trends_btn.click(
            get_trends_data,
            inputs=[period_select],
            outputs=[trends_summary, trends_chart]
        )
    with gr.Tab("🎤 Audio Transcription (STT)"):
        gr.Markdown("""
        ## Speech-to-Text for Persian Audio
        Upload audio files or transcribe existing files from the audio_files/ directory.
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📤 Upload Audio File")
                
                audio_upload = gr.File(
                    label="Upload Audio",
                    file_types=[".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"],
                    type="filepath"
                )
                
                upload_btn = gr.Button("Upload", variant="secondary")
                upload_status = gr.Markdown("")
                uploaded_path = gr.Textbox(visible=False)
                
                gr.Markdown("---")
                
                gr.Markdown("### 📂 Available Files")
                refresh_files_btn = gr.Button("Refresh File List", variant="secondary")
                files_list = gr.Markdown("")
            
            with gr.Column(scale=2):
                gr.Markdown("### 🎯 Transcribe Audio")
                
                audio_file_input = gr.Textbox(
                    label="Audio File Path",
                    placeholder="Path to audio file or upload above",
                    lines=1
                )
                
                language_audio = gr.Dropdown(
                    choices=[("Persian (فارسی)", "fa"), ("English", "en")],
                    value="fa",
                    label="Language"
                )
                
                transcribe_btn = gr.Button("🎤 Transcribe Audio", variant="primary", size="lg")
                
                transcription_output = gr.Markdown(label="Transcription Result")
                
                with gr.Accordion("📥 Download Transcription", open=False):
                    transcription_text = gr.Textbox(
                        label="Plain Text",
                        lines=10,
                        max_lines=20
                    )
                    download_btn = gr.Button("Download as TXT", variant="secondary")
        
        # Event handlers for STT tab
        upload_btn.click(
            upload_audio_file,
            inputs=[audio_upload],
            outputs=[upload_status, uploaded_path]
        )
        
        # Auto-fill path when file uploaded
        uploaded_path.change(
            lambda x: x if x else "",
            inputs=[uploaded_path],
            outputs=[audio_file_input]
        )
        
        refresh_files_btn.click(
            list_audio_with_autoconnect,
            outputs=[files_list]
        )
        
        transcribe_btn.click(
            transcribe_audio,
            inputs=[audio_file_input, language_audio],
            outputs=[transcription_output, transcription_text]
        )
        
        # Auto-refresh file list on tab load
        # app.load(list_available_audio, outputs=[files_list])

def run_gradio_app():
    """Run the Gradio application"""
    print("Starting Gradio interface...")
    print("Access the interface at: http://localhost:7860")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True,
        show_error=True
    )
    app.load(connect_server, outputs=[server_status, connection_msg])

if __name__ == "__main__":
    run_gradio_app()