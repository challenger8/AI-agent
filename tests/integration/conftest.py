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
import uuid
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from database.database import create_database_manager
from models.repositories import create_repositories
from models.deal_model import Deal, DealActivity, CRMAgent
from services.deal_service import DealService
from services.sentiment_service import SentimentService
from services.analytics_service import AnalyticsService
from services.cache_service import get_cache_service
from tests.conftest import (
    check_database_available,
    check_redis_available,
    check_chromadb_available
)
from tests.utils.test_helpers import parse_result

# ============================================================================
# SERVICE AVAILABILITY CHECKS (inherited from root conftest)
# ============================================================================
import json





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
# SAMPLE DATA FIXTURES - For testing with realistic data
# ============================================================================

@pytest.fixture(scope="function")
def sample_deal():
    """Sample Deal with realistic Persian data"""
    return Deal(
        Id=str(uuid.uuid4()),
        Title='فروش محصول نرم‌افزاری',
        Description='پروژه فروش سیستم ERP برای شرکت بزرگ',
        RegisterTime=datetime.now() - timedelta(days=30),
        Price=Decimal('50000000'),
        Status='در حال پیگیری',
        PipelineStageId='stage-001',
        PipelineId='pipeline-001',
        ChangeToWonTime=None,
        ChangeToLossTime=None,
        LastTrackingTime=datetime.now() - timedelta(days=2),
        NextTrackingTime=datetime.now() + timedelta(days=3),
        ExpectedCloseDate=datetime.now() + timedelta(days=30),
        LastActivityUpdateTime=datetime.now() - timedelta(days=1),
        LastUpdateTime=datetime.now(),
        Probability=0.65,
        ContactId='contact-001',
        OwnerId='owner-001',
        CreatorId='creator-001',
        LabelId='label-001',
        LostReasonId=None,
        Pin=False,
        IsIdle=False,
        IsRotten=False,
        Fields='{}',
        Items='[]',
        MobilePhone='+98912345678'
    )


@pytest.fixture(scope="function")
def sample_deals_list():
    """Sample list of Deals with different statuses"""
    deals = []
    statuses = ['Pending','Lost','Won']
    
    for i in range(10):
        deal = Deal(
            Id=str(uuid.uuid4()),
            Title=f'سند فروش شماره {i+1}',
            Description=f'توضیح پروژه شماره {i+1}',
            RegisterTime=datetime.now() - timedelta(days=50-i*5),
            Price=Decimal(str(10000000 * (i+1))),
            Status=statuses[i % 3],
            PipelineStageId=f'stage-{i%5}',
            PipelineId='pipeline-001',
            ChangeToWonTime=datetime.now() - timedelta(days=5) if i % 3 == 1 else None,
            ChangeToLossTime=datetime.now() - timedelta(days=10) if i % 3 == 2 else None,
            LastTrackingTime=datetime.now() - timedelta(days=i),
            NextTrackingTime=datetime.now() + timedelta(days=i+5),
            ExpectedCloseDate=datetime.now() + timedelta(days=60-i*5),
            LastActivityUpdateTime=datetime.now() - timedelta(days=i+1),
            LastUpdateTime=datetime.now(),
            Probability=max(0.1, 0.8 - (i*0.05)),
            ContactId=f'contact-{i}',
            OwnerId=f'owner-{i%3}',
            CreatorId='creator-001',
            LabelId=f'label-{i%4}',
            LostReasonId=None,
            Pin=False,
            IsIdle=i % 5 == 0,
            IsRotten=i % 7 == 0,
            Fields='{}',
            Items='[]',
            MobilePhone=f'+9891234567{i}'
        )
        deals.append(deal)
    
    return deals


@pytest.fixture(scope="function")
def sample_activity(sample_deal):
    """Sample DealActivity for a deal"""
    return DealActivity(
        id=str(uuid.uuid4()),
        title='تماس تلفنی با مشتری',
        note='مشتری برای دیدار توافق کرد',
        resultnote='نتیجه: موفق - قرار ملاقات تنظیم شد',
        activitytypeid='call',
        isprivate=False,
        isdone=True,
        ispinned=False,
        duedate=datetime.now() - timedelta(days=5),
        finishdate=datetime.now() - timedelta(days=5),
        donedate=datetime.now() - timedelta(days=5),
        registerdate=datetime.now() - timedelta(days=5),
        lastupdatetime=datetime.now() - timedelta(days=5),
        dealid=sample_deal.Id,
        creatorid='creator-001',
        ownerid='owner-001',
        updaterid='updater-001',
        sentiment_score=0.8,
        sentiment_label='مثبت'
    )


@pytest.fixture(scope="function")
def sample_activities_list(sample_deal):
    """Sample list of DealActivities"""
    activities = []
    activity_types = ['call', 'meeting', 'email', 'note']
    sentiments = ['مثبت', 'خنثی', 'منفی']
    titles = [
        'تماس تلفنی با مشتری',
        'جلسه حضوری',
        'ارسال پیشنهاد',
        'پیگیری پس از جلسه',
        'مذاکره قیمت',
    ]
    
    for i in range(12):
        activity = DealActivity(
            id=str(uuid.uuid4()),
            title=titles[i % len(titles)],
            note=f'یادداشت فعالیت شماره {i+1}',
            resultnote=f'نتیجه: {"موفق" if i % 2 == 0 else "نیاز به پیگیری"}',
            activitytypeid=activity_types[i % 4],
            isprivate=False,
            isdone=i % 3 != 0,
            ispinned=i == 0,
            duedate=datetime.now() - timedelta(days=20-i),
            finishdate=datetime.now() - timedelta(days=20-i) if i % 3 != 0 else None,
            donedate=datetime.now() - timedelta(days=20-i) if i % 3 != 0 else None,
            registerdate=datetime.now() - timedelta(days=25-i),
            lastupdatetime=datetime.now() - timedelta(days=18-i),
            dealid=sample_deal.Id,
            creatorid=f'creator-{i%2}',
            ownerid='owner-001',
            updaterid='updater-001',
            sentiment_score=0.4 + (i % 3) * 0.25,
            sentiment_label=sentiments[i % 3]
        )
        activities.append(activity)
    
    return activities


@pytest.fixture(scope="function")
def sample_agent():
    """Sample CRM Agent"""
    return CRMAgent(
        id=str(uuid.uuid4()),
        groupowner='تیم فروش اصلی',
        ownername='علی احمدی',
        adminid='admin-001',
        role='Senior Sales Executive',
        phone='+9851234567',
        mobilephone='+989123456789',
        personalid='1001234567',
        groupphone='+9851234500'
    )


@pytest.fixture(scope="function")
def sample_agents_list():
    """Sample list of CRM Agents"""
    agents = []
    agent_names = ['علی احمدی', 'فاطمه رضوی', 'حسن محمودی', 'مریم کریمی']
    
    for i, name in enumerate(agent_names):
        agent = CRMAgent(
            id=str(uuid.uuid4()),
            groupowner=f'تیم {i+1}',
            ownername=name,
            adminid=f'admin-{i}',
            role=['Sales Manager', 'Senior Executive', 'Coordinator', 'Analyst'][i],
            phone=f'+985{1000+i*100}',
            mobilephone=f'+98912345{600+i}',
            personalid=f'{1000+i}00000000',
            groupphone=f'+985{1200+i*100}'
        )
        agents.append(agent)
    
    return agents


# ============================================================================
# SCENARIO FIXTURES - Complex scenarios with multiple data
# ============================================================================

@pytest.fixture(scope="function")
def healthy_deal_scenario(sample_deal):
    """Scenario: A healthy deal with good progress"""
    # Modify deal to be healthy
    deal = Deal(
        Id=str(uuid.uuid4()),
        Title='فروش موفق - نزدیک به پایان',
        Description='پروژه فروش با پیشرفت خوب',
        RegisterTime=datetime.now() - timedelta(days=45),
        Price=Decimal('100000000'),
        Status='در حال پیگیری',
        PipelineStageId='stage-advanced',
        PipelineId='pipeline-001',
        ChangeToWonTime=None,
        ChangeToLossTime=None,
        LastTrackingTime=datetime.now() - timedelta(hours=6),  # Recently tracked
        NextTrackingTime=datetime.now() + timedelta(days=2),
        ExpectedCloseDate=datetime.now() + timedelta(days=10),  # Closing soon
        LastActivityUpdateTime=datetime.now() - timedelta(hours=12),  # Recent activity
        LastUpdateTime=datetime.now(),
        Probability=0.85,  # High probability
        ContactId='contact-001',
        OwnerId='owner-001',
        CreatorId='creator-001',
        LabelId='label-001',
        LostReasonId=None,
        Pin=False,
        IsIdle=False,
        IsRotten=False,
        Fields='{}',
        Items='[]',
        MobilePhone='+98912345678'
    )
    
    # Create many recent, positive activities
    activities = []
    activity_types = ['call', 'meeting', 'email']
    for i in range(8):
        activity = DealActivity(
            id=str(uuid.uuid4()),
            title=['تماس موفق', 'جلسه مثبت', 'تایید شرایط'][i % 3],
            note=f'فعالیت مثبت شماره {i+1}',
            resultnote='نتیجه: بسیار موفق و مثبت',
            activitytypeid=activity_types[i % 3],
            isprivate=False,
            isdone=True,  # All done
            ispinned=i == 0,
            duedate=datetime.now() - timedelta(days=10-i),
            finishdate=datetime.now() - timedelta(days=10-i),
            donedate=datetime.now() - timedelta(days=10-i),
            registerdate=datetime.now() - timedelta(days=15-i),
            lastupdatetime=datetime.now() - timedelta(days=8-i),
            dealid=deal.Id,
            creatorid='creator-001',
            ownerid='owner-001',
            updaterid='updater-001',
            sentiment_score=0.85 + (i % 2) * 0.1,  # High positive sentiment
            sentiment_label='مثبت'  # All positive
        )
        activities.append(activity)
    
    return {
        'deal': deal,
        'activities': activities
    }


@pytest.fixture(scope="function")
def at_risk_deal_scenario(sample_deal):
    """Scenario: An at-risk deal with poor progress"""
    # Modify deal to be at-risk
    deal = Deal(
        Id=str(uuid.uuid4()),
        Title='فروش در خطر - نیاز پیگیری',
        Description='پروژه فروش با مشکلات و تاخیرها',
        RegisterTime=datetime.now() - timedelta(days=90),  # Old deal
        Price=Decimal('50000000'),
        Status='در حال پیگیری',
        PipelineStageId='stage-stuck',
        PipelineId='pipeline-001',
        ChangeToWonTime=None,
        ChangeToLossTime=None,
        LastTrackingTime=datetime.now() - timedelta(days=15),  # Not tracked recently
        NextTrackingTime=datetime.now() - timedelta(days=3),  # Overdue
        ExpectedCloseDate=datetime.now() - timedelta(days=20),  # Past deadline
        LastActivityUpdateTime=datetime.now() - timedelta(days=20),  # Old activity
        LastUpdateTime=datetime.now() - timedelta(days=15),
        Probability=0.20,  # Low probability
        ContactId='contact-002',
        OwnerId='owner-002',
        CreatorId='creator-001',
        LabelId='label-002',
        LostReasonId=None,
        Pin=False,
        IsIdle=True,  # Idle flag
        IsRotten=True,  # Rotten flag
        Fields='{}',
        Items='[]',
        MobilePhone='+98987654321'
    )
    
    # Create few, old activities with mixed sentiment
    activities = []
    activity_types = ['email', 'note', 'call']
    for i in range(5):
        activity = DealActivity(
            id=str(uuid.uuid4()),
            title=['عدم پاسخ', 'مشکل فنی', 'تاخیر مشتری'][i % 3],
            note=f'فعالیت منفی یا خنثی شماره {i+1}',
            resultnote=['بدون نتیجه', 'نیاز تصحیح', 'منتظر پاسخ'][i % 3],
            activitytypeid=activity_types[i % 3],
            isprivate=False,
            isdone=i % 2 == 0,  # Some not done
            ispinned=False,
            duedate=datetime.now() - timedelta(days=30-i),
            finishdate=datetime.now() - timedelta(days=30-i) if i % 2 == 0 else None,
            donedate=datetime.now() - timedelta(days=30-i) if i % 2 == 0 else None,
            registerdate=datetime.now() - timedelta(days=40-i),
            lastupdatetime=datetime.now() - timedelta(days=25-i),
            dealid=deal.Id,
            creatorid='creator-001',
            ownerid='owner-002',
            updaterid='updater-001',
            sentiment_score=0.2 + (i % 2) * 0.3,  # Low to neutral sentiment
            sentiment_label=['منفی', 'خنثی', 'منفی'][i % 3]
        )
        activities.append(activity)
    
    return {
        'deal': deal,
        'activities': activities
    }


# ============================================================================
# DATABASE SAMPLE FIXTURES (function scope for fresh data per test)
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
# COMPATIBILITY ALIAS
# ============================================================================

@pytest.fixture(scope="function")
def test_repositories(integration_repositories):
    """Alias for compatibility - integration tests use this name"""
    return integration_repositories


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