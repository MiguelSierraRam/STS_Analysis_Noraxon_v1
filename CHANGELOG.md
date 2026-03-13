# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/SemVer).

## [2.1.0] - 2025-01-04

### Added
- **Performance Benchmarking Framework** (`src/benchmark.py`):
  - `PerformanceTimer` context manager for execution timing
  - `profile_memory_usage()` for memory profiling with psutil
  - `benchmark_function()` for multi-run performance testing
  - `create_benchmark_data()` for synthetic STS data generation
  - `run_performance_benchmarks()` for comprehensive system benchmarking
  - Cross-platform memory monitoring (Windows/Linux compatibility)

- **Extended Clinical Documentation** (`docs/USE_CASES.md`):
  - Parkinson's disease assessment protocols
  - Rehabilitation progress tracking
  - Fatigue studies methodology
  - EMG integration guidelines
  - Batch processing workflows
  - Clinical interpretation guidelines

- **Comprehensive Export Module Testing** (`tests/test_export.py`):
  - 14 test classes covering all export functionality
  - Excel export validation (3-sheet structure)
  - JSON export testing with special characters
  - Advanced sheet export with kinematic metrics
  - Integration testing for complete workflows
  - Error handling and edge case coverage

- **Advanced Validation Module** (`src/validation.py`):
  - Data integrity checks
  - Configuration validation
  - File format verification
  - Comprehensive error reporting

### Improved
- **Test Coverage**: Increased from 63% to 81% overall
  - `export.py`: 25% → 92% coverage
  - `validation.py`: 72% coverage with 31 tests
  - Added benchmark module testing framework
- **Documentation**: Professional README with installation, usage, and API reference
- **Code Quality**: Google-style docstrings throughout
- **Error Handling**: Robust exception management in all modules

### Fixed
- **API Compatibility**: Resolved export function parameter mismatches
- **Memory Profiling**: Fixed Windows compatibility for psutil peak memory tracking
- **Data Type Handling**: Proper NaN/None conversion in Excel exports
- **RepResult Dataclass**: Corrected constructor usage in tests

### Technical Details
- **Dependencies**: Added psutil for performance monitoring
- **Platform Support**: Windows and Linux compatibility verified
- **Testing**: 103 tests passing with comprehensive coverage
- **Performance**: Benchmarking utilities for optimization tracking

### Changed
- **Export API**: Updated `export_to_excel()` to use structured parameters
- **Test Structure**: Comprehensive test suite with proper fixtures
- **Documentation**: Modular documentation with clinical use cases

## [2.0.1] - 2024-12-15

### Fixed
- Minor bug fixes and documentation improvements

## [2.0.0] - 2024-12-10

### Added
- Initial release with core STS analysis functionality
- Basic export capabilities (Excel, JSON)
- Fundamental validation and error handling
- Initial test suite (63% coverage)

### Changed
- Complete architecture redesign for modularity
- Enhanced analysis algorithms
- Professional code structure with type hints