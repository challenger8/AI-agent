"""
tests/conftest.py
=================
Root-level pytest configuration and shared utilities

This file contains:
- Pytest hooks (configuration, test collection)
- Service availability checks (reusable across all test types)
- Environment setup
- Shared constants

Unit-specific fixtures → moved to tests/unit/conftest.py
Integration-specific fixtures → moved to tests/integration/conftest.py
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock

import pytest
from dotenv import load_dotenv

# ============================================================================
# ENVIRONMENT & PATHS
# ============================================================================

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# ============================================================================
# SERVICE AVAILABILITY DETECTION (Shared across all tests)
# ============================================================================

def check_database_available():
    """Check if PostgreSQL database is available"""
    try:
        from database.database import DatabaseManager
        db = DatabaseManager()
        result = db.test_connection()
        db.close()
        print("✅ Database available")
        return result
    except Exception as e:
        print(f"⚠️  Database unavailable: {type(e).__name__}")
        return False


def check_redis_available():
    """Check if Redis is available"""
    try:
        import redis
        host = os.getenv('REDIS_HOST', 'localhost')
        port = int(os.getenv('REDIS_PORT', 6379))
        r = redis.Redis(
            host=host, 
            port=port, 
            socket_connect_timeout=2,
            socket_timeout=2
        )
        r.ping()
        print("✅ Redis available")
        return True
    except Exception as e:
        print(f"⚠️  Redis unavailable: {type(e).__name__}")
        return False


def check_chromadb_available():
    """Check if ChromaDB is available"""
    try:
        import chromadb
        from config.rag_settings import RAGSettings
        RAGSettings.validate_paths()
        client = chromadb.PersistentClient(path=str(RAGSettings.CHROMA_DB_DIR))
        print("✅ ChromaDB available")
        return True
    except Exception as e:
        print(f"⚠️  ChromaDB unavailable: {type(e).__name__}")
        return False


# Cache availability status to avoid repeated checks
_service_status = {
    'database': None,
    'redis': None,
    'chromadb': None
}


def get_service_status(service_name: str) -> bool:
    """
    Get cached service availability status
    
    Args:
        service_name: 'database', 'redis', or 'chromadb'
        
    Returns:
        Boolean indicating if service is available
    """
    if _service_status[service_name] is None:
        if service_name == 'database':
            _service_status[service_name] = check_database_available()
        elif service_name == 'redis':
            _service_status[service_name] = check_redis_available()
        elif service_name == 'chromadb':
            _service_status[service_name] = check_chromadb_available()
    return _service_status[service_name]


# ============================================================================
# PYTEST CONFIGURATION & HOOKS
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest at startup
    
    Registers custom markers for test categorization
    """
    markers = [
        "unit: Unit tests (fast, mocked, no dependencies)",
        "integration: Integration tests (slower, uses real components)",
        "smoke: Smoke/verification tests",
        "slow: Slow running tests (>5 seconds)",
        "requires_db: Tests that require database connection",
        "requires_redis: Tests that require Redis",
        "requires_chromadb: Tests that require ChromaDB",
        "requires_gpu: Tests that require GPU",
        "asyncio: Async/await tests",
        "flaky: Tests known to be flaky/unreliable",
    ]
    
    for marker_desc in markers:
        config.addinivalue_line("markers", marker_desc)


def pytest_collection_modifyitems(config, items):
    """
    Automatically apply markers based on test location
    
    Rules:
    - tests/unit/* → @pytest.mark.unit
    - tests/integration/* → @pytest.mark.integration
    - tests/smoke/* → @pytest.mark.smoke
    """
    for item in items:
        path_str = str(item.fspath)
        
        if "integration" in path_str:
            item.add_marker(pytest.mark.integration)
        elif "unit" in path_str:
            item.add_marker(pytest.mark.unit)
        elif "smoke" in path_str:
            item.add_marker(pytest.mark.smoke)


# ============================================================================
# CLEANUP & TEARDOWN
# ============================================================================

@pytest.fixture(scope="function", autouse=True)
def cleanup_after_test():
    """
    Automatic cleanup after each test
    
    Runs after every test function regardless of location
    """
    yield
    # Cleanup code here if needed


# ============================================================================
# SHARED TEST CONFIGURATION
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """
    Shared test configuration constants
    
    Available to all tests across all categories
    """
    return {
        'test_db_name': 'persian_crm_test_db',
        'health_score_threshold_high': 70,
        'health_score_threshold_medium': 40,
        'stale_activity_days': 14,
        'aging_deal_days': 60
    }


# ============================================================================
# EXPORTS FOR SUBMODULES
# ============================================================================
# ============================================================================
# MOCK REPOSITORIES (Unit Tests)
# ============================================================================

@pytest.fixture
def mock_repositories():
    """
    Mock repository manager with stateful in-memory storage
    
    Tracks all created deals, activities, agents, and sentiments
    Returns proper values for nonexistent IDs instead of dummy data
    """
    repos = Mock()
    
    # In-memory storage for this test
    storage = {
        'deals': {},
        'activities': {},
        'agents': {},
        'sentiments': {}
    }
    
    # ===== DEALS =====
    repos.deals.create_deal = Mock(side_effect=lambda deal: (storage['deals'].update({deal.Id: deal}), deal.Id)[1])
    repos.deals.get_deal_by_id = Mock(side_effect=lambda deal_id: storage['deals'].get(deal_id))
    repos.deals.get_all_deals = Mock(side_effect=lambda: list(storage['deals'].values()))
    repos.deals.get_deals_by_status = Mock(side_effect=lambda status: [d for d in storage['deals'].values() if d.Status == status])
    repos.deals.update_deal = Mock(side_effect=lambda deal: (storage['deals'].update({deal.Id: deal}), True)[1])
    repos.deals.get_deals_statistics = Mock(return_value={'total_deals': len(storage['deals']), 'by_status': {}})
    
    # ===== ACTIVITIES =====
    repos.activities.create_activity = Mock(side_effect=lambda activity: (storage['activities'].update({activity.id: activity}), activity.id)[1])
    repos.activities.get_activity_by_id = Mock(side_effect=lambda activity_id: storage['activities'].get(activity_id))
    repos.activities.get_activities_by_deal = Mock(side_effect=lambda deal_id: [a for a in storage['activities'].values() if a.dealid == deal_id])
    repos.activities.get_pending_activities = Mock(side_effect=lambda: [a for a in storage['activities'].values() if not a.isdone])
    
    def update_sentiment(activity_id, sentiment_score, sentiment_label):
        """Update activity sentiment, return True if success"""
        if activity_id in storage['activities']:
            storage['activities'][activity_id].sentiment_score = sentiment_score
            storage['activities'][activity_id].sentiment_label = sentiment_label
            return True
        return False
    
    repos.activities.update_activity_sentiment = Mock(side_effect=update_sentiment)
    
    # ===== AGENTS =====
    repos.agents.create_agent = Mock(side_effect=lambda agent: (storage['agents'].update({agent.id: agent}), agent.id)[1])
    repos.agents.get_agent_by_id = Mock(side_effect=lambda agent_id: storage['agents'].get(agent_id))
    repos.agents.get_all_agents = Mock(side_effect=lambda: list(storage['agents'].values()))
    repos.agents.get_agents_by_role = Mock(side_effect=lambda role: [a for a in storage['agents'].values() if a.role == role])
    
    # ===== SENTIMENT =====
    repos.sentiment.save_sentiment = Mock(side_effect=lambda sentiment: (storage['sentiments'].update({len(storage['sentiments']) + 1: sentiment}), len(storage['sentiments']))[1])
    repos.sentiment.get_sentiment_by_activity = Mock(side_effect=lambda activity_id: next((s for s in storage['sentiments'].values() if getattr(s, 'activity_id', None) == activity_id), None))
    repos.sentiment.get_sentiments_by_deal = Mock(side_effect=lambda deal_id: [s for s in storage['sentiments'].values() if getattr(s, 'deal_id', None) == deal_id])
    
    # Context manager support
    repos.__enter__ = Mock(return_value=repos)
    repos.__exit__ = Mock(return_value=False)
    
    return repos
# These are available to unit/conftest.py and integration/conftest.py
__all__ = [
    'get_service_status',
    'check_database_available',
    'check_redis_available',
    'check_chromadb_available',
    'pytest_configure',
    'pytest_collection_modifyitems',
    'cleanup_after_test',
    'test_config',
]


# ============================================================================
# USEFUL NOTES
# ============================================================================
#
# This is the ROOT conftest.py that is shared by ALL tests.
# 
# For category-specific fixtures, see:
# - tests/unit/conftest.py (mock fixtures, unit test utilities)
# - tests/integration/conftest.py (real service fixtures, DB setup)
#
# The pytest collection system loads conftest.py files in this order:
# 1. tests/conftest.py (THIS FILE - root level)
# 2. tests/unit/conftest.py (for tests in unit/)
# 3. tests/integration/conftest.py (for tests in integration/)
#
# This means fixtures in subdir conftest.py override root conftest.py
#
# ============================================================================