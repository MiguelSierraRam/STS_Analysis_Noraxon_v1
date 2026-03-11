"""
Módulos de análisis STS - Sit-to-Stand analysis tool.

Estructura:
- utils: funciones matemáticas y utilidades básicas
- detection: detección de eventos (starts, peaks, ends)
- metrics: cálculo de métricas por repetición
- plotting: generación de gráficos
- export: exportación a Excel y JSON
- advanced_metrics: PhaseComputer y métricas avanzadas (Hip_Z, EMG, CoP)
- metadata: lectura de metadatos Noraxon
- config: manejo centralizado de configuración (config.yaml)
- logger: logging profesional centralizado
"""

__version__ = "2.1.0"

from src.utils import centered_slope, cumulative_trapezoid, detect_column
from src.detection import (
    compute_vector_displacements,
    compute_windows,
    detect_conc_starts,
    detect_peaks,
    detect_ecc_ends,
    pair_repetitions,
    compute_phase_events,
    compute_acc_phases,
    RepEvents,
)
from src.metrics import RepResult, compute_metrics, mark_ok_repetitions
from src.plotting import generate_plots
from src.export import create_sheet1_variables, export_to_excel, export_to_json, export_advanced_sheet3
from src.advanced_metrics import PhaseComputer, detect_emg_columns, detect_cop_columns, trapz_manual
from src.metadata import read_metadata
from src.config import Config, load_config, get_config
from src.logger import get_logger, LoggerManager

__all__ = [
    # Utils
    'centered_slope',
    'cumulative_trapezoid',
    'detect_column',
    # Detection
    'compute_vector_displacements',
    'compute_windows',
    'detect_conc_starts',
    'detect_peaks',
    'detect_ecc_ends',
    'pair_repetitions',
    'compute_phase_events',
    'compute_acc_phases',
    'RepEvents',
    # Metrics
    'RepResult',
    'compute_metrics',
    'mark_ok_repetitions',
    # Plotting
    'generate_plots',
    # Export
    'create_sheet1_variables',
    'export_to_excel',
    'export_to_json',
    'export_advanced_sheet3',
    # Advanced metrics
    'PhaseComputer',
    'detect_emg_columns',
    'detect_cop_columns',
    'trapz_manual',
    # Metadata
    'read_metadata',
    # Config & Logging (NEW)
    'Config',
    'load_config',
    'get_config',
    'get_logger',
    'LoggerManager',
]

