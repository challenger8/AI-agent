# Persian Deal Analyzer - Project Overview (Updated)

## 📋 Executive Summary

A comprehensive local AI agent for Persian CRM deal analysis with sentiment insights, RAG capabilities, speech-to-text, and mixture of experts architecture. Features both MCP protocol access and Gradio web interface for personal use.

**Current Status:** 🟢 **Core Complete - Enhancement Phase** (~85% complete)

**Target:** Personal AI agent running locally (no cloud dependencies)

---

## 🏗️ Enhanced Architecture

### High-Level Architecture (With New Features)

```
┌───────────────────────────────────────────────────────────────┐
│                     Client Layer                               │
├───────────────────────────────────────────────────────────────┤
│  MCP Protocol Clients    │  Gradio Web Interface              │
│  (Claude Desktop, etc)   │  (Browser + Voice Recording)       │
└──────────┬────────────────┴──────────────┬───────────────────┘
           │                               │
           ▼                               ▼
┌───────────────────────────────────────────────────────────────┐
│                      API Layer                                 │
├───────────────────────────────────────────────────────────────┤
│  MCP Server (mcp_spec/server.py)                              │
│  - Tool Handlers      - Resource Handlers                      │
│  - RAG Tools         - STT Tools         - MoE Routing        │
└──────────┬────────────────────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────────────────────────────┐
│              AI Services Layer (NEW + EXISTING)                │
├───────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ RAG Service  │  │  STT Service │  │  MoE Router  │       │
│  │ (NEW)        │  │  (NEW)       │  │  (NEW)       │       │
│  │              │  │              │  │              │       │
│  │ ChromaDB     │  │ Whisper-FA   │  │ Expert       │       │
│  │ Embeddings   │  │ Whisper-v3   │  │ Selector     │       │
│  │ Qwen2        │  │              │  │              │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                  │               │
│         └─────────────────┼──────────────────┘               │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────┐      │
│  │          Expert Models Pool (MoE)                  │      │
│  ├───────────────────────────────────────────────────┤      │
│  │  Expert 1: Sentiment Analysis ✅ (HooshvareLab)   │      │
│  │  Expert 2: Summarization (NEW - T5/mT5)          │      │
│  │  Expert 3: Entity Extraction (NEW - NER)         │      │
│  │  Expert 4: Question Answering (NEW - QA model)   │      │
│  └────────────────────────────────────────────────────┘      │
│                           │                                  │
│  ┌────────────────────────▼──────────────────────────┐      │
│  │         Existing Services (COMPLETE)               │      │
│  ├───────────────────────────────────────────────────┤      │
│  │  Deal Service      │  Analytics Service           │      │
│  │  Sentiment Service │  Cache Service               │      │
│  └────────────────────────────────────────────────────┘      │
│                                                                │
└──────────┬─────────────────────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────────────────────────────┐
│                    Repository Layer                            │
├───────────────────────────────────────────────────────────────┤
│  Deal Repo  │  Activity Repo  │  Agent Repo  │  Sentiment    │
│  NEW: Document Repo (for RAG) │  NEW: Audio Repo (for STT)   │
└──────────┬─────────────────────────────────────────────────────┘
           │
           ▼
┌───────────────────────────────────────────────────────────────┐
│                     Data Layer                                 │
├───────────────────────────────────────────────────────────────┤
│  PostgreSQL    │  Redis Cache   │  ChromaDB      │  Audio     │
│  (CRM Data)    │  (Fast Access) │  (Vectors)     │  Storage   │
└───────────────────────────────────────────────────────────────┘
```

---

## ✅ Currently Complete (85% of Core Project)

### 1. ✅ Database Layer - 100% COMPLETE
- PostgreSQL connection management
- Connection pooling
- Query execution (all CRUD operations)
- Transaction handling
- SSH tunnel support
- **Fully tested** (37 tests passing)

### 2. ✅ Data Models - 100% COMPLETE
- Deal, DealActivity, CRMAgent models
- SentimentAnalysis model
- Serialization/deserialization
- **Fully tested**

### 3. ✅ Repository Layer - 100% COMPLETE
- DealRepository
- DealActivityRepository
- CRMAgentRepository
- SentimentRepository
- Repository Manager pattern
- **Fully tested**

### 4. ✅ Services Layer - 100% COMPLETE
- **DealService** - Deal management and timelines
- **SentimentService** - Persian sentiment analysis (HooshvareLab BERT)
- **AnalyticsService** - Health scoring, risk analysis, insights (Persian)
- **CacheService** - Redis integration with stats
- **Fully tested** (12 cache tests, all service tests)

### 5. ✅ MCP Server - 100% COMPLETE
- Async initialization
- Tool handlers (6 tools)
- Resource handlers (5 resources)
- Error handling
- **Fully tested**

### 6. ✅ Gradio Interface - 100% COMPLETE
- Server connection management
- Sentiment analysis tab
- Deal analytics visualization
- Sentiment trends charts
- **Functional and tested**

### 7. ✅ Testing Infrastructure - 100% COMPLETE
- **49+ tests total** across all layers
- Unit tests (database, cache, models, repositories, services)
- Integration tests (MCP, end-to-end, caching)
- Manual tests (quick verification, analytics)
- pytest fixtures and configuration
- Test runner script
- **All core tests passing**

### 8. ✅ Configuration & Utilities - 100% COMPLETE
- Environment configuration
- Logging setup
- Custom exceptions
- Settings management
- Feature flags

### 9. ✅ Docker Support - 90% COMPLETE
- docker-compose.yml
- Multi-service orchestration
- Volume mounts
- Service dependencies
- (Production optimization pending, but not needed for local use)

---

## 🚀 Planned Enhancements (New Features)

### Phase 1: RAG System (Retrieval-Augmented Generation)

**Purpose:** Search and retrieve relevant CRM deal data using natural language

**Components:**
```
services/rag_service.py
├── Document ingestion (deals, activities, notes)
├── Embedding generation (paraphrase-multilingual-mpnet-base-v2)
├── Vector storage (ChromaDB - local)
├── Semantic search
└── Context augmentation for Qwen2
```

**Key Features:**
- Index all CRM deals and activities
- Natural language queries: "Find deals about solar panels from last month"
- Retrieve relevant context for LLM queries
- Integration with Qwen2 for answer generation
- Persian language support

**Storage:**
- **ChromaDB** - Local vector database
- Embeddings stored alongside deal IDs
- Incremental indexing on new deals

**Integration Points:**
- New MCP tools: `search_deals_semantic`, `ask_about_deals`
- Gradio tab: "RAG Search"
- Analytics service enhancement

---

### Phase 2: Speech-to-Text Service

**Purpose:** Transcribe Persian audio to text for deal notes and activities

**Components:**
```
services/stt_service.py
├── Audio file handling (upload)
├── Persian transcription (whisper-fa / whisper-large-v3)
├── Post-processing (Persian text cleanup)
├── Integration with deal activities
└── Batch processing support
```

**Models:**
- **Primary:** `whisper-fa` (optimized for Persian)
- **Fallback:** OpenAI `whisper-large-v3` or `medium`
- Local execution (Hugging Face Transformers)

**Use Cases:**
- Upload voice notes → Auto-create deal activities
- Transcribe meeting recordings
- Voice-to-text in Gradio interface
- Batch process multiple audio files

**Integration Points:**
- New MCP tool: `transcribe_audio`
- Gradio: File upload widget for audio
- Analytics: Sentiment analysis on transcribed text
- Auto-create activities from transcriptions

---

### Phase 3: Mixture of Experts (MoE) System

**Purpose:** Route queries to specialized expert models for optimal results

**Architecture:**
```
services/moe_service.py
├── ML Router (small classification model)
│   ├── Analyzes incoming query
│   ├── Determines task type
│   └── Selects best expert
│
├── Expert Models Pool
│   ├── Expert 1: Sentiment Analysis ✅ (existing)
│   ├── Expert 2: Summarization (T5/mT5)
│   ├── Expert 3: Entity Extraction (NER model)
│   └── Expert 4: Question Answering (QA model)
│
└── Response Aggregation
    └── Combines multi-expert outputs
```

**Router Model:**
- Small BERT-based classifier
- Trained on task classification
- Input: User query → Output: Expert ID
- Fast inference (<50ms)

**Expert Capabilities:**

**Expert 1: Sentiment (Existing) ✅**
- Persian sentiment analysis
- Already integrated

**Expert 2: Summarization (NEW)**
- Model: `csebuetnlp/mT5_multilingual_XLSum` or similar
- Summarizes long deal descriptions
- Persian text support
- Generates executive summaries

**Expert 3: Entity Extraction (NEW)**
- Model: Persian NER model or multilingual NER
- Extracts: Names, Organizations, Amounts, Dates, Locations
- Structured data from unstructured text
- Auto-populate deal fields

**Expert 4: Question Answering (NEW)**
- Model: Multilingual QA model
- Answers questions about specific deals
- Works with RAG context
- Persian question understanding

**Routing Logic:**
```python
Query: "این معامله چه احساسی داره؟"
Router: → Sentiment Expert

Query: "این توضیحات رو خلاصه کن"
Router: → Summarization Expert

Query: "اسم مشتری و مبلغ رو پیدا کن"
Router: → Entity Extraction Expert

Query: "آخرین فعالیت این معامله چی بود؟"
Router: → Question Answering Expert (+ RAG)
```

**Integration Points:**
- New MCP tool: `moe_analyze` (auto-routing)
- Explicit tools: `summarize_text`, `extract_entities`, `answer_question`
- Gradio: "Multi-Expert Analysis" tab
- Analytics enhancement with entity extraction

---

## 📊 Updated Completion Status

| Component | Status | Completion | Notes |
|-----------|--------|------------|-------|
| **Core System** |
| Database Layer | ✅ | 100% | Fully tested |
| Data Models | ✅ | 100% | Fully tested |
| Repositories | ✅ | 100% | Fully tested |
| Services (Existing) | ✅ | 100% | All tested |
| MCP Server | ✅ | 100% | Tested |
| Gradio Interface | ✅ | 100% | Functional |
| Testing Suite | ✅ | 100% | 49+ tests |
| Cache Service | ✅ | 100% | Redis integrated |
| Configuration | ✅ | 95% | Complete for local use |
| Docker Setup | ✅ | 90% | Works locally |
| **New Features** |
| RAG Service | 🔴 | 0% | Not started |
| STT Service | 🔴 | 0% | Not started |
| MoE System | 🔴 | 0% | Not started |
| Expert 2: Summarization | 🔴 | 0% | Not started |
| Expert 3: Entity Extraction | 🔴 | 0% | Not started |
| Expert 4: Question Answering | 🔴 | 0% | Not started |
| MoE Router | 🔴 | 0% | Not started |

**Current Overall: 85% (Core System Complete)**  
**Target with New Features: 100%**

---

## 🎯 Development Priorities

### ✅ Already Complete - No Action Needed:
1. Core CRM functionality
2. Sentiment analysis
3. Analytics and health scoring
4. Database and caching
5. Testing infrastructure
6. MCP and Gradio interfaces

### 🔴 To Be Implemented (In Order):

**Phase 1: Speech-to-Text** (Estimated: 3-4 days)
- Easiest to implement
- Immediate practical value
- Foundation for voice-based features

**Phase 2: RAG System** (Estimated: 5-7 days)
- Semantic search over CRM data
- ChromaDB integration
- Qwen2 integration
- High value for query capabilities

**Phase 3: MoE System** (Estimated: 7-10 days)
- Router model training/selection
- Expert model integration (3 new models)
- Response aggregation
- Most complex but powerful

---

## 🔧 Technology Stack

### Current Stack:
- **Language:** Python 3.11+
- **Database:** PostgreSQL (local)
- **Cache:** Redis 7
- **ML Framework:** Hugging Face Transformers
- **Sentiment:** HooshvareLab BERT (Persian)
- **MCP:** Model Context Protocol SDK
- **Web UI:** Gradio 4.0+
- **Testing:** pytest, pytest-asyncio, pytest-cov

### New Stack Additions:
- **Vector DB:** ChromaDB (local, embedded)
- **Embeddings:** sentence-transformers (paraphrase-multilingual-mpnet-base-v2)
- **LLM:** Qwen2 (local)
- **STT:** whisper-fa / whisper-large-v3 (local)
- **Summarization:** mT5 or similar (multilingual)
- **NER:** Persian/Multilingual NER model
- **QA:** Multilingual QA model
- **Router:** Small BERT classifier

---

## 🎨 Design Patterns

### Current Patterns:
- Repository Pattern (Data access)
- Service Pattern (Business logic)
- Factory Pattern (Object creation)
- Dependency Injection
- Singleton Pattern (DB, Cache)

### New Patterns:
- **Strategy Pattern** - MoE expert selection
- **Chain of Responsibility** - RAG retrieval pipeline
- **Observer Pattern** - Document indexing on data changes
- **Adapter Pattern** - Multiple STT model backends

---

## 📦 Project Structure (Updated)

```
persian-deal-analyzer/
├── database/              # ✅ Complete
├── models/                # ✅ Complete
├── services/
│   ├── deal_service.py           # ✅ Complete
│   ├── sentiment_service.py      # ✅ Complete
│   ├── analytics_service.py      # ✅ Complete
│   ├── cache_service.py          # ✅ Complete
│   ├── rag_service.py            # 🔴 NEW - To implement
│   ├── stt_service.py            # 🔴 NEW - To implement
│   └── moe_service.py            # 🔴 NEW - To implement
├── mcp_spec/              # ✅ Complete (needs new tools)
├── tests/                 # ✅ Complete (needs new tests)
├── config/                # ✅ Complete
├── utils/                 # ✅ Complete
├── gradio_mcp_client.py   # ✅ Complete (needs new tabs)
├── main.py                # ✅ Complete
└── requirements.txt       # 🟡 Needs updates for new deps

NEW Directories:
├── vector_store/          # 🔴 ChromaDB data
├── audio_files/           # 🔴 Uploaded audio storage
└── models_cache/          # 🔴 Downloaded model weights
```

---

## 🚀 Quick Start (Current System)

```bash
# 1. Start services
docker-compose up -d  # Redis + PostgreSQL

# 2. Run MCP server
python main.py

# 3. Run Gradio interface
python launch_gradio.py

# 4. Run tests
pytest tests/ --cov
```

---

## 📈 Performance Targets

### Current Performance:
- Sentiment Analysis: ~200-400ms per text
- Deal Query: ~20-50ms
- Analytics: ~300-600ms
- Test Coverage: 85%+

### Target Performance (with new features):
- RAG Search: <500ms per query
- STT Transcription: ~1-3 seconds per minute of audio
- MoE Routing: <50ms (router only)
- Expert Inference: 100-500ms depending on expert
- End-to-end (RAG + MoE): <2 seconds

---

## 💾 Storage Requirements

### Current:
- Database: ~100MB (typical CRM data)
- Redis: ~50MB (cache)
- Models: ~2GB (sentiment model)

### After New Features:
- ChromaDB: ~500MB (embedded CRM data)
- STT Models: ~3GB (whisper-large) or ~1GB (medium)
- MoE Models: ~4-6GB (all 4 experts)
- Audio Files: Variable (user uploads)

**Total Estimated: ~15GB**

---

## 🎯 Success Criteria

### Core System (Already Met ✅):
- ✅ All tests passing
- ✅ MCP server functional
- ✅ Gradio interface responsive
- ✅ Sentiment analysis accurate
- ✅ Analytics providing insights
- ✅ Cache working efficiently

### New Features (To Achieve):
- 🔴 RAG returns relevant deals with >80% accuracy
- 🔴 STT transcribes Persian audio with <10% WER
- 🔴 MoE router selects correct expert >90% of time
- 🔴 All experts perform their tasks accurately
- 🔴 End-to-end latency <3 seconds
- 🔴 New tests achieve >85% coverage

---

**Last Updated:** December 2025  
**Status:** Core Complete, Enhancement Phase  
**Next Milestone:** Speech-to-Text Integration