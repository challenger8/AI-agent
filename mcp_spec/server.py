"""
mcp_spec/server.py
------------------
Main MCP Server for Persian Deal Analyzer
Clean, modular, and extensible architecture
"""

import asyncio
from typing import Optional
from mcp_spec.handlers.tool_handlers import ToolHandlers 
from mcp_spec.handlers.tool_handlers import ToolHandlers
from mcp_spec.handlers.resource_handlers import ResourceHandlers
from models.repositories import RepositoryManager
from database.database import create_database_manager
from utils.logging_config import setup_logging, get_logger
import logging
import sys
from pathlib import Path
from mcp.server import Server
from mcp.server.stdio import stdio_server  
from mcp.server.models import InitializationOptions
from services.stt_service import get_stt_service, STTService
from config.settings import get_stt_available
from services.cag_orchestrator_service import CAGOrchestrator, CAGSearchManager

# MCP imports - Fixed to avoid conflicts with local module
from mcp_spec.schemas.tool_schemas import (
    # ... existing imports ...
    TRANSCRIBE_AUDIO_SCHEMA,
    TRANSCRIBE_BATCH_SCHEMA,
    VALIDATE_AUDIO_SCHEMA,
    LIST_AUDIO_FILES_SCHEMA
)

# Database imports - Fixed
try:
 
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
 
    def create_repositories(db_manager):
        return RepositoryManager(db_manager)
            
except ImportError as e:
    raise ImportError(f"Database modules required: {e}") from e

# Application imports - with error handling
try:
    from config.settings import MCPSettings, get_sentiment_available
except ImportError:
    # Create placeholder settings if config doesn't exist
    class MCPSettings:
        SERVER_NAME = "Persian Deal Analyzer"
        SERVER_VERSION = "1.0.0"
    
    def get_sentiment_available():
        return False


    def setup_logging():
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger("MCP")
    
    def get_logger(name):
        return logging.getLogger(name)

try:
    from utils.exceptions import PersianDealAnalyzerError, ConfigurationError
except ImportError:
    class PersianDealAnalyzerError(Exception):
        pass
    
    class ConfigurationError(Exception):
        pass

try:
    from services.sentiment_service import SentimentService
except ImportError:
    class SentimentService:
        def __init__(self, repositories=None):
            self.model_loaded = False
        
        async def initialize(self):
            return False
        
        def clear_cache(self):
            pass

try:
    from services.analytics_service import AnalyticsService
except ImportError:
    class AnalyticsService:
        def __init__(self, repositories=None, sentiment_service=None):
            pass


    class ToolHandlers:
        def __init__(self, analytics_service=None, sentiment_service=None):
            pass
        
        def get_tools(self):
            return []
        
        async def handle_tool_call(self, name, arguments):
            return [{"type": "text", "text": f"Tool {name} not implemented"}]


    class ResourceHandlers:
        def __init__(self, analytics_service=None, sentiment_service=None):
            pass
        
        def get_resources(self):
            return []
        
        async def handle_resource_request(self, uri):
            return f'{{"error": "Resource {uri} not implemented"}}'

class PersianDealAnalyzerMCPServer:
    """
    Main MCP Server for Persian Deal Analyzer
    Clean architecture with dependency injection and proper separation of concerns
    """
    
    def __init__(self):
        """Initialize MCP server with all components"""
        # Setup logging
        self.logger = setup_logging()
        self.logger.info(f"Initializing {MCPSettings.SERVER_NAME}")
        
        # Initialize MCP server
        self.server = Server(MCPSettings.SERVER_NAME)
        
        # Initialize components
        self.db_manager: Optional[object] = None
        self.repositories: Optional[object] = None
        self.sentiment_service: Optional[SentimentService] = None
        self.analytics_service: Optional[AnalyticsService] = None
        self.stt_service: Optional[STTService] = None 
        self.tool_handlers: Optional[ToolHandlers] = None
        self.resource_handlers: Optional[ResourceHandlers] = None
        self.cag_orchestrator = None
        self.cag_manager = None
        # Setup server handlers
        self._setup_mcp_handlers()
        
        self.logger.info("MCP Server initialized successfully")
    
    async def initialize_services(self) -> bool:
        """
        Initialize all services and dependencies
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize database
            await self._initialize_database()
            
            # Initialize sentiment service
            await self._initialize_sentiment_service()
            
            await self._initialize_stt_service()
            # Initialize analytics service
            self._initialize_analytics_service()
            
            # Initialize handlers
            self._initialize_handlers()
            await self._initialize_cag_orchestrator()
            self.logger.info("All services initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Service initialization failed: {e}")
            return False
    async def _initialize_cag_orchestrator(self):
        """Initialize CAG orchestrator"""
        try:
            self.logger.info("Initializing CAG...")
            self.cag_orchestrator = CAGOrchestrator(self.repositories)
            await self.cag_orchestrator.initialize()
            self.cag_manager = CAGSearchManager(self.cag_orchestrator)
            self.logger.info("CAG initialized")
        except Exception as e:
            self.logger.error(f"CAG init failed: {e}")
            self.cag_orchestrator = None
    async def _initialize_database(self):
        """Initialize database connection and repositories"""
        try:
            self.logger.info("Initializing database connection...")
            
            # Create database manager
            self.db_manager = create_database_manager()
            
            # Check if setup_connection method exists and call it
            if hasattr(self.db_manager, 'setup_connection'):
                self.logger.info("Calling setup_connection...")
                if not self.db_manager.setup_connection():
                    raise ConfigurationError("Database connection failed")
            else:
                # For original DatabaseManager, setup_connection is done automatically
                self.logger.info("No setup_connection method found, checking if connection works...")
                # Try to test the connection instead
                if hasattr(self.db_manager, 'test_connection'):
                    if not self.db_manager.test_connection():
                        raise ConfigurationError("Database connection test failed")
                else:
                    self.logger.warning("No connection test method available, proceeding...")
            
            # Create repositories
            self.repositories = create_repositories(self.db_manager)
            
            self.logger.info("Database connection established")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise ConfigurationError(f"Database setup failed: {e}")
    
    async def _initialize_sentiment_service(self):
        """Initialize sentiment analysis service"""
        if not get_sentiment_available():
            self.logger.warning("Sentiment analysis not available - transformers not installed")
            return
        
        try:
            self.logger.info("Initializing sentiment service...")
            self.sentiment_service = SentimentService(self.repositories)
            
            # Pre-load model for better performance
            await self.sentiment_service.initialize()
            
            self.logger.info("Sentiment service initialized")
            
        except Exception as e:
            self.logger.error(f"Sentiment service initialization failed: {e}")
            # Continue without sentiment service
            self.sentiment_service = None
    async def _initialize_stt_service(self):
        """Initialize STT (Speech-to-Text) service"""
        if not get_stt_available():
            self.logger.warning("STT not available - whisper not installed")
            return
        
        try:
            self.logger.info("Initializing STT service...")
            self.stt_service = get_stt_service(self.repositories)
            
            # Pre-load model for better performance
            await self.stt_service.initialize()
            
            self.logger.info("STT service initialized")
            
        except Exception as e:
            self.logger.error(f"STT service initialization failed: {e}")
            # Continue without STT service
            self.stt_service = None
    def _initialize_analytics_service(self):
        """Initialize analytics service"""
        try:
            self.logger.info("Initializing analytics service...")
            self.analytics_service = AnalyticsService(
                repositories=self.repositories,
                sentiment_service=self.sentiment_service
            )
            self.logger.info("Analytics service initialized")
            
        except Exception as e:
            self.logger.error(f"Analytics service initialization failed: {e}")
            raise ConfigurationError(f"Analytics service setup failed: {e}")
    
    def _initialize_handlers(self):
        """Initialize MCP handlers"""
        try:
            self.logger.info("Initializing MCP handlers...")
            
            self.tool_handlers = ToolHandlers(
                analytics_service=self.analytics_service,
                sentiment_service=self.sentiment_service
            )
            
            self.resource_handlers = ResourceHandlers(
                analytics_service=self.analytics_service,
                sentiment_service=self.sentiment_service
            )
            
            self.logger.info("MCP handlers initialized")
            
        except Exception as e:
            self.logger.error(f"Handler initialization failed: {e}")
            raise ConfigurationError(f"Handler setup failed: {e}")
    
    def _setup_mcp_handlers(self):
        """Setup MCP protocol handlers"""
        
        @self.server.list_resources()
        async def handle_list_resources():
            """Handle MCP list resources request"""
            try:
                if not self.resource_handlers:
                    return []
                return self.resource_handlers.get_resources()
            except Exception as e:
                self.logger.error(f"Error listing resources: {e}")
                return []
        
        @self.server.read_resource()
        async def handle_read_resource(uri: str) -> str:
            """Handle MCP read resource request"""
            try:
                if not self.resource_handlers:
                    return '{"error": "Resource handlers not initialized"}'
                return await self.resource_handlers.handle_resource_request(uri)
            except Exception as e:
                self.logger.error(f"Error reading resource {uri}: {e}")
                return f'{{"error": "Failed to read resource: {str(e)}"}}'
        
        @self.server.list_tools()
        async def handle_list_tools():
            """Handle MCP list tools request"""
            try:
                if not self.tool_handlers:
                    return []
                return self.tool_handlers.get_tools()
            except Exception as e:
                self.logger.error(f"Error listing tools: {e}")
                return []
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict):
            """Handle MCP tool call request"""
            try:
                if not self.tool_handlers:
                    error_response = [{"type": "text", "text": '{"error": "Tool handlers not initialized"}'}]
                    return error_response
                
                return await self.tool_handlers.handle_tool_call(name, arguments)
                
            except Exception as e:
                self.logger.error(f"Error calling tool {name}: {e}")
                error_response = [{"type": "text", "text": f'{{"error": "Tool call failed: {str(e)}"}}'}]
                return error_response
        @self.server.call_tool()
        async def handle_cag_search(query: str, n_results: int = 5):
            """CAG semantic search"""
            if not self.cag_manager:
                return [{"type": "text", "text": '{"error": "CAG not available"}'}]
            try:
                result = self.cag_manager.search(query, n_results=n_results)
                info = f"Query: {query}\nCorrection: {result['correction']['applied']}\nConfidence: {result['confidence_metrics'].get('average_score', 0):.3f}\nDeals: {len(result['results'].get('deals', []))}\nActivities: {len(result['results'].get('activities', []))}"
                return [{"type": "text", "text": info}]
            except Exception as e:
                return [{"type": "text", "text": f'{{"error": "{str(e)}"}}'}]

        @self.server.call_tool()
        async def handle_cag_stats():
            """Get CAG statistics"""
            if not self.cag_manager:
                return [{"type": "text", "text": '{"error": "CAG not available"}'}]
            try:
                stats = self.cag_manager.get_stats()
                info = f"Total Searches: {stats['total_searches']}\nRewrites Triggered: {stats['rewrites_triggered']}\nRewrite Rate: {stats.get('rewrite_rate', 0):.1%}"
                return [{"type": "text", "text": info}]
            except Exception as e:
                return [{"type": "text", "text": f'{{"error": "{str(e)}"}}'}]
    async def run(self):
        """Run the MCP server"""
        try:
            self.logger.info(f"Starting {MCPSettings.SERVER_NAME}")
            
            # Initialize all services
            if not await self.initialize_services():
                raise RuntimeError("Service initialization failed")
            
            # Run MCP server
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name=MCPSettings.SERVER_NAME,
                        server_version=MCPSettings.SERVER_VERSION,
                        capabilities={}  # Use empty dict instead of calling get_capabilities()
                    )
                )
                
        except KeyboardInterrupt:
            self.logger.info("Server stopped by user")
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            raise
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Cleanup server resources"""
        try:
            self.logger.info("Cleaning up server resources...")
            
            # Cleanup sentiment service
            if self.sentiment_service:
                self.sentiment_service.clear_cache()
                
            if self.stt_service:
                await self.stt_service.cleanup()
            # Cleanup database
            if self.db_manager:
                self.db_manager.close()
            
            self.logger.info("Server cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_server_status(self) -> dict:
        """Get server status information"""
        return {
            "server_name": MCPSettings.SERVER_NAME,
            "server_version": MCPSettings.SERVER_VERSION,
            "database_connected": self.db_manager is not None,
            "sentiment_available": self.sentiment_service is not None and hasattr(self.sentiment_service, 'model_loaded') and self.sentiment_service.model_loaded,
            "stt_available": self.stt_service is not None and hasattr(self.stt_service, 'model_loaded') and self.stt_service.model_loaded,
            "analytics_ready": self.analytics_service is not None,
            "handlers_initialized": self.tool_handlers is not None and self.resource_handlers is not None
        }


# Factory function for creating server
def create_mcp_server() -> PersianDealAnalyzerMCPServer:
    """
    Factory function to create MCP server instance
    
    Returns:
        Configured MCP server instance
    """
    return PersianDealAnalyzerMCPServer()


async def main():
    """Main entry point for MCP server"""
    server = None
    try:
        # Create and run server
        server = create_mcp_server()
        await server.run()
        
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    finally:
        if server:
            await server.cleanup()
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))