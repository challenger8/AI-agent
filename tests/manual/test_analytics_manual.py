#!/usr/bin/env python3
"""
Test script for Analytics Service
Run this to verify the analytics service works correctly

Place this in: tests/manual/test_analytics_manual.py
Run from project root: python tests/manual/test_analytics_manual.py
"""

import sys
import os

# FIX: Set working directory to project root
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
os.chdir(project_root)

# FIX: Add project root to Python path
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"📂 Working directory: {os.getcwd()}")
print(f"📂 Project root: {project_root}")
print(f"📂 Python path: {sys.path[0]}")

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded")
except ImportError:
    print("⚠️  python-dotenv not found, using system environment")

def test_imports():
    """Test 1: Check if all imports work"""
    print("\n" + "="*60)
    print("TEST 1: Checking Imports")
    print("="*60)
    
    try:
        from database.database import create_database_manager
        print("✅ Database manager imported")
        
        from models.repositories import create_repositories
        print("✅ Repositories imported")
        
        from services.analytics_service import AnalyticsService
        print("✅ Analytics service imported")
        
        from services.sentiment_service import SentimentService
        print("✅ Sentiment service imported")
        
        from services.deal_service import DealService
        print("✅ Deal service imported")
        
        from config.settings import AnalysisSettings
        print("✅ Settings imported")
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Test 2: Check database connection"""
    print("\n" + "="*60)
    print("TEST 2: Database Connection")
    print("="*60)
    
    try:
        from database.database import create_database_manager
        
        db = create_database_manager()
        print("✅ Database manager created")
        
        # Test connection
        if db.test_connection():
            print("✅ Database connection successful")
            
            # Get stats
            stats = db.get_database_stats()
            print(f"✅ Database stats retrieved:")
            for key, value in stats.items():
                print(f"   - {key}: {value}")
            
            db.close()
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analytics_service_creation():
    """Test 3: Create Analytics Service instance"""
    print("\n" + "="*60)
    print("TEST 3: Analytics Service Creation")
    print("="*60)
    
    try:
        from database.database import create_database_manager
        from models.repositories import create_repositories
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Create database and repositories
        db = create_database_manager()
        repositories = create_repositories(db)
        print("✅ Repositories created")
        
        # Create sentiment service (optional)
        sentiment_service = SentimentService(repositories)
        print("✅ Sentiment service created")
        
        # Create analytics service
        analytics_service = AnalyticsService(repositories, sentiment_service)
        print("✅ Analytics service created")
        
        # Check methods exist
        methods = [
            'analyze_deal_comprehensive',
            'analyze_portfolio_overview',
            '_calculate_health_score',
            '_identify_risk_indicators',
            '_generate_insights',
            '_create_activity_timeline'
        ]
        
        for method in methods:
            if hasattr(analytics_service, method):
                print(f"✅ Method exists: {method}")
            else:
                print(f"❌ Method missing: {method}")
                return False
        
        db.close()
        print("\n✅ Analytics service creation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Analytics service creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_portfolio_overview():
    """Test 4: Run portfolio overview analysis"""
    print("\n" + "="*60)
    print("TEST 4: Portfolio Overview Analysis")
    print("="*60)
    
    try:
        from database.database import create_database_manager
        from models.repositories import create_repositories
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Setup
        db = create_database_manager()
        repositories = create_repositories(db)
        sentiment_service = SentimentService(repositories)
        analytics_service = AnalyticsService(repositories, sentiment_service)
        
        print("🔄 Running portfolio overview analysis...")
        
        # Run analysis
        result = analytics_service.analyze_portfolio_overview(days=30)
        
        print("\n✅ Portfolio analysis completed!")
        print("\n📊 Results:")
        print(f"   - Total deals: {result.get('summary', {}).get('total_deals', 0)}")
        print(f"   - Recent deals: {result.get('summary', {}).get('recent_deals', 0)}")
        print(f"   - Total activities: {result.get('summary', {}).get('total_activities', 0)}")
        
        if result.get('health_overview'):
            print(f"\n💚 Health Overview:")
            print(f"   - Average health: {result['health_overview'].get('average_health_score', 0)}")
            print(f"   - Healthy deals: {result['health_overview'].get('healthy_count', 0)}")
            print(f"   - At-risk deals: {result['health_overview'].get('at_risk_count', 0)}")
        
        if result.get('insights'):
            print(f"\n💡 Insights:")
            for insight in result['insights'][:5]:
                print(f"   - {insight}")
        
        db.close()
        print("\n✅ Portfolio overview test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Portfolio overview test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_deal_comprehensive_analysis():
    """Test 5: Run comprehensive deal analysis"""
    print("\n" + "="*60)
    print("TEST 5: Comprehensive Deal Analysis")
    print("="*60)
    
    try:
        from database.database import create_database_manager
        from models.repositories import create_repositories
        from services.analytics_service import AnalyticsService
        from services.sentiment_service import SentimentService
        
        # Setup
        db = create_database_manager()
        repositories = create_repositories(db)
        
        # Get a sample deal
        print("🔄 Finding a sample deal...")
        deals = repositories.deals.get_all_deals()
        
        if not deals:
            print("⚠️  No deals in database - skipping this test")
            db.close()
            return True
        
        sample_deal = deals[0]
        deal_id = sample_deal.Id
        print(f"✅ Found deal: {deal_id} - {sample_deal.Title}")
        
        # Create services
        sentiment_service = SentimentService(repositories)
        analytics_service = AnalyticsService(repositories, sentiment_service)
        
        print(f"🔄 Analyzing deal {deal_id}...")
        
        # Run analysis
        result = analytics_service.analyze_deal_comprehensive(deal_id)
        
        print("\n✅ Deal analysis completed!")
        print("\n📊 Results:")
        print(f"   - Deal: {result.get('deal', {}).get('title', 'N/A')}")
        print(f"   - Health Score: {result.get('health_score', 0)}/100")
        print(f"   - Health Category: {result.get('health_category', 'N/A')}")
        print(f"   - Total Activities: {result.get('activities', {}).get('total_count', 0)}")
        
        if result.get('risk_indicators'):
            print(f"\n⚠️  Risk Indicators ({len(result['risk_indicators'])}):")
            for risk in result['risk_indicators'][:3]:
                print(f"   - [{risk.get('severity', 'unknown')}] {risk.get('description', 'N/A')}")
        
        if result.get('insights'):
            print(f"\n💡 Insights:")
            for insight in result['insights'][:5]:
                print(f"   - {insight}")
        
        if result.get('recommendations'):
            print(f"\n🎯 Recommendations:")
            for rec in result['recommendations'][:3]:
                print(f"   - {rec}")
        
        db.close()
        print("\n✅ Comprehensive deal analysis test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Comprehensive deal analysis test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("="*60)
    print("🧪 ANALYTICS SERVICE TEST SUITE")
    print("="*60)
    
    results = {
        "Test 1: Imports": test_imports(),
        "Test 2: Database Connection": test_database_connection(),
        "Test 3: Service Creation": test_analytics_service_creation(),
        "Test 4: Portfolio Overview": test_portfolio_overview(),
        "Test 5: Deal Analysis": test_deal_comprehensive_analysis()
    }
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\n{'='*60}")
    print(f"Results: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 All tests passed! Analytics Service is working correctly!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)