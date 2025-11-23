# Persian Deal Analyzer

A CRM system with AI insights for deal analysis, featuring Persian language support and a Mixture of Experts (MoE) architecture.

## Features

- **Deal Analysis**: Comprehensive health scoring and risk assessment
- **Sentiment Analysis**: Persian text sentiment analysis using Qwen2 model
- **RAG/CAG Systems**: Retrieval and Corrective Augmented Generation
- **Speech-to-Text**: Persian audio transcription
- **Mixture of Experts**: Intelligent routing to specialized AI experts
- **Gradio Interface**: Web-based user interface

## Architecture

### Mixture of Experts (MoE) System

The MoE system routes queries to specialized experts:

- **Deal Analysis Expert**: Health scoring, deal metrics
- **Sentiment Expert**: Persian/English sentiment analysis
- **Activity Expert**: Timeline and activity analysis
- **Risk Assessment Expert**: Risk evaluation and indicators
- **Search Expert**: RAG/CAG semantic search

### Services

- Analytics Service
- Sentiment Service
- Deal Management
- Activity Tracking
- RAG/CAG Integration

## Installation

```bash
pip install -r requirements.txt
```

### Optional Dependencies

- `gradio`: Web interface
- `chromadb`: Vector database for RAG
- `psycopg2`: PostgreSQL support

## Usage

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/database/

# Run with verbose output
pytest -v
```

### Running Gradio Interface

```bash
python gradio_mcp_client.py
```

## Project Structure

```
AI-agent/
├── config/
│   ├── settings.py
│   └── moe_settings.py
├── services/
│   ├── analytics_service.py
│   ├── sentiment_service.py
│   └── moe/
│       ├── moe_orchestrator.py
│       ├── expert_router.py
│       ├── expert_ensemble.py
│       └── experts/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── database/
└── gradio_mcp_client.py
```

## Done Tasks

### Mixture of Experts Implementation
- [x] MoE configuration (`config/moe_settings.py`)
- [x] Base expert abstract class with result dataclass
- [x] Expert router with hybrid routing strategy (rule-based + pattern matching)
- [x] Expert ensemble with multiple combination strategies (weighted_average, winner_take_all, hierarchical)
- [x] MoE orchestrator for query processing
- [x] Deal Analysis Expert
- [x] Sentiment Expert
- [x] Activity Expert
- [x] Risk Assessment Expert
- [x] Search Expert

### Gradio Integration
- [x] MoE integration in Gradio client
- [x] MoE query processing method
- [x] MoE result formatting
- [x] MoE Assistant tab in Gradio interface
- [x] Expert descriptions display

### Test Suite
- [x] Unit tests for Gradio client (21 tests)
- [x] Unit tests for Expert Router (18 tests)
- [x] Unit tests for Experts (28 tests)
- [x] Unit tests for MoE Orchestrator (18 tests)
- [x] Integration tests for Gradio interface
- [x] Integration tests for Gradio MoE
- [x] Integration tests for MoE system

### Test Results
- 218 tests passed
- 22 tests skipped (Gradio not installed)
- 7 tests expected failures (no PostgreSQL in test environment)

## To-Do Tasks

### High Priority
- [ ] Add embedding-based routing strategy
- [ ] Implement expert caching layer
- [ ] Add performance monitoring dashboard
- [ ] Create API documentation

### Medium Priority
- [ ] Add more Persian language patterns to router
- [ ] Implement expert feedback loop for learning
- [ ] Add batch processing for multiple queries
- [ ] Create CLI interface for MoE system

### Low Priority
- [ ] Add visualization for expert contributions
- [ ] Implement A/B testing for routing strategies
- [ ] Add export functionality for analysis results
- [ ] Create Docker deployment configuration

### Testing Improvements
- [ ] Add end-to-end tests with real database
- [ ] Add performance benchmarks
- [ ] Add load testing for concurrent queries
- [ ] Increase test coverage to 90%+

## Configuration

### Environment Variables

```bash
# MoE Settings
MOE_ROUTING_STRATEGY=hybrid          # rule_based, embedding_based, hybrid
MOE_ROUTING_CONFIDENCE=0.7           # Minimum confidence threshold
MOE_ENSEMBLE_STRATEGY=weighted_average  # weighted_average, winner_take_all, hierarchical
MOE_PARALLEL_EXECUTION=true          # Enable parallel expert execution
MOE_EXPERT_TIMEOUT=30                # Expert timeout in seconds

# Database
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request
