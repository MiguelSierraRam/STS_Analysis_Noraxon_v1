"""
Funciones de análisis avanzadas: cálculo de métricas por fase, HIP Z, EMG y CoP.
"""
from typing import List, Dict, Optional
import numpy as np
import pandas as pd
from .utils import centered_slope


def trapz_manual(y: np.ndarray, dx: float) -> float:
    """Integración por trapecios sin depender de NumPy >=2."""
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
    """Encapsula utilidades para extraer métricas de una fase temporal.

    Los métodos trabajan sobre un DataFrame y un vector de tiempos.
    """
    def __init__(self, df: pd.DataFrame, time_col: str) -> None:
        self.df: pd.DataFrame = df
        self.time: np.ndarray[tuple[int], np.dtype[np.floating[np.Any]]] = df[time_col].astype(float).to_numpy()
        self.cols: pd.Index[str] = df.columns
        self.dt = float(pd.Series(np.diff(self.time)).median())

    def _slice(self, t0: float, t1: float) -> slice:
        i0 = int(np.argmin(np.abs(self.time - t0)))
        i1 = int(np.argmin(np.abs(self.time - t1)))
        if i1 < i0:
            i0, i1 = i1, i0
        return slice(i0, i1 + 1)

    def range_mm_to_m(self, col: str, t0: float, t1: float) -> tuple[None, None, None] | tuple[float, float, float]:
        if col not in self.cols:
            return (None, None, None)
        sl: slice[Any, Any, Any] = self._slice(t0, t1)
        vals: np.ndarray[tuple[int], np.dtype[np.Any]] = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        if not np.any(np.isfinite(vals)):
            return (None, None, None)
        mx: float = float(np.nanmax(vals)) / 1000.0
        mn: float = float(np.nanmin(vals)) / 1000.0
        return (mx, mn, mx - mn)

    def stats(self, col: Optional[str], arr_fallback: Optional[np.ndarray], t0: float, t1: float) -> tuple[None, None, None] | tuple[float, float, float]:
        sl: slice[Any, Any, Any] = self._slice(t0, t1)
        if col and (col in self.cols):
            vals: np.ndarray[tuple[int], np.dtype[np.Any]] = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        elif arr_fallback is not None:
            vals: np.ndarray[tuple[Any, ...], np.dtype[np.Any]] = arr_fallback[sl]
        else:
            return (None, None, None)
        if not np.any(np.isfinite(vals)):
            return (None, None, None)
        return (float(np.nanmean(vals)), float(np.nanmax(vals)), float(np.nanmin(vals)))

    def power_work(self, power_col: Optional[str], vel_col: Optional[str], mass_kg: Optional[float], t0: float, t1: float) -> tuple[None, None, None] | tuple[float, float, float]:
        sl: slice[Any, Any, Any] = self._slice(t0, t1)
        if power_col and (power_col in self.cols):
            p: np.ndarray[tuple[int], np.dtype[np.Any]] = pd.to_numeric(self.df[power_col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        elif mass_kg is not None and vel_col and (vel_col in self.cols):
            g = 9.80665
            v: np.ndarray[tuple[int], np.dtype[np.Any]] = pd.to_numeric(self.df[vel_col].iloc[sl], errors='coerce').to_numpy(dtype=float)
            p = mass_kg * g * v
        else:
            return (None, None, None)
        if not np.any(np.isfinite(p)):
            return (None, None, None)
        mean_p = float(np.nanmean(p))
        max_p = float(np.nanmax(p))
        work: float = trapz_manual(p[np.isfinite(p)], self.dt)
        return (mean_p, max_p, work)

    def mean(self, col: str, t0: float, t1: float) -> None | float:
        if col not in self.cols:
            return None
        sl: slice[Any, Any, Any] = self._slice(t0, t1)
        vals: np.ndarray[tuple[int], np.dtype[np.Any]] = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        if not np.any(np.isfinite(vals)):
            return None
        return float(np.nanmean(vals))

    def stdev(self, col: str, t0: float, t1: float) -> None | float:
        if col not in self.cols:
            return None
        sl: slice[Any, Any, Any] = self._slice(t0, t1)
        vals: np.ndarray[tuple[int], np.dtype[np.Any]] = pd.to_numeric(self.df[col].iloc[sl], errors='coerce').to_numpy(dtype=float)
        vals: np.ndarray[tuple[Any, ...], np.dtype[np.Any]] = vals[np.isfinite(vals)]
        if vals.size < 2:
            return None
        return float(np.nanstd(vals, ddof=1))


def generate_phase_dataframe(
    df: pd.DataFrame,
    time_col: str,
    rep_events: List[Dict],
    marker_to_time: Dict[int, float],
    z_mm: np.ndarray,
    vel_m_s: np.ndarray,
    acc_m_s2: np.ndarray,
    power_W: np.ndarray,
    mass_kg: Optional[float],
    dt: float,
    half_window_derivative: int,
    close_last_seated_at_end: bool = True,
) -> pd.DataFrame:
    """
    Construye el DataFrame de Hoja3 con todas las métricas (BCM, HIP, EMG, CoP).
    """
    pc = PhaseComputer(df, time_col)

    # detectar columnas útiles
    disp_bcmz: str | None = next((c for c in df.columns if 'body center of mass-z' in str(c).lower()), None)
    disp_hipz: str | None = next((c for c in df.columns if 'hip rt-z' in str(c).lower()), None)
    vel_hipz_native: str | None = next((c for c in df.columns if 'veloc_hip_z' in str(c).lower() or 'vel hip z' in str(c).lower()), None)
    power_hipz_native: str | None = next((c for c in df.columns if 'mean power_hip_z' in str(c).lower()), None)
    work_hipz_native: str | None = next((c for c in df.columns if 'mech work_hip_z' in str(c).lower()), None)

    emg_cols: List[str] = [
        'RT TIB.ANT. (%)','RT VLO (%)','RT RECTUS FEM. (%)',
        'RT MED. GASTRO (%)','RT SEMITEND. (%)','RT GLUT. MAX. (%)','RT LUMBAR ES (%)'
    ]
    emg_cols: List[str] = [c for c in emg_cols if c in df.columns]

    raw_cop_candidates: Dict[str, List[str]] = {
        'AP': ['CoP_Disp_X','CoP_AP','CoP_X'],
        'ML': ['CoP_Disp_Y','CoP_ML','CoP_Y'],
        'Result': ['CoP_Disp_R','CoP_Result','CoP_R']
    }

    rows: List[Dict[str, object]] = []
    for ev in rep_events:
        for phase in ('Concéntrica', 'Excéntrica', 'Sentado'):
            m1 = (ev.rep - 1) * 3 + 1
            m2 = m1 + 1
            m3 = m1 + 2
            if phase == 'Concéntrica':
                sm, em = m1, m2
            elif phase == 'Excéntrica':
                sm, em = m2, m3
            else:
                sm, em = m3, m3 + 1
            if sm not in marker_to_time:
                continue
            t0: float = marker_to_time[sm]
            t1: float = marker_to_time[em] if em in marker_to_time else (float(pc.time[-1]) if close_last_seated_at_end else t0)
            tf: float = max(0.0, t1 - t0)
            row = {
                'Repeticion': ev.rep, 'Fase': phase,
                'Inicio_Tiempo': t0, 'Final_Tiempo': t1, 'Tiempo fase': tf,
            }
            # BCM Z
            mx, mn, rg = pc.range_mm_to_m(disp_bcmz, t0, t1) if disp_bcmz else (None,None,None)
            row['BCM_Z_Max (m)'] = mx
            row['BCM_Z_Min (m)'] = mn
            row['BCM_Z_Range (m)'] = rg
            mV, MV, mVn = pc.stats(None, vel_m_s, t0, t1)
            row['BCM_Z_Vel_Mean (m/s)'] = mV
            row['BCM_Z_Vel_Max (m/s)'] = MV
            row['BCM_Z_Vel_Min (m/s)'] = mVn
            MP, XP, WK = pc.power_work(None, None, mass_kg, t0, t1)
            # recompute if necessary as v3.1 did using derived vel
            if mass_kg is not None:
                sl: slice[Any, Any, Any] = pc._slice(t0, t1)
                P_series = mass_kg * 9.80665 * vel_m_s[sl]
                if np.any(np.isfinite(P_series)):
                    MP = float(np.nanmean(P_series))
                    XP = float(np.nanmax(P_series))
                    WK: float = trapz_manual(P_series[np.isfinite(P_series)], dt)
            row['BCM_Z_Power_Mean (W)'] = MP
            row['BCM_Z_Power_Max (W)'] = XP
            row['BCM_Z_Work (J)'] = WK

            # HIP Z
            if disp_hipz:
                hmx, hmn, hrg = pc.range_mm_to_m(disp_hipz, t0, t1)
                row['HIP_Z_Max (m)'] = hmx
                row['HIP_Z_Min (m)'] = hmn
                row['HIP_Z_Range (m)'] = hrg
            if vel_hipz_native and vel_hipz_native in df.columns:
                hVm, hVx, hVn = pc.stats(vel_hipz_native, None, t0, t1)
            elif disp_hipz:
                hip_mm: np.ndarray[tuple[int], np.dtype[np.Any]] = pd.to_numeric(df[disp_hipz], errors='coerce').to_numpy(dtype=float)
                hip_m = hip_mm/1000.0
                hip_vel = centered_slope(hip_m, dt, half_window_derivative)
                hVm, hVx, hVn = pc.stats(None, hip_vel, t0, t1)
            else:
                hVm = hVx = hVn = None
            row['HIP_Z_Vel_Mean (m/s)'] = hVm
            row['HIP_Z_Vel_Max (m/s)'] = hVx
            row['HIP_Z_Vel_Min (m/s)'] = hVn
            if power_hipz_native and power_hipz_native in df.columns:
                hPM: None | float = pc.mean(power_hipz_native, t0, t1)
                hPX: None | float = pc.stats(power_hipz_native, None, t0, t1)[1]
                row['HIP_Z_Power_Mean (W)'] = hPM
                row['HIP_Z_Power_Max (W)'] = hPX
            if work_hipz_native and work_hipz_native in df.columns:
                sl: slice[Any, Any, Any] = pc._slice(t0, t1)
                series: np.ndarray[tuple[int], np.dtype[np.Any]] = pd.to_numeric(df[work_hipz_native].iloc[sl], errors='coerce').to_numpy(dtype=float)
                series: np.ndarray[tuple[Any, ...], np.dtype[np.Any]] = series[np.isfinite(series)]
                row['HIP_Z_Work (J)'] = float(series[-1]-series[0]) if series.size>=2 else (float(series[0]) if series.size==1 else None)

            # EMG means
            for emg in emg_cols:
                row[f'EMG Mean {emg}'] = pc.mean(emg, t0, t1)

            # CoP SD
            if 'CoP_SD Displ_AP' in df.columns:
                row['CoP_SD_AP'] = pc.mean('CoP_SD Displ_AP', t0, t1)
            else:
                for cand in raw_cop_candidates['AP']:
                    if cand in df.columns:
                        row['CoP_SD_AP'] = pc.stdev(cand, t0, t1)
                        break
            if 'CoP_SD Displ_ML' in df.columns:
                row['CoP_SD_ML'] = pc.mean('CoP_SD Displ_ML', t0, t1)
            else:
                for cand in raw_cop_candidates['ML']:
                    if cand in df.columns:
                        row['CoP_SD_ML'] = pc.stdev(cand, t0, t1)
                        break
            if 'CoP_SD Displ_Result' in df.columns:
                row['CoP_SD_Result'] = pc.mean('CoP_SD Displ_Result', t0, t1)
            else:
                for cand in raw_cop_candidates['Result']:
                    if cand in df.columns:
                        row['CoP_SD_Result'] = pc.stdev(cand, t0, t1)
                        break

            rows.append(row)

    return pd.DataFrame(rows)
