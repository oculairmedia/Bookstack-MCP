"""Metrics and monitoring for BookStack MCP server."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
from datetime import datetime, timedelta
import threading


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    
    timestamp: float
    method: str
    endpoint: str
    duration: float
    status: int
    error: Optional[str] = None


@dataclass
class ToolMetrics:
    """Metrics for tool execution."""
    
    tool_name: str
    call_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    last_called: Optional[float] = None
    errors: List[str] = field(default_factory=list)
    
    def record_call(self, duration: float, success: bool, error: Optional[str] = None):
        """Record a tool call."""
        self.call_count += 1
        self.total_duration += duration
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)
        self.last_called = time.time()
        
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
            if error:
                self.errors.append(error)
                # Keep only last 100 errors
                if len(self.errors) > 100:
                    self.errors = self.errors[-100:]
    
    @property
    def avg_duration(self) -> float:
        """Calculate average duration."""
        return self.total_duration / self.call_count if self.call_count > 0 else 0.0
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage."""
        return (self.success_count / self.call_count * 100) if self.call_count > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "call_count": self.call_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": f"{self.success_rate:.2f}%",
            "avg_duration_ms": f"{self.avg_duration * 1000:.2f}",
            "min_duration_ms": f"{self.min_duration * 1000:.2f}",
            "max_duration_ms": f"{self.max_duration * 1000:.2f}",
            "last_called": datetime.fromtimestamp(self.last_called).isoformat() if self.last_called else None,
            "recent_errors": self.errors[-10:],  # Last 10 errors
        }


class MetricsCollector:
    """Centralized metrics collection and reporting."""
    
    def __init__(self):
        self._lock = threading.RLock()
        self._start_time = time.time()
        
        # Request metrics
        self._requests: List[RequestMetrics] = []
        self._request_counts: Dict[str, int] = defaultdict(int)
        self._status_counts: Dict[int, int] = defaultdict(int)
        
        # Tool metrics
        self._tool_metrics: Dict[str, ToolMetrics] = {}
        
        # Entity metrics
        self._entity_operations: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Error tracking
        self._errors: List[Dict[str, Any]] = []
        
        # Performance tracking
        self._slow_requests: List[RequestMetrics] = []
        self._slow_threshold = 5.0  # seconds
    
    def record_request(
        self,
        method: str,
        endpoint: str,
        duration: float,
        status: int,
        error: Optional[str] = None,
    ):
        """Record an API request."""
        with self._lock:
            metrics = RequestMetrics(
                timestamp=time.time(),
                method=method,
                endpoint=endpoint,
                duration=duration,
                status=status,
                error=error,
            )
            
            self._requests.append(metrics)
            self._request_counts[f"{method} {endpoint}"] += 1
            self._status_counts[status] += 1
            
            if duration > self._slow_threshold:
                self._slow_requests.append(metrics)
                # Keep only last 100 slow requests
                if len(self._slow_requests) > 100:
                    self._slow_requests = self._slow_requests[-100:]
            
            if error:
                self._errors.append({
                    "timestamp": metrics.timestamp,
                    "method": method,
                    "endpoint": endpoint,
                    "error": error,
                })
                # Keep only last 1000 errors
                if len(self._errors) > 1000:
                    self._errors = self._errors[-1000:]
            
            # Keep only last 10000 requests
            if len(self._requests) > 10000:
                self._requests = self._requests[-10000:]
    
    def record_tool_call(
        self,
        tool_name: str,
        duration: float,
        success: bool,
        error: Optional[str] = None,
    ):
        """Record a tool execution."""
        with self._lock:
            if tool_name not in self._tool_metrics:
                self._tool_metrics[tool_name] = ToolMetrics(tool_name=tool_name)
            
            self._tool_metrics[tool_name].record_call(duration, success, error)
    
    def record_entity_operation(self, entity_type: str, operation: str):
        """Record an entity operation."""
        with self._lock:
            self._entity_operations[entity_type][operation] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary."""
        with self._lock:
            uptime = time.time() - self._start_time
            total_requests = len(self._requests)
            
            # Calculate request rate
            requests_per_second = total_requests / uptime if uptime > 0 else 0
            
            # Calculate average duration
            total_duration = sum(r.duration for r in self._requests)
            avg_duration = total_duration / total_requests if total_requests > 0 else 0
            
            # Calculate error rate
            error_count = sum(1 for r in self._requests if r.error)
            error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "uptime_seconds": uptime,
                "uptime_formatted": str(timedelta(seconds=int(uptime))),
                "total_requests": total_requests,
                "requests_per_second": f"{requests_per_second:.2f}",
                "avg_duration_ms": f"{avg_duration * 1000:.2f}",
                "error_count": error_count,
                "error_rate": f"{error_rate:.2f}%",
                "status_codes": dict(self._status_counts),
                "slow_requests_count": len(self._slow_requests),
            }
    
    def get_tool_metrics(self) -> Dict[str, Any]:
        """Get tool-specific metrics."""
        with self._lock:
            return {
                tool_name: metrics.to_dict()
                for tool_name, metrics in self._tool_metrics.items()
            }
    
    def get_entity_metrics(self) -> Dict[str, Any]:
        """Get entity operation metrics."""
        with self._lock:
            return {
                entity_type: dict(operations)
                for entity_type, operations in self._entity_operations.items()
            }
    
    def get_recent_errors(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent errors."""
        with self._lock:
            return self._errors[-limit:]
    
    def get_slow_requests(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get slow requests."""
        with self._lock:
            return [
                {
                    "timestamp": datetime.fromtimestamp(r.timestamp).isoformat(),
                    "method": r.method,
                    "endpoint": r.endpoint,
                    "duration_ms": f"{r.duration * 1000:.2f}",
                    "status": r.status,
                }
                for r in self._slow_requests[-limit:]
            ]
    
    def get_top_endpoints(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently called endpoints."""
        with self._lock:
            sorted_endpoints = sorted(
                self._request_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            return [
                {"endpoint": endpoint, "count": count}
                for endpoint, count in sorted_endpoints[:limit]
            ]
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self._requests.clear()
            self._request_counts.clear()
            self._status_counts.clear()
            self._tool_metrics.clear()
            self._entity_operations.clear()
            self._errors.clear()
            self._slow_requests.clear()
            self._start_time = time.time()


# Global metrics collector
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    return _metrics_collector


def track_request(method: str, endpoint: str):
    """Decorator to track request metrics."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            status = 200
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                _metrics_collector.record_request(method, endpoint, duration, status, error)
        
        return wrapper
    return decorator


def track_tool(tool_name: str):
    """Decorator to track tool execution metrics."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = str(e)
                success = False
                raise
            finally:
                duration = time.time() - start_time
                _metrics_collector.record_tool_call(tool_name, duration, success, error)
        
        return wrapper
    return decorator

