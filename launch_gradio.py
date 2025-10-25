#!/usr/bin/env python3
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

def main():
    """Main launcher function"""
    logger.info("Starting Gradio MCP Client Launcher...")
    
    # Setup environment
    current_dir = setup_environment()
    logger.info(f"Working directory: {current_dir}")
    
    # Check dependencies
    
    
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
        logger.info("\n👋 Gradio client stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Error starting Gradio client: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code or 0)
