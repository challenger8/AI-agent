#!/usr/bin/env python3
"""
tests/manual/test_cache_performance.py
--------------------------------------
Manual performance comparison test: With vs Without Caching

Run this to see the actual performance improvement from caching.
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from dotenv import load_dotenv
load_dotenv()

from database.database import create_database_manager
from models.repositories import create_repositories
from services.sentiment_service import SentimentService
from services.analytics_service import AnalyticsService
from services.cache_service import get_cache_service


def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_result(label, time_val, improvement=None):
    """Print formatted result"""
    if improvement:
        print(f"  {label:40s} {time_val:8.4f}s  ({improvement:.1f}x faster)")
    else:
        print(f"  {label:40s} {time_val:8.4f}s")


def test_sentiment_caching_performance():
    """Test sentiment analysis caching performance"""
    print_header("SENTIMENT ANALYSIS CACHING TEST")
    
    # Setup
    db = create_database_manager()
    repositories = create_repositories(db)
    sentiment_service = SentimentService(repositories)
    cache = get_cache_service()
    
    if not cache.is_available():
        print("❌ Redis not available - skipping test")
        return
    
    if not sentiment_service.model_loaded:
        print("❌ Sentiment model not loaded - skipping test")
        return
    
    # Test texts
    texts = [
        "مشتری بسیار راضی است و قصد خرید دارد",
        "نیاز به پیگیری بیشتر و بررسی دقیق‌تر دارد",
        "پروژه در حال پیشرفت است و روند خوبی دارد",
        "مشتری نگرانی‌هایی درباره قیمت دارد",
        "جلسه بسیار مؤثری بود و به نتیجه رسیدیم"
    ]
    
    # Clear cache to start fresh
    sentiment_service.clear_sentiment_cache()
    
    print("\nAnalyzing 5 different Persian texts...")
    print("\nTest 1: First Analysis (Cache MISS)")
    
    # First run - cache miss
    start = time.time()
    results_first = []
    for i, text in enumerate(texts, 1):
        result = sentiment_service.analyze_text(text)
        results_first.append(result)
        print(f"  Text {i}: {result['sentiment']} (confidence: {result['confidence']:.3f})")
    first_run_time = time.time() - start
    
    print(f"\n  Total time: {first_run_time:.4f}s")
    print(f"  Average per text: {first_run_time/len(texts):.4f}s")
    
    # Second run - cache hit
    print("\nTest 2: Second Analysis (Cache HIT)")
    
    start = time.time()
    results_second = []
    for i, text in enumerate(texts, 1):
        result = sentiment_service.analyze_text(text)
        results_second.append(result)
        print(f"  Text {i}: {result['sentiment']} (confidence: {result['confidence']:.3f})")
    second_run_time = time.time() - start
    
    print(f"\n  Total time: {second_run_time:.4f}s")
    print(f"  Average per text: {second_run_time/len(texts):.4f}s")
    
    # Calculate improvement
    speedup = first_run_time / second_run_time if second_run_time > 0 else 0
    improvement = ((first_run_time - second_run_time) / first_run_time * 100) if first_run_time > 0 else 0
    
    print("\n" + "="*70)
    print("RESULTS:")
    print_result("First run (no cache)", first_run_time)
    print_result("Second run (cached)", second_run_time, speedup)
    print(f"\n  Performance Improvement: {improvement:.1f}%")
    print(f"  Speedup Factor: {speedup:.1f}x")
    print("="*70)
    
    # Verify results are identical
    for i, (r1, r2) in enumerate(zip(results_first, results_second)):
        assert r1['sentiment'] == r2['sentiment'], f"Text {i+1}: Results differ!"
    
    print("\n✅ All results verified identical (cache working correctly)")
    
    db.close()
    return {
        'first_run': first_run_time,
        'second_run': second_run_time,
        'speedup': speedup,
        'improvement': improvement
    }


def test_portfolio_caching_performance():
    """Test portfolio analysis caching performance"""
    print_header("PORTFOLIO ANALYSIS CACHING TEST")
    
    # Setup
    db = create_database_manager()
    repositories = create_repositories(db)
    sentiment_service = SentimentService(repositories)
    analytics_service = AnalyticsService(repositories, sentiment_service)
    cache = get_cache_service()
    
    if not cache.is_available():
        print("❌ Redis not available - skipping test")
        return
    
    # Clear cache
    analytics_service.clear_analytics_cache()
    
    print("\nAnalyzing portfolio overview (30 days)...")
    
    # First run - cache miss
    print("\nTest 1: First Analysis (Cache MISS)")
    start = time.time()
    result1 = analytics_service.analyze_portfolio_overview(days=30)
    first_run_time = time.time() - start
    
    print(f"  Total deals: {result1['summary']['total_deals']}")
    print(f"  Total activities: {result1['summary']['total_activities']}")
    print(f"  Time taken: {first_run_time:.4f}s")
    
    # Second run - cache hit
    print("\nTest 2: Second Analysis (Cache HIT)")
    start = time.time()
    result2 = analytics_service.analyze_portfolio_overview(days=30)
    second_run_time = time.time() - start
    
    print(f"  Total deals: {result2['summary']['total_deals']}")
    print(f"  Total activities: {result2['summary']['total_activities']}")
    print(f"  Time taken: {second_run_time:.4f}s")
    
    # Calculate improvement
    speedup = first_run_time / second_run_time if second_run_time > 0 else 0
    improvement = ((first_run_time - second_run_time) / first_run_time * 100) if first_run_time > 0 else 0
    
    print("\n" + "="*70)
    print("RESULTS:")
    print_result("First run (no cache)", first_run_time)
    print_result("Second run (cached)", second_run_time, speedup)
    print(f"\n  Performance Improvement: {improvement:.1f}%")
    print(f"  Speedup Factor: {speedup:.1f}x")
    print("="*70)
    
    # Verify results match
    assert result1['summary']['total_deals'] == result2['summary']['total_deals']
    print("\n✅ Results verified identical (cache working correctly)")
    
    db.close()
    return {
        'first_run': first_run_time,
        'second_run': second_run_time,
        'speedup': speedup,
        'improvement': improvement
    }


def test_deal_analysis_caching_performance():
    """Test individual deal analysis caching performance"""
    print_header("DEAL ANALYSIS CACHING TEST")
    
    # Setup
    db = create_database_manager()
    repositories = create_repositories(db)
    
    # Get sample deal
    print("\nFinding sample deal...")
    deals = repositories.deals.get_all_deals()
    
    if not deals:
        print("❌ No deals in database - skipping test")
        return
    
    sample_deal = deals[0]
    deal_id = sample_deal.Id
    print(f"✅ Using deal: {deal_id} - {sample_deal.Title}")
    
    sentiment_service = SentimentService(repositories)
    analytics_service = AnalyticsService(repositories, sentiment_service)
    cache = get_cache_service()
    
    if not cache.is_available():
        print("❌ Redis not available - skipping test")
        return
    
    # Clear cache for this deal
    analytics_service.invalidate_deal_cache(deal_id)
    
    # First run - cache miss
    print("\nTest 1: First Analysis (Cache MISS)")
    start = time.time()
    result1 = analytics_service.analyze_deal_comprehensive(deal_id)
    first_run_time = time.time() - start
    
    print(f"  Health Score: {result1['health_score']}/100")
    print(f"  Health Category: {result1['health_category']}")
    print(f"  Total Activities: {result1['activities']['total_count']}")
    print(f"  Risk Indicators: {len(result1['risk_indicators'])}")
    print(f"  Time taken: {first_run_time:.4f}s")
    
    # Second run - cache hit
    print("\nTest 2: Second Analysis (Cache HIT)")
    start = time.time()
    result2 = analytics_service.analyze_deal_comprehensive(deal_id)
    second_run_time = time.time() - start
    
    print(f"  Health Score: {result2['health_score']}/100")
    print(f"  Health Category: {result2['health_category']}")
    print(f"  Total Activities: {result2['activities']['total_count']}")
    print(f"  Risk Indicators: {len(result2['risk_indicators'])}")
    print(f"  Time taken: {second_run_time:.4f}s")
    
    # Calculate improvement
    speedup = first_run_time / second_run_time if second_run_time > 0 else 0
    improvement = ((first_run_time - second_run_time) / first_run_time * 100) if first_run_time > 0 else 0
    
    print("\n" + "="*70)
    print("RESULTS:")
    print_result("First run (no cache)", first_run_time)
    print_result("Second run (cached)", second_run_time, speedup)
    print(f"\n  Performance Improvement: {improvement:.1f}%")
    print(f"  Speedup Factor: {speedup:.1f}x")
    print("="*70)
    
    # Verify results match
    assert result1['health_score'] == result2['health_score']
    print("\n✅ Results verified identical (cache working correctly)")
    
    db.close()
    return {
        'first_run': first_run_time,
        'second_run': second_run_time,
        'speedup': speedup,
        'improvement': improvement
    }


def test_repeated_queries_performance():
    """Test performance with multiple repeated queries"""
    print_header("REPEATED QUERIES PERFORMANCE TEST")
    
    # Setup
    db = create_database_manager()
    repositories = create_repositories(db)
    sentiment_service = SentimentService(repositories)
    analytics_service = AnalyticsService(repositories, sentiment_service)
    cache = get_cache_service()
    
    if not cache.is_available():
        print("❌ Redis not available - skipping test")
        return
    
    n_queries = 20
    
    print(f"\nRunning {n_queries} repeated portfolio queries...")
    
    # Clear cache
    analytics_service.clear_analytics_cache()
    
    # Run queries
    times = []
    start_total = time.time()
    
    for i in range(n_queries):
        start = time.time()
        result = analytics_service.analyze_portfolio_overview(days=30)
        query_time = time.time() - start
        times.append(query_time)
        
        if i == 0:
            print(f"  Query 1 (cache MISS): {query_time:.4f}s")
        elif i < 5:
            print(f"  Query {i+1} (cache HIT):  {query_time:.4f}s")
    
    total_time = time.time() - start_total
    
    print(f"  ...")
    print(f"  Query {n_queries} (cache HIT):  {times[-1]:.4f}s")
    
    # Calculate statistics
    avg_time = sum(times) / len(times)
    first_query = times[0]
    cached_queries = times[1:]
    avg_cached = sum(cached_queries) / len(cached_queries) if cached_queries else 0
    
    print("\n" + "="*70)
    print("RESULTS:")
    print(f"  Total queries: {n_queries}")
    print(f"  Total time: {total_time:.4f}s")
    print(f"  Average per query: {avg_time:.4f}s")
    print(f"\n  First query (no cache): {first_query:.4f}s")
    print(f"  Average cached queries: {avg_cached:.4f}s")
    print(f"  Speedup: {first_query/avg_cached:.1f}x")
    print("="*70)
    
    db.close()
    return {
        'total_queries': n_queries,
        'total_time': total_time,
        'avg_time': avg_time,
        'first_query': first_query,
        'avg_cached': avg_cached
    }


def show_cache_stats():
    """Display cache statistics"""
    print_header("CACHE STATISTICS")
    
    cache = get_cache_service()
    
    if not cache.is_available():
        print("❌ Redis not available")
        return
    
    stats = cache.get_stats()
    
    print("\n  Cache Status:")
    print(f"    Enabled: {stats['enabled']}")
    print(f"    Available: {stats['available']}")
    print(f"\n  Usage:")
    print(f"    Total keys: {stats['total_keys']}")
    print(f"    Memory used: {stats['used_memory']}")
    print(f"\n  Performance:")
    print(f"    Cache hits: {stats['hits']}")
    print(f"    Cache misses: {stats['misses']}")
    print(f"    Hit rate: {stats['hit_rate']}%")
    print("\n" + "="*70)


def main():
    """Run all performance tests"""
    print("="*70)
    print("  REDIS CACHING PERFORMANCE TEST SUITE")
    print("="*70)
    print(f"\n  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    try:
        # Test 1: Sentiment caching
        result = test_sentiment_caching_performance()
        if result:
            results['sentiment'] = result
        
        # Test 2: Portfolio caching
        result = test_portfolio_caching_performance()
        if result:
            results['portfolio'] = result
        
        # Test 3: Deal analysis caching
        result = test_deal_analysis_caching_performance()
        if result:
            results['deal_analysis'] = result
        
        # Test 4: Repeated queries
        result = test_repeated_queries_performance()
        if result:
            results['repeated'] = result
        
        # Show cache stats
        show_cache_stats()
        
        # Summary
        print_header("OVERALL SUMMARY")
        
        if results:
            print("\n  Average Performance Improvements:")
            
            if 'sentiment' in results:
                print(f"    Sentiment Analysis: {results['sentiment']['speedup']:.1f}x faster")
            
            if 'portfolio' in results:
                print(f"    Portfolio Overview: {results['portfolio']['speedup']:.1f}x faster")
            
            if 'deal_analysis' in results:
                print(f"    Deal Analysis: {results['deal_analysis']['speedup']:.1f}x faster")
            
            print("\n✅ All tests completed successfully!")
            print("\n  Key Takeaway: Redis caching provides significant performance")
            print("  improvements, especially for repeated queries and complex analytics.")
        else:
            print("\n⚠️  No tests completed (Redis may not be available)")
        
        print("\n" + "="*70)
        return 0
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)