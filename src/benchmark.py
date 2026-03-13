"""
Performance benchmarking and profiling utilities for STS analysis.

Provides tools to measure execution time, memory usage, and performance
characteristics of critical functions. Useful for optimization and
comparative analysis.
"""

import time
import psutil
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Callable, Optional
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class PerformanceTimer:
    """Context manager for timing code execution."""

    def __init__(self, name: str = "operation"):
        self.name = name
        self.start_time = None
        self.end_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        elapsed = self.end_time - self.start_time
        logger.info(".4f")
        return False

    @property
    def elapsed_seconds(self) -> float:
        """Get elapsed time in seconds."""
        if self.end_time is None:
            return time.perf_counter() - self.start_time
        return self.end_time - self.start_time


@contextmanager
def memory_monitor():
    """Context manager to monitor memory usage."""
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    yield

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    delta_memory = final_memory - initial_memory
    logger.info(".2f")


def benchmark_function(
    func: Callable,
    *args,
    n_runs: int = 10,
    warmup_runs: int = 2,
    **kwargs
) -> Dict[str, Any]:
    """
    Benchmark a function's performance over multiple runs.

    Args:
        func: Function to benchmark
        *args: Positional arguments for func
        n_runs: Number of benchmark runs
        warmup_runs: Number of warmup runs (discarded)
        **kwargs: Keyword arguments for func

    Returns:
        Dict with timing statistics: mean, std, min, max, median
    """
    times = []

    # Warmup runs
    for _ in range(warmup_runs):
        func(*args, **kwargs)

    # Benchmark runs
    for _ in range(n_runs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        times.append(end - start)

    times_array = np.array(times)

    return {
        "mean": float(np.mean(times_array)),
        "std": float(np.std(times_array)),
        "min": float(np.min(times_array)),
        "max": float(np.max(times_array)),
        "median": float(np.median(times_array)),
        "n_runs": n_runs,
        "result": result,  # Last result for verification
    }


def create_benchmark_data(n_samples: int = 10000, n_reps: int = 5) -> pd.DataFrame:
    """
    Create synthetic STS data for benchmarking.

    Args:
        n_samples: Number of time samples
        n_reps: Number of repetitions to simulate

    Returns:
        DataFrame with synthetic STS data
    """
    np.random.seed(42)  # Reproducible results

    # Time vector (100 Hz sampling)
    time = np.arange(0, n_samples / 100, 0.01)

    # BCM Z: sinusoidal with noise
    bcm_z = 600 + 150 * np.sin(2 * np.pi * 0.5 * time) + np.random.normal(0, 10, len(time))

    # Velocity: derivative-like signal
    velocity = 0.5 * np.cos(2 * np.pi * 0.5 * time) + np.random.normal(0, 0.1, len(time))

    # Acceleration: second derivative
    acceleration = -0.5 * np.sin(2 * np.pi * 0.5 * time) + np.random.normal(0, 0.05, len(time))

    # Create repetitions by adding phase shifts
    rep_events = []
    for i in range(n_reps):
        start_time = i * 2.0  # 2 seconds apart
        peak_time = start_time + 0.8
        end_time = start_time + 1.6

        rep_events.append({
            'stand_idx': int(start_time * 100),
            'peak_idx': int(peak_time * 100),
            'sit_idx': int(end_time * 100),
            'rep_idx': i
        })

    df = pd.DataFrame({
        'Tiempo': time,
        'BCM Z': bcm_z,
        'Velocidad': velocity,
        'Aceleración': acceleration,
    })

    return df, rep_events


def run_performance_benchmarks() -> Dict[str, Any]:
    """
    Run comprehensive performance benchmarks on critical STS functions.

    Returns:
        Dict with benchmark results for each tested function
    """
    logger.info("Starting STS performance benchmarks...")

    # Create test data
    df, rep_events = create_benchmark_data(n_samples=5000, n_reps=3)

    results = {}

    # Benchmark detection
    try:
        from src.detection import compute_phase_events

        logger.info("Benchmarking phase detection...")
        results["phase_detection"] = benchmark_function(
            compute_phase_events,
            df, "Tiempo", mass_kg=75.0, window=30,
            n_runs=5
        )
    except Exception as e:
        logger.warning(f"Phase detection benchmark failed: {e}")
        results["phase_detection"] = {"error": str(e)}

    # Benchmark analysis
    try:
        from src.analysis import generate_phase_dataframe

        logger.info("Benchmarking phase analysis...")
        z_mm = df['BCM Z'].values
        vel_m_s = df['Velocidad'].values
        acc_m_s2 = df['Aceleración'].values

        results["phase_analysis"] = benchmark_function(
            generate_phase_dataframe,
            df, "Tiempo", rep_events, [0, 1, 2], z_mm, vel_m_s, acc_m_s2,
            None, 0.01, 7, True,
            n_runs=5
        )
    except Exception as e:
        logger.warning(f"Phase analysis benchmark failed: {e}")
        results["phase_analysis"] = {"error": str(e)}

    # Benchmark validation
    try:
        from src.validation import validate_sts_data

        logger.info("Benchmarking data validation...")
        results["data_validation"] = benchmark_function(
            validate_sts_data,
            df, "Tiempo",
            n_runs=10
        )
    except Exception as e:
        logger.warning(f"Data validation benchmark failed: {e}")
        results["data_validation"] = {"error": str(e)}

    # Benchmark export (if possible)
    try:
        from src.export import create_sheet1_variables

        logger.info("Benchmarking data export...")
        results["data_export"] = benchmark_function(
            create_sheet1_variables,
            df, rep_events, "Tiempo", 75.0, 0.01,
            n_runs=5
        )
    except Exception as e:
        logger.warning(f"Data export benchmark failed: {e}")
        results["data_export"] = {"error": str(e)}

    logger.info("Performance benchmarks completed")
    return results


def print_benchmark_report(benchmark_results: Dict[str, Any]) -> None:
    """
    Print formatted benchmark report.

    Args:
        benchmark_results: Output from run_performance_benchmarks()
    """
    print("\n" + "=" * 70)
    print("STS ANALYSIS PERFORMANCE BENCHMARK REPORT")
    print("=" * 70)

    for operation, result in benchmark_results.items():
        print(f"\n🔧 {operation.replace('_', ' ').title()}:")

        if "error" in result:
            print(f"   ❌ Failed: {result['error']}")
            continue

        print(".4f")
        print(".4f")
        print(".4f")
        print(".4f")
        print(".4f")
        print(f"   📊 Runs: {result['n_runs']}")

    print("\n" + "=" * 70)
    print("Note: Benchmarks use synthetic data (5000 samples, 3 reps)")
    print("Results are for relative comparison, not absolute performance")
    print("=" * 70 + "\n")


def profile_memory_usage(func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """
    Profile memory usage of a function.

    Args:
        func: Function to profile
        *args: Arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Dict with memory usage statistics
    """
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    # Use peak_wset for Windows, peak_rss for Unix-like systems
    peak_memory_attr = getattr(process.memory_info(), 'peak_wset', getattr(process.memory_info(), 'peak_rss', process.memory_info().rss))
    peak_memory = peak_memory_attr / 1024 / 1024  # MB

    return {
        "initial_memory_mb": initial_memory,
        "final_memory_mb": final_memory,
        "peak_memory_mb": peak_memory,
        "memory_delta_mb": final_memory - initial_memory,
        "execution_time_s": end_time - start_time,
        "result": result,
    }


if __name__ == "__main__":
    # Run benchmarks when executed directly
    results = run_performance_benchmarks()
    print_benchmark_report(results)