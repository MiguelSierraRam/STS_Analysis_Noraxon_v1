#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Herramienta de análisis STS (Sit-to-Stand) - Versión modular.

Replicar la lógica de detección de fases del Excel SMP011_Sencillo:
- Concéntrica (Levantarse): primera fila de una repetición en la que
  (a) una ventana futura de N vectores de desplazamiento es positiva,
  (b) la velocidad supera el umbral +Vth.
- Transición Conc->Exc: máximo local de BCM Z con ventana ±N.
- Fin de Excéntrica (fin de sentarse): primera/última fila del bloque negativo según la lógica del Excel:
  (a) una ventana previa de N vectores es negativa,
  (b) la velocidad es menor que -Vth,
  (c) la siguiente fila ya no cumple el bloque negativo.

Salida (3 hojas):
1) Hoja1_Variables: todas las variables por muestra.
2) Hoja2_Parametros_Grafica: parámetros usados + gráfico de detección.
3) Hoja3_Resultados_Repeticion: resultados por repetición.

Módulos:
- src.utils: funciones matemáticas
- src.detection: detección de eventos
- src.metrics: cálculo de métricas
- src.plotting: generación de gráficos
- src.export: exportación Excel/JSON
"""

import argparse
import os
from typing import Optional, List, Tuple

import numpy as np
import pandas as pd

# Importar módulos
from src.utils import centered_slope, cumulative_trapezoid, detect_column
from src.detection import (
    compute_vector_displacements,
    compute_windows,
    detect_conc_starts,
    detect_peaks,
    detect_ecc_ends,
    pair_repetitions,
    compute_phase_events,
)
from src.metrics import RepResult, compute_metrics, mark_ok_repetitions
from src.plotting import generate_plots
from src.export import create_sheet1_variables, export_to_excel, export_to_json


# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def run_tool(
    file_path: str,
    sheet_name: str = 'Reducido',
    time_col: str = 'time',
    disp_col: Optional[str] = None,
    mass_kg: Optional[float] = None,
    window: int = 30,
    n_positive: int = 30,
    vel_th_m_s: float = 0.1,
    ok_th: float = 0.85,
    half_window_derivative: int = 3,
    out_prefix: Optional[str] = None,
    make_plot: bool = True,
    per_rep_plots: bool = True,
) -> Tuple[str, Optional[str], str]:
    """
    Ejecuta el análisis STS completo.
    
    Args:
        file_path: Ruta del archivo Excel.
        sheet_name: Hoja a analizar.
        time_col: Columna de tiempo.
        disp_col: Columna de desplazamiento (autodetecta si es None).
        mass_kg: Masa corporal para calcular potencia.
        window: Tamaño de ventana de detección.
        n_positive: N de celdas positivas/negativas para eventos.
        vel_th_m_s: Umbral de velocidad.
        ok_th: Umbral relativo de amplitud.
        half_window_derivative: Semiventana para derivadas.
        out_prefix: Prefijo de salida.
        make_plot: Generar gráfico general.
        per_rep_plots: Generar gráficos por repetición.
        
    Returns:
        (excel_path, plot_path, json_path)
    """
    # --------
    # 1. LEER DATOS
    # --------
    df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
    if time_col not in df.columns:
        raise ValueError(f'No se encontró la columna de tiempo "{time_col}" en la hoja {sheet_name}.')
    
    t = df[time_col].astype(float).to_numpy()
    if len(t) < 3:
        raise ValueError('No hay suficientes muestras para analizar.')
    
    dt = float(pd.Series(np.diff(t)).median())
    n = len(t)
    
    # Detectar columna de desplazamiento BCM Z
    if disp_col is None:
        disp_col = detect_column(
            df,
            candidates=['Disp_BCM_Z', 'BCM_Z', 'Body center of mass-z (mm)'],
            contains_all=['body center of mass', 'z', '(mm)']
        )
        if disp_col is None:
            for c in df.columns:
                cl = str(c).lower()
                if ('body center of mass' in cl) and ('z' in cl) and ('mm' in cl):
                    disp_col = c
                    break
    
    if disp_col is None:
        raise ValueError('No se encontró la columna de desplazamiento BCM en eje Z.')
    
    z_mm = df[disp_col].astype(float).to_numpy()
    z_m = z_mm / 1000.0
    
    # --------
    # 2. CALCULAR VARIABLES DERIVADAS
    # --------
    vel_m_s = centered_slope(z_m, dt, half_window_derivative)
    acc_m_s2 = centered_slope(vel_m_s, dt, half_window_derivative)
    
    force_est_N = np.full_like(vel_m_s, np.nan)
    if mass_kg is not None:
        force_est_N[:] = mass_kg * 9.80665
        power_W = force_est_N * vel_m_s
    else:
        power_W = np.full_like(vel_m_s, np.nan)
    
    work_cum_J = cumulative_trapezoid(power_W, dt)
    
    # --------
    # 3. DETECCIÓN DE EVENTOS
    # --------
    vector_disp = compute_vector_displacements(z_mm)
    future_sum, previous_sum = compute_windows(vector_disp, window)
    
    vel_conc_flag = np.where(vel_m_s > vel_th_m_s, 1, np.nan)
    vel_ecc_flag = np.where(vel_m_s < -vel_th_m_s, 1, np.nan)
    
    conc_start = detect_conc_starts(future_sum, vel_conc_flag, n_positive)
    conc_exc = detect_peaks(z_mm, window)
    ecc_end = detect_ecc_ends(previous_sum, vel_ecc_flag, n_positive)
    
    conc_event, conc_graph, ecc_event, ecc_graph, any_phase_event = compute_phase_events(
        conc_start, conc_exc, ecc_end
    )
    
    # --------
    # 4. EMPAREJAR REPETICIONES
    # --------
    idx_starts = list(np.where(conc_start == 10000)[0])
    idx_peaks = list(np.where(conc_exc == 10000)[0])
    idx_ends = list(np.where(ecc_end == 10000)[0])
    
    reps_data, phase_id, phase_label = pair_repetitions(idx_starts, idx_peaks, idx_ends, n)
    
    # --------
    # 5. CALCULAR MÉTRICAS POR REPETICIÓN
    # --------
    reps: List[RepResult] = []
    for rep_num, (s, p, e) in enumerate(reps_data, start=1):
        next_s = idx_starts[rep_num] if rep_num < len(idx_starts) else n - 1
        rep = compute_metrics(
            rep_num, s, p, e, next_s, n,
            z_mm, vel_m_s, acc_m_s2, power_W,
            t, dt
        )
        reps.append(rep)
    
    mark_ok_repetitions(reps, ok_th)
    
    # Crear DataFrame de resultados
    reps_df = pd.DataFrame([r.__dict__ for r in reps])
    
    # --------
    # 6. CREAR DATAFRAME COMPLETO (HOJA 1)
    # --------
    rep_id = np.full(n, np.nan)
    for rr in reps:
        s, p, e = rr.idx_conc_start, rr.idx_peak, rr.idx_ecc_end
        if s is not None and p is not None:
            rep_id[s:p + 1] = rr.rep
        if p is not None and e is not None:
            rep_id[p:e + 1] = rr.rep
        if e is not None:
            next_starts = [x for x in idx_starts if x > e]
            ns = next_starts[0] if next_starts else n
            rep_id[e + 1:ns] = rr.rep
    
    sheet1 = create_sheet1_variables(
        df, z_mm, vel_m_s, acc_m_s2, force_est_N, power_W, work_cum_J,
        vector_disp, future_sum, previous_sum,
        vel_conc_flag, vel_ecc_flag,
        conc_start, conc_exc, ecc_end,
        conc_event, conc_graph, ecc_event, ecc_graph, any_phase_event,
        phase_id, phase_label, rep_id
    )
    
    # --------
    # 7. GENERAR GRÁFICOS
    # --------
    out_prefix = out_prefix or os.path.splitext(file_path)[0] + '_analysis_exact'
    plot_path, rep_dir = generate_plots(
        t, z_mm, vel_m_s,
        idx_starts, idx_peaks, idx_ends,
        reps, out_prefix,
        make_plot, per_rep_plots
    )
    
    # --------
    # 8. EXPORTAR DATOS
    # --------
    # Parámetros
    params = {
        'input_file': file_path,
        'sheet_name': sheet_name,
        'time_col': time_col,
        'disp_col': disp_col,
        'dt_s': dt,
        'window': window,
        'n_positive': n_positive,
        'vel_th_m_s': vel_th_m_s,
        'ok_th': ok_th,
        'mass_kg': mass_kg,
        'half_window_derivative': half_window_derivative,
        'n_conc_start': len(idx_starts),
        'n_peaks': len(idx_peaks),
        'n_ecc_end': len(idx_ends),
        'n_reps': len(reps),
    }
    
    # Excel
    out_excel = out_prefix + '.xlsx'
    export_to_excel(sheet1, reps_df, params, plot_path, out_excel)
    
    # JSON
    out_json = out_prefix + '_params.json'
    export_to_json(params, out_json)
    
    return out_excel, plot_path, out_json


def main():
    parser = argparse.ArgumentParser(description='Análisis STS replicando la lógica de detección de fases del Excel SMP011_Sencillo.')
    parser.add_argument('--input', required=True, help='Ruta del archivo .xlsx de entrada')
    parser.add_argument('--sheet', default='Reducido', help='Hoja a procesar (por defecto: Reducido)')
    parser.add_argument('--time-col', default='time', help='Nombre de la columna de tiempo (por defecto: time)')
    parser.add_argument('--disp-col', default=None, help='Nombre exacto de la columna de desplazamiento BCM Z; si no, se autodetecta')
    parser.add_argument('--mass-kg', type=float, default=None, help='Masa corporal (kg) para potencia/trabajo con P≈m*g*v')
    parser.add_argument('--window', type=int, default=30, help='Ventana de detección (por defecto: 30)')
    parser.add_argument('--n-positive', type=int, default=30, help='N celdas positivas/negativas requeridas (por defecto: 30)')
    parser.add_argument('--vel-th', type=float, default=0.1, help='Umbral fijo de velocidad en m/s (por defecto: 0.1)')
    parser.add_argument('--ok-th', type=float, default=0.85, help='Umbral relativo de amplitud para marcar OK (por defecto: 0.85)')
    parser.add_argument('--half-window-derivative', type=int, default=3, help='Semiventana de la pendiente centrada para derivadas (3 => 7 puntos)')
    parser.add_argument('--no-plot', action='store_true', help='No generar gráfico general')
    parser.add_argument('--no-per-rep', action='store_true', help='No generar gráficos por repetición')
    parser.add_argument('--out-prefix', default=None, help='Prefijo de salida (sin extensión)')
    args = parser.parse_args()

    excel, plot, params = run_tool(
        file_path=args.input,
        sheet_name=args.sheet,
        time_col=args.time_col,
        disp_col=args.disp_col,
        mass_kg=args.mass_kg,
        window=args.window,
        n_positive=args.n_positive,
        vel_th_m_s=args.vel_th,
        ok_th=args.ok_th,
        half_window_derivative=args.half_window_derivative,
        out_prefix=args.out_prefix,
        make_plot=(not args.no_plot),
        per_rep_plots=(not args.no_per_rep),
    )
    print('\nLISTO')
    print('Excel:', excel)
    print('Gráfico:', plot)
    print('Parámetros:', params)


if __name__ == '__main__':
    main()
