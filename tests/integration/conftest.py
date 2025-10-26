"""
tests/integration/conftest.py
-----------------------------
Integration test fixtures - Real services, real database
Scope: module (shared across integration test suite)
"""
import pytest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.database import create_database_manager
from models.repositories import create_repositories
from services.deal_service import DealService
from services.sentiment_service import SentimentService
from services.analytics_service import AnalyticsService
from services.cache_service import get_cache_service


# ============================================================================
# SERVICE AVAILABILITY CHECKS (inherited from root conftest)
# ============================================================================

def check_database_available():
    """Check if PostgreSQL is available"""
    try:
        db = create_database_manager()
        result = db.test_connection()
        db.close()
        return result
    except Exception:
        return False


def check_redis_available():
    """Check if Redis is available"""
    try:
        import redis
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', 6379))
        r = redis.Redis(host=host, port=port, socket_connect_timeout=2, socket_timeout=2)
        r.ping()
        return True
    except Exception:
        return False


def check_chromadb_available():
    """Check if ChromaDB is available"""
    try:
        import chromadb
        from config.rag_settings import RAGSettings
        RAGSettings.validate_paths()
        client = chromadb.PersistentClient(path=str(RAGSettings.CHROMA_DB_DIR))
        return True
    except Exception:
        return False


# ============================================================================
# REAL DATABASE FIXTURES (scope=module for efficiency)
# ============================================================================

@pytest.fixture(scope="module")
def integration_db():
    """Real database connection for integration tests (module scope)"""
    if not check_database_available():
        pytest.skip("Database not available")
    
    db = create_database_manager()
    yield db
    db.close()


@pytest.fixture(scope="module")
def integration_repositories(integration_db):
    """Real repositories connected to real database (module scope)"""
    repos = create_repositories(integration_db)
    yield repos
    repos.close() if hasattr(repos, 'close') else None


# ============================================================================
# REAL SERVICE FIXTURES (scope=module, use real repositories)
# ============================================================================

@pytest.fixture(scope="module")
def integration_deal_service(integration_repositories):
    """Real DealService with real database"""
    return DealService(integration_repositories)


@pytest.fixture(scope="module")
def integration_sentiment_service(integration_repositories):
    """Real SentimentService with real database"""
    service = SentimentService(integration_repositories)
    service.model_loaded = False  # Don't actually load model in tests
    service.available = False
    return service


@pytest.fixture(scope="module")
def integration_analytics_service(integration_repositories, integration_sentiment_service):
    """Real AnalyticsService with real services"""
    return AnalyticsService(integration_repositories, integration_sentiment_service)


# ============================================================================
# CACHE SERVICE FIXTURE (optional, real or mock)
# ============================================================================

@pytest.fixture(scope="module")
def integration_cache_service():
    """Real Redis cache if available, mock fallback"""
    if check_redis_available():
        try:
            return get_cache_service()
        except Exception:
            pass
    
    # Fallback to mock
    mock_cache = Mock()
    mock_cache.get = Mock(return_value=None)
    mock_cache.set = Mock(return_value=True)
    mock_cache.delete = Mock(return_value=True)
    mock_cache.clear = Mock(return_value=True)
    mock_cache.is_available = Mock(return_value=False)
    return mock_cache


# ============================================================================
# VECTOR STORE FIXTURES (for RAG integration tests)
# ============================================================================

@pytest.fixture(scope="module")
def temp_chromadb_dir():
    """Temporary directory for ChromaDB during integration tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture(scope="module")
def integration_vector_store(integration_repositories, temp_chromadb_dir):
    """Vector store service for RAG testing"""
    if not check_chromadb_available():
        pytest.skip("ChromaDB not available")
    
    try:
        from services.vector_store_service import VectorStoreService
        store = VectorStoreService(integration_repositories, persist_dir=temp_chromadb_dir)
        yield store
    except Exception as e:
        pytest.skip(f"Vector store initialization failed: {e}")


@pytest.fixture(scope="module")
def integration_embedding_service(integration_repositories):
    """Embedding service for RAG testing"""
    try:
        from services.embedding_service import EmbeddingService
        service = EmbeddingService(integration_repositories)
        yield service
    except Exception as e:
        pytest.skip(f"Embedding service initialization failed: {e}")


# ============================================================================
# TEST DATA FIXTURES (function scope for fresh data per test)
# ============================================================================

@pytest.fixture(scope="function")
def sample_deal_from_db(integration_repositories):
    """Get a real deal from database"""
    try:
        deals = integration_repositories.deals.get_all_deals()
        if deals:
            return deals[0]
    except Exception:
        pass
    return None


@pytest.fixture(scope="function")
def sample_deals_from_db(integration_repositories):
    """Get real deals from database"""
    try:
        return integration_repositories.deals.get_all_deals()
    except Exception:
        return []


@pytest.fixture(scope="function")
def sample_activities_from_db(integration_repositories):
    """Get real activities from database"""
    try:
        return integration_repositories.activities.get_all_activities()
    except Exception:
        return []


# ============================================================================
# PYTEST HOOKS (auto-skip if services unavailable)
# ============================================================================

def pytest_collection_modifyitems(config, items):
    """Auto-skip integration tests if services not available"""
    skip_integration = pytest.mark.skip(reason="Integration services not available")
    
    for item in items:
        if "integration" in str(item.fspath):
            if not check_database_available():
                item.add_marker(skip_integration)