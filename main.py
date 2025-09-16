"""
Main application entry point
"""
import sys
import os
import asyncio

# Load environment variables FIRST
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Environment variables loaded successfully")
except ImportError:
    print("Warning: python-dotenv not installed, using system environment variables")

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import from your MCP server module
from mcp_spec.server import create_mcp_server

async def main():
    """
    Main application function
    """
    try:
        print("Creating MCP server...")
        
        # Create your MCP server using your factory function
        server = create_mcp_server()
        
        print("Server created successfully!")
        print("Server status:", server.get_server_status())
        
        # Run the server
        print("Starting MCP server...")
        await server.run()
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return 0
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code or 0)