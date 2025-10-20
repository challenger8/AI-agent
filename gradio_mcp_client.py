"""
Integration module for RAG search in Gradio interface with caching
Add this to gradio_mcp_client.py

Place this code in the appropriate section of gradio_mcp_client.py
"""

import asyncio
import logging
from typing import Dict, List, Tuple, Any
import gradio as gr

logger = logging.getLogger(__name__)


class RAGSearchManager:
    """Manages RAG search operations in Gradio with caching"""
    
    def __init__(self):
        self.rag_service = None
        self.cached_rag_service = None
        self.initialized = False
        self.cache_stats_updated = False
    
    async def initialize_rag(self):
        """Initialize RAG search service with caching"""
        try:
            from services.rag_search_service import RAGSearchService
            from services.rag_search_cache_service import RAGSearchWithCache
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
            
            # Wrap with caching
            self.cached_rag_service = RAGSearchWithCache(self.rag_service)
            
            self.initialized = True
            logger.info("✅ RAG service initialized with caching")
            return True
        except Exception as e:
            logger.error(f"❌ RAG initialization failed: {e}")
            return False
    
    def search(self, query: str, search_type: str = "all", n_results: int = 5) -> Dict[str, Any]:
        """
        Perform semantic search with caching
        
        Args:
            query: Search query
            search_type: 'all', 'deals', 'activities', or 'agents'
            n_results: Number of results
            
        Returns:
            Search results (with cache info)
        """
        if not self.initialized or not self.cached_rag_service:
            return {'error': 'RAG service not initialized'}
        
        try:
            # Use cached search
            result = self.cached_rag_service.search(query, search_type, n_results)
            return result
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
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics and info"""
        if not self.initialized or not self.cached_rag_service:
            return {'error': 'Cache not available'}
        
        try:
            return self.cached_rag_service.get_cache_info()
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return {'error': str(e)}
    
    def clear_cache(self) -> str:
        """Clear search cache"""
        if not self.initialized or not self.cached_rag_service:
            return "❌ Cache not available"
        
        try:
            count = self.cached_rag_service.clear_cache()
            return f"✅ Cache cleared ({count} entries removed)"
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return f"❌ Error: {e}"


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


# Usage in main gradio_mcp_client.py:
# Inside the gr.Blocks() context, add:
# create_rag_search_tab()