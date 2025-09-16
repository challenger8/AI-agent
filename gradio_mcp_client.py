"""
Gradio client for Deal Activity Sentiment Analyzer MCP Server
"""
import asyncio
import json
import gradio as gr
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

if __name__ == "__main__":
    run_gradio_app()