# Persian Deal Analyzer - Project Overview

## What This Project Does

This is a local AI assistant that helps analyze Persian CRM deals. It understands Persian language, analyzes sentiment in conversations, and provides insights about your business deals. Everything runs on your own computer—no cloud services needed.

**Current Status:** The core system is complete and working. We're about 90% done with the planned features.

**Goal:** A personal AI agent for deal analysis that runs entirely on your machine.

---

## How It Works

Think of this system like a smart filing cabinet with an AI assistant:

1. **You interact** through either:
   - A web browser interface (Gradio)
   - Claude Desktop (MCP protocol)

2. **The AI processes** your requests using:
   - Speech-to-text for Persian audio
   - Sentiment analysis to understand emotions in conversations
   - Analytics to calculate deal health and provide insights

3. **Data is stored** in:
   - PostgreSQL database (your CRM data)
   - Redis cache (for quick access)
   - Local audio files (your recordings)

---

## What's Working Right Now

### Core Features (All Complete)

**Database & Storage**
- PostgreSQL database for all your CRM data
- Redis caching for faster responses
- Everything stored locally on your machine

**Deal Management**
- Track all your deals and activities
- Store customer information
- Record agent interactions

**Sentiment Analysis**
- Understands Persian language
- Analyzes emotions in conversations
- Uses HooshvareLab BERT model

**Analytics**
- Calculate deal health scores
- Identify at-risk deals
- Provide actionable insights
- Track portfolio performance

**Speech-to-Text (Recently Added)**
- Convert Persian audio to text
- Supports MP3, WAV, M4A, FLAC, OGG, WEBM formats
- Fast transcription with Whisper model
- Works with recordings from calls or meetings

**User Interfaces**
- Web interface (Gradio) - easy to use in your browser
- MCP server - integrates with Claude Desktop
- Both interfaces work with all features

**Testing**
- Over 55 tests to ensure everything works
- 85%+ test coverage
- Automated testing for reliability

---

## What's Coming Next

### Phase 2: Smart Search (RAG System)

This will let you search through your CRM data using natural language. Ask questions like "show me deals where customers mentioned pricing concerns" and get relevant results.

**Timeline:** 5-7 days

### Phase 3: Expert System (MoE)

Multiple AI models working together, each specializing in different tasks:
- Summarizing conversations
- Extracting key information
- Answering specific questions

**Timeline:** 7-10 days

---

## Technical Details (For Developers)

### Current Technology

- **Language:** Python 3.11+
- **Database:** PostgreSQL (local)
- **Cache:** Redis 7
- **AI Framework:** Hugging Face Transformers
- **Sentiment Model:** HooshvareLab BERT (Persian)
- **Speech-to-Text:** Whisper Large (Persian)
- **Interface:** Gradio 4.0+ for web, MCP for Claude Desktop
- **Testing:** pytest with async support

### Coming Soon

- **Vector Database:** ChromaDB for semantic search
- **Language Model:** Qwen2 for advanced queries
- **Additional AI Models:** For summarization, entity extraction, and Q&A

---

## Project Structure

```
persian-deal-analyzer/
├── database/              # Database connection and management
├── models/                # Data models (deals, activities, agents)
├── services/              # Business logic
│   ├── deal_service.py           # Deal management
│   ├── sentiment_service.py      # Emotion analysis
│   ├── analytics_service.py      # Insights and scoring
│   ├── cache_service.py          # Fast data access
│   └── stt_service.py            # Speech-to-text
├── mcp_spec/              # MCP server for Claude integration
├── tests/                 # Automated tests
├── config/                # Settings and configuration
├── audio_files/           # Audio storage
├── models_cache/          # Downloaded AI models
└── gradio_mcp_client.py   # Web interface
```

---

## Getting Started

### First Time Setup

1. **Start the databases**
   ```bash
   docker-compose up -d
   ```
   This starts PostgreSQL and Redis in the background.

2. **Run the MCP server**
   ```bash
   python main.py
   ```
   First time will download the AI models (about 3-4 GB). After that, it starts instantly.

3. **Open the web interface**
   ```bash
   python launch_gradio.py
   ```
   Then open your browser to the URL it shows.

4. **Run tests** (optional, to verify everything works)
   ```bash
   pytest tests/ --cov
   ```

### Daily Use

After setup, you just need:
```bash
docker-compose up -d    # Start databases
python main.py          # Start the server
python launch_gradio.py # Open web interface
```

---

## Performance

### What You Can Expect

- **Sentiment Analysis:** Half a second per text
- **Deal Queries:** Nearly instant (under 50ms)
- **Analytics:** About half a second
- **Speech-to-Text:** 1-3 seconds per minute of audio
- **Test Coverage:** 85% of code is tested

### Storage Needs

**Current:**
- Database: ~100 MB (your CRM data)
- Redis Cache: ~50 MB
- AI Models: ~3.5 GB
- Audio Files: Varies based on your recordings

**Total Current:** About 4 GB

**After All Features:** About 15 GB (with all AI models)

---

## Success Metrics

### Already Achieved

- All automated tests passing
- MCP server working smoothly
- Web interface is responsive
- Sentiment analysis is accurate
- Analytics provide useful insights
- Caching makes everything fast
- Speech-to-text handles Persian audio well

### Future Goals

- Smart search returns relevant results 80%+ of the time
- Expert system picks the right AI model 90%+ of the time
- All AI tasks perform accurately
- Full workflow completes in under 3 seconds

---

## What's Next

**Immediate Priority:** Smart Search (RAG System)

We'll add the ability to search through your deals using natural language questions. This includes:
1. Setting up ChromaDB for vector storage
2. Creating document indexes
3. Adding semantic search
4. Integrating with the Qwen2 language model
5. Building search tools for both MCP and web interfaces
6. Writing tests for the new features

**Estimated Time:** 5-7 days

---

## Questions?

- For setup help: Check the main README.md
- For technical details: See TESTING_GUIDE.md
- For development: See TEST_IMPLEMENTATION_SUMMARY.md

---

**Last Updated:** October 8, 2025  
**Status:** Core system complete, speech-to-text working  
**Progress:** 90% complete  
**Next Step:** Adding smart search capabilities