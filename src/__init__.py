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
"""

__version__ = "2.0.0"

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

__all__ = [
    'centered_slope',
    'cumulative_trapezoid',
    'detect_column',
    'compute_vector_displacements',
    'compute_windows',
    'detect_conc_starts',
    'detect_peaks',
    'detect_ecc_ends',
    'pair_repetitions',
    'compute_phase_events',
    'compute_acc_phases',
    'RepEvents',
    'RepResult',
    'compute_metrics',
    'mark_ok_repetitions',
    'generate_plots',
    'create_sheet1_variables',
    'export_to_excel',
    'export_to_json',
    'export_advanced_sheet3',
    'PhaseComputer',
    'detect_emg_columns',
    'detect_cop_columns',
    'trapz_manual',
    'read_metadata',
]

