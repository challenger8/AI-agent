#!/usr/bin/env python3
"""
Gradio MCP Client Interface
Web interface for Persian Deal Analyzer using Gradio
"""

import gradio as gr
import pandas as pd
import plotly.graph_objects as go
import logging
from typing import Dict, List, Any
import os
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import services
try:
    from database.database import create_database_manager
    from models.repositories import create_repositories
    from services.analytics_service import AnalyticsService
    from services.sentiment_service import SentimentService
    from services.deal_service import DealService
    from services.moe.moe_orchestrator import MoEOrchestrator
    logger.info("Services imported successfully")
except ImportError as e:
    logger.error(f"Failed to import services: {e}")
    services_available = False
else:
    services_available = True

# Flag for MoE availability
moe_available = True
try:
    from services.moe.moe_orchestrator import MoEOrchestrator
except ImportError:
    moe_available = False
    logger.warning("MoE module not available")


class GradioMCPClient:
    """Gradio interface for Persian Deal Analyzer"""
    
    def __init__(self):
        """Initialize the Gradio client"""
        self.db_manager = None
        self.repositories = None
        self.analytics_service = None
        self.sentiment_service = None
        self.deal_service = None
        self.moe_orchestrator = None

        if services_available:
            self.initialize_services()
    
    def initialize_services(self):
        """Initialize backend services"""
        try:
            self.db_manager = create_database_manager()
            self.repositories = create_repositories(self.db_manager)
            self.sentiment_service = SentimentService(self.repositories)
            self.analytics_service = AnalyticsService(self.repositories, self.sentiment_service)
            self.deal_service = DealService(self.repositories)

            # Initialize MoE orchestrator
            if moe_available:
                services = {
                    'analytics': self.analytics_service,
                    'sentiment': self.sentiment_service,
                    'deal': self.deal_service
                }
                self.moe_orchestrator = MoEOrchestrator(
                    repositories=self.repositories,
                    services=services
                )
                logger.info("MoE Orchestrator initialized")

            logger.info("All services initialized")
            logger.info("Sentiment model will load on first use")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            import traceback
            traceback.print_exc()
    
    def analyze_deal(self, deal_id: str) -> Dict[str, Any]:
        """Analyze a single deal"""
        if not self.analytics_service:
            return {"error": "Analytics service not available"}
        
        try:
            result = self.analytics_service.analyze_deal_comprehensive(deal_id)
            return result
        except Exception as e:
            logger.error(f"Error analyzing deal: {e}")
            return {"error": str(e)}
    
    def get_portfolio_overview(self) -> Dict[str, Any]:
        """Get portfolio overview"""
        if not self.analytics_service:
            return {"error": "Analytics service not available"}
        
        try:
            result = self.analytics_service.analyze_portfolio_overview()
            return result
        except Exception as e:
            logger.error(f"Error getting portfolio overview: {e}")
            return {"error": str(e)}
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text"""
        if not text or not text.strip():
            return {"error": "Please enter some text to analyze"}
        
        if not self.sentiment_service:
            return {"error": "Sentiment service not available"}
        
        # Ensure model is loaded
        if not self.sentiment_service.model_loaded:
            logger.info("Loading sentiment model (first use)...")
            try:
                import asyncio
                asyncio.run(self.sentiment_service.initialize())
                logger.info("✅ Sentiment model loaded successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize sentiment model: {e}")
                return {
                    "sentiment": "unknown",
                    "confidence": 0.0,
                    "error": f"Model not available: {str(e)}"
                }
        
        try:
            result = self.sentiment_service.analyze_text(text)
            if result and "error" not in result:
                logger.info(f"Sentiment analysis: {result}")
            return result
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            import traceback
            traceback.print_exc()
            return {
                "sentiment": "unknown",
                "confidence": 0.0,
                "error": f"Analysis failed: {str(e)}"
            }
    
    def format_portfolio_data(self, data: Dict[str, Any]) -> tuple:
        """Format portfolio data for display"""
        if "error" in data:
            return str(data), None
        
        # Create summary text
        summary = f"""
        📊 Portfolio Overview
        
        Total Deals: {data.get('summary', {}).get('total_deals', 0)}
        Active Deals: {data.get('summary', {}).get('active_deals', 0)}
        Total Value: {data.get('summary', {}).get('total_value', 0)}
        
        Status Distribution:
        """
        
        for status, count in data.get('status_distribution', {}).items():
            summary += f"\n  • {status}: {count}"
        
        return summary, None
    
    def format_deal_analysis(self, data: Dict[str, Any]) -> str:
        """Format deal analysis for display"""
        if "error" in data:
            return str(data)
        
        analysis = f"""
        🎯 Deal Analysis
        
        Health Score: {data.get('health_score', 0)}/100
        Status: {data.get('deal_status', 'Unknown')}
        
        Risk Indicators:
        """
        
        for risk in data.get('risk_indicators', []):
            analysis += f"\n  ⚠️  {risk}"
        
        analysis += "\n\nRecommendations:"
        for rec in data.get('recommendations', []):
            analysis += f"\n  ✓ {rec}"
        
        return analysis
    
    def format_sentiment_result(self, data: Dict[str, Any]) -> str:
        """Format sentiment analysis result"""
        if "error" in data:
            return str(data)

        sentiment = data.get("sentiment", "unknown")
        confidence = data.get("confidence", 0)

        emoji = "positive" if sentiment == "positive" else "negative" if sentiment == "negative" else "neutral"

        return f"""
        Sentiment Analysis

        Sentiment: {sentiment} ({emoji})
        Confidence: {confidence:.2%}
        """

    def moe_query(self, query: str) -> Dict[str, Any]:
        """Process query through MoE system"""
        if not query or not query.strip():
            return {"error": "Please enter a query"}

        if not self.moe_orchestrator:
            return {"error": "MoE orchestrator not available"}

        try:
            import asyncio
            result = asyncio.run(self.moe_orchestrator.process(query))
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error in MoE query: {e}")
            return {"error": str(e)}

    def format_moe_result(self, data: Dict[str, Any]) -> str:
        """Format MoE result for display"""
        if "error" in data:
            return f"Error: {data['error']}"

        output = []
        output.append("MoE Analysis Result")
        output.append("=" * 40)

        # Primary expert
        primary = data.get('primary_expert', 'unknown')
        confidence = data.get('combined_confidence', 0)
        output.append(f"\nPrimary Expert: {primary}")
        output.append(f"Confidence: {confidence:.2%}")

        # Strategy used
        strategy = data.get('strategy_used', 'unknown')
        output.append(f"Strategy: {strategy}")

        # Execution time
        exec_time = data.get('execution_time_ms', 0)
        output.append(f"Execution Time: {exec_time:.2f}ms")

        # Reasoning
        reasoning = data.get('reasoning', '')
        if reasoning:
            output.append(f"\nReasoning: {reasoning}")

        # Combined data
        combined_data = data.get('combined_data', {})
        if combined_data and 'error' not in combined_data:
            output.append("\n" + "-" * 40)
            output.append("Analysis Results:")

            # Format based on content
            if 'health_score' in combined_data:
                output.append(f"  Health Score: {combined_data['health_score']}/100")

            if 'sentiment' in combined_data:
                output.append(f"  Sentiment: {combined_data['sentiment']}")

            if 'risk_indicators' in combined_data:
                risks = combined_data['risk_indicators']
                if risks:
                    output.append("  Risk Indicators:")
                    for risk in risks[:5]:
                        output.append(f"    - {risk}")

            if 'recommendations' in combined_data:
                recs = combined_data['recommendations']
                if recs:
                    output.append("  Recommendations:")
                    for rec in recs[:5]:
                        output.append(f"    - {rec}")

            if 'total_results' in combined_data:
                output.append(f"  Search Results: {combined_data['total_results']}")

        # Expert results summary
        expert_results = data.get('expert_results', [])
        if expert_results:
            output.append("\n" + "-" * 40)
            output.append("Expert Contributions:")
            for result in expert_results:
                expert_type = result.get('expert_type', 'unknown')
                success = "Success" if result.get('success') else "Failed"
                conf = result.get('confidence', 0)
                output.append(f"  {expert_type}: {success} (confidence: {conf:.2f})")

        return "\n".join(output)

    def get_moe_experts(self) -> str:
        """Get available MoE experts"""
        if not self.moe_orchestrator:
            return "MoE not available"

        descriptions = self.moe_orchestrator.get_expert_descriptions()
        output = ["Available Experts:", "=" * 40]

        for expert_type, description in descriptions.items():
            output.append(f"\n{expert_type}:")
            output.append(f"  {description}")

        return "\n".join(output)


# Create global client instance
client = GradioMCPClient()


def create_interface():
    """Create Gradio interface"""
    
    with gr.Blocks(title="Persian Deal Analyzer") as app:
        gr.Markdown("# 🎯 Persian Deal Analyzer - MCP Client")
        gr.Markdown("Analyze deals, sentiment, and portfolio performance")
        
        with gr.Tabs():
            # Tab 1: Deal Analysis
            with gr.Tab("📈 Deal Analysis"):
                gr.Markdown("### Analyze Individual Deal")
                with gr.Row():
                    deal_id = gr.Textbox(label="Deal ID", placeholder="Enter deal ID")
                    analyze_btn = gr.Button("Analyze Deal")
                
                deal_output = gr.Textbox(label="Analysis Result", lines=10)
                
                analyze_btn.click(
                    fn=lambda id: client.format_deal_analysis(client.analyze_deal(id)),
                    inputs=[deal_id],
                    outputs=[deal_output]
                )
            
            # Tab 2: Portfolio Overview
            with gr.Tab("🏢 Portfolio Overview"):
                gr.Markdown("### Portfolio Summary")
                portfolio_btn = gr.Button("Get Portfolio Overview")
                portfolio_output = gr.Textbox(label="Portfolio Data", lines=15)
                
                portfolio_btn.click(
                    fn=lambda: client.format_portfolio_data(client.get_portfolio_overview()),
                    inputs=[],
                    outputs=[portfolio_output]
                )
            
            # Tab 3: Sentiment Analysis
            with gr.Tab("Sentiment Analysis"):
                gr.Markdown("### Analyze Text Sentiment")
                gr.Markdown("Note: Model loads on first use (may take 1-2 minutes)")
                with gr.Row():
                    sentiment_input = gr.Textbox(
                        label="Enter Persian Text",
                        placeholder="Enter Persian text here...",
                        lines=3
                    )
                    sentiment_btn = gr.Button("Analyze Sentiment")

                sentiment_output = gr.Textbox(label="Sentiment Result", lines=5)

                sentiment_btn.click(
                    fn=lambda text: client.format_sentiment_result(client.analyze_sentiment(text)),
                    inputs=[sentiment_input],
                    outputs=[sentiment_output]
                )

            # Tab 4: MoE Smart Assistant
            with gr.Tab("MoE Assistant"):
                gr.Markdown("### Mixture of Experts Smart Assistant")
                gr.Markdown("Ask any question - the system will automatically route to the best expert(s)")

                with gr.Row():
                    with gr.Column(scale=3):
                        moe_input = gr.Textbox(
                            label="Your Query",
                            placeholder="e.g., 'Analyze deal 123', 'What are the risks?', 'Find deals related to...'",
                            lines=3
                        )
                    with gr.Column(scale=1):
                        moe_btn = gr.Button("Process Query", variant="primary")
                        experts_btn = gr.Button("Show Experts")

                moe_output = gr.Textbox(label="MoE Result", lines=20)

                moe_btn.click(
                    fn=lambda query: client.format_moe_result(client.moe_query(query)),
                    inputs=[moe_input],
                    outputs=[moe_output]
                )

                experts_btn.click(
                    fn=lambda: client.get_moe_experts(),
                    inputs=[],
                    outputs=[moe_output]
                )

                gr.Markdown("""
                **Available Query Types:**
                - **Deal Analysis**: "Analyze deal 123", "How is deal 456 performing?"
                - **Sentiment**: "What's the sentiment of this text?", Analyze Persian text
                - **Activities**: "Show recent activities", "What happened last week?"
                - **Risk Assessment**: "What are the risks?", "Check for problems"
                - **Search**: "Find deals related to...", "Search for..."
                """)

            # Tab 5: About
            with gr.Tab("About"):
                gr.Markdown("""
                ## Persian Deal Analyzer

                A comprehensive system for analyzing Persian business deals with:
                - **Deal Analytics**: Health scores, risk identification, recommendations
                - **Sentiment Analysis**: Understanding emotions in deal communications
                - **Portfolio Management**: Overview of all active deals
                - **MoE System**: Intelligent routing to specialized experts

                ### Features
                - Real-time deal analysis
                - Persian text sentiment analysis
                - Portfolio health metrics
                - Risk identification
                - Actionable recommendations
                - Mixture of Experts (MoE) intelligent routing

                ### MoE Experts
                - **Deal Analysis Expert**: Health scoring, performance insights
                - **Sentiment Expert**: Persian text emotion analysis
                - **Activity Expert**: Timeline and trend analysis
                - **Risk Assessment Expert**: Risk evaluation and mitigation
                - **Search Expert**: Semantic search using RAG/CAG

                ### Version
                v1.1.0 (with MoE)
                """)
    
    return app


def run_gradio_app():
    """Launch the Gradio application"""
    logger.info("Creating Gradio interface...")
    app = create_interface()
    
    logger.info("🚀 Launching Gradio application...")
    logger.info("📱 Access the interface at: http://localhost:7860")
    logger.info("💡 Press Ctrl+C to stop the server")
    
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        debug=True,
        show_error=True
    )


if __name__ == "__main__":
    run_gradio_app()