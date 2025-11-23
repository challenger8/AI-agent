"""
services/moe/monitoring.py
--------------------------
Performance monitoring and metrics dashboard for MoE system
"""

import json
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from threading import Lock

from config.moe_settings import MoESettings
from utils.logging_config import get_logger


@dataclass
class QueryMetric:
    """Metric for a single query"""
    query_id: str
    query: str
    timestamp: float
    routing_time_ms: float
    execution_time_ms: float
    total_time_ms: float
    selected_experts: List[str]
    expert_times: Dict[str, float]
    success: bool
    error: Optional[str] = None


@dataclass
class ExpertMetric:
    """Aggregated metrics for an expert"""
    expert_type: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0
    avg_confidence: float = 0.0


class PerformanceMonitor:
    """Monitor and track MoE system performance"""

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
        self._lock = Lock()

        # Query metrics
        self._query_metrics: List[QueryMetric] = []
        self._max_query_history = 1000

        # Expert metrics
        self._expert_metrics: Dict[str, ExpertMetric] = {}
        for expert_type in MoESettings.EXPERT_TYPES:
            self._expert_metrics[expert_type] = ExpertMetric(expert_type=expert_type)

        # System metrics
        self._system_metrics = {
            'start_time': time.time(),
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_routing_time_ms': 0.0,
            'total_execution_time_ms': 0.0,
            'cache_hits': 0,
            'cache_misses': 0
        }

        # Time-series data for charts
        self._time_series: Dict[str, List[tuple]] = defaultdict(list)

    def record_query(self, query_metric: QueryMetric):
        """
        Record metrics for a query

        Args:
            query_metric: Query metric to record
        """
        with self._lock:
            # Add to query history
            self._query_metrics.append(query_metric)

            # Trim history if needed
            if len(self._query_metrics) > self._max_query_history:
                self._query_metrics = self._query_metrics[-self._max_query_history:]

            # Update system metrics
            self._system_metrics['total_queries'] += 1
            if query_metric.success:
                self._system_metrics['successful_queries'] += 1
            else:
                self._system_metrics['failed_queries'] += 1

            self._system_metrics['total_routing_time_ms'] += query_metric.routing_time_ms
            self._system_metrics['total_execution_time_ms'] += query_metric.execution_time_ms

            # Update expert metrics
            for expert in query_metric.selected_experts:
                if expert in self._expert_metrics:
                    metric = self._expert_metrics[expert]
                    metric.total_calls += 1

                    if query_metric.success:
                        metric.successful_calls += 1
                    else:
                        metric.failed_calls += 1

                    if expert in query_metric.expert_times:
                        exec_time = query_metric.expert_times[expert]
                        metric.total_time_ms += exec_time
                        metric.min_time_ms = min(metric.min_time_ms, exec_time)
                        metric.max_time_ms = max(metric.max_time_ms, exec_time)
                        metric.avg_time_ms = metric.total_time_ms / metric.total_calls

            # Record time-series data
            timestamp = query_metric.timestamp
            self._time_series['query_count'].append((timestamp, 1))
            self._time_series['response_time'].append((timestamp, query_metric.total_time_ms))

    def record_cache_hit(self):
        """Record a cache hit"""
        with self._lock:
            self._system_metrics['cache_hits'] += 1

    def record_cache_miss(self):
        """Record a cache miss"""
        with self._lock:
            self._system_metrics['cache_misses'] += 1

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get data for dashboard display

        Returns:
            Dashboard data dictionary
        """
        with self._lock:
            uptime = time.time() - self._system_metrics['start_time']
            total = self._system_metrics['total_queries']

            # Calculate rates
            success_rate = (
                self._system_metrics['successful_queries'] / total
                if total > 0 else 0.0
            )
            cache_total = (
                self._system_metrics['cache_hits'] +
                self._system_metrics['cache_misses']
            )
            cache_hit_rate = (
                self._system_metrics['cache_hits'] / cache_total
                if cache_total > 0 else 0.0
            )
            avg_routing_time = (
                self._system_metrics['total_routing_time_ms'] / total
                if total > 0 else 0.0
            )
            avg_execution_time = (
                self._system_metrics['total_execution_time_ms'] / total
                if total > 0 else 0.0
            )

            return {
                'system': {
                    'uptime_seconds': uptime,
                    'total_queries': total,
                    'successful_queries': self._system_metrics['successful_queries'],
                    'failed_queries': self._system_metrics['failed_queries'],
                    'success_rate': success_rate,
                    'avg_routing_time_ms': avg_routing_time,
                    'avg_execution_time_ms': avg_execution_time,
                    'avg_total_time_ms': avg_routing_time + avg_execution_time,
                    'queries_per_minute': total / (uptime / 60) if uptime > 0 else 0,
                    'cache_hit_rate': cache_hit_rate
                },
                'experts': {
                    expert_type: {
                        'total_calls': metric.total_calls,
                        'successful_calls': metric.successful_calls,
                        'failed_calls': metric.failed_calls,
                        'success_rate': (
                            metric.successful_calls / metric.total_calls
                            if metric.total_calls > 0 else 0.0
                        ),
                        'avg_time_ms': metric.avg_time_ms,
                        'min_time_ms': (
                            metric.min_time_ms
                            if metric.min_time_ms != float('inf') else 0.0
                        ),
                        'max_time_ms': metric.max_time_ms
                    }
                    for expert_type, metric in self._expert_metrics.items()
                },
                'recent_queries': [
                    {
                        'query_id': m.query_id,
                        'query': m.query[:50] + '...' if len(m.query) > 50 else m.query,
                        'experts': m.selected_experts,
                        'total_time_ms': m.total_time_ms,
                        'success': m.success
                    }
                    for m in self._query_metrics[-10:]
                ]
            }

    def get_expert_comparison(self) -> Dict[str, Any]:
        """
        Get expert comparison data

        Returns:
            Comparison data for all experts
        """
        with self._lock:
            comparison = {}
            for expert_type, metric in self._expert_metrics.items():
                comparison[expert_type] = {
                    'usage_percentage': (
                        metric.total_calls / self._system_metrics['total_queries'] * 100
                        if self._system_metrics['total_queries'] > 0 else 0.0
                    ),
                    'avg_response_time': metric.avg_time_ms,
                    'reliability': (
                        metric.successful_calls / metric.total_calls * 100
                        if metric.total_calls > 0 else 0.0
                    )
                }
            return comparison

    def get_time_series(self, metric_name: str, window_seconds: int = 3600) -> List[tuple]:
        """
        Get time series data for a metric

        Args:
            metric_name: Name of metric
            window_seconds: Time window in seconds

        Returns:
            List of (timestamp, value) tuples
        """
        with self._lock:
            cutoff = time.time() - window_seconds
            return [
                (ts, val) for ts, val in self._time_series.get(metric_name, [])
                if ts >= cutoff
            ]

    def export_metrics(self, filepath: str = None) -> str:
        """
        Export metrics to JSON file

        Args:
            filepath: Output file path

        Returns:
            Path to exported file
        """
        if filepath is None:
            filepath = MoESettings.METRICS_DIR / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        data = self.get_dashboard_data()
        data['export_timestamp'] = datetime.now().isoformat()

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"Exported metrics to {filepath}")
        return str(filepath)

    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            self._query_metrics.clear()
            self._system_metrics = {
                'start_time': time.time(),
                'total_queries': 0,
                'successful_queries': 0,
                'failed_queries': 0,
                'total_routing_time_ms': 0.0,
                'total_execution_time_ms': 0.0,
                'cache_hits': 0,
                'cache_misses': 0
            }
            for metric in self._expert_metrics.values():
                metric.total_calls = 0
                metric.successful_calls = 0
                metric.failed_calls = 0
                metric.total_time_ms = 0.0
                metric.avg_time_ms = 0.0
                metric.min_time_ms = float('inf')
                metric.max_time_ms = 0.0
            self._time_series.clear()

        self.logger.info("Metrics reset")

    def format_dashboard(self) -> str:
        """
        Format dashboard data as text

        Returns:
            Formatted dashboard string
        """
        data = self.get_dashboard_data()
        sys = data['system']

        lines = [
            "=" * 60,
            "MoE Performance Dashboard",
            "=" * 60,
            "",
            "System Overview",
            "-" * 40,
            f"  Uptime: {sys['uptime_seconds']:.1f}s",
            f"  Total Queries: {sys['total_queries']}",
            f"  Success Rate: {sys['success_rate']*100:.1f}%",
            f"  Avg Response Time: {sys['avg_total_time_ms']:.2f}ms",
            f"  Queries/min: {sys['queries_per_minute']:.2f}",
            f"  Cache Hit Rate: {sys['cache_hit_rate']*100:.1f}%",
            "",
            "Expert Performance",
            "-" * 40
        ]

        for expert_type, stats in data['experts'].items():
            if stats['total_calls'] > 0:
                lines.append(
                    f"  {expert_type}: {stats['total_calls']} calls, "
                    f"{stats['avg_time_ms']:.1f}ms avg, "
                    f"{stats['success_rate']*100:.0f}% success"
                )

        lines.extend([
            "",
            "Recent Queries",
            "-" * 40
        ])

        for query in data['recent_queries'][-5:]:
            status = "✓" if query['success'] else "✗"
            lines.append(
                f"  {status} {query['query']} "
                f"[{', '.join(query['experts'])}] "
                f"{query['total_time_ms']:.0f}ms"
            )

        lines.append("=" * 60)

        return "\n".join(lines)


# Global monitor instance
_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor
