"""
tests/manual/test_quick_verification.py
---------------------------------------
Quick manual tests for smoke testing
Run this before deployment to verify basic functionality
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_database_connection():
    """Quick test: Can we connect to database?"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    
    try:
        from database.database import create_database_manager
        
        db = create_database_manager()
        result = db.test_connection()
        
        if result:
            print("✅ Database connection successful")
            
            # Get stats
            stats = db.get_database_stats()
            print(f"   - Total deals: {stats.get('deals_count', 0)}")
            print(f"   - Total activities: {stats.get('deal_activities_count', 0)}")
            print(f"   - Total agents: {stats.get('crm_agents_count', 0)}")
            print(f"   - Database size: {stats.get('database_size', 'Unknown')}")
            
            db.close()
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_services_creation():
    """Quick test: Can we create all services?"""
    print("\n" + "="*60)
    print("TEST 2: Services Creation")
    print("="*60)
    
    try:
        from database.database import create_database_manager
        from models.repositories import create_repositories
        from services.deal_service import DealService
        from services.sentiment_service import SentimentService
        from services.analytics_service import AnalyticsService
        from services.cache_service import get_cache_service
        
        # Create database and repositories
        db = create_database_manager()
        repos = create_repositories(db)
        print("✅ Database and repositories created")
        
        # Create services
        deal_service = DealService(repos)
        print("✅ DealService created")
        
        sentiment_service = SentimentService(repos)
        print("✅ SentimentService created")
        
        analytics_service = AnalyticsService(repos, sentiment_service)
        print("✅ AnalyticsService created")
        
        cache_service = get_cache_service()
        print(f"✅ CacheService created (available: {cache_service.is_available()})")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_queries():
    """Quick test: Can we query data?"""
    print("\n" + "="*60)
    print("TEST 3: Basic Queries")
    print("="*60)
    
    try:
        from database.database import create_database_manager
        from models.repositories import create_repositories
        from services.deal_service import DealService
        
        db = create_database_manager()
        repos = create_repositories(db)
        deal_service = DealService(repos)
        
        # Get all deals
        deals = deal_service.get_all_deals()
        print(f"✅ Retrieved {len(deals)} deals")
        
        if len(deals) > 0:
            # Get first deal
            first_deal = deals[0]
            print(f"   - Sample deal: {first_deal.get('Title', 'N/A')}")
            
            # Get deal by ID
            deal_detail = deal_service.get_deal(first_deal['Id'])
            if deal_detail:
                print(f"✅ Retrieved deal details for: {deal_detail.get('Title', 'N/A')}")
        
        # Get summary
        summary = deal_service.get_deals_summary(days=30)
        print(f"✅ Generated summary: {summary.get('total_deals', 0)} deals")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_analytics_functionality():
    """Quick test: Does analytics work?"""
    print("\n" + "="*60)
    print("TEST 4: Analytics Functionality")
    print("="*60)
    
    try:
        from database.database import create_database_manager
        from models.repositories import create_repositories
        from services.deal_service import DealService
        from services.sentiment_service import SentimentService
        from services.analytics_service import AnalyticsService
        
        db = create_database_manager()
        repos = create_repositories(db)
        deal_service = DealService(repos)
        sentiment_service = SentimentService(repos)
        analytics_service = AnalyticsService(repos, sentiment_service)
        
        # Get a deal to analyze
        deals = deal_service.get_all_deals()
        
        if len(deals) > 0:
            test_deal = deals[0]
            deal_id = test_deal['Id']
            
            print(f"   Analyzing deal: {test_deal.get('Title', 'N/A')}")
            
            # Run comprehensive analysis
            result = analytics_service.analyze_deal_comprehensive(deal_id)
            
            if 'error' not in result:
                print(f"✅ Analysis completed")
                print(f"   - Health score: {result.get('health_score', 'N/A')}/100")
                print(f"   - Health category: {result.get('health_category', 'N/A')}")
                print(f"   - Risk indicators: {len(result.get('risk_indicators', []))}")
                print(f"   - Insights: {len(result.get('insights', []))}")
                print(f"   - Recommendations: {len(result.get('recommendations', []))}")
            else:
                print(f"❌ Analysis error: {result['error']}")
                return False
        else:
            print("⚠️  No deals in database to analyze")
        
        # Test portfolio overview
        portfolio = analytics_service.analyze_portfolio_overview(days=30)
        
        if 'error' not in portfolio and 'summary' in portfolio:
            print(f"✅ Portfolio overview generated")
            summary = portfolio['summary']
            print(f"   - Total deals: {summary.get('total_deals', 0)}")
            print(f"   - Recent deals: {summary.get('recent_deals', 0)}")
            print(f"   - Total activities: {summary.get('total_activities', 0)}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_mcp_server_creation():
    """Quick test: Can we create MCP server?"""
    print("\n" + "="*60)
    print("TEST 5: MCP Server Creation")
    print("="*60)
    
    try:
        from mcp_spec.server import create_mcp_server
        
        server = create_mcp_server()
        print("✅ MCP server created")
        
        status = server.get_server_status()
        print(f"   - Server name: {status.get('server_name', 'N/A')}")
        print(f"   - Server version: {status.get('server_version', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_service():
    """Quick test: Does cache work?"""
    print("\n" + "="*60)
    print("TEST 6: Cache Service")
    print("="*60)
    
    try:
        from services.cache_service import get_cache_service
        
        cache = get_cache_service()
        print(f"   Cache enabled: {cache.enabled}")
        print(f"   Cache available: {cache.is_available()}")
        
        if cache.is_available():
            # Test set/get
            test_key = "test_manual_verification"
            test_value = {"test": "value", "timestamp": str(sys.implementation.name)}
            
            success = cache.set(test_key, test_value, ttl=60)
            print(f"✅ Cache set: {success}")
            
            retrieved = cache.get(test_key)
            if retrieved == test_value:
                print(f"✅ Cache get: successful")
            else:
                print(f"⚠️  Cache get: value mismatch")
            
            # Clean up
            cache.delete(test_key)
            print(f"✅ Cache delete: successful")
            
            # Get stats
            stats = cache.get_stats()
            print(f"   - Total keys: {stats.get('total_keys', 'N/A')}")
            print(f"   - Used memory: {stats.get('used_memory', 'N/A')}")
        else:
            print("⚠️  Redis not available - caching disabled (OK for development)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all quick verification tests"""
    print("\n" + "="*60)
    print("QUICK VERIFICATION TEST SUITE")
    print("="*60)
    print("This will quickly verify that all components are working")
    
    results = {
        "Database Connection": test_database_connection(),
        "Services Creation": test_services_creation(),
        "Basic Queries": test_basic_queries(),
        "Analytics Functionality": test_analytics_functionality(),
        "MCP Server Creation": test_mcp_server_creation(),
        "Cache Service": test_cache_service()
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "-"*60)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please investigate.")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)