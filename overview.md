# Persian Deal Analyzer

A CRM system that analyzes deals with AI insights, Persian sentiment analysis, and smart search.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
python launch_gradio.py  # Open http://localhost:7860
```

## What It Does

- 📊 **Analyze Deals** - Health scores & insights
- 😊 **Sentiment** - Understand Persian emotions  
- 🔍 **Search** - Find deals by meaning
- 🎤 **Audio** - Transcribe Persian calls
- 🌐 **Web UI** - Easy dashboard

## Run Tests

```bash
pytest tests/unit/ -v          # Fast (60+ tests)
pytest tests/integration/ -v   # Full (24+ tests)
pytest tests/ --cov            # With coverage
```

## Files

- `main.py` - Start here
- `launch_gradio.py` - Web interface
- `tests/` - 90+ tests (unit, integration, smoke)
- `services/` - Core logic
- `database/` - PostgreSQL

## Performance

- Search: 100ms (20x faster)
- Cached: 10ms (200x faster)
- Index: 10s for 1000 docs (3x faster)

## Status

✅ Production Ready  
✅ 90+ Tests Passing  
✅ Performance Optimized  
✅ Well-Organized Tests