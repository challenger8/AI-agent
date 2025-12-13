#!/usr/bin/env python3
"""
Script to create all necessary Gradio MCP Client files
Run this script to automatically generate all required files
"""

import os
import sys
def create_gradio_mcp_client():
    """Create the main gradio_mcp_client.py file"""
    content = '''"""
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
        
    async def connect_to_server(self):
        """Connect to the MCP server"""
        try:
            # Import your MCP server
            from mcp_spec.server import create_mcp_server
            
            self.server = create_mcp_server()
            self.server_status = self.server.get_server_status()
            
            # Start the server in the background
            await self.server.initialize()
            self.connection_status = "Connected"
            
            return True, "Successfully connected to MCP server"
        except Exception as e:
            self.connection_status = "Connection Failed"
            return False, f"Failed to connect: {str(e)}"
    
    async def get_server_status(self):
        """Get current server status"""
        try:
            if hasattr(self, 'server'):
                self.server_status = self.server.get_server_status()
                return self.server_status
            return {"error": "Server not connected"}
        except Exception as e:
            return {"error": str(e)}
    
    async def analyze_sentiment(self, text: str, language: str = "fa"):
        """Analyze sentiment of given text"""
        try:
            if not hasattr(self, 'server'):
                return {"error": "Server not connected"}
            
            # Call the sentiment analysis method
            result = await self.server.analyze_text_sentiment(text, language)
            return result
        except Exception as e:
            return {"error": f"Sentiment analysis failed: {str(e)}"}
    
    async def get_deal_analytics(self, start_date: str = None, end_date: str = None):
        """Get deal analytics data"""
        try:
            if not hasattr(self, 'server'):
                return {"error": "Server not connected"}
            
            # Call analytics method
            result = await self.server.get_deal_analytics(start_date, end_date)
            return result
        except Exception as e:
            return {"error": f"Analytics retrieval failed: {str(e)}"}
    
    async def get_sentiment_trends(self, period: str = "30d"):
        """Get sentiment trends over time"""
        try:
            if not hasattr(self, 'server'):
                return {"error": "Server not connected"}
            
            result = await self.server.get_sentiment_trends(period)
            return result
        except Exception as e:
            return {"error": f"Trend analysis failed: {str(e)}"}

# Global MCP client instance
mcp_client = MCPClient()

def create_status_display(status_info):
    """Create a formatted status display"""
    if isinstance(status_info, dict) and "error" not in status_info:
        status_text = "🟢 **Server Status: Online**\\n\\n"
        for key, value in status_info.items():
            emoji = "✅" if value else "❌"
            status_text += f"{emoji} {key.replace('_', ' ').title()}: {value}\\n"
    else:
        status_text = "🔴 **Server Status: Offline**\\n\\n"
        if isinstance(status_info, dict) and "error" in status_info:
            status_text += f"Error: {status_info['error']}"
    
    return status_text

async def connect_server():
    """Connect to MCP server"""
    success, message = await mcp_client.connect_to_server()
    status = await mcp_client.get_server_status()
    
    return create_status_display(status), message

async def refresh_status():
    """Refresh server status"""
    status = await mcp_client.get_server_status()
    return create_status_display(status)

async def analyze_text_sentiment(text, language):
    """Analyze sentiment of input text"""
    if not text.strip():
        return "Please enter text to analyze", None
    
    result = await mcp_client.analyze_sentiment(text, language)
    
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
    else:
        fig = None
    
    # Format result text
    result_text = f"**Primary Sentiment:** {result.get('primary_sentiment', 'Unknown')}\\n"
    result_text += f"**Confidence:** {result.get('confidence', 0):.2%}\\n\\n"
    
    if "sentiment_scores" in result:
        result_text += "**Detailed Scores:**\\n"
        for sentiment, score in result["sentiment_scores"].items():
            result_text += f"- {sentiment.title()}: {score:.3f}\\n"
    
    return result_text, fig

async def get_analytics_data(start_date, end_date):
    """Get analytics data and create visualizations"""
    result = await mcp_client.get_deal_analytics(
        start_date.strftime("%Y-%m-%d") if start_date else None,
        end_date.strftime("%Y-%m-%d") if end_date else None
    )
    
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
    summary_text = "**Analytics Summary**\\n\\n"
    if "total_deals" in result:
        summary_text += f"Total Deals: {result['total_deals']}\\n"
    if "average_sentiment" in result:
        summary_text += f"Average Sentiment Score: {result['average_sentiment']:.3f}\\n"
    if "top_keywords" in result:
        summary_text += f"\\n**Top Keywords:**\\n"
        for keyword, count in result["top_keywords"].items():
            summary_text += f"- {keyword}: {count}\\n"
    
    return summary_text, fig_activity, fig_sentiment

async def get_trends_data(period):
    """Get sentiment trends data"""
    result = await mcp_client.get_sentiment_trends(period)
    
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
    summary = "**Trends Summary**\\n\\n"
    if "summary" in result:
        for key, value in result["summary"].items():
            summary += f"{key.replace('_', ' ').title()}: {value}\\n"
    
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
        show_error=True
    )

if __name__ == "__main__":
    run_gradio_app()
'''
    
    with open('gradio_mcp_client.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created: gradio_mcp_client.py")

def create_launch_gradio():
    """Create the launch_gradio.py file"""
    content = '''#!/usr/bin/env python3
"""
Launcher script for Gradio MCP Client
"""
import sys
import os
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment and paths"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        logger.info("Environment variables loaded successfully")
    except ImportError:
        logger.warning("python-dotenv not installed, using system environment variables")
    
    # Add current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    
    return current_dir

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'gradio',
        'pandas',
        'plotly',
        'transformers',
        'tensorflow'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is installed")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} is missing")
    
    if missing_packages:
        logger.error(f"Missing packages: {', '.join(missing_packages)}")
        logger.error("Please install missing packages using:")
        logger.error(f"pip install {' '.join(missing_packages)}")
        return False
    
    logger.info("All dependencies are satisfied")
    return True

def main():
    """Main launcher function"""
    logger.info("Starting Gradio MCP Client Launcher...")
    
    # Setup environment
    current_dir = setup_environment()
    logger.info(f"Working directory: {current_dir}")
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Exiting...")
        return 1
    
    try:
        # Import and run the Gradio app
        from gradio_mcp_client import run_gradio_app
        
        logger.info("Launching Gradio interface...")
        logger.info("=" * 50)
        logger.info("🚀 Deal Activity Sentiment Analyzer")
        logger.info("🌐 Interface will be available at: http://localhost:7860")
        logger.info("🔧 Make sure your MCP server is ready to accept connections")
        logger.info("=" * 50)
        
        # Run the Gradio app
        run_gradio_app()
        
    except KeyboardInterrupt:
        logger.info("\\n👋 Gradio client stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Error starting Gradio client: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code or 0)
'''
    
    with open('launch_gradio.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created: launch_gradio.py")

def create_requirements():
    """Create requirements_gradio.txt file"""
    content = '''# Requirements for Gradio MCP Client
gradio>=6.0.0
pandas>=1.5.0
plotly>=5.0.0
python-dotenv>=1.0.0
asyncio-compat>=0.1.0

# Your existing MCP server dependencies should already be installed
# transformers
# tensorflow
# torch
# paramiko
# psycopg2-binary
# matplotlib
# numpy
'''
    
    with open('requirements_gradio.txt', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created: requirements_gradio.txt")

def create_install_script():
    """Create install script"""
    content = '''#!/usr/bin/env python3
"""
Install script for Gradio MCP Client
"""
import subprocess
import sys

def install_requirements():
    """Install required packages"""
    print("Installing Gradio MCP Client requirements...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "gradio>=6.0.0",
            "pandas>=1.5.0", 
            "plotly>=5.0.0",
            "python-dotenv>=1.0.0"
        ])
        print("✅ All requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

if __name__ == "__main__":
    success = install_requirements()
    if success:
        print("\\n🚀 Ready to run!")
        print("Run: python launch_gradio.py")
    else:
        print("\\n❌ Installation failed. Please install manually:")
        print("pip install gradio pandas plotly python-dotenv")
'''
    
    with open('install_gradio.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ Created: install_gradio.py")

def main():
    """Main function to create all files"""
    print("Creating Gradio MCP Client files...")
    print("=" * 40)
    
    try:
        create_gradio_mcp_client()
        create_launch_gradio()
        create_requirements()
        create_install_script()
        
        print("=" * 40)
        print("🎉 All files created successfully!")
        print()
        print("📋 Next steps:")
        print("1. Install dependencies: python install_gradio.py")
        print("2. Run the interface: python launch_gradio.py")
        print("3. Open browser: http://localhost:7860")
        print()
        print("📁 Files created:")
        print("- gradio_mcp_client.py (main interface)")
        print("- launch_gradio.py (launcher script)")
        print("- requirements_gradio.txt (dependencies)")
        print("- install_gradio.py (installer)")
        
    except Exception as e:
        print(f"❌ Error creating files: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code or 0)