"""
Tests for src/benchmark.py performance utilities.

Tests cover:
- PerformanceTimer context manager
- benchmark_function timing accuracy
- create_benchmark_data synthetic data generation
- Memory profiling functionality
"""

import pytest
import pandas as pd
import numpy as np
import time
from unittest.mock import patch
from src.benchmark import (
    PerformanceTimer,
    benchmark_function,
    create_benchmark_data,
    profile_memory_usage,
)


class TestPerformanceTimer:
    """Tests for PerformanceTimer context manager."""

    def test_timer_measures_time(self):
        """Timer should accurately measure elapsed time."""
        with PerformanceTimer("test") as timer:
            time.sleep(0.01)  # 10ms sleep

        assert timer.elapsed_seconds >= 0.009  # At least 9ms
        assert timer.elapsed_seconds < 0.2  # Less than 200ms (allowing for timing variance)

    def test_timer_properties(self):
        """Timer should have correct properties."""
        timer = PerformanceTimer("test_operation")
        assert timer.name == "test_operation"
        assert timer.start_time is None
        assert timer.end_time is None

    def test_timer_elapsed_before_exit(self):
        """Elapsed time should be available before context exit."""
        timer = PerformanceTimer("test")
        with timer:
            time.sleep(0.01)
            elapsed = timer.elapsed_seconds
            assert elapsed >= 0.009


class TestBenchmarkFunction:
    """Tests for benchmark_function utility."""

    def test_benchmark_returns_statistics(self):
        """Benchmark should return timing statistics."""
        def dummy_func(x):
            time.sleep(0.001)  # 1ms
            return x * 2

        result = benchmark_function(dummy_func, 5, n_runs=3, warmup_runs=1)

        assert "mean" in result
        assert "std" in result
        assert "min" in result
        assert "max" in result
        assert "median" in result
        assert result["n_runs"] == 3
        assert result["result"] == 10  # 5 * 2

    def test_benchmark_timing_accuracy(self):
        """Benchmark timing should be reasonably accurate."""
        def fast_func():
            return 42

        result = benchmark_function(fast_func, n_runs=5, warmup_runs=0)

        # Fast function should complete in microseconds
        assert result["mean"] < 0.001  # Less than 1ms
        assert result["min"] >= 0
        assert result["max"] >= result["min"]

    def test_benchmark_with_kwargs(self):
        """Benchmark should handle keyword arguments."""
        def func_with_kwargs(x, multiplier=1):
            time.sleep(0.001)
            return x * multiplier

        result = benchmark_function(
            func_with_kwargs, 3, n_runs=2, warmup_runs=0, multiplier=4
        )

        assert result["result"] == 12  # 3 * 4


class TestCreateBenchmarkData:
    """Tests for create_benchmark_data function."""

    def test_creates_dataframe_with_correct_columns(self):
        """Should create DataFrame with expected columns."""
        df, rep_events = create_benchmark_data(n_samples=100, n_reps=2)

        required_cols = ["Tiempo", "BCM Z", "Velocidad", "Aceleración"]
        for col in required_cols:
            assert col in df.columns

    def test_creates_correct_number_of_repetitions(self):
        """Should create correct number of repetition events."""
        df, rep_events = create_benchmark_data(n_samples=1000, n_reps=3)

        assert len(rep_events) == 3

        # Check that events have required keys
        for event in rep_events:
            assert "stand_idx" in event
            assert "peak_idx" in event
            assert "sit_idx" in event
            assert "rep_idx" in event

    def test_time_vector_properties(self):
        """Time vector should have correct properties."""
        df, rep_events = create_benchmark_data(n_samples=100, n_reps=1)

        time_col = df["Tiempo"]
        assert len(time_col) == 100
        assert time_col.iloc[0] == 0.0
        assert time_col.iloc[-1] == 0.99  # 100 samples at 0.01s intervals

        # Check monotonic increasing
        assert time_col.is_monotonic_increasing

    def test_data_has_reasonable_values(self):
        """Generated data should have reasonable value ranges."""
        df, rep_events = create_benchmark_data(n_samples=1000, n_reps=2)

        # BCM Z should be around 600mm ± 150mm
        bcm_z = df["BCM Z"]
        assert bcm_z.mean() > 500
        assert bcm_z.mean() < 700
        assert bcm_z.std() > 50  # Should have variation

        # Velocity should be small values
        velocity = df["Velocidad"]
        assert abs(velocity.mean()) < 1.0
        assert velocity.std() > 0.05

    def test_reproducible_results(self):
        """Results should be reproducible with same seed."""
        df1, events1 = create_benchmark_data(n_samples=100, n_reps=1)
        df2, events2 = create_benchmark_data(n_samples=100, n_reps=1)

        pd.testing.assert_frame_equal(df1, df2)
        assert events1 == events2


class TestProfileMemoryUsage:
    """Tests for profile_memory_usage function."""

    def test_memory_profiling_basic(self):
        """Memory profiling should return usage statistics."""
        def test_func():
            data = [1] * 1000  # Allocate some memory
            return sum(data)

        result = profile_memory_usage(test_func)

        assert "initial_memory_mb" in result
        assert "final_memory_mb" in result
        assert "peak_memory_mb" in result
        assert "memory_delta_mb" in result
        assert "execution_time_s" in result
        assert result["result"] == 1000

    def test_memory_profiling_with_args(self):
        """Memory profiling should handle function arguments."""
        def test_func(n):
            return list(range(n))

        result = profile_memory_usage(test_func, 100)

        assert isinstance(result["result"], list)
        assert len(result["result"]) == 100
        assert result["execution_time_s"] >= 0


class TestBenchmarkIntegration:
    """Integration tests for benchmark utilities."""

    def test_full_benchmark_workflow(self):
        """Test complete benchmark workflow."""
        # This would normally test run_performance_benchmarks()
        # but that requires all STS modules to be working
        # For now, just test the synthetic data creation
        df, events = create_benchmark_data(n_samples=500, n_reps=2)

        assert isinstance(df, pd.DataFrame)
        assert len(events) == 2
        assert len(df) == 500

        # Verify data quality
        assert not df.isnull().any().any()  # No NaN values
        assert df["Tiempo"].is_monotonic_increasing