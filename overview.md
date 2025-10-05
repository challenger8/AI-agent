# Persian Deal Analyzer - Project Overview

## 📋 Executive Summary

A comprehensive MCP (Model Context Protocol) server for Persian CRM deal analysis with sentiment insights, featuring both API access and a Gradio web interface. The system provides automated sentiment analysis on Persian text, deal activity tracking, and advanced analytics for CRM pipeline management.

**Current Status:** 🟡 Development/Pre-Production (Core functionality ~70% complete)

---

## 🏗️ Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Client Layer                          │
├─────────────────────────────────────────────────────────┤
│  MCP Protocol Clients  │  Gradio Web Interface          │
│  (Claude Desktop, etc) │  (Browser-based UI)            │
└────────────┬────────────┴──────────────┬─────────────────┘
             │                           │
             ▼                           ▼
┌─────────────────────────────────────────────────────────┐
│                    API Layer                             │
├─────────────────────────────────────────────────────────┤
│  MCP Server (mcp_spec/server.py)                        │
│  - Tool Handlers      - Resource Handlers                │
│  - Protocol Management                                   │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                  Services Layer                          │
├─────────────────────────────────────────────────────────┤
│  Deal Service  │  Sentiment Service  │  Analytics Service│
│  - CRUD ops    │  - Persian NLP      │  - Health Scoring │
│  - Timelines   │  - HF Transformers  │  - Insights Gen.  │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                Repository Layer                          │
├─────────────────────────────────────────────────────────┤
│  Deal Repo  │  Activity Repo  │  Agent Repo  │ Sentiment│
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│                  Data Layer                              │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL Database  │  Redis Cache  │  File Storage    │
└─────────────────────────────────────────────────────────┘
```

---

## ✅ Completed Components

### 1. Database Layer (`database/`)

**Status:** ✅ **Complete & Functional**

#### `database.py` - Database Manager
- PostgreSQL connection with pooling
- Query execution methods (SELECT, INSERT, UPDATE, DELETE)
- Batch operations support
- Transaction management
- SSH tunnel support for remote databases
- Health checks and statistics
- Backup utilities

**Key Features:**
- Connection pooling with psycopg2
- Automatic placeholder conversion (? → %s)
- Context manager support
- Comprehensive error handling

#### `models/` - Data Models
**Complete Models:**
- ✅ `Deal` - Business deal representation
- ✅ `DealActivity` - Activities/interactions on deals
- ✅ `CRMAgent` - Team members and roles
- ✅ `SentimentAnalysis` - Sentiment analysis results

**Repository Pattern:**
- ✅ `DealRepository` - Deal CRUD operations
- ✅ `DealActivityRepository` - Activity management
- ✅ `CRMAgentRepository` - Agent management with performance metrics
- ✅ `SentimentRepository` - Sentiment result storage
- ✅ `RepositoryManager` - Unified repository access

**Migration Utility:**
- ✅ `simplified_migration_utility.py` - CSV to database migration
- ✅ Data type conversion and validation
- ✅ Integrity validation
- ✅ Migration reporting

### 2. Services Layer (`services/`)

**Status:** 🟡 **Partially Complete**

#### ✅ `base_service.py` - Base Service Class
- Common functionality for all services
- Caching support
- Field validation
- Safe execution wrapper
- Logging integration

#### ✅ `deal_service.py` - Deal Management Service
**Implemented Methods:**
- `get_deal(deal_id)` - Retrieve single deal
- `get_deals_by_status(status)` - Filter by status
- `get_all_deals()` - Retrieve all deals
- `get_deals_summary(days)` - Summary statistics
- `get_deal_timeline(deal_id)` - Deal timeline with milestones
- `_calculate_deal_duration()` - Duration calculation

#### ✅ `sentiment_service.py` - Sentiment Analysis Service
**Implemented Methods:**
- `initialize()` - Load Persian sentiment model
- `analyze_text(text)` - Single text analysis
- `analyze_batch(texts)` - Batch analysis
- `analyze_activities_sentiment(activities)` - Activity-based analysis
- `get_sentiment_trends(activities, days)` - Temporal trends
- Caching for sentiment results
- Support for HooshvareLab BERT-based Persian model

**Key Features:**
- Hugging Face Transformers integration
- Persian language support
- Label mapping (مثبت/خنثی/منفی)
- Confidence scoring
- Text truncation for long inputs

#### ⚠️ `analytics_service.py` - Advanced Analytics Service
**Status:** 🔴 **INCOMPLETE - CRITICAL**

**Current State:**
```python
def analyze_deal_comprehensive(self, deal_id: int) -> Dict[str, Any]:
    """
    Comprehensive
    """
    # TRUNCATED - NOT IMPLEMENTED
```

**Missing Implementations:**
- `analyze_deal_comprehensive()` - Full deal analysis
- `analyze_portfolio_overview()` - Portfolio-wide analytics
- `analyze_portfolio_health()` - Health scoring
- `_create_activity_timeline()` - Timeline generation
- Health score calculation algorithm
- Risk indicator identification
- Insight generation

### 3. MCP Server (`mcp_spec/`)

**Status:** ✅ **Complete** (but depends on incomplete AnalyticsService)

#### `server.py` - Main MCP Server
**Implemented Features:**
- Clean server initialization
- Service dependency injection
- Lifecycle management (startup/shutdown)
- Health status reporting
- Async service initialization
- Proper cleanup on exit

**Initialization Flow:**
1. Database connection setup
2. Repository creation
3. Sentiment service initialization (async)
4. Analytics service initialization
5. Handler initialization
6. MCP protocol handler registration

#### `handlers/tool_handlers.py` - MCP Tool Handlers
**Implemented Tools:**
- ✅ `analyze_deal` - Comprehensive deal analysis
- ✅ `analyze_deals_overview` - Portfolio analysis
- ✅ `get_deal_activities_with_sentiment` - Activities with sentiment
- ✅ `analyze_portfolio_health` - Health metrics
- ✅ `analyze_text_sentiment` - Text sentiment analysis
- ✅ `get_sentiment_trends` - Temporal sentiment trends

**Features:**
- Input schema validation
- Error handling and logging
- Async model loading on demand
- JSON response formatting

#### `handlers/resource_handlers.py` - MCP Resource Handlers
**Implemented Resources:**
- ✅ `deals://dashboard` - Comprehensive dashboard
- ✅ `deals://portfolio-health` - Health metrics
- ✅ `deals://activity-summary` - Activity summary
- ✅ `deals://sentiment-overview` - Sentiment overview
- ✅ `deals://sentiment-trends` - Temporal trends

#### `schemas/tool_schemas.py` - Input Schemas
- ✅ All tool input schemas defined
- ✅ Type validation
- ✅ Required field specification
- ✅ Enum constraints for known values

### 4. Web Interface (`gradio_mcp_client.py`)

**Status:** ✅ **Complete & Functional**

#### Features:
- **Server Connection Tab:**
  - Connect to MCP server
  - Real-time status display
  - Service availability indicators

- **Sentiment Analysis Tab:**
  - Text input for analysis
  - Language selection (Persian/English)
  - Visualization with Plotly
  - Confidence scoring display

- **Deal Analytics Tab:**
  - Date range selection
  - Activity charts
  - Sentiment distribution
  - Summary statistics

- **Sentiment Trends Tab:**
  - Period selection (7d, 30d, 90d, 180d)
  - Trend visualization
  - Summary metrics

**Technical Implementation:**
- Async/sync wrappers for Gradio compatibility
- Event loop management
- Mock data fallback for testing
- Error handling and user feedback
- Responsive layout with Gradio Blocks

### 5. Configuration & Utilities

#### ✅ `config/settings.py` - Configuration Management
**Settings Classes:**
- `AppSettings` - Application metadata
- `MCPSettings` - MCP server configuration
- `SentimentSettings` - Model configuration
- `AnalysisSettings` - Analytics thresholds
- `PathSettings` - Directory management
- `FeatureFlags` - Feature toggles

#### ✅ `utils/logging_config.py` - Logging Setup
- Centralized logging configuration
- Multiple formatters (simple/detailed)
- File and console handlers
- Module-specific loggers

#### ✅ `utils/exceptions.py` - Custom Exceptions
- `PersianDealAnalyzerError` - Base exception
- `DatabaseError` - Database issues
- `ServiceError` - Service layer errors
- `SentimentAnalysisError` - Sentiment errors
- `ValidationError` - Input validation
- `ConfigurationError` - Config issues
- `MCPServerError` - MCP protocol errors

### 6. Deployment Configuration

#### ✅ Docker Support
**Files:**
- `docker-compose.yml` - Multi-service orchestration
- `Dockerfile` (mentioned in docker_setup.txt)
- `.dockerignore` - Build optimization

**Services Defined:**
- `deal-analyzer-web` - Gradio interface (port 7860)
- `deal-analyzer-mcp` - MCP server
- `nginx` - Reverse proxy (ports 80/443)
- `redis` - Caching layer (port 6379)
- PostgreSQL support (commented out)

**Features:**
- Volume mounts for logs, models, cache
- Health checks
- Resource limits
- Restart policies
- Network isolation

#### ✅ Dependency Management
- `requirements.txt` - Main dependencies
- `requirements_gradio.txt` - Web interface dependencies
- `pyproject.toml` - Project metadata and optional dependencies

---

## 🚧 Incomplete Components

### 1. Analytics Service (CRITICAL)

**File:** `services/analytics_service.py`

**Problem:** Implementation is truncated at line 24

**Impact:** 
- MCP tools cannot provide comprehensive analytics
- Health scoring non-functional
- Portfolio analysis unavailable
- Insight generation missing

**Required Implementations:**

```python
def analyze_deal_comprehensive(self, deal_id: int) -> Dict[str, Any]:
    """
    Combine deal data, activities, and sentiment into comprehensive analysis
    
    Returns:
    {
        "deal": {...},
        "activities": [...],
        "sentiment_summary": {...},
        "health_score": 85,
        "risk_indicators": [...],
        "recommendations": [...]
    }
    """
    # TODO: Implement
    pass

def analyze_portfolio_overview(self, status=None, days=30) -> Dict[str, Any]:
    """
    Portfolio-wide analytics
    
    Returns:
    {
        "summary": {...},
        "activity_breakdown": {...},
        "sentiment_overview": {...},
        "health_overview": {...},
        "insights": [...]
    }
    """
    # TODO: Implement
    pass

def analyze_portfolio_health(self, status_filter=None, days=30) -> Dict[str, Any]:
    """
    Health scoring and risk identification
    
    Returns:
    {
        "overall_health_score": 75,
        "deals_by_health": {...},
        "risk_indicators": [...],
        "recommendations": [...]
    }
    """
    # TODO: Implement
    pass

def _create_activity_timeline(self, activities) -> List[Dict]:
    """Generate chronological timeline of activities"""
    # TODO: Implement
    pass

def _calculate_health_score(self, deal, activities, sentiments) -> int:
    """
    Calculate health score (0-100) based on:
    - Activity recency
    - Activity frequency
    - Sentiment trends
    - Deal age
    - Status progression
    """
    # TODO: Implement using AnalysisSettings thresholds
    pass
```

### 2. Database Schema & Migrations

**Missing:**
- ❌ SQL schema files
- ❌ Migration system (Alembic or custom)
- ❌ Seed data scripts
- ❌ Schema versioning

**Issues:**
- Table name inconsistency: code references both `crmteam` and `crm_agents`
- `deal_activities.sentiment_score` and `sentiment_label` columns mentioned in code but may not exist in database
- No formal migration history

**Needed:**
```sql
-- database/migrations/001_initial_schema.sql
CREATE TABLE deals (...);
CREATE TABLE deal_activities (...);
CREATE TABLE crm_agents (...);
CREATE TABLE sentiment_analysis (...);

-- Indexes for performance
CREATE INDEX idx_deals_status ON deals(status);
CREATE INDEX idx_activities_deal_id ON deal_activities(deal_id);
CREATE INDEX idx_activities_date ON deal_activities(register_date);

-- database/migrations/002_add_sentiment_columns.sql
ALTER TABLE deal_activities 
ADD COLUMN sentiment_score FLOAT,
ADD COLUMN sentiment_label VARCHAR(50);
```

### 3. Redis Integration

**Status:** Docker service defined but not integrated in code

**Missing:**
- ❌ Redis client wrapper
- ❌ Cache service layer
- ❌ Caching decorators
- ❌ Cache invalidation strategy

**Needed:**
```python
# services/cache_service.py
class CacheService:
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def cache_sentiment(self, text_hash, result, ttl=3600):
        """Cache sentiment analysis result"""
        pass
    
    def get_cached_sentiment(self, text_hash):
        """Retrieve cached sentiment"""
        pass
    
    def cache_analytics(self, key, data, ttl=300):
        """Cache analytics results"""
        pass
```

### 4. Testing Suite

**Missing:**
- ❌ Unit tests
- ❌ Integration tests
- ❌ Test fixtures
- ❌ Test data
- ❌ CI/CD pipeline
- ❌ Coverage reporting

**Needed Structure:**
```
tests/
├── conftest.py                  # Pytest fixtures
├── test_database/
│   ├── test_database.py        # Database manager tests
│   └── test_repositories.py    # Repository tests
├── test_services/
│   ├── test_deal_service.py
│   ├── test_sentiment_service.py
│   └── test_analytics_service.py
├── test_mcp/
│   ├── test_server.py
│   ├── test_handlers.py
│   └── test_schemas.py
├── test_models/
│   └── test_data_models.py
└── test_integration/
    ├── test_end_to_end.py
    └── test_gradio_interface.py
```

### 5. Production Infrastructure

#### Security (CRITICAL for Production)
**Missing:**
- ❌ Authentication system
- ❌ Authorization/RBAC
- ❌ API rate limiting
- ❌ Input sanitization
- ❌ SQL injection prevention (using parameterized queries - good, but needs review)
- ❌ XSS prevention in Gradio interface
- ❌ CORS configuration
- ❌ Secrets management (credentials in .env file)

#### Monitoring & Observability
**Missing:**
- ❌ Prometheus metrics
- ❌ Grafana dashboards
- ❌ Error tracking (Sentry)
- ❌ Request tracing
- ❌ Performance monitoring
- ❌ Alert system

**Needed:**
```python
# services/monitoring.py
from prometheus_client import Counter, Histogram, Gauge

request_count = Counter('mcp_requests_total', 'Total requests', ['tool', 'status'])
request_duration = Histogram('mcp_request_duration_seconds', 'Request duration')
model_inference_time = Histogram('sentiment_inference_seconds', 'Model inference time')
active_connections = Gauge('mcp_active_connections', 'Active connections')
```

#### Deployment
**Missing:**
- ❌ Production-ready Nginx configuration
- ❌ SSL/TLS certificate management
- ❌ Environment-specific configurations
- ❌ Kubernetes manifests (mentioned in docker_setup.txt but not complete)
- ❌ Health check endpoints
- ❌ Graceful shutdown handling
- ❌ Database backup strategy

### 6. Documentation

**Missing:**
- ❌ API documentation (OpenAPI/Swagger)
- ❌ Deployment guide
- ❌ Developer guide
- ❌ User guide for Gradio interface
- ❌ Architecture decision records (ADRs)
- ❌ Troubleshooting guide

**Needed:**
```
docs/
├── api/
│   ├── mcp_protocol.md
│   ├── tools.md
│   └── resources.md
├── deployment/
│   ├── requirements.md
│   ├── installation.md
│   ├── configuration.md
│   └── troubleshooting.md
├── development/
│   ├── architecture.md
│   ├── contributing.md
│   ├── testing.md
│   └── code_style.md
└── user_guide/
    ├── gradio_interface.md
    └── use_cases.md
```

---

## 🎯 Production Readiness Roadmap

### Phase 1: Complete Core Functionality (1-2 weeks)

**Priority: CRITICAL**

#### Week 1: Analytics Service
- [ ] Implement `analyze_deal_comprehensive()`
  - Combine deal, activities, sentiment data
  - Calculate derived metrics
  - Generate insights
- [ ] Implement `analyze_portfolio_overview()`
  - Aggregate statistics
  - Activity pattern analysis
  - Sentiment distribution
- [ ] Implement health scoring algorithm
  - Define scoring components
  - Apply weights from AnalysisSettings
  - Calculate risk indicators
- [ ] Implement `_create_activity_timeline()`
  - Sort chronologically
  - Identify milestones
  - Calculate durations

#### Week 2: Database & Integration
- [ ] Create database schema files
  - Initial schema SQL
  - Migration scripts
  - Seed data
- [ ] Set up Alembic for migrations
  - Initialize Alembic
  - Create migration templates
  - Version control
- [ ] Integrate Redis caching
  - Create CacheService
  - Implement caching decorators
  - Cache sentiment results
  - Cache analytics queries
- [ ] Test data migration utility
  - Test with real CSV data
  - Validate data integrity
  - Performance testing

### Phase 2: Testing & Quality Assurance (1 week)

**Priority: HIGH**

#### Unit Tests (3 days)
- [ ] Database layer tests
  - Connection management
  - Query execution
  - Repository operations
- [ ] Service layer tests
  - DealService methods
  - SentimentService with mock model
  - Analytics calculations
- [ ] MCP server tests
  - Handler routing
  - Schema validation
  - Response formatting

#### Integration Tests (2 days)
- [ ] End-to-end MCP tool calls
- [ ] Database → Service → API flow
- [ ] Gradio interface functionality
- [ ] Docker container builds

#### Test Infrastructure (2 days)
- [ ] Set up pytest configuration
- [ ] Create test fixtures
- [ ] Mock external dependencies
- [ ] Set up coverage reporting (target: 80%+)

### Phase 3: Production Infrastructure (1-2 weeks)

**Priority: HIGH**

#### Security (3-4 days)
- [ ] Implement authentication
  - API key system for MCP
  - Session management for Gradio
  - JWT tokens
- [ ] Add authorization
  - Role-based access control
  - Permission checks
  - Deal ownership validation
- [ ] Security hardening
  - Rate limiting
  - Input validation
  - SQL injection review
  - XSS prevention
  - CORS configuration
- [ ] Secrets management
  - Move from .env to vault
  - Rotate credentials
  - Encryption at rest

#### Monitoring (2-3 days)
- [ ] Prometheus metrics
  - Request counters
  - Latency histograms
  - Error rates
  - Model performance
- [ ] Logging infrastructure
  - Structured logging
  - Log aggregation
  - Request tracing
- [ ] Error tracking
  - Sentry integration
  - Error alerting
  - Stack trace capture
- [ ] Dashboards
  - Grafana setup
  - Key metrics visualization
  - Alert rules

#### Deployment (2-3 days)
- [ ] Production Nginx config
  - SSL/TLS setup
  - Load balancing
  - Request buffering
  - Compression
- [ ] Environment configs
  - development.env
  - staging.env
  - production.env
- [ ] CI/CD pipeline
  - GitHub Actions or GitLab CI
  - Automated testing
  - Docker image building
  - Automated deployment
- [ ] Database backup
  - Automated backup script
  - Backup verification
  - Restore procedures
  - Retention policy

### Phase 4: Documentation (Ongoing)

**Priority: MEDIUM**

#### Week 1-2: Core Documentation
- [ ] API documentation
  - MCP protocol reference
  - Tool descriptions with examples
  - Resource schemas
- [ ] Deployment guide
  - System requirements
  - Step-by-step installation
  - Configuration reference
  - Troubleshooting guide

#### Week 3-4: User & Developer Docs
- [ ] Developer guide
  - Architecture overview
  - Code organization
  - Adding new features
  - Testing guidelines
  - Contributing guide
- [ ] User guide
  - Gradio interface walkthrough
  - Common use cases
  - FAQ
  - Screenshots/videos

### Phase 5: Performance Optimization (As Needed)

**Priority: LOW (unless performance issues identified)**

#### Database Optimization
- [ ] Query optimization
  - Identify slow queries
  - Add/optimize indexes
  - Query plan analysis
- [ ] Connection pooling tuning
- [ ] Read replicas for analytics

#### Caching Strategy
- [ ] Cache warming on startup
- [ ] Intelligent cache invalidation
- [ ] Cache hit rate monitoring

#### Model Optimization
- [ ] Model quantization for faster inference
- [ ] Batch processing optimization
- [ ] GPU support (if available)

#### API Optimization
- [ ] Response pagination
- [ ] Field filtering
- [ ] Async processing for heavy operations
- [ ] Request queuing

---

## 📊 Current Status Summary

### Completion Percentage by Component

| Component | Status | Completion | Notes |
|-----------|--------|------------|-------|
| **Database Layer** | ✅ | 95% | Missing formal migrations |
| **Data Models** | ✅ | 100% | Complete and functional |
| **Repositories** | ✅ | 100% | Well-structured |
| **Deal Service** | ✅ | 100% | Fully implemented |
| **Sentiment Service** | ✅ | 95% | Needs Redis integration |
| **Analytics Service** | 🔴 | 20% | CRITICAL: Incomplete |
| **MCP Server** | ✅ | 90% | Depends on Analytics |
| **Tool Handlers** | ✅ | 100% | Complete |
| **Resource Handlers** | ✅ | 100% | Complete |
| **Gradio Interface** | ✅ | 100% | Functional |
| **Configuration** | ✅ | 90% | Needs secrets mgmt |
| **Docker Setup** | ✅ | 80% | Needs production config |
| **Testing** | 🔴 | 0% | Not started |
| **Documentation** | 🟡 | 30% | Basic README only |
| **Security** | 🔴 | 10% | Not production-ready |
| **Monitoring** | 🔴 | 5% | Logging only |

**Overall Project Completion: ~65%**

### Blocking Issues

1. **CRITICAL:** Analytics Service incomplete - blocks full MCP functionality
2. **HIGH:** No test coverage - risky for production
3. **HIGH:** No authentication - security vulnerability
4. **MEDIUM:** Missing database migrations - deployment inconsistency
5. **MEDIUM:** Redis defined but not integrated - performance impact

---

## 💡 Architecture Strengths

### What's Working Well

1. **Clean Separation of Concerns**
   - Clear layering (Data → Repository → Service → API)
   - Each layer has single responsibility
   - Easy to test and maintain

2. **Repository Pattern**
   - Abstracts database operations
   - Easy to swap database implementations
   - Testable without database

3. **Service-Oriented Design**
   - Business logic isolated in services
   - Reusable across MCP and web interfaces
   - Easy to extend with new features

4. **MCP Protocol Implementation**
   - Proper tool and resource handlers
   - Schema validation
   - Clean async initialization

5. **Dual Interface Support**
   - MCP protocol for AI assistants
   - Gradio for human users
   - Both use same backend services

6. **Configuration Management**
   - Centralized settings
   - Feature flags for easy toggling
   - Environment-based configuration

7. **Docker Support**
   - Multi-service orchestration
   - Easy local development
   - Ready for containerized deployment

### Design Patterns Used

- **Repository Pattern** - Data access abstraction
- **Service Pattern** - Business logic encapsulation
- **Factory Pattern** - Object creation (create_repositories, create_mcp_server)
- **Dependency Injection** - Services receive dependencies in constructor
- **Strategy Pattern** - Different sentiment models can be swapped
- **Singleton Pattern** - Database manager singleton
- **Template Method** - BaseService for common functionality

---

## 🔧 Technology Stack

### Core Technologies
- **Language:** Python 3.11+
- **Database:** PostgreSQL 15+
- **Cache:** Redis 7
- **Web Server:** Nginx 1.25
- **ML Framework:** Hugging Face Transformers
- **MCP:** Model Context Protocol SDK
- **Web UI:** Gradio 4.0+

### Key Python Libraries
- **Database:** psycopg2-binary, SQLAlchemy
- **Data:** pandas, numpy
- **ML/NLP:** transformers, torch, tokenizers
- **Visualization:** plotly
- **Networking:** paramiko (SSH tunnels)
- **Configuration:** python-dotenv
- **Async:** asyncio, aiofiles

### Development Tools (Needed)
- **Testing:** pytest, pytest-asyncio, pytest-cov
- **Linting:** black, isort, flake8, mypy
- **Documentation:** Sphinx, mkdocs
- **CI/CD:** GitHub Actions / GitLab CI
- **Monitoring:** Prometheus, Grafana, Sentry

---

## 🚀 Quick Start Guide

### Prerequisites
```bash
# System requirements
- Python 3.11+
- PostgreSQL 15+
- Redis 7+ (optional but recommended)
- Docker & Docker Compose (for containerized deployment)
- 4GB+ RAM
- 10GB+ disk space (for models)
```

### Installation

#### Option 1: Local Development
```bash
# 1. Clone repository
git clone <repository-url>
cd persian-deal-analyzer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# 5. Set up database
python scripts/setup_db.py  # TODO: Create this script

# 6. Run migrations
python scripts/migrate.py   # TODO: Create this script

# 7. (Optional) Import sample data
python models/simplified_migration_utility.py

# 8. Run MCP server
python main.py

# 9. (In another terminal) Run Gradio interface
python launch_gradio.py
```

#### Option 2: Docker
```bash
# 1. Clone repository
git clone <repository-url>
cd persian-deal-analyzer

# 2. Create .env file
cp .env.example .env
# Edit .env with your settings

# 3. Build and start services
docker-compose up -d

# 4. Check status
docker-compose ps

# 5. View logs
docker-compose logs -f

# Access Gradio interface at http://localhost:7860
# MCP server available for protocol connections
```

### Verification
```bash
# Test database connection
python -c "from database.database import test_database_connection; test_database_connection()"

# Test sentiment model loading
python -c "from services.sentiment_service import SentimentService; import asyncio; s = SentimentService(); asyncio.run(s.initialize()); print('Model loaded:', s.model_loaded)"

# Check Gradio interface
curl http://localhost:7860
```

---

## 📈 Performance Considerations

### Current Limitations
1. **Sentiment Model Loading:** ~5-10 seconds on first request
2. **No Query Caching:** Repeated queries hit database
3. **Synchronous Processing:** Sentiment analysis blocks requests
4. **No Connection Pooling Limits:** Can exhaust database connections

### Optimization Opportunities
1. **Model Preloading:** Load sentiment model at startup
2. **Redis Caching:** Cache frequent queries and sentiment results
3. **Async Processing:** Queue sentiment analysis with Celery
4. **Query Optimization:** Add indexes, optimize N+1 queries
5. **Response Pagination:** Limit large result sets
6. **Model Quantization:** Reduce model size for faster inference
7. **Read Replicas:** Separate analytics queries from OLTP

### Expected Performance (Estimated)
- **Sentiment Analysis:** ~100-500ms per text (CPU), ~50-100ms (GPU)
- **Deal Query:** ~10-50ms (with indexes)
- **Analytics Dashboard:** ~200-500ms (needs optimization)
- **Concurrent Users:** ~10-50 (current), ~100-500 (with optimization)

---

## 🔐 Security Considerations

### Current Security Posture: 🔴 **NOT PRODUCTION-READY**

#### Vulnerabilities
1. **No Authentication:** Anyone can access MCP server and Gradio interface
2. **No Authorization:** No permission checks on data access
3. **Credentials in .env:** Database passwords in plain text
4. **No Rate Limiting:** Susceptible to DoS attacks
5. **No Input Sanitization:** Potential injection risks
6. **No HTTPS:** Data transmitted in plain text
7. **No Audit Logging:** Can't track who did what

#### Remediation Required Before Production
- [ ] Implement authentication (API keys, JWT)
- [ ] Add RBAC for authorization
- [ ] Use secrets manager (HashiCorp Vault, AWS Secrets Manager)
- [ ] Add rate limiting (per IP, per user)
- [ ] Validate and sanitize all inputs
- [ ] Set up SSL/TLS with Let's Encrypt
- [ ] Implement audit logging
- [ ] Regular security scanning (Snyk, OWASP ZAP)
- [ ] Penetration testing

---

## 📞 Support & Contribution

### Getting Help
- **Issues:** File issues in repository