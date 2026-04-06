"""Tests for metrics collection and monitoring."""

from __future__ import annotations

import time
from typing import Any, Dict

import pytest

from fastmcp_server.bookstack.metrics import (
    MetricsCollector,
    ToolMetrics,
    get_metrics_collector,
    track_tool,
)


@pytest.fixture
def metrics_collector():
    """Provide a fresh MetricsCollector instance for each test."""
    collector = MetricsCollector()
    return collector


class TestToolMetrics:
    """Test ToolMetrics functionality."""

    def test_record_call_increments_counts(self):
        """Test that record_call increments call counts."""
        metrics = ToolMetrics(tool_name="test_tool")
        
        metrics.record_call(duration=0.5, success=True)
        assert metrics.call_count == 1
        assert metrics.success_count == 1
        assert metrics.error_count == 0
        
        metrics.record_call(duration=1.0, success=False, error="Test error")
        assert metrics.call_count == 2
        assert metrics.success_count == 1
        assert metrics.error_count == 1
        assert len(metrics.errors) == 1
        assert metrics.errors[0] == "Test error"

    def test_record_call_tracks_durations(self):
        """Test that record_call tracks min/max/total durations."""
        metrics = ToolMetrics(tool_name="test_tool")
        
        metrics.record_call(duration=0.5, success=True)
        metrics.record_call(duration=1.5, success=True)
        metrics.record_call(duration=0.2, success=True)
        
        assert metrics.total_duration == pytest.approx(2.2)
        assert metrics.min_duration == pytest.approx(0.2)
        assert metrics.max_duration == pytest.approx(1.5)
        assert metrics.last_called is not None

    def test_success_rate_property(self):
        """Test success_rate property calculation."""
        metrics = ToolMetrics(tool_name="test_tool")
        
        # No calls yet
        assert metrics.success_rate == 0.0
        
        # 3 successes, 1 failure = 75%
        metrics.record_call(duration=0.1, success=True)
        metrics.record_call(duration=0.1, success=True)
        metrics.record_call(duration=0.1, success=True)
        metrics.record_call(duration=0.1, success=False)
        
        assert metrics.success_rate == 75.0

    def test_avg_duration_property(self):
        """Test avg_duration property calculation."""
        metrics = ToolMetrics(tool_name="test_tool")
        
        # No calls yet
        assert metrics.avg_duration == 0.0
        
        metrics.record_call(duration=0.5, success=True)
        metrics.record_call(duration=1.5, success=True)
        
        assert metrics.avg_duration == pytest.approx(1.0)

    def test_record_call_limits_error_storage(self):
        """Test that error storage is limited to last 100 errors."""
        metrics = ToolMetrics(tool_name="test_tool")
        
        # Record 150 errors
        for i in range(150):
            metrics.record_call(duration=0.1, success=False, error=f"Error {i}")
        
        # Should only keep last 100
        assert len(metrics.errors) == 100
        # Should have errors 50-149
        assert metrics.errors[0] == "Error 50"
        assert metrics.errors[-1] == "Error 149"


class TestMetricsCollector:
    """Test MetricsCollector functionality."""

    def test_record_request_stores_metrics(self, metrics_collector):
        """Test that record_request stores request metrics."""
        metrics_collector.record_request(
            method="GET",
            endpoint="/api/books",
            duration=0.5,
            status=200,
        )
        
        assert len(metrics_collector._requests) == 1
        assert metrics_collector._request_counts["GET /api/books"] == 1
        assert metrics_collector._status_counts[200] == 1

    def test_record_request_increments_counts(self, metrics_collector):
        """Test that multiple requests increment counts."""
        metrics_collector.record_request("GET", "/api/books", 0.5, 200)
        metrics_collector.record_request("GET", "/api/books", 0.3, 200)
        metrics_collector.record_request("POST", "/api/books", 0.8, 201)
        
        assert metrics_collector._request_counts["GET /api/books"] == 2
        assert metrics_collector._request_counts["POST /api/books"] == 1
        assert metrics_collector._status_counts[200] == 2
        assert metrics_collector._status_counts[201] == 1

    def test_record_request_tracks_slow_requests(self, metrics_collector):
        """Test that slow requests (>5s) are tracked separately."""
        # Fast request
        metrics_collector.record_request("GET", "/api/books", 2.0, 200)
        assert len(metrics_collector._slow_requests) == 0
        
        # Slow request
        metrics_collector.record_request("GET", "/api/pages", 6.0, 200)
        assert len(metrics_collector._slow_requests) == 1
        assert metrics_collector._slow_requests[0].duration == 6.0

    def test_record_request_limits_slow_requests_storage(self, metrics_collector):
        """Test that slow requests storage is limited to last 100."""
        for i in range(150):
            metrics_collector.record_request("GET", f"/api/test/{i}", 10.0, 200)
        
        assert len(metrics_collector._slow_requests) == 100

    def test_record_tool_call_creates_metrics(self, metrics_collector):
        """Test that record_tool_call creates ToolMetrics if needed."""
        metrics_collector.record_tool_call("test_tool", 0.5, True)
        
        assert "test_tool" in metrics_collector._tool_metrics
        assert metrics_collector._tool_metrics["test_tool"].call_count == 1

    def test_record_tool_call_reuses_existing_metrics(self, metrics_collector):
        """Test that record_tool_call reuses existing ToolMetrics."""
        metrics_collector.record_tool_call("test_tool", 0.5, True)
        metrics_collector.record_tool_call("test_tool", 0.3, True)
        
        assert len(metrics_collector._tool_metrics) == 1
        assert metrics_collector._tool_metrics["test_tool"].call_count == 2

    def test_get_summary_returns_stats(self, metrics_collector):
        """Test that get_summary returns comprehensive stats."""
        metrics_collector.record_request("GET", "/api/books", 0.5, 200)
        metrics_collector.record_request("GET", "/api/pages", 0.3, 200)
        metrics_collector.record_request("POST", "/api/books", 0.8, 500, error="Test error")
        
        summary = metrics_collector.get_summary()
        
        assert "uptime_seconds" in summary
        assert summary["total_requests"] == 3
        assert "requests_per_second" in summary
        assert "avg_duration_ms" in summary
        assert summary["error_count"] == 1
        assert "error_rate" in summary
        assert summary["status_codes"] == {200: 2, 500: 1}

    def test_get_summary_uptime_calculation(self, metrics_collector):
        """Test that get_summary correctly calculates uptime."""
        summary = metrics_collector.get_summary()
        
        # Should have non-zero uptime
        assert summary["uptime_seconds"] > 0
        assert "uptime_formatted" in summary

    def test_get_summary_request_rate(self, metrics_collector):
        """Test that get_summary calculates request rate."""
        metrics_collector.record_request("GET", "/api/books", 0.5, 200)
        
        summary = metrics_collector.get_summary()
        
        # Should have non-zero request rate
        requests_per_second = float(summary["requests_per_second"])
        assert requests_per_second > 0

    def test_get_summary_error_rate(self, metrics_collector):
        """Test that get_summary calculates error rate correctly."""
        metrics_collector.record_request("GET", "/api/books", 0.5, 200)
        metrics_collector.record_request("GET", "/api/pages", 0.3, 200)
        metrics_collector.record_request("POST", "/api/books", 0.8, 500, error="Error 1")
        metrics_collector.record_request("PUT", "/api/pages", 0.6, 500, error="Error 2")
        
        summary = metrics_collector.get_summary()
        
        # 2 errors out of 4 requests = 50%
        assert summary["error_count"] == 2
        assert "50.00%" in summary["error_rate"]

    def test_get_tool_metrics_returns_dict(self, metrics_collector):
        """Test that get_tool_metrics returns tool stats as dict."""
        metrics_collector.record_tool_call("tool1", 0.5, True)
        metrics_collector.record_tool_call("tool2", 0.3, False, "Error")
        
        tool_metrics = metrics_collector.get_tool_metrics()
        
        assert "tool1" in tool_metrics
        assert "tool2" in tool_metrics
        assert tool_metrics["tool1"]["call_count"] == 1
        assert tool_metrics["tool2"]["error_count"] == 1

    def test_get_entity_metrics_tracks_operations(self, metrics_collector):
        """Test that get_entity_metrics tracks entity operations."""
        metrics_collector.record_entity_operation("book", "create")
        metrics_collector.record_entity_operation("book", "read")
        metrics_collector.record_entity_operation("book", "create")
        metrics_collector.record_entity_operation("page", "create")
        
        entity_metrics = metrics_collector.get_entity_metrics()
        
        assert entity_metrics["book"]["create"] == 2
        assert entity_metrics["book"]["read"] == 1
        assert entity_metrics["page"]["create"] == 1

    def test_get_recent_errors_returns_limited_list(self, metrics_collector):
        """Test that get_recent_errors respects limit parameter."""
        for i in range(100):
            metrics_collector.record_request("GET", f"/api/test/{i}", 0.5, 500, error=f"Error {i}")
        
        errors = metrics_collector.get_recent_errors(limit=10)
        assert len(errors) == 10
        
        errors = metrics_collector.get_recent_errors(limit=25)
        assert len(errors) == 25

    def test_get_recent_errors_returns_last_n(self, metrics_collector):
        """Test that get_recent_errors returns the last N errors."""
        for i in range(10):
            metrics_collector.record_request("GET", f"/api/test/{i}", 0.5, 500, error=f"Error {i}")
        
        errors = metrics_collector.get_recent_errors(limit=3)
        
        # Should get the last 3 errors
        assert len(errors) == 3
        assert errors[0]["error"] == "Error 7"
        assert errors[1]["error"] == "Error 8"
        assert errors[2]["error"] == "Error 9"

    def test_get_slow_requests_returns_limited_list(self, metrics_collector):
        """Test that get_slow_requests respects limit parameter."""
        for i in range(100):
            metrics_collector.record_request("GET", f"/api/test/{i}", 10.0, 200)
        
        slow = metrics_collector.get_slow_requests(limit=10)
        assert len(slow) == 10
        
        slow = metrics_collector.get_slow_requests(limit=30)
        assert len(slow) == 30

    def test_get_top_endpoints_returns_sorted_list(self, metrics_collector):
        """Test that get_top_endpoints returns endpoints sorted by count."""
        metrics_collector.record_request("GET", "/api/books", 0.5, 200)
        metrics_collector.record_request("GET", "/api/books", 0.5, 200)
        metrics_collector.record_request("GET", "/api/books", 0.5, 200)
        metrics_collector.record_request("GET", "/api/pages", 0.5, 200)
        metrics_collector.record_request("GET", "/api/pages", 0.5, 200)
        metrics_collector.record_request("POST", "/api/images", 0.5, 200)
        
        top = metrics_collector.get_top_endpoints(limit=3)
        
        assert len(top) == 3
        assert top[0]["endpoint"] == "GET /api/books"
        assert top[0]["count"] == 3
        assert top[1]["endpoint"] == "GET /api/pages"
        assert top[1]["count"] == 2
        assert top[2]["endpoint"] == "POST /api/images"
        assert top[2]["count"] == 1

    def test_reset_clears_all_state(self, metrics_collector):
        """Test that reset clears all metrics state."""
        # Add various metrics
        metrics_collector.record_request("GET", "/api/books", 0.5, 200)
        metrics_collector.record_request("GET", "/api/pages", 6.0, 500, error="Error")
        metrics_collector.record_tool_call("test_tool", 0.5, True)
        metrics_collector.record_entity_operation("book", "create")
        
        # Reset
        metrics_collector.reset()
        
        # Everything should be cleared
        assert len(metrics_collector._requests) == 0
        assert len(metrics_collector._request_counts) == 0
        assert len(metrics_collector._status_counts) == 0
        assert len(metrics_collector._tool_metrics) == 0
        assert len(metrics_collector._entity_operations) == 0
        assert len(metrics_collector._errors) == 0
        assert len(metrics_collector._slow_requests) == 0


class TestTrackToolDecorator:
    """Test the @track_tool decorator."""

    def test_track_tool_records_success(self):
        """Test that @track_tool records successful calls."""
        collector = get_metrics_collector()
        collector.reset()
        
        @track_tool("test_decorator")
        def test_function():
            return "success"
        
        result = test_function()
        
        assert result == "success"
        assert "test_decorator" in collector._tool_metrics
        assert collector._tool_metrics["test_decorator"].success_count == 1
        assert collector._tool_metrics["test_decorator"].error_count == 0

    def test_track_tool_records_failure(self):
        """Test that @track_tool records failures and re-raises."""
        collector = get_metrics_collector()
        collector.reset()
        
        @track_tool("test_decorator_fail")
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValueError, match="Test error"):
            test_function()
        
        assert "test_decorator_fail" in collector._tool_metrics
        assert collector._tool_metrics["test_decorator_fail"].success_count == 0
        assert collector._tool_metrics["test_decorator_fail"].error_count == 1
        assert "Test error" in collector._tool_metrics["test_decorator_fail"].errors

    def test_track_tool_records_duration(self):
        """Test that @track_tool records execution duration."""
        collector = get_metrics_collector()
        collector.reset()
        
        @track_tool("test_decorator_duration")
        def test_function():
            time.sleep(0.05)  # 50ms
            return "done"
        
        test_function()
        
        metrics = collector._tool_metrics["test_decorator_duration"]
        # Should be at least 50ms
        assert metrics.total_duration >= 0.05
