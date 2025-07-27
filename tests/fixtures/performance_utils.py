"""Simple performance testing utilities for StarHTML handlers."""

import gc
import time
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

import psutil


class SimplePerformanceMonitor:
    """Simple performance monitor with memory tracking."""

    def __init__(self):
        self.start_time: float | None = None
        self.start_memory: float | None = None
        self.process = psutil.Process()

    def start(self):
        """Start monitoring."""
        gc.collect()
        self.start_time = time.perf_counter()
        self.start_memory = self.process.memory_info().rss / 1024 / 1024

    def stop(self) -> dict[str, Any]:
        """Stop monitoring and return results."""
        if self.start_time is None or self.start_memory is None:
            raise RuntimeError("Performance monitor not started")

        end_time = time.perf_counter()
        gc.collect()

        duration = end_time - self.start_time
        end_memory = self.process.memory_info().rss / 1024 / 1024
        memory_used = end_memory - self.start_memory

        return {
            "duration": duration,
            "memory_start": self.start_memory,
            "memory_end": end_memory,
            "memory_used": memory_used,
        }


@contextmanager
def performance_context():
    """Context manager for performance monitoring."""
    monitor = SimplePerformanceMonitor()
    monitor.start()
    try:
        yield monitor
    finally:
        monitor.stop()


def benchmark_function(func: Callable, iterations: int = 1000) -> dict[str, Any]:
    """Benchmark a function execution."""
    monitor = SimplePerformanceMonitor()
    monitor.start()

    for _ in range(iterations):
        func()

    results = monitor.stop()
    results["iterations"] = iterations
    results["avg_per_iteration"] = results["duration"] / iterations

    return results


def format_performance_results(results: dict[str, Any]) -> str:
    """Format performance results for display."""
    output = []
    output.append(f"Duration: {results['duration']:.4f}s")

    if "iterations" in results:
        output.append(f"Iterations: {results['iterations']}")
        output.append(f"Avg per iteration: {results['avg_per_iteration'] * 1000:.2f}ms")

    output.append(f"Memory used: {results['memory_used']:.2f}MB")

    return " | ".join(output)
