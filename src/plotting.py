"""
Generación de gráficos: general y por repetición.
"""

from typing import List
import os
import numpy as np
import matplotlib.pyplot as plt
from src.metrics import RepResult


def plot_general_segmentation(
    t: np.ndarray,
    z_mm: np.ndarray,
    vel_m_s: np.ndarray,
    idx_starts: List[int],
    idx_peaks: List[int],
    idx_ends: List[int],
    reps: List[RepResult],
    out_path: str
) -> None:
    """
    Genera gráfico general de detección de fases.
    
    Args:
        t: Tiempo en s.
        z_mm: Desplazamiento en mm.
        vel_m_s: Velocidad en m/s.
        idx_starts: Índices de starts.
        idx_peaks: Índices de picos.
        idx_ends: Índices de ends.
        reps: Lista de repeticiones.
        out_path: Ruta de salida.
    """
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    ax1.plot(t, z_mm, color='tab:blue', label='BCM Z (mm)')
    ax2.plot(t, vel_m_s, color='tab:orange', alpha=0.7, label='Vel BCM Z (m/s)')
    
    # Sombreado por fases
    for rr in reps:
        if rr.idx_conc_start is not None and rr.idx_peak is not None:
            ax1.axvspan(t[rr.idx_conc_start], t[rr.idx_peak], color='green', alpha=0.10)
        if rr.idx_peak is not None and rr.idx_ecc_end is not None:
            ax1.axvspan(t[rr.idx_peak], t[rr.idx_ecc_end], color='red', alpha=0.08)
        if rr.idx_ecc_end is not None:
            next_starts = [x for x in idx_starts if x > rr.idx_ecc_end]
            ns = next_starts[0] if next_starts else len(t) - 1
            if ns > rr.idx_ecc_end:
                ax1.axvspan(t[rr.idx_ecc_end], t[ns], color='gray', alpha=0.06)
    
    # Eventos
    if idx_starts:
        ax1.scatter(t[idx_starts], z_mm[idx_starts], color='green', marker='^', label='Conc Start')
    if idx_peaks:
        ax1.scatter(t[idx_peaks], z_mm[idx_peaks], color='purple', marker='o', label='Conc-Exc')
    if idx_ends:
        ax1.scatter(t[idx_ends], z_mm[idx_ends], color='red', marker='v', label='Ecc End')
    
    ax1.set_xlabel('Tiempo (s)')
    ax1.set_ylabel('Desplazamiento BCM Z (mm)')
    ax2.set_ylabel('Velocidad BCM Z (m/s)')
    ax1.set_title('Detección de fases STS (lógica exacta del Excel)')
    
    # Leyenda combinada
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc='upper left')
    
    plt.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_per_repetition(
    rep: RepResult,
    t: np.ndarray,
    z_mm: np.ndarray,
    vel_m_s: np.ndarray,
    idx_starts: List[int],
    dt: float,
    out_dir: str
) -> None:
    """
    Genera gráfico para una repetición individual.
    
    Args:
        rep: Datos de la repetición.
        t: Tiempo en s.
        z_mm: Desplazamiento en mm.
        vel_m_s: Velocidad en m/s.
        idx_starts: Índices de todos los starts.
        dt: Intervalo temporal.
        out_dir: Directorio de salida.
    """
    n = len(t)
    s = rep.idx_conc_start if rep.idx_conc_start is not None else 0
    e = rep.idx_ecc_end if rep.idx_ecc_end is not None else min(n - 1, s + int(2 / dt))
    next_starts = [x for x in idx_starts if x > e]
    ns = next_starts[0] if next_starts else min(n - 1, e + int(1 / dt))
    lo = max(0, s - int(0.5 / dt))
    hi = min(n - 1, ns + int(0.5 / dt))
    
    fig, ax = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax[0].plot(t[lo:hi+1], z_mm[lo:hi+1], 'b-', label='BCM Z (mm)')
    ax[1].plot(t[lo:hi+1], vel_m_s[lo:hi+1], color='orange', label='Vel BCM Z (m/s)')
    
    if rep.idx_peak is not None:
        ax[0].axvspan(t[s], t[rep.idx_peak], color='green', alpha=0.10, label='Levantarse')
    if rep.idx_peak is not None and rep.idx_ecc_end is not None:
        ax[0].axvspan(t[rep.idx_peak], t[rep.idx_ecc_end], color='red', alpha=0.08, label='Sentarse')
    if rep.idx_ecc_end is not None and ns > rep.idx_ecc_end:
        ax[0].axvspan(t[rep.idx_ecc_end], t[ns], color='gray', alpha=0.06, label='Sentado')
    
    ax[0].set_ylabel('z (mm)')
    ax[1].set_ylabel('v (m/s)')
    ax[1].set_xlabel('Tiempo (s)')
    ax[0].legend(loc='best')
    ax[0].set_title(f'Repetición {rep.rep}: Levantarse / Sentarse / Sentado')
    
    plt.tight_layout()
    fig.savefig(os.path.join(out_dir, f'rep_{rep.rep:02d}.png'), dpi=130)
    plt.close(fig)


def generate_plots(
    t: np.ndarray,
    z_mm: np.ndarray,
    vel_m_s: np.ndarray,
    idx_starts: List[int],
    idx_peaks: List[int],
    idx_ends: List[int],
    reps: List[RepResult],
    out_prefix: str,
    make_plot: bool = True,
    per_rep_plots: bool = True
) -> tuple:
    """
    Genera todos los gráficos.
    
    Args:
        t: Tiempo en s.
        z_mm: Desplazamiento en mm.
        vel_m_s: Velocidad en m/s.
        idx_starts: Índices de starts.
        idx_peaks: Índices de picos.
        idx_ends: Índices de ends.
        reps: Lista de repeticiones.
        out_prefix: Prefijo de salida.
        make_plot: Generar gráfico general.
        per_rep_plots: Generar gráficos por repetición.
        
    Returns:
        (plot_path, rep_dir)
    """
    dt = float(np.median(np.diff(t)))
    plot_path = None
    rep_dir = None
    
    if make_plot:
        plot_path = out_prefix + '_segmentation.png'
        plot_general_segmentation(
            t, z_mm, vel_m_s,
            idx_starts, idx_peaks, idx_ends,
            reps, plot_path
        )
    
    if per_rep_plots and make_plot and reps:
        rep_dir = out_prefix + '_perrep'
        os.makedirs(rep_dir, exist_ok=True)
        for rep in reps:
            plot_per_repetition(
                rep, t, z_mm, vel_m_s,
                idx_starts, dt, rep_dir
            )
    
    return plot_path, rep_dir
