"""
Utilidades matemáticas y búsqueda de columnas.
"""

from typing import Optional, List
import numpy as np
import pandas as pd


def centered_slope(y: np.ndarray, dt: float, half_window: int = 3) -> np.ndarray:
    """
    Derivada mediante pendiente centrada de 2*half_window+1 muestras (por defecto 7).
    
    Args:
        y: Vector de valores.
        dt: Intervalo temporal (paso de integración).
        half_window: Semiventana (por defecto 3 => 7 puntos).
        
    Returns:
        Vector de derivadas.
    """
    y = np.asarray(y, dtype=float)
    dy = np.full_like(y, np.nan)
    w = half_window
    for i in range(w, len(y) - w):
        dy[i] = (y[i + w] - y[i - w]) / (2 * w * dt)
    return dy


def cumulative_trapezoid(y: np.ndarray, dx: float) -> np.ndarray:
    """
    Integral acumulada por trapecios sin SciPy.
    
    Args:
        y: Vector de valores (ej. potencia).
        dx: Intervalo de integración.
        
    Returns:
        Vector de integrales acumuladas.
    """
    y = np.asarray(y, dtype=float)
    out = np.full_like(y, np.nan)
    if len(y) == 0:
        return out
    out[0] = 0.0
    for i in range(1, len(y)):
        a = y[i - 1]
        b = y[i]
        if np.isnan(a) or np.isnan(b):
            out[i] = out[i - 1]
        else:
            out[i] = out[i - 1] + 0.5 * (a + b) * dx
    return out


def detect_column(
    df: pd.DataFrame,
    candidates: List[str],
    contains_all: List[str] = None
) -> Optional[str]:
    """
    Detecta una columna en DataFrame por nombre exacto o contiene keywords.
    
    Args:
        df: DataFrame a buscar.
        candidates: Lista de nombres exactos a buscar.
        contains_all: Keywords que deben estar (case-insensitive).
        
    Returns:
        Nombre de la columna encontrada, o None.
    """
    contains_all = contains_all or []
    
    # Coincidencia exacta primero
    for c in candidates:
        if c in df.columns:
            return c
    
    # Si no, por contenido
    for col in df.columns:
        cl = str(col).lower()
        if all(k.lower() in cl for k in contains_all):
            return col
    
    return None
