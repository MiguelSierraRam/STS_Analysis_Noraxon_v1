"""
Data validation and input quality checks for STS analysis.

Provides comprehensive validation utilities to detect and report:
- Missing or invalid columns
- Empty DataFrames
- Data type mismatches
- Outliers and suspicious values
- Missing metadata
"""

from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation failures."""

    pass


class ValidationWarning:
    """Container for non-critical validation issues."""

    def __init__(self, message: str, severity: str = "warning"):
        """
        Args:
            message: Description of the issue
            severity: 'warning' or 'info'
        """
        self.message = message
        self.severity = severity

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.message}"


def validate_dataframe(
    df: pd.DataFrame,
    min_rows: int = 10,
    min_columns: int = 3,
    raise_on_error: bool = True,
) -> Tuple[bool, List[str]]:
    """
    Validate basic DataFrame structure.

    Args:
        df: DataFrame to validate
        min_rows: Minimum required rows
        min_columns: Minimum required columns
        raise_on_error: If True, raise ValidationError on failure

    Returns:
        Tuple of (is_valid, errors_list)

    Raises:
        ValidationError: If raise_on_error=True and validation fails
    """
    errors = []

    if df is None:
        errors.append("DataFrame is None")
    elif df.empty:
        errors.append("DataFrame is empty")
    elif len(df) < min_rows:
        errors.append(f"DataFrame has {len(df)} rows, need at least {min_rows}")
    elif len(df.columns) < min_columns:
        errors.append(
            f"DataFrame has {len(df.columns)} columns, need at least {min_columns}"
        )

    if errors and raise_on_error:
        raise ValidationError(" | ".join(errors))

    return len(errors) == 0, errors


def validate_required_columns(
    df: pd.DataFrame,
    required_cols: List[str],
    raise_on_error: bool = True,
    case_insensitive: bool = True,
) -> Tuple[bool, List[str], Dict[str, str]]:
    """
    Validate that DataFrame contains required columns.

    Args:
        df: DataFrame to check
        required_cols: List of column names that must exist
        raise_on_error: If True, raise ValidationError on missing columns
        case_insensitive: If True, match columns case-insensitively

    Returns:
        Tuple of (is_valid, missing_cols, found_mapping)
        - is_valid: True if all columns found
        - missing_cols: List of not-found columns
        - found_mapping: Dict mapping required names to actual column names

    Raises:
        ValidationError: If raise_on_error=True and columns missing
    """
    missing = []
    found_mapping = {}

    if df is None or df.empty:
        return False, required_cols, {}

    df_cols_lower = {col.lower(): col for col in df.columns}
    df_cols = set(df.columns)

    for col in required_cols:
        if col in df_cols:
            found_mapping[col] = col
        elif case_insensitive and col.lower() in df_cols_lower:
            found_mapping[col] = df_cols_lower[col.lower()]
        else:
            missing.append(col)

    if missing and raise_on_error:
        error_msg = (
            f"Missing required columns: {missing}\n"
            f"Available columns: {list(df.columns)[:10]}"
        )
        raise ValidationError(error_msg)

    return len(missing) == 0, missing, found_mapping


def validate_column_types(
    df: pd.DataFrame,
    expected_types: Dict[str, type],
    raise_on_error: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validate that columns have expected data types.

    Args:
        df: DataFrame to validate
        expected_types: Dict of column_name -> expected_type
        raise_on_error: If True, raise ValidationError on mismatch

    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []

    for col, expected_type in expected_types.items():
        if col not in df.columns:
            continue

        actual_dtype = df[col].dtype

        # Check if dtype is numeric or datetime as expected
        if expected_type == float and not pd.api.types.is_numeric_dtype(actual_dtype):
            errors.append(f"Column '{col}': expected numeric, got {actual_dtype}")
        elif expected_type == int and not pd.api.types.is_integer_dtype(actual_dtype):
            errors.append(f"Column '{col}': expected int, got {actual_dtype}")
        elif expected_type == str and not pd.api.types.is_string_dtype(actual_dtype):
            errors.append(f"Column '{col}': expected string, got {actual_dtype}")

    if errors and raise_on_error:
        raise ValidationError(" | ".join(errors))

    return len(errors) == 0, errors


def validate_numeric_range(
    df: pd.DataFrame,
    col: str,
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    allow_nan: bool = False,
    raise_on_error: bool = False,
) -> Tuple[bool, List[str]]:
    """
    Validate that numeric column values fall within expected range.

    Args:
        df: DataFrame
        col: Column name to validate
        min_val: Minimum allowed value (None = no lower bound)
        max_val: Maximum allowed value (None = no upper bound)
        allow_nan: If False, NaN values are errors
        raise_on_error: If True, raise ValidationError on failure

    Returns:
        Tuple of (is_valid, errors_list)
    """
    errors = []

    if col not in df.columns:
        errors.append(f"Column '{col}' not found")
        if raise_on_error:
            raise ValidationError(" | ".join(errors))
        return False, errors

    col_data = df[col]

    # Check for NaN
    nan_count = col_data.isna().sum()
    if nan_count > 0 and not allow_nan:
        errors.append(f"Column '{col}': {nan_count} NaN values found")

    # Check range
    valid_data = col_data.dropna()
    if len(valid_data) > 0:
        if min_val is not None and (valid_data < min_val).any():
            below_count = (valid_data < min_val).sum()
            errors.append(
                f"Column '{col}': {below_count} values below {min_val} "
                f"(min: {valid_data.min()})"
            )
        if max_val is not None and (valid_data > max_val).any():
            above_count = (valid_data > max_val).sum()
            errors.append(
                f"Column '{col}': {above_count} values above {max_val} "
                f"(max: {valid_data.max()})"
            )

    if errors and raise_on_error:
        raise ValidationError(" | ".join(errors))

    return len(errors) == 0, errors


def validate_time_column(
    df: pd.DataFrame,
    time_col: str,
    expected_dt: Optional[float] = None,
    raise_on_error: bool = False,
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Validate time column structure and consistency.

    Args:
        df: DataFrame
        time_col: Name of time column
        expected_dt: Expected sampling period in seconds (None = auto-detect)
        raise_on_error: If True, raise ValidationError on failure

    Returns:
        Tuple of (is_valid, errors_list, stats_dict)
        - stats_dict contains: duration, n_samples, dt_mean, dt_std, sampling_rate
    """
    errors = []
    stats = {
        "duration_s": 0,
        "n_samples": 0,
        "dt_mean": 0,
        "dt_std": 0,
        "sampling_rate_hz": 0,
        "is_monotonic": True,
    }

    if time_col not in df.columns:
        errors.append(f"Time column '{time_col}' not found")
        if raise_on_error:
            raise ValidationError(" | ".join(errors))
        return False, errors, stats

    time_data = df[time_col].dropna()

    if len(time_data) < 2:
        errors.append(f"Time column has {len(time_data)} samples, need at least 2")
        if raise_on_error:
            raise ValidationError(" | ".join(errors))
        return False, errors, stats

    # Check monotonicity
    is_monotonic = time_data.is_monotonic_increasing
    if not is_monotonic:
        errors.append("Time column is not monotonically increasing")
        stats["is_monotonic"] = False

    # Compute statistics
    dt_array = np.diff(time_data.values)
    stats["duration_s"] = float(time_data.iloc[-1] - time_data.iloc[0])
    stats["n_samples"] = len(time_data)
    stats["dt_mean"] = float(np.mean(dt_array))
    stats["dt_std"] = float(np.std(dt_array))
    stats["sampling_rate_hz"] = 1.0 / stats["dt_mean"] if stats["dt_mean"] > 0 else 0

    # Check sampling rate consistency
    if stats["dt_std"] > stats["dt_mean"] * 0.1:  # >10% variation
        errors.append(
            f"Inconsistent sampling: dt_mean={stats['dt_mean']:.4f}, "
            f"dt_std={stats['dt_std']:.6f}"
        )

    # Check expected dt if provided
    if expected_dt is not None:
        dt_diff = abs(stats["dt_mean"] - expected_dt) / expected_dt
        if dt_diff > 0.05:  # >5% difference
            errors.append(
                f"Actual dt={stats['dt_mean']:.4f}s, "
                f"expected {expected_dt:.4f}s (diff: {dt_diff*100:.1f}%)"
            )

    if errors and raise_on_error:
        raise ValidationError(" | ".join(errors))

    return len(errors) == 0, errors, stats


def validate_sts_data(
    df: pd.DataFrame,
    time_col: str = "Tiempo",
    required_cols: Optional[List[str]] = None,
    raise_on_error: bool = True,
) -> Dict[str, Any]:
    """
    Complete validation for STS analysis data.

    Args:
        df: Input DataFrame
        time_col: Name of time column
        required_cols: Columns that must exist (default: common STS columns)
        raise_on_error: If True, raise ValidationError on critical failure

    Returns:
        Dict with validation results:
        - is_valid (bool)
        - errors (list of error messages)
        - warnings (list of ValidationWarning objects)
        - stats (dict with data statistics)
    """
    if required_cols is None:
        required_cols = ["Tiempo", "BCM Z", "Velocidad", "Aceleración"]

    result = {"is_valid": True, "errors": [], "warnings": [], "stats": {}}

    # 1. Validate DataFrame structure
    try:
        is_valid, errors = validate_dataframe(df, min_rows=10, raise_on_error=True)
        if not is_valid:
            result["is_valid"] = False
            result["errors"].extend(errors)
    except ValidationError as e:
        result["is_valid"] = False
        result["errors"].append(str(e))
        if raise_on_error:
            raise
        return result

    # 2. Validate required columns
    is_valid, missing, mapping = validate_required_columns(
        df, required_cols, raise_on_error=False, case_insensitive=True
    )
    if not is_valid:
        result["errors"].append(f"Missing columns: {missing}")
        if raise_on_error:
            raise ValidationError(f"Missing columns: {missing}")

    # 3. Validate time column
    time_col_actual = mapping.get(time_col, time_col)
    if time_col_actual in df.columns:
        is_valid, time_errors, time_stats = validate_time_column(
            df, time_col_actual, expected_dt=0.01, raise_on_error=False
        )
        result["stats"]["time"] = time_stats
        if time_errors:
            result["warnings"].extend(
                [ValidationWarning(e, "warning") for e in time_errors]
            )

    # 4. Validate BCM Z range
    bcm_col = mapping.get("BCM Z", "BCM Z")
    if bcm_col in df.columns:
        is_valid, bcm_errors = validate_numeric_range(
            df, bcm_col, min_val=0, max_val=2000, allow_nan=True, raise_on_error=False
        )
        if bcm_errors:
            result["warnings"].extend(
                [ValidationWarning(e, "warning") for e in bcm_errors]
            )
        result["stats"]["bcm_z"] = {
            "mean": float(df[bcm_col].mean()),
            "std": float(df[bcm_col].std()),
            "min": float(df[bcm_col].min()),
            "max": float(df[bcm_col].max()),
        }

    # 5. Validate velocity range
    vel_col = mapping.get("Velocidad", "Velocidad")
    if vel_col in df.columns:
        is_valid, vel_errors = validate_numeric_range(
            df, vel_col, min_val=-2, max_val=2, allow_nan=True, raise_on_error=False
        )
        if vel_errors:
            result["warnings"].extend(
                [ValidationWarning(e, "warning") for e in vel_errors]
            )

    # 6. Check for empty repetitions (all-zero velocity)
    if vel_col in df.columns:
        vel_data = df[vel_col].abs()
        zero_fraction = (vel_data < 0.001).sum() / len(vel_data)
        if zero_fraction > 0.9:
            result["warnings"].append(
                ValidationWarning(
                    f"Velocity is near-zero for {zero_fraction*100:.1f}% of data. "
                    "Check if data contains valid repetitions.",
                    "warning",
                )
            )

    logger.info(f"Validation complete: {len(result['errors'])} errors, "
                f"{len(result['warnings'])} warnings")

    return result


def print_validation_report(validation_result: Dict[str, Any]) -> None:
    """
    Print formatted validation report to console.

    Args:
        validation_result: Output from validate_sts_data or similar
    """
    print("\n" + "=" * 60)
    print("DATA VALIDATION REPORT")
    print("=" * 60)

    if validation_result.get("is_valid"):
        print("✅ Validation PASSED")
    else:
        print("❌ Validation FAILED")

    errors = validation_result.get("errors", [])
    if errors:
        print(f"\n❌ ERRORS ({len(errors)}):")
        for i, error in enumerate(errors, 1):
            print(f"   {i}. {error}")

    warnings = validation_result.get("warnings", [])
    if warnings:
        print(f"\n⚠️  WARNINGS ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")

    stats = validation_result.get("stats", {})
    if stats:
        print(f"\n📊 DATA STATISTICS:")
        if "time" in stats:
            ts = stats["time"]
            print(f"   Duration: {ts.get('duration_s', 0):.2f} s")
            print(f"   Samples: {ts.get('n_samples', 0)}")
            print(f"   Sampling rate: {ts.get('sampling_rate_hz', 0):.1f} Hz")
        if "bcm_z" in stats:
            bz = stats["bcm_z"]
            print(f"   BCM Z range: {bz.get('min', 0):.1f} - {bz.get('max', 0):.1f} mm")
            print(f"   BCM Z mean: {bz.get('mean', 0):.1f} ± {bz.get('std', 0):.1f} mm")

    print("=" * 60 + "\n")
