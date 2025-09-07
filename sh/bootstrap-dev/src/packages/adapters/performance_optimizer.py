"""
Performance Optimization Module for AI Guardrails Bootstrap

Provides performance monitoring, optimization utilities, and caching
for the plugin system and bootstrap operations.

Features:
- Performance monitoring and profiling
- Caching for plugin operations
- Async operation support
- Memory optimization
- Installation speed optimization
- Plugin dependency resolution optimization
"""

import time
import asyncio
import functools
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import logging
import hashlib
import json
from datetime import datetime, timedelta
import weakref

from ..domain.plugin_models import PluginManifest
from ..core.plugin_validator import PluginValidator


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations."""

    operation: str
    start_time: float
    end_time: float
    duration: float
    memory_usage: int = 0
    cpu_usage: float = 0.0
    io_operations: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CacheEntry:
    """Cache entry with expiration."""

    value: Any
    created_at: datetime
    expires_at: Optional[datetime] = None
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)


class PerformanceMonitor:
    """Monitor and track performance metrics."""

    def __init__(self):
        self.metrics: List[PerformanceMetrics] = []
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()

    def start_operation(self, operation: str) -> str:
        """Start monitoring an operation."""
        operation_id = f"{operation}_{int(time.time() * 1000000)}"
        return operation_id

    def record_metric(self, metric: PerformanceMetrics):
        """Record a performance metric."""
        with self._lock:
            self.metrics.append(metric)

    def get_metrics(
        self, operation: str = None, since: datetime = None
    ) -> List[PerformanceMetrics]:
        """Get performance metrics."""
        with self._lock:
            filtered_metrics = self.metrics.copy()

        if operation:
            filtered_metrics = [m for m in filtered_metrics if m.operation == operation]

        if since:
            filtered_metrics = [
                m
                for m in filtered_metrics
                if datetime.fromtimestamp(m.start_time) >= since
            ]

        return filtered_metrics

    def get_summary(self, operation: str = None) -> Dict[str, Any]:
        """Get performance summary."""
        metrics = self.get_metrics(operation)

        if not metrics:
            return {}

        durations = [m.duration for m in metrics]

        return {
            "operation": operation or "all",
            "count": len(metrics),
            "total_duration": sum(durations),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_cache_hits": sum(m.cache_hits for m in metrics),
            "total_cache_misses": sum(m.cache_misses for m in metrics),
            "cache_hit_ratio": self._calculate_cache_hit_ratio(metrics),
        }

    def _calculate_cache_hit_ratio(self, metrics: List[PerformanceMetrics]) -> float:
        """Calculate cache hit ratio."""
        total_hits = sum(m.cache_hits for m in metrics)
        total_misses = sum(m.cache_misses for m in metrics)
        total = total_hits + total_misses

        return total_hits / total if total > 0 else 0.0


class PerformanceCache:
    """High-performance cache with TTL and memory management."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)

        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def get(self, key: str, default=None) -> Any:
        """Get value from cache."""
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                return default

            # Check expiration
            if entry.expires_at and datetime.now() > entry.expires_at:
                del self._cache[key]
                return default

            # Update access info
            entry.access_count += 1
            entry.last_accessed = datetime.now()

            return entry.value

    def set(self, key: str, value: Any, ttl: int = None):
        """Set value in cache."""
        with self._lock:
            ttl = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl) if ttl > 0 else None

            self._cache[key] = CacheEntry(
                value=value, created_at=datetime.now(), expires_at=expires_at
            )

            # Evict if over size limit
            if len(self._cache) > self.max_size:
                self._evict_lru()

    def delete(self, key: str):
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Get cache size."""
        with self._lock:
            return len(self._cache)

    def _evict_lru(self):
        """Evict least recently used entries."""
        if not self._cache:
            return

        # Sort by last accessed time
        sorted_entries = sorted(self._cache.items(), key=lambda x: x[1].last_accessed)

        # Remove oldest 10% or at least 1
        evict_count = max(1, len(self._cache) // 10)

        for i in range(evict_count):
            if i < len(sorted_entries):
                key = sorted_entries[i][0]
                del self._cache[key]

    def _cleanup_loop(self):
        """Background cleanup of expired entries."""
        while True:
            try:
                time.sleep(300)  # Cleanup every 5 minutes
                self._cleanup_expired()
            except Exception as e:
                self.logger.error(f"Cache cleanup error: {e}")

    def _cleanup_expired(self):
        """Remove expired cache entries."""
        with self._lock:
            now = datetime.now()
            expired_keys = [
                key
                for key, entry in self._cache.items()
                if entry.expires_at and now > entry.expires_at
            ]

            for key in expired_keys:
                del self._cache[key]


class AsyncPluginProcessor:
    """Asynchronous plugin operations processor."""

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger(__name__)

    async def process_plugins_parallel(
        self, plugins: List[Path], processor_func: Callable, *args, **kwargs
    ) -> List[Any]:
        """Process multiple plugins in parallel."""
        loop = asyncio.get_event_loop()

        tasks = []
        for plugin_path in plugins:
            task = loop.run_in_executor(
                self.executor, processor_func, plugin_path, *args, **kwargs
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

    async def validate_plugins_async(
        self, plugins: List[Path]
    ) -> Dict[Path, List[str]]:
        """Validate multiple plugins asynchronously."""
        validator = PluginValidator()

        def validate_single(plugin_path: Path) -> List[str]:
            try:
                manifest_path = plugin_path / "plugin-manifest.yaml"
                if not manifest_path.exists():
                    return ["Missing plugin-manifest.yaml"]

                with open(manifest_path) as f:
                    import yaml

                    manifest_data = yaml.safe_load(f)

                manifest = PluginManifest.from_dict(manifest_data)
                return validator.validate_plugin_manifest(manifest)

            except Exception as e:
                return [f"Validation error: {e}"]

        results = await self.process_plugins_parallel(plugins, validate_single)

        return {
            plugin: result if not isinstance(result, Exception) else [str(result)]
            for plugin, result in zip(plugins, results)
        }

    def shutdown(self):
        """Shutdown the executor."""
        self.executor.shutdown(wait=True)


def performance_monitor(operation: str = None):
    """Decorator for monitoring function performance."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                success = True
            except Exception as e:
                result = e
                success = False

            end_time = time.time()
            duration = end_time - start_time

            # Record metric
            metric = PerformanceMetrics(
                operation=op_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                metadata={"success": success},
            )

            # Get global monitor if available
            monitor = getattr(performance_monitor, "_monitor", None)
            if monitor:
                monitor.record_metric(metric)

            if not success:
                raise result

            return result

        return wrapper

    return decorator


def cached(ttl: int = 3600, key_func: Callable = None):
    """Decorator for caching function results."""

    def decorator(func: Callable) -> Callable:
        cache = PerformanceCache()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = _generate_cache_key(func.__name__, args, kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(cache_key, result, ttl)

            return result

        wrapper._cache = cache
        return wrapper

    return decorator


def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function arguments."""
    key_data = {
        "function": func_name,
        "args": str(args),
        "kwargs": sorted(kwargs.items()),
    }

    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.md5(key_str.encode()).hexdigest()


class PluginInstallationOptimizer:
    """Optimize plugin installation performance."""

    def __init__(self):
        self.cache = PerformanceCache(max_size=500, default_ttl=7200)  # 2 hour TTL
        self.logger = logging.getLogger(__name__)

    @cached(ttl=3600)
    def get_dependency_order(self, plugins: List[str]) -> List[str]:
        """Get optimal installation order for plugins."""
        # This would implement dependency resolution
        # For now, return as-is
        return plugins

    def optimize_file_operations(self, file_operations: List[Dict]) -> List[Dict]:
        """Optimize file operations for better performance."""
        # Group operations by type
        copy_ops = []
        template_ops = []
        other_ops = []

        for op in file_operations:
            if op.get("action") == "copy":
                copy_ops.append(op)
            elif op.get("action") == "template":
                template_ops.append(op)
            else:
                other_ops.append(op)

        # Return in optimal order (copy first, then templates, then others)
        return copy_ops + template_ops + other_ops

    def batch_file_operations(
        self, operations: List[Dict], batch_size: int = 10
    ) -> List[List[Dict]]:
        """Batch file operations for parallel processing."""
        batches = []
        for i in range(0, len(operations), batch_size):
            batch = operations[i : i + batch_size]
            batches.append(batch)

        return batches


class MemoryOptimizer:
    """Memory optimization utilities."""

    def __init__(self):
        self.weak_refs: Dict[str, weakref.ref] = {}
        self.logger = logging.getLogger(__name__)

    def register_object(self, name: str, obj: Any):
        """Register object for weak reference tracking."""
        self.weak_refs[name] = weakref.ref(obj)

    def cleanup_refs(self):
        """Clean up dead weak references."""
        dead_refs = [name for name, ref in self.weak_refs.items() if ref() is None]

        for name in dead_refs:
            del self.weak_refs[name]

    def get_memory_usage(self) -> Dict[str, int]:
        """Get memory usage statistics."""
        import sys

        usage = {}
        for name, ref in self.weak_refs.items():
            obj = ref()
            if obj is not None:
                usage[name] = sys.getsizeof(obj)

        return usage


# Global instances
_performance_monitor = PerformanceMonitor()
_global_cache = PerformanceCache()
_memory_optimizer = MemoryOptimizer()

# Set global monitor for decorator
performance_monitor._monitor = _performance_monitor


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor."""
    return _performance_monitor


def get_global_cache() -> PerformanceCache:
    """Get global cache instance."""
    return _global_cache


def get_memory_optimizer() -> MemoryOptimizer:
    """Get global memory optimizer."""
    return _memory_optimizer


class PerformanceError(Exception):
    """Exception raised during performance operations."""

    pass
