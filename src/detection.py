"""
Detección de eventos (starts, peaks, ends) y lógica de fases.
"""

from typing import List, Tuple
import numpy as np


def compute_vector_displacements(z_mm: np.ndarray) -> np.ndarray:
    """
    Computa vector de desplazamientos: signo(dz/dt).
    Primera fila es 0.
    
    Args:
        z_mm: Desplazamiento en mm.
        
    Returns:
        Vector de signos: 1 (arriba), -1 (abajo), 0 (sin cambio).
    """
    n = len(z_mm)
    vector_disp = np.zeros(n, dtype=float)
    dz = np.diff(z_mm, prepend=z_mm[0])
    vector_disp[dz > 0] = 1
    vector_disp[dz < 0] = -1
    vector_disp[0] = 0
    return vector_disp


def compute_windows(
    vector_disp: np.ndarray,
    window: int
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Computa sumas de ventanas futura y previa.
    
    Args:
        vector_disp: Vector de desplazamientos.
        window: Tamaño de ventana.
        
    Returns:
        (future_sum, previous_sum) arrays.
    """
    n = len(vector_disp)
    future_sum = np.full(n, np.nan)
    previous_sum = np.full(n, np.nan)
    
    for i in range(n):
        if i + window <= n:
            future_sum[i] = np.nansum(vector_disp[i:i + window])
        if i - window + 1 >= 0:
            previous_sum[i] = np.nansum(vector_disp[i - window + 1:i + 1])
    
    return future_sum, previous_sum


def detect_conc_starts(
    future_sum: np.ndarray,
    vel_conc_flag: np.ndarray,
    n_positive: int
) -> np.ndarray:
    """
    Detecta starts de fase concéntrica (HA).
    Primera fila del bloque que cumple ventana positiva + vel umbral.
    
    Args:
        future_sum: Suma de ventana futura.
        vel_conc_flag: Flag de velocidad > umbral.
        n_positive: N celdas positivas requeridas.
        
    Returns:
        Array con 10000 en índices de starts.
    """
    n = len(future_sum)
    conc_start = np.zeros(n, dtype=int)
    
    for i in range(n):
        if np.isnan(future_sum[i]):
            continue
        cond = future_sum[i] >= n_positive and not np.isnan(vel_conc_flag[i])
        prev_cond = False
        if i > 0 and (not np.isnan(future_sum[i - 1])):
            prev_cond = (future_sum[i - 1] >= n_positive) and (not np.isnan(vel_conc_flag[i - 1]))
        if cond and (not prev_cond):
            conc_start[i] = 10000
    
    return conc_start


def detect_peaks(z_mm: np.ndarray, window: int) -> np.ndarray:
    """
    Detecta picos (Conc-Exc): máximos locales con ventana ±window.
    
    Args:
        z_mm: Desplazamiento en mm.
        window: Tamaño de ventana.
        
    Returns:
        Array con 10000 en índices de picos.
    """
    n = len(z_mm)
    conc_exc = np.zeros(n, dtype=int)
    
    for i in range(n):
        if i - window < 0 or i + window >= n:
            continue
        prev_max = np.nanmax(z_mm[i - window:i])
        next_max = np.nanmax(z_mm[i + 1:i + 1 + window])
        if (z_mm[i] > prev_max) and (z_mm[i] > next_max):
            conc_exc[i] = 10000
    
    return conc_exc


def detect_ecc_ends(
    previous_sum: np.ndarray,
    vel_ecc_flag: np.ndarray,
    n_positive: int
) -> np.ndarray:
    """
    Detecta ends de fase excéntrica (HC).
    Última fila del bloque negativo con ventana previa negativa + vel umbral.
    
    Args:
        previous_sum: Suma de ventana previa.
        vel_ecc_flag: Flag de velocidad < -umbral.
        n_positive: N celdas negativas requeridas.
        
    Returns:
        Array con 10000 en índices de ends.
    """
    n = len(previous_sum)
    ecc_end = np.zeros(n, dtype=int)
    
    for i in range(n):
        if np.isnan(previous_sum[i]):
            continue
        cond = (previous_sum[i] <= -n_positive) and (not np.isnan(vel_ecc_flag[i]))
        next_cond = False
        if i + 1 < n and (not np.isnan(previous_sum[i + 1])):
            next_cond = (previous_sum[i + 1] <= -n_positive) and (not np.isnan(vel_ecc_flag[i + 1]))
        if cond and (not next_cond):
            ecc_end[i] = 10000
    
    return ecc_end


def pair_repetitions(
    idx_starts: List[int],
    idx_peaks: List[int],
    idx_ends: List[int],
    n: int
) -> Tuple[List[Tuple[int, int, int]], np.ndarray, np.ndarray]:
    """
    Empareja starts → peaks → ends en orden temporal.
    Asigna fases (ID y etiquetas) a todas las muestras.
    
    Args:
        idx_starts: Índices de starts.
        idx_peaks: Índices de picos.
        idx_ends: Índices de ends.
        n: Longitud de vectores.
        
    Returns:
        (reps, phase_id, phase_label) donde:
        - reps: lista de (s, p, e) tuplas.
        - phase_id: array numérico de fases.
        - phase_label: array de etiquetas de fase.
    """
    phase_id = np.full(n, np.nan)
    phase_label = np.array([''] * n, dtype=object)
    
    # Sentado antes del primer start
    if idx_starts:
        phase_id[:idx_starts[0]] = 0
        phase_label[:idx_starts[0]] = 'Sentado'
    
    reps = []
    peak_cursor = 0
    end_cursor = 0
    
    for rep_num, s in enumerate(idx_starts, start=1):
        # Buscar primer pico posterior al start
        while peak_cursor < len(idx_peaks) and idx_peaks[peak_cursor] <= s:
            peak_cursor += 1
        p = idx_peaks[peak_cursor] if peak_cursor < len(idx_peaks) else None
        if p is not None:
            peak_cursor += 1
        
        # Buscar primer end posterior al pico
        e = None
        if p is not None:
            while end_cursor < len(idx_ends) and idx_ends[end_cursor] <= p:
                end_cursor += 1
            if end_cursor < len(idx_ends):
                e = idx_ends[end_cursor]
                end_cursor += 1
        
        # Siguiente start para fase sentado posterior
        next_s = idx_starts[rep_num] if rep_num < len(idx_starts) else n - 1
        
        # Asignar fases por muestra
        if p is not None and p >= s:
            phase_id[s:p] = 1
            phase_label[s:p] = 'Levantarse'
        if p is not None and e is not None and e >= p:
            phase_id[p:e + 1] = 2
            phase_label[p:e + 1] = 'Sentarse'
        if e is not None and next_s > e:
            phase_id[e + 1:next_s] = 0
            phase_label[e + 1:next_s] = 'Sentado'
        elif e is not None and rep_num == len(idx_starts):
            phase_id[e + 1:] = 0
            phase_label[e + 1:] = 'Sentado'
        
        reps.append((s, p, e))
    
    return reps, phase_id, phase_label


def compute_phase_events(
    conc_start: np.ndarray,
    conc_exc: np.ndarray,
    ecc_end: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Computa arrays de eventos y gráficas acumulativas.
    
    Args:
        conc_start: Array de starts.
        conc_exc: Array de picos.
        ecc_end: Array de ends.
        
    Returns:
        (conc_event, conc_graph, ecc_event, ecc_graph, any_phase_event)
    """
    conc_event = np.where((conc_start == 10000) | (conc_exc == 10000), 1, np.nan)
    ecc_event = np.where((conc_exc == 10000) | (ecc_end == 10000), 1, np.nan)
    conc_graph = np.nancumsum(np.where(np.isnan(conc_event), 0, 1))
    ecc_graph = np.nancumsum(np.where(np.isnan(ecc_event), 0, 1))
    any_phase_event = np.where((conc_start == 10000) | (conc_exc == 10000) | (ecc_end == 10000), 1, np.nan)
    
    return conc_event, conc_graph, ecc_event, ecc_graph, any_phase_event
