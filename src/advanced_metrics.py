"""
Cálculo avanzado de métricas por fase y computador de estadísticos.
Incluye soporte para:
- Hip Z (desplazamiento y velocidad)
- EMG (electromiografía)
- CoP SD (estabilidad de Centro de Presión)
"""

from typing import Optional, Tuple, Dict
import numpy as np
import pandas as pd


def trapz_manual(y: np.ndarray, dx: float) -> float:
    """Integración trapezoidal manual sin necesidad de np.trapz."""
    y = np.asarray(y, dtype=float)
    if y.size < 2:
        return 0.0
    s = 0.0
    for i in range(1, y.size):
        a = y[i - 1]
        b = y[i]
        if np.isfinite(a) and np.isfinite(b):
            s += 0.5 * (a + b) * dx
    return float(s)


class PhaseComputer:
    """
    Computador genérico de estadísticos por fase temporal.
    
    Permite calcular medias, máximos, mínimos, rangos,
    desviaciones estándar y potencia/trabajo sobre periodos
    arbitrarios definidos por tiempo inicial y final.
    """
    
    def __init__(self, df: pd.DataFrame, time_col: str):
        """
        Inicializa el computador de fases.
        
        Args:
            df: DataFrame con todas las series de tiempo.
            time_col: Nombre de la columna de tiempo (segundos).
        """
        self.df = df
        self.time = df[time_col].astype(float).to_numpy()
        self.cols = df.columns
        self.dt = float(pd.Series(np.diff(self.time)).median())
    
    def _slice(self, t0: float, t1: float) -> slice:
        """
        Convierte tiempos a índices de slice.
        
        Args:
            t0: Tiempo inicial.
            t1: Tiempo final.
            
        Returns:
            Slice para indexar arrays.
        """
        i0 = int(np.argmin(np.abs(self.time - t0)))
        i1 = int(np.argmin(np.abs(self.time - t1)))
        if i1 < i0:
            i0, i1 = i1, i0
        return slice(i0, i1 + 1)
    
    def range_mm_to_m(self, col: str, t0: float, t1: float) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Calcula rango de desplazamiento en columna (mm → m).
        
        Args:
            col: Nombre de columna en mm.
            t0: Tiempo inicial.
            t1: Tiempo final.
            
        Returns:
            (máximo_m, mínimo_m, rango_m)
        """
        if col not in self.cols:
            return (None, None, None)
        sl = self._slice(t0, t1)
        vals = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        if not np.any(np.isfinite(vals)):
            return (None, None, None)
        mx = float(np.nanmax(vals)) / 1000.0
        mn = float(np.nanmin(vals)) / 1000.0
        return (mx, mn, mx - mn)
    
    def stats(
        self,
        col: Optional[str],
        arr_fallback: Optional[np.ndarray],
        t0: float,
        t1: float
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Calcula media, máximo y mínimo sobre un período.
        
        Args:
            col: Nombre de columna (o None para usar fallback).
            arr_fallback: Array alternativo si col no existe.
            t0: Tiempo inicial.
            t1: Tiempo final.
            
        Returns:
            (media, máximo, mínimo)
        """
        sl = self._slice(t0, t1)
        if col and (col in self.cols):
            vals = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        elif arr_fallback is not None:
            vals = arr_fallback[sl]
        else:
            return (None, None, None)
        
        if not np.any(np.isfinite(vals)):
            return (None, None, None)
        
        return (
            float(np.nanmean(vals)),
            float(np.nanmax(vals)),
            float(np.nanmin(vals))
        )
    
    def power_work(
        self,
        power_col: Optional[str],
        vel_col: Optional[str],
        mass_kg: Optional[float],
        t0: float,
        t1: float
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Calcula potencia (media, máxima) y trabajo sobre un período.
        
        Si existe columna de potencia nativa, la utiliza.
        Si no, aproxima con P ≈ m*g*v (para BCM Z).
        
        Args:
            power_col: Columna de potencia nativa (opcional).
            vel_col: Columna de velocidad.
            mass_kg: Masa corporal para aproximación.
            t0: Tiempo inicial.
            t1: Tiempo final.
            
        Returns:
            (potencia_media_W, potencia_máxima_W, trabajo_J)
        """
        sl = self._slice(t0, t1)
        if power_col and (power_col in self.cols):
            p = pd.to_numeric(self.df[power_col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        elif mass_kg is not None and vel_col and (vel_col in self.cols):
            g = 9.80665
            v = pd.to_numeric(self.df[vel_col].iloc[sl], errors='coerce').to_numpy(dtype=float)
            p = mass_kg * g * v
        else:
            return (None, None, None)
        
        if not np.any(np.isfinite(p)):
            return (None, None, None)
        
        mean_p = float(np.nanmean(p))
        max_p = float(np.nanmax(p))
        work = trapz_manual(p[np.isfinite(p)], self.dt)
        
        return (mean_p, max_p, work)
    
    def mean(self, col: str, t0: float, t1: float) -> Optional[float]:
        """
        Calcula media de una columna en un período.
        
        Args:
            col: Nombre de columna.
            t0: Tiempo inicial.
            t1: Tiempo final.
            
        Returns:
            Media o None.
        """
        if col not in self.cols:
            return None
        sl = self._slice(t0, t1)
        vals = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        if not np.any(np.isfinite(vals)):
            return None
        return float(np.nanmean(vals))
    
    def stdev(self, col: str, t0: float, t1: float) -> Optional[float]:
        """
        Calcula desviación estándar (STDEV.S) sobre un período.
        
        Args:
            col: Nombre de columna.
            t0: Tiempo inicial.
            t1: Tiempo final.
            
        Returns:
            Desv. estándar o None.
        """
        if col not in self.cols:
            return None
        sl = self._slice(t0, t1)
        vals = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        vals = vals[np.isfinite(vals)]
        if vals.size < 2:
            return None
        return float(np.nanstd(vals, ddof=1))
    
    def max_val(self, col: str, t0: float, t1: float) -> Optional[float]:
        """Máximo de una columna en un período."""
        if col not in self.cols:
            return None
        sl = self._slice(t0, t1)
        vals = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        if not np.any(np.isfinite(vals)):
            return None
        return float(np.nanmax(vals))
    
    def min_val(self, col: str, t0: float, t1: float) -> Optional[float]:
        """Mínimo de una columna en un período."""
        if col not in self.cols:
            return None
        sl = self._slice(t0, t1)
        vals = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        if not np.any(np.isfinite(vals)):
            return None
        return float(np.nanmin(vals))


def detect_column_variants(df: pd.DataFrame, keywords: list) -> Optional[str]:
    """
    Detecta columna por múltiples keywords (case-insensitive).
    
    Args:
        df: DataFrame.
        keywords: Lista de keywords a buscar.
        
    Returns:
        Nombre de columna o None.
    """
    for col in df.columns:
        col_lower = str(col).lower()
        if all(kw.lower() in col_lower for kw in keywords):
            return col
    return None


def detect_emg_columns(df: pd.DataFrame) -> list:
    """
    Detecta columnas de EMG estándar en formato Noraxon.
    
    Returns:
        Lista de columnas EMG presentes en el DataFrame.
    """
    emg_patterns = [
        'RT TIB.ANT. (%)',
        'RT VLO (%)',
        'RT RECTUS FEM. (%)',
        'RT MED. GASTRO (%)',
        'RT SEMITEND. (%)',
        'RT GLUT. MAX. (%)',
        'RT LUMBAR ES (%)'
    ]
    return [col for col in emg_patterns if col in df.columns]


def detect_cop_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Detecta columnas de Centro de Presión (CoP) en el DataFrame.
    
    Busca tanto columnas pre-calculadas (SD) como crudas.
    
    Returns:
        Dict con claves como 'SD_AP', 'SD_ML', 'SD_Result', etc.
    """
    result = {}
    
    # Pre-calculadas (SD)
    for key in ['CoP_SD Displ_AP', 'CoP_SD Displ_ML', 'CoP_SD Displ_Result']:
        result[key] = key if key in df.columns else None
    
    # Crudas (para calcular SD)
    raw_patterns = {
        'AP': ['CoP_Disp_X', 'CoP_AP', 'CoP_X'],
        'ML': ['CoP_Disp_Y', 'CoP_ML', 'CoP_Y'],
        'Result': ['CoP_Disp_R', 'CoP_Result', 'CoP_R']
    }
    
    for direction, candidates in raw_patterns.items():
        for cand in candidates:
            if cand in df.columns:
                result[f'raw_{direction}'] = cand
                break
    
    return result
