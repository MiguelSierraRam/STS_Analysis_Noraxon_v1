"""
Tests for src/validation.py module.

Tests cover:
- DataFrame structure validation
- Required column detection
- Data type validation
- Numeric range validation
- Time column consistency
- Complete STS data validation
"""

import pytest
import pandas as pd
import numpy as np
from src.validation import (
    ValidationError,
    ValidationWarning,
    validate_dataframe,
    validate_required_columns,
    validate_column_types,
    validate_numeric_range,
    validate_time_column,
    validate_sts_data,
)


class TestValidateDataFrame:
    """Tests for validate_dataframe function."""

    def test_valid_dataframe(self):
        """Valid DataFrame should pass."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        is_valid, errors = validate_dataframe(df, min_rows=2, min_columns=2, raise_on_error=False)
        assert is_valid
        assert len(errors) == 0

    def test_empty_dataframe(self):
        """Empty DataFrame should fail."""
        df = pd.DataFrame()
        is_valid, errors = validate_dataframe(df, raise_on_error=False)
        assert not is_valid
        assert len(errors) > 0

    def test_none_dataframe(self):
        """None DataFrame should fail."""
        is_valid, errors = validate_dataframe(None, raise_on_error=False)
        assert not is_valid

    def test_insufficient_rows(self):
        """DataFrame with too few rows should fail."""
        df = pd.DataFrame({"A": [1, 2]})
        is_valid, errors = validate_dataframe(df, min_rows=10, raise_on_error=False)
        assert not is_valid

    def test_raises_on_error(self):
        """ValidationError should be raised when raise_on_error=True."""
        df = pd.DataFrame()
        with pytest.raises(ValidationError):
            validate_dataframe(df, raise_on_error=True)


class TestValidateRequiredColumns:
    """Tests for validate_required_columns function."""

    def test_all_columns_present(self):
        """When all columns exist, should succeed."""
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4], "C": [5, 6]})
        is_valid, missing, mapping = validate_required_columns(
            df, ["A", "B"], raise_on_error=False
        )
        assert is_valid
        assert len(missing) == 0
        assert mapping == {"A": "A", "B": "B"}

    def test_missing_columns(self):
        """When columns are missing, should detect them."""
        df = pd.DataFrame({"A": [1, 2], "B": [3, 4]})
        is_valid, missing, mapping = validate_required_columns(
            df, ["A", "B", "C"], raise_on_error=False
        )
        assert not is_valid
        assert "C" in missing

    def test_case_insensitive_match(self):
        """Should match columns case-insensitively."""
        df = pd.DataFrame({"tiempo": [1, 2], "velocidad": [3, 4]})
        is_valid, missing, mapping = validate_required_columns(
            df, ["Tiempo", "Velocidad"], case_insensitive=True, raise_on_error=False
        )
        assert is_valid
        assert mapping["Tiempo"] == "tiempo"
        assert mapping["Velocidad"] == "velocidad"

    def test_case_sensitive_fails(self):
        """Case-sensitive match should fail if case differs."""
        df = pd.DataFrame({"tiempo": [1, 2]})
        is_valid, missing, mapping = validate_required_columns(
            df, ["Tiempo"], case_insensitive=False, raise_on_error=False
        )
        assert not is_valid


class TestValidateColumnTypes:
    """Tests for validate_column_types function."""

    def test_numeric_column_correct(self):
        """Numeric column should validate as float."""
        df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
        is_valid, errors = validate_column_types(
            df, {"value": float}, raise_on_error=False
        )
        assert is_valid

    def test_numeric_column_incorrect(self):
        """String column should fail numeric validation."""
        df = pd.DataFrame({"value": ["a", "b", "c"]})
        is_valid, errors = validate_column_types(
            df, {"value": float}, raise_on_error=False
        )
        assert not is_valid

    def test_missing_column_skipped(self):
        """Missing column should not be reported as error."""
        df = pd.DataFrame({"A": [1, 2]})
        is_valid, errors = validate_column_types(
            df, {"B": float}, raise_on_error=False
        )
        assert is_valid  # Missing columns are skipped


class TestValidateNumericRange:
    """Tests for validate_numeric_range function."""

    def test_values_in_range(self):
        """Values within range should pass."""
        df = pd.DataFrame({"value": [1.0, 2.0, 3.0]})
        is_valid, errors = validate_numeric_range(
            df, "value", min_val=0, max_val=5, raise_on_error=False
        )
        assert is_valid

    def test_values_exceed_max(self):
        """Values exceeding max should fail."""
        df = pd.DataFrame({"value": [1.0, 2.0, 10.0]})
        is_valid, errors = validate_numeric_range(
            df, "value", min_val=0, max_val=5, raise_on_error=False
        )
        assert not is_valid
        assert len(errors) > 0

    def test_values_below_min(self):
        """Values below min should fail."""
        df = pd.DataFrame({"value": [-5.0, 2.0, 3.0]})
        is_valid, errors = validate_numeric_range(
            df, "value", min_val=0, max_val=5, raise_on_error=False
        )
        assert not is_valid

    def test_nan_not_allowed(self):
        """NaN values should fail when allow_nan=False."""
        df = pd.DataFrame({"value": [1.0, np.nan, 3.0]})
        is_valid, errors = validate_numeric_range(
            df, "value", allow_nan=False, raise_on_error=False
        )
        assert not is_valid

    def test_nan_allowed(self):
        """NaN values should pass when allow_nan=True."""
        df = pd.DataFrame({"value": [1.0, np.nan, 3.0]})
        is_valid, errors = validate_numeric_range(
            df, "value", allow_nan=True, raise_on_error=False
        )
        assert is_valid


class TestValidateTimeColumn:
    """Tests for validate_time_column function."""

    def test_valid_time_column(self):
        """Valid monotonic time column should pass."""
        df = pd.DataFrame({"time": np.arange(0, 1.0, 0.01)})
        is_valid, errors, stats = validate_time_column(
            df, "time", raise_on_error=False
        )
        assert is_valid
        assert stats["sampling_rate_hz"] > 0
        assert stats["is_monotonic"]

    def test_non_monotonic_time(self):
        """Non-monotonic time should fail."""
        df = pd.DataFrame({"time": [0, 0.01, 0.02, 0.01, 0.03]})
        is_valid, errors, stats = validate_time_column(
            df, "time", raise_on_error=False
        )
        assert not is_valid
        assert not stats["is_monotonic"]

    def test_missing_time_column(self):
        """Missing time column should fail."""
        df = pd.DataFrame({"data": [1, 2, 3]})
        is_valid, errors, stats = validate_time_column(
            df, "time", raise_on_error=False
        )
        assert not is_valid

    def test_insufficient_samples(self):
        """Time column with <2 samples should fail."""
        df = pd.DataFrame({"time": [0.0]})
        is_valid, errors, stats = validate_time_column(
            df, "time", raise_on_error=False
        )
        assert not is_valid

    def test_time_stats_computation(self):
        """Time statistics should be correctly computed."""
        df = pd.DataFrame({"time": [0, 0.01, 0.02, 0.03, 0.04]})
        is_valid, errors, stats = validate_time_column(
            df, "time", raise_on_error=False
        )
        assert stats["duration_s"] == pytest.approx(0.04, abs=1e-3)
        assert stats["n_samples"] == 5
        assert stats["sampling_rate_hz"] == pytest.approx(100, abs=1)

    def test_dt_consistency_check(self):
        """Inconsistent sampling should be flagged."""
        # Create irregular sampling: mostly 0.01s but one jump
        time = np.array([0, 0.01, 0.02, 0.05, 0.06])  # 0.05 is an outlier
        df = pd.DataFrame({"time": time})
        is_valid, errors, stats = validate_time_column(
            df, "time", raise_on_error=False
        )
        assert not is_valid  # Should detect inconsistency


class TestValidateSTSData:
    """Tests for complete validate_sts_data function."""

    def test_valid_sts_data(self):
        """Valid STS data should pass all checks."""
        time = np.arange(0, 5.0, 0.01)
        df = pd.DataFrame({
            "Tiempo": time,
            "BCM Z": 600 + 100 * np.sin(time),
            "Velocidad": np.cos(time) * 0.5,
            "Aceleración": -np.sin(time) * 0.5,
        })
        result = validate_sts_data(df, raise_on_error=False)
        assert result["is_valid"]
        assert len(result["errors"]) == 0

    def test_missing_required_columns(self):
        """Missing columns should be detected."""
        df = pd.DataFrame({
            "Tiempo": [1, 2, 3],
            "BCM Z": [600, 610, 620],
        })
        result = validate_sts_data(df, raise_on_error=False)
        assert not result["is_valid"]
        assert len(result["errors"]) > 0

    def test_case_insensitive_columns(self):
        """Column names should be matched case-insensitively."""
        df = pd.DataFrame({
            "tiempo": np.arange(0, 1.0, 0.01),
            "bcm z": 600 + np.random.randn(100),
            "velocidad": np.random.randn(100) * 0.1,
            "aceleración": np.random.randn(100) * 0.1,
        })
        result = validate_sts_data(df, time_col="Tiempo", raise_on_error=False)
        assert result["is_valid"]

    def test_warnings_for_suspicious_data(self):
        """Should generate warnings for suspicious data."""
        df = pd.DataFrame({
            "Tiempo": np.arange(0, 1.0, 0.01),
            "BCM Z": [500] * 100,  # All zeros = no motion
            "Velocidad": [0.0001] * 100,  # Near-zero velocity
            "Aceleración": [0] * 100,
        })
        result = validate_sts_data(df, raise_on_error=False)
        # Should have warnings about near-zero velocity
        assert len(result["warnings"]) > 0

    def test_statistics_computation(self):
        """Statistics should be correctly computed."""
        time = np.arange(0, 1.0, 0.01)
        bcm_z = 600 + 50 * np.sin(2 * np.pi * time)
        df = pd.DataFrame({
            "Tiempo": time,
            "BCM Z": bcm_z,
            "Velocidad": np.random.randn(100) * 0.1,
            "Aceleración": np.random.randn(100) * 0.1,
        })
        result = validate_sts_data(df, raise_on_error=False)
        assert "time" in result["stats"]
        assert "bcm_z" in result["stats"]
        assert result["stats"]["bcm_z"]["mean"] > 0

    def test_raises_on_critical_error(self):
        """Should raise ValidationError on critical failure."""
        df = pd.DataFrame()  # Empty
        with pytest.raises(ValidationError):
            validate_sts_data(df, raise_on_error=True)


class TestValidationWarning:
    """Tests for ValidationWarning class."""

    def test_creates_warning(self):
        """Should create warning object."""
        warn = ValidationWarning("test message", "warning")
        assert warn.message == "test message"
        assert warn.severity == "warning"

    def test_warning_string_representation(self):
        """String representation should include severity."""
        warn = ValidationWarning("test", "warning")
        assert "[WARNING]" in str(warn)
        assert "test" in str(warn)
