"""
Estructura de datos y cálculo de métricas por repetición.
"""

from dataclasses import dataclass
from typing import Optional, List
import numpy as np


@dataclass
class RepResult:
    """Resultados de una repetición STS (Sit-to-Stand)."""
    rep: int
    idx_conc_start: Optional[int]
    idx_peak: Optional[int]
    idx_ecc_end: Optional[int]
    t_conc_start_s: Optional[float]
    t_peak_s: Optional[float]
    t_ecc_end_s: Optional[float]
    amp_up_mm: Optional[float]
    amp_down_mm: Optional[float]
    dur_up_s: Optional[float]
    dur_down_s: Optional[float]
    dur_seated_after_s: Optional[float]
    vmax_up_m_s: Optional[float]
    vmin_down_m_s: Optional[float]
    t_to_vmax_up_s: Optional[float]
    t_to_vmin_down_s: Optional[float]
    t_pos_acc_up_s: Optional[float]
    t_neg_acc_down_s: Optional[float]
    pmax_up_W: Optional[float]
    pmin_down_W: Optional[float]
    work_up_J: Optional[float]
    work_down_J: Optional[float]
    ok_up: Optional[int]


def compute_metrics(
    rep_num: int,
    s: int,
    p: Optional[int],
    e: Optional[int],
    next_s: int,
    n: int,
    z_mm: np.ndarray,
    vel_m_s: np.ndarray,
    acc_m_s2: np.ndarray,
    power_W: np.ndarray,
    t: np.ndarray,
    dt: float,
) -> RepResult:
    """
    Calcula todas las métricas para una repetición.
    
    Args:
        rep_num: Número de repetición.
        s: Índice de inicio concéntrica.
        p: Índice de pico (Conc-Exc).
        e: Índice de fin excéntrica.
        next_s: Índice del siguiente start (o n).
        n: Longitud total de vectores.
        z_mm: Desplazamiento en mm.
        vel_m_s: Velocidad en m/s.
        acc_m_s2: Aceleración en m/s².
        power_W: Potencia en W.
        t: Temporal en s.
        dt: Intervalo temporal.
        
    Returns:
        RepResult con todas las métricas calculadas.
    """
    # Amplitudes
    amp_up = (z_mm[p] - z_mm[s]) if (p is not None) else None
    amp_down = (z_mm[p] - z_mm[e]) if (p is not None and e is not None) else None
    
    # Duraciones
    dur_up = ((p - s) * dt) if (p is not None) else None
    dur_down = ((e - p) * dt) if (p is not None and e is not None) else None
    dur_seated_after = ((next_s - (e + 1)) * dt) if (e is not None and next_s > e + 1) else None
    
    # Métricas en fase de levantarse (UP)
    vmax_up = t_to_vmax = t_pos_acc = pmax_up = work_up = None
    if p is not None:
        seg_up_v = vel_m_s[s:p + 1]
        seg_up_a = acc_m_s2[s:p + 1]
        seg_up_p = power_W[s:p + 1]
        
        if np.any(~np.isnan(seg_up_v)):
            vmax_up = float(np.nanmax(seg_up_v))
            t_to_vmax = float(np.nanargmax(seg_up_v) * dt)
        
        if np.any(~np.isnan(seg_up_a)):
            t_pos_acc = float(np.nansum(seg_up_a > 0) * dt)
        
        if np.any(~np.isnan(seg_up_p)):
            pmax_up = float(np.nanmax(seg_up_p))
        
        if np.any(np.isfinite(seg_up_p)):
            work_up = float(np.trapezoid(seg_up_p[np.isfinite(seg_up_p)], dx=dt))
    
    # Métricas en fase de sentarse (DOWN)
    vmin_down = t_to_vmin = t_neg_acc = pmin_down = work_down = None
    if p is not None and e is not None:
        seg_dn_v = vel_m_s[p:e + 1]
        seg_dn_a = acc_m_s2[p:e + 1]
        seg_dn_p = power_W[p:e + 1]
        
        if np.any(~np.isnan(seg_dn_v)):
            vmin_down = float(np.nanmin(seg_dn_v))
            t_to_vmin = float(np.nanargmin(seg_dn_v) * dt)
        
        if np.any(~np.isnan(seg_dn_a)):
            t_neg_acc = float(np.nansum(seg_dn_a < 0) * dt)
        
        if np.any(~np.isnan(seg_dn_p)):
            pmin_down = float(np.nanmin(seg_dn_p))
        
        if np.any(np.isfinite(seg_dn_p)):
            work_down = float(np.trapezoid(seg_dn_p[np.isfinite(seg_dn_p)], dx=dt))
    
    return RepResult(
        rep=rep_num,
        idx_conc_start=s,
        idx_peak=p,
        idx_ecc_end=e,
        t_conc_start_s=float(t[s]) if s is not None else None,
        t_peak_s=float(t[p]) if p is not None else None,
        t_ecc_end_s=float(t[e]) if e is not None else None,
        amp_up_mm=float(amp_up) if amp_up is not None else None,
        amp_down_mm=float(amp_down) if amp_down is not None else None,
        dur_up_s=float(dur_up) if dur_up is not None else None,
        dur_down_s=float(dur_down) if dur_down is not None else None,
        dur_seated_after_s=float(dur_seated_after) if dur_seated_after is not None else None,
        vmax_up_m_s=vmax_up,
        vmin_down_m_s=vmin_down,
        t_to_vmax_up_s=t_to_vmax,
        t_to_vmin_down_s=t_to_vmin,
        t_pos_acc_up_s=t_pos_acc,
        t_neg_acc_down_s=t_neg_acc,
        pmax_up_W=pmax_up,
        pmin_down_W=pmin_down,
        work_up_J=work_up,
        work_down_J=work_down,
        ok_up=None,
    )


def mark_ok_repetitions(reps: List[RepResult], ok_th: float = 0.85) -> None:
    """
    Marca repeticiones como OK según amplitud relativa.
    
    Args:
        reps: Lista de repeticiones.
        ok_th: Umbral relativo (por defecto 0.85).
    """
    amps_up = np.array([r.amp_up_mm for r in reps if r.amp_up_mm is not None], dtype=float)
    max_amp = float(np.nanmax(amps_up)) if amps_up.size else np.nan
    
    for r in reps:
        if r.amp_up_mm is None or np.isnan(max_amp):
            r.ok_up = None
        else:
            r.ok_up = int(r.amp_up_mm >= ok_th * max_amp)
