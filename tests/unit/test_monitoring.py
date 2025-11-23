"""
tests/unit/test_monitoring.py
-----------------------------
Unit tests for performance monitoring
"""

import pytest
import time

from services.moe.monitoring import (
    PerformanceMonitor,
    QueryMetric,
    get_monitor
)


class TestQueryMetric:
    """Tests for QueryMetric dataclass"""

    def test_query_metric_creation(self):
        """Test creating query metric"""
        metric = QueryMetric(
            query_id="q1",
            query="test query",
            timestamp=time.time(),
            routing_time_ms=10.5,
            execution_time_ms=100.0,
            total_time_ms=110.5,
            selected_experts=['deal_analysis'],
            expert_times={'deal_analysis': 95.0},
            success=True
        )
        assert metric.query_id == "q1"
        assert metric.success is True
        assert metric.total_time_ms == 110.5


class TestPerformanceMonitor:
    """Tests for PerformanceMonitor"""

    @pytest.fixture
    def monitor(self):
        """Create fresh monitor instance"""
        monitor = PerformanceMonitor()
        monitor.reset_metrics()
        return monitor

    def test_initialization(self, monitor):
        """Test monitor initialization"""
        assert monitor is not None
        assert len(monitor._expert_metrics) == 5

    def test_record_query(self, monitor):
        """Test recording a query"""
        metric = QueryMetric(
            query_id="q1",
            query="test query",
            timestamp=time.time(),
            routing_time_ms=10.0,
            execution_time_ms=50.0,
            total_time_ms=60.0,
            selected_experts=['deal_analysis'],
            expert_times={'deal_analysis': 45.0},
            success=True
        )
        monitor.record_query(metric)

        data = monitor.get_dashboard_data()
        assert data['system']['total_queries'] == 1
        assert data['system']['successful_queries'] == 1

    def test_record_failed_query(self, monitor):
        """Test recording a failed query"""
        metric = QueryMetric(
            query_id="q1",
            query="failed query",
            timestamp=time.time(),
            routing_time_ms=5.0,
            execution_time_ms=20.0,
            total_time_ms=25.0,
            selected_experts=['sentiment'],
            expert_times={'sentiment': 15.0},
            success=False,
            error="Test error"
        )
        monitor.record_query(metric)

        data = monitor.get_dashboard_data()
        assert data['system']['failed_queries'] == 1

    def test_expert_metrics(self, monitor):
        """Test expert metrics are updated"""
        metric = QueryMetric(
            query_id="q1",
            query="test",
            timestamp=time.time(),
            routing_time_ms=10.0,
            execution_time_ms=50.0,
            total_time_ms=60.0,
            selected_experts=['deal_analysis', 'sentiment'],
            expert_times={'deal_analysis': 30.0, 'sentiment': 20.0},
            success=True
        )
        monitor.record_query(metric)

        data = monitor.get_dashboard_data()
        assert data['experts']['deal_analysis']['total_calls'] == 1
        assert data['experts']['sentiment']['total_calls'] == 1

    def test_cache_hit_miss_tracking(self, monitor):
        """Test cache hit/miss tracking"""
        monitor.record_cache_hit()
        monitor.record_cache_hit()
        monitor.record_cache_miss()

        data = monitor.get_dashboard_data()
        assert data['system']['cache_hit_rate'] == pytest.approx(2/3, abs=0.01)

    def test_get_expert_comparison(self, monitor):
        """Test getting expert comparison"""
        # Record multiple queries
        for i in range(3):
            metric = QueryMetric(
                query_id=f"q{i}",
                query=f"query {i}",
                timestamp=time.time(),
                routing_time_ms=10.0,
                execution_time_ms=50.0,
                total_time_ms=60.0,
                selected_experts=['deal_analysis'],
                expert_times={'deal_analysis': 45.0},
                success=True
            )
            monitor.record_query(metric)

        comparison = monitor.get_expert_comparison()
        assert 'deal_analysis' in comparison
        assert comparison['deal_analysis']['usage_percentage'] == 100.0

    def test_time_series(self, monitor):
        """Test time series data"""
        metric = QueryMetric(
            query_id="q1",
            query="test",
            timestamp=time.time(),
            routing_time_ms=10.0,
            execution_time_ms=50.0,
            total_time_ms=60.0,
            selected_experts=['search'],
            expert_times={'search': 45.0},
            success=True
        )
        monitor.record_query(metric)

        series = monitor.get_time_series('query_count', window_seconds=60)
        assert len(series) > 0

    def test_reset_metrics(self, monitor):
        """Test resetting metrics"""
        # Record a query
        metric = QueryMetric(
            query_id="q1",
            query="test",
            timestamp=time.time(),
            routing_time_ms=10.0,
            execution_time_ms=50.0,
            total_time_ms=60.0,
            selected_experts=['search'],
            expert_times={'search': 45.0},
            success=True
        )
        monitor.record_query(metric)

        # Reset
        monitor.reset_metrics()

        data = monitor.get_dashboard_data()
        assert data['system']['total_queries'] == 0

    def test_format_dashboard(self, monitor):
        """Test formatting dashboard"""
        metric = QueryMetric(
            query_id="q1",
            query="test query for dashboard",
            timestamp=time.time(),
            routing_time_ms=10.0,
            execution_time_ms=50.0,
            total_time_ms=60.0,
            selected_experts=['deal_analysis'],
            expert_times={'deal_analysis': 45.0},
            success=True
        )
        monitor.record_query(metric)

        dashboard = monitor.format_dashboard()
        assert "MoE Performance Dashboard" in dashboard
        assert "Total Queries: 1" in dashboard

    def test_recent_queries(self, monitor):
        """Test recent queries list"""
        for i in range(15):
            metric = QueryMetric(
                query_id=f"q{i}",
                query=f"query {i}",
                timestamp=time.time(),
                routing_time_ms=10.0,
                execution_time_ms=50.0,
                total_time_ms=60.0,
                selected_experts=['search'],
                expert_times={'search': 45.0},
                success=True
            )
            monitor.record_query(metric)

        data = monitor.get_dashboard_data()
        # Should only keep last 10
        assert len(data['recent_queries']) == 10


class TestGetMonitor:
    """Tests for global monitor"""

    def test_get_monitor_singleton(self):
        """Test global monitor is singleton"""
        m1 = get_monitor()
        m2 = get_monitor()
        assert m1 is m2
