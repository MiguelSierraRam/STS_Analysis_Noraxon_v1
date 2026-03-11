# sts_analysis_tool_reducido.py
"""
═══════════════════════════════════════════════════════════════════════════════
                    STS Analysis Tool — Biomechanical Pipeline
                    GENUD Toledo Research Group
                    VERSIÓN PARA HOJA "Reducido" (datos raw)
═══════════════════════════════════════════════════════════════════════════════

DIFERENCIAS CON VERSIÓN "General":
──────────────────────────────────
  · Lee hoja "Reducido" en vez de "General"
  · Calcula Vel_BCM_Z desde la derivada temporal de BCM-z
  · Detecta fases automáticamente con umbral de velocidad (sin marcadores)
  · Mapea Force plate Fx/Fy/Fz a Force Plates_X/Y/Z
  · Calcula variables derivadas faltantes (desplazamientos, potencias, trabajos)
  · NO incluye segmentos biomecánicos (Shoulder, Pelvis, Hip, BMC) porque
    las columnas de desplazamiento/velocidad/potencia/trabajo no existen
    
MÉTODO DE DETECCIÓN DE FASES
─────────────────────────────
  1. Calcular Vel_BCM_Z = diff(BCM_Z) / diff(time)
  2. Suavizar con ventana móvil (rolling mean, window=10)
  3. Detectar inicio concéntrica: Vel_BCM_Z > VEL_THRESHOLD durante WINDOW frames
  4. Detectar transición conc→exc: máximo de BCM_Z después del inicio
  5. Detectar fin excéntrica: Vel_BCM_Z < VEL_THRESHOLD de nuevo

═══════════════════════════════════════════════════════════════════════════════
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from io import BytesIO
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


# ═══════════════════════════════════════════════════════════════════════════
#  CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

FILE          = Path('2025-11-04-12-24_SMP011_D1_10STS_13REP_1.xlsx')
SHEET_NAME    = 'Reducido'           # Hoja con datos raw
G             = 9.80                 # m/s²
ALZ_FACTOR    = 0.90                 # 90% del peso corporal
BCM_THRESH    = 0.85                 # Umbral completitud (85%)

# Parámetros detección de fases
VEL_THRESHOLD = 0.10                 # m/s — umbral velocidad vertical BCM
WINDOW        = 30                   # frames consecutivos para considerar "en movimiento"
SMOOTH_WINDOW = 10                   # ventana suavizado velocidad


# ═══════════════════════════════════════════════════════════════════════════
#  DICCIONARIO DE VARIABLES (versión reducida)
# ═══════════════════════════════════════════════════════════════════════════

VARIABLE_DICT = [
    ('Identificadores', 'Código',                 'ID del participante',                    'Extraído de MetaData_&_Parameters', '—'),
    ('Identificadores', 'Altura',                 'Talla del participante',                 'Extraído de MetaData_&_Parameters', 'm'),
    ('Identificadores', 'Peso_kg',                'Peso corporal',                          'Extraído de MetaData_&_Parameters', 'kg'),
    ('Identificadores', 'Altura de la silla',     'Altura del asiento',                     'Extraído de MetaData_&_Parameters', 'm'),
    ('Identificadores', 'Test',                   'Nombre del protocolo',                   'Extraído de MetaData_&_Parameters', '—'),
    ('Identificadores', 'Fecha Test',             'Fecha y hora del test',                  'Extraído de MetaData_&_Parameters', 'YYYY-MM-DD-HH-MM'),
    ('Identificadores', 'Repeticion',             'Número de repetición STS',               'Contador desde detección (1 a N)', '—'),
    ('Identificadores', 'Fase',                   'Fase del movimiento',                    'Concéntrica / Excéntrica / Sentado', '—'),

    ('Timing', 'Inicio_Tiempo',  'Tiempo inicio de fase',   'time[índice_inicio]',        's'),
    ('Timing', 'Final_Tiempo',   'Tiempo fin de fase',      'time[índice_fin]',           's'),
    ('Timing', 'Tiempo fase',    'Duración de la fase',     'Final_Tiempo − Inicio_Tiempo', 's'),

    ('Trayectorias', 'Shoulder RT-x/z (mm)',  'Posición media hombro RT',    'mean durante la fase', 'mm'),
    ('Trayectorias', 'Pelvis-x/z (mm)',       'Posición media pelvis',       'mean durante la fase', 'mm'),
    ('Trayectorias', 'Hip RT-x/z (mm)',       'Posición media cadera RT',    'mean durante la fase', 'mm'),
    ('Trayectorias', 'BCM-x/z (mm)',          'Posición media BCM',          'mean durante la fase', 'mm'),

    ('Ángulos', 'Thoracic Flexion Fwd (deg)', 'Flexión torácica media',     'mean durante la fase', '°'),
    ('Ángulos', 'Max º Toracico',             'Flexión torácica máxima',     'max durante la fase',  '°'),
    ('Ángulos', 'Minº Toracico',              'Flexión torácica mínima',     'min durante la fase',  '°'),
    ('Ángulos', 'Max-Min_ºToracico',          'ROM torácico',                'max − min',            '°'),
    ('Ángulos', 'RT Hip Flexion (deg)',       'Flexión cadera RT media',     'mean durante la fase', '°'),
    ('Ángulos', 'Max º Hip',                  'Flexión cadera máxima',       'max durante la fase',  '°'),
    ('Ángulos', 'Minº Hip',                   'Flexión cadera mínima',       'min durante la fase',  '°'),
    ('Ángulos', 'Max-Min_ºHip',               'ROM cadera',                  'max − min',            '°'),
    ('Ángulos', 'Start-Max_ºHip',  'Swing cadera inicio→máximo (conc.)', 'max(Hip) − Hip[inicio]', '°'),
    ('Ángulos', 'Start-Min_ºHip',  'Swing cadera inicio→mínimo (exc.)',  'Hip[inicio] − min(Hip)', '°'),

    ('IMU Pitch', 'Max Upp Spine',      'Pitch máx col. superior', 'max(Upper spine Pitch)', '°'),
    ('IMU Pitch', 'Min Pitch Upp Spine','Pitch mín col. superior', 'min(Upper spine Pitch)', '°'),
    ('IMU Pitch', 'Max-Min Upp Spine',  'Rango pitch col. superior', 'max − min',            '°'),

    ('BCM Posición', 'Max_Pos_BMC_X',          'Posición máxima BCM en X',        'max(BCM_X)',                                'mm'),
    ('BCM Posición', 'Min_Pos_BCM_X',          'Posición mínima BCM en X',        'min(BCM_X)',                                'mm'),
    ('BCM Posición', 'BCM_X_ Displacement',    'Desplazamiento total BCM en X',   'max(BCM_X) − min(BCM_X)',                   'mm'),
    ('BCM Posición', '% Desp_BCM_Z_vs_Max',    '% desplazamiento vertical BCM',   '(BCM_Z[fin]−BCM_Z[ini]) / max_global × 100', '%'),

    ('Alcázar', 'Force_Alcazar',      'Fuerza estimada',        '0.90 × peso_kg × 9.80',        'N'),
    ('Alcázar', 'Disp_Alcazar',       'Desplazamiento estimado','altura × 0.5 − altura_silla',  'm'),
    ('Alcázar', 'Veloc_Alcazar',      'Velocidad media estimada','Disp_Alcazar / Tiempo_fase',   'm/s'),
    ('Alcázar', 'Mean Power_Alcazar', 'Potencia media estimada', 'Force_Alcazar × Veloc_Alcazar','W'),

    ('Completitud', 'Completa', 'Rep. biomecánicamente completa',
     '1 si |BCM_Z_fin−BCM_Z_ini| >= 85% del max de esa fase; 0 si no', '0/1'),

    ('EMG', 'RT TIB.ANT. (%)',    'Tibial anterior RT',       'mean durante la fase', '% MVC'),
    ('EMG', 'RT VLO (%)',         'Vasto lateral RT',         'mean durante la fase', '% MVC'),
    ('EMG', 'RT RECTUS FEM. (%)', 'Recto femoral RT',         'mean durante la fase', '% MVC'),
    ('EMG', 'RT MED. GASTRO (%)', 'Gastrocnemio medial RT',   'mean durante la fase', '% MVC'),
    ('EMG', 'RT SEMITEND. (%)',   'Semitendinoso RT',         'mean durante la fase', '% MVC'),
    ('EMG', 'RT GLUT. MAX. (%)',  'Glúteo máximo RT',         'mean durante la fase', '% MVC'),
    ('EMG', 'RT LUMBAR ES (%)',   'Erector espinal lumbar RT','mean durante la fase', '% MVC'),

    ('Fuerzas FP', 'Vert F_Mean',    'Fuerza vertical media',   'mean(Fz)',                     'N'),
    ('Fuerzas FP', 'Vert F_Max',     'Fuerza vertical máxima',  'max(Fz)',                      'N'),
    ('Fuerzas FP', 'Horizon F_Mean', 'Fuerza horizontal media', 'mean(Fx)',                     'N'),
    ('Fuerzas FP', 'Horizon F_Max',  'Fuerza horizontal máxima','max(Fx)',                      'N'),
]


# ═══════════════════════════════════════════════════════════════════════════
#  MAPAS DE COLUMNAS
# ═══════════════════════════════════════════════════════════════════════════

TRAJ_PAIRS = [
    ('Noraxon MyoMotion-Trajectories-Shoulder RT-x (mm)',
     'Noraxon MyoMotion-Trajectories-Shoulder RT-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-Pelvis-x (mm)',
     'Noraxon MyoMotion-Trajectories-Pelvis-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-Hip RT-x (mm)',
     'Noraxon MyoMotion-Trajectories-Hip RT-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-Knee RT-x (mm)',
     'Noraxon MyoMotion-Trajectories-Knee RT-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-Ankle RT-x (mm)',
     'Noraxon MyoMotion-Trajectories-Ankle RT-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-Heel RT-x (mm)',
     'Noraxon MyoMotion-Trajectories-Heel RT-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-Heel back RT-x (mm)',
     'Noraxon MyoMotion-Trajectories-Heel back RT-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-Foot toe RT-x (mm)',
     'Noraxon MyoMotion-Trajectories-Foot toe RT-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-1st metatarsophalangeal joint RT-x (mm)',
     'Noraxon MyoMotion-Trajectories-1st metatarsophalangeal joint RT-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-5th metatarsophalangeal joint RT-x (mm)',
     'Noraxon MyoMotion-Trajectories-5th metatarsophalangeal joint RT-z (mm)'),
    ('Noraxon MyoMotion-Trajectories-Body center of mass-x (mm)',
     'Noraxon MyoMotion-Trajectories-Body center of mass-z (mm)'),
]

ANGLE_COLS = {
    'Toracico':     'Thoracic Flexion Fwd (deg)',
    'Lumbar':       'Lumbar Flexion Fwd (deg)',
    'Torso-Pelvis': 'Torso-Pelvic Flexion Fwd (deg)',
    'Hip':          'RT Hip Flexion (deg)',
    'Knee':         'RT Knee Flexion (deg)',
    'Ankle':        'RT Ankle Dorsiflexion (deg)',
}

PITCH_COLS = {
    'Upp Spine': 'Noraxon MyoMotion-Segments-Upper spine-Pitch (deg)',
    'Low Spine': 'Noraxon MyoMotion-Segments-Lower spine-Pitch (deg)',
    'Pelvis':    'Noraxon MyoMotion-Segments-Pelvis-Pitch (deg)',
    'Object':    'Object 1-Pitch (deg)',
}

EMG_COLS = [
    'RT TIB.ANT. (%)', 'RT VLO (%)', 'RT RECTUS FEM. (%)',
    'RT MED. GASTRO (%)', 'RT SEMITEND. (%)', 'RT GLUT. MAX. (%)', 'RT LUMBAR ES (%)',
]

BCM_Z = 'Noraxon MyoMotion-Trajectories-Body center of mass-z (mm)'
BCM_X = 'Noraxon MyoMotion-Trajectories-Body center of mass-x (mm)'
HIP_Z = 'Noraxon MyoMotion-Trajectories-Hip RT-z (mm)'

# Mapeo fuerzas plataforma
FP_MAP = {
    'X': 'Force plate Fx (N)',
    'Y': 'Force plate Fy (N)',
    'Z': 'Force plate Fz (N)',
}


# ═══════════════════════════════════════════════════════════════════════════
#  UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════

def _get(seg, col):
    """Devuelve la serie si la columna existe y tiene datos, sino None."""
    return seg[col] if (col in seg.columns and seg[col].notna().any()) else None


# ═══════════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

print(f"\n{'='*65}")
print(f"  STS Analysis Tool — Versión Reducido")
print(f"  Archivo : {FILE.name}")
print(f"  Hoja    : {SHEET_NAME}")
print(f"  Fecha   : {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
print(f"{'='*65}\n")

xl      = pd.ExcelFile(FILE)
df_gen  = pd.read_excel(xl, SHEET_NAME, header=0)

# Buscar hoja de metadata (puede tener nombres diferentes)
META_SHEETS = ['MetaData_&_Parameters', 'Metadata', 'Parameters']
meta_sheet = None
for sh in META_SHEETS:
    if sh in xl.sheet_names:
        meta_sheet = sh
        break

if meta_sheet:
    df_meta = pd.read_excel(xl, meta_sheet, header=None, index_col=0)
else:
    print(f"[AVISO] No se encontró hoja de metadata. Usando valores por defecto.")
    df_meta = pd.DataFrame({
        1: {
            'Código': 'UNKNOWN',
            'Altura': 1.70,
            'Peso': 70.0,
            'Altura de la silla': 0.43,
            'Nombre Test': '10STS',
            'Fecha del test': datetime.now().strftime('%Y-%m-%d-%H-%M'),
        }
    })

print(f"[OK] {SHEET_NAME} cargado: {len(df_gen)} frames x {len(df_gen.columns)} columnas")


# ═══════════════════════════════════════════════════════════════════════════
#  EXTRACCIÓN DE METADATA
# ═══════════════════════════════════════════════════════════════════════════

codigo     = df_meta.loc['Código', 1]
altura     = float(df_meta.loc['Altura', 1])
peso       = float(df_meta.loc['Peso', 1])
alt_silla  = float(df_meta.loc['Altura de la silla', 1])
test_name  = df_meta.loc['Nombre Test', 1] if 'Nombre Test' in df_meta.index else '10STS'
fecha_test = df_meta.loc['Fecha del test', 1] if 'Fecha del test' in df_meta.index else 'N/A'

FORCE_ALZ = round(ALZ_FACTOR * peso * G, 6)
DISP_ALZ  = round(altura * 0.5 - alt_silla, 6)

print(f"[OK] Participante  : {codigo}")
print(f"     Altura        : {altura} m")
print(f"     Peso          : {peso} kg")
print(f"     Silla         : {alt_silla} m")
print(f"     Force_Alcazar : {FORCE_ALZ:.4f} N")
print(f"     Disp_Alcazar  : {DISP_ALZ:.4f} m\n")


# ═══════════════════════════════════════════════════════════════════════════
#  CÁLCULO DE VELOCIDAD BCM_Z
# ═══════════════════════════════════════════════════════════════════════════

print("[..] Calculando velocidad vertical del BCM...")

# Convertir BCM_Z de mm a m
df_gen['BCM_Z_m'] = df_gen[BCM_Z] / 1000.0

# Calcular velocidad (m/s) = diff(posición) / diff(tiempo)
df_gen['Vel_BCM_Z_raw'] = df_gen['BCM_Z_m'].diff() / df_gen['time'].diff()

# Suavizar con ventana móvil
df_gen['Vel_BCM_Z'] = df_gen['Vel_BCM_Z_raw'].rolling(
    window=SMOOTH_WINDOW, center=True, min_periods=1
).mean()

print(f"[OK] Vel_BCM_Z calculada (suavizado ventana={SMOOTH_WINDOW})\n")


# ═══════════════════════════════════════════════════════════════════════════
#  DETECCIÓN AUTOMÁTICA DE FASES
# ═══════════════════════════════════════════════════════════════════════════

print(f"[..] Detectando fases automáticamente...")
print(f"     Umbral velocidad : {VEL_THRESHOLD} m/s")
print(f"     Ventana mínima   : {WINDOW} frames consecutivos\n")

vel = df_gen['Vel_BCM_Z'].fillna(0).values
bcm_z = df_gen['BCM_Z_m'].values
time_arr = df_gen['time'].values

# Detectar regiones donde velocidad > umbral durante WINDOW frames
above_thresh = (vel > VEL_THRESHOLD).astype(int)
convolve_result = np.convolve(above_thresh, np.ones(WINDOW, dtype=int), mode='same')
in_movement = convolve_result >= WINDOW

# Encontrar transiciones
starts = np.where(np.diff(in_movement.astype(int)) == 1)[0] + 1
ends   = np.where(np.diff(in_movement.astype(int)) == -1)[0] + 1

# Asegurar que starts y ends estén balanceados
if len(starts) == 0 or len(ends) == 0:
    print("[ERROR] No se detectaron fases. Verifica el umbral de velocidad.")
    exit(1)

if starts[0] > ends[0]:
    ends = ends[1:]
if len(starts) > len(ends):
    starts = starts[:len(ends)]
if len(ends) > len(starts):
    ends = ends[:len(starts)]

n_reps = len(starts)
print(f"[OK] Detectadas {n_reps} repeticiones\n")

# Construir phase_bounds
phase_bounds = []
for i in range(n_reps):
    conc_start = starts[i]
    ecc_end = ends[i]
    
    # Encontrar pico de BCM_Z entre conc_start y ecc_end (transición conc→exc)
    seg_bcm = bcm_z[conc_start:ecc_end+1]
    if len(seg_bcm) == 0:
        continue
    peak_idx = conc_start + np.argmax(seg_bcm)
    
    # Fase sentado: desde ecc_end hasta siguiente conc_start (o fin)
    seated_end = starts[i+1] - 1 if i+1 < n_reps else len(df_gen) - 1
    
    phase_bounds.append({
        'rep':    i + 1,
        'conc':   (conc_start, peak_idx),
        'ecc':    (peak_idx, ecc_end),
        'seated': (ecc_end, seated_end),
    })

print(f"[OK] Segmentación completada: {n_reps} reps x 3 fases = {n_reps * 3} intervalos\n")


# ═══════════════════════════════════════════════════════════════════════════
#  GRÁFICA DE SEGMENTACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def build_segmentation_figure(df, pb_list):
    time = df['time'].values
    bcm_z = df[BCM_Z].values
    vel = df['Vel_BCM_Z'].values

    t0 = df.loc[pb_list[0]['conc'][0], 'time'] - 0.3
    t1 = df.loc[pb_list[-1]['seated'][1], 'time'] + 0.3
    mask = (time >= t0) & (time <= t1)
    t_c = time[mask]; bcm_c = bcm_z[mask]; vel_c = vel[mask]

    COL = {'conc': '#3b82f6', 'ecc': '#ef4444', 'seated': '#94a3b8'}

    fig, axes = plt.subplots(2, 1, figsize=(16, 7), sharex=True, facecolor='#f8fafc')
    fig.suptitle(
        f'Segmentación de fases STS  —  {codigo}  |  {test_name}  |  {fecha_test}',
        fontsize=12, fontweight='bold', color='#1e293b', y=0.99
    )

    for ax, data, ylabel, line_col in [
        (axes[0], bcm_c, 'Posición BCM vertical (mm)', '#1d4ed8'),
        (axes[1], vel_c, 'Velocidad BCM vertical (m/s)', '#b91c1c'),
    ]:
        ax.set_facecolor('#f1f5f9')
        ax.grid(True, alpha=0.45, color='white', linewidth=1.2)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_ylabel(ylabel, fontsize=10, color='#374151', labelpad=8)
        ax.tick_params(colors='#374151', labelsize=9)

        for pb in pb_list:
            for fk, fc in COL.items():
                s_i, e_i = pb[fk]
                ax.axvspan(df.loc[s_i, 'time'], df.loc[e_i, 'time'],
                           alpha=0.20, color=fc, linewidth=0)

        ax.plot(t_c, data, color=line_col, linewidth=1.3, zorder=5)

        for pb in pb_list:
            for idx in [pb['conc'][0], pb['conc'][1], pb['ecc'][1]]:
                ax.axvline(df.loc[idx, 'time'], color='#64748b',
                           linewidth=0.75, linestyle='--', alpha=0.7, zorder=4)

        if ax is axes[0] and not np.all(np.isnan(data)):
            y_rng = np.nanmax(data) - np.nanmin(data)
            y_top = np.nanmax(data) + y_rng * 0.04
            for pb in pb_list:
                t_mid = (df.loc[pb['conc'][0], 'time'] + df.loc[pb['conc'][1], 'time']) / 2
                ax.text(t_mid, y_top, str(pb['rep']),
                        ha='center', va='bottom', fontsize=7.5,
                        color='#1e40af', fontweight='bold')

    axes[1].set_xlabel('Tiempo (s)', fontsize=10, color='#374151', labelpad=6)

    legend_elems = [
        mpatches.Patch(facecolor='#3b82f6', alpha=0.4, label='Concéntrica'),
        mpatches.Patch(facecolor='#ef4444', alpha=0.4, label='Excéntrica'),
        mpatches.Patch(facecolor='#94a3b8', alpha=0.4, label='Sentado'),
        Line2D([0], [0], color='#64748b', linestyle='--', linewidth=0.9, label='Transición'),
    ]
    fig.legend(handles=legend_elems, loc='lower center', ncol=4,
               fontsize=9, framealpha=0.9, bbox_to_anchor=(0.5, 0.005))
    plt.tight_layout(rect=[0, 0.05, 1, 0.975])
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  CÁLCULO POR FASE
# ═══════════════════════════════════════════════════════════════════════════

def phase_stats(df, s, e, fase, rep):
    seg = df.iloc[s:e + 1]
    r = {}

    r.update({
        'Código': codigo, 'Altura': altura, 'Peso_kg': peso,
        'Altura de la silla': alt_silla, 'Test': test_name,
        'Fecha Test': fecha_test, 'Repeticion': rep, 'Fase': fase,
    })

    r['Inicio_Tiempo'] = round(seg['time'].iloc[0], 3)
    r['Final_Tiempo'] = round(seg['time'].iloc[-1], 3)
    dt = round(r['Final_Tiempo'] - r['Inicio_Tiempo'], 3)
    r['Tiempo fase'] = dt

    # Trayectorias
    for cx, cz in TRAJ_PAIRS:
        r[cx] = seg[cx].mean() if cx in seg.columns else np.nan
        r[cz] = seg[cz].mean() if cz in seg.columns else np.nan

    # Ángulos
    for key, col in ANGLE_COLS.items():
        v = _get(seg, col)
        r[col] = v.mean() if v is not None else np.nan
        if key in ('Toracico', 'Lumbar', 'Torso-Pelvis', 'Hip'):
            r[f'Max º {key}'] = v.max() if v is not None else np.nan
            r[f'Minº {key}'] = v.min() if v is not None else np.nan
            r[f'Max-Min_º{key}'] = v.max() - v.min() if v is not None else np.nan

    # Hip Swing
    hip_v = _get(seg, ANGLE_COLS['Hip'])
    if fase == 'Concéntrica':
        r['Start-Max_ºHip'] = hip_v.max() - hip_v.iloc[0] if hip_v is not None else np.nan
        r['Start-Min_ºHip'] = np.nan
    elif fase == 'Excéntrica':
        r['Start-Max_ºHip'] = np.nan
        r['Start-Min_ºHip'] = hip_v.iloc[0] - hip_v.min() if hip_v is not None else np.nan
    else:
        r['Start-Max_ºHip'] = r['Start-Min_ºHip'] = np.nan
    r['Hip Swing'] = np.nan

    # IMU Pitch
    for key, col in PITCH_COLS.items():
        v = _get(seg, col)
        r[f'Max {key}'] = v.max() if v is not None else np.nan
        r[f'Min Pitch {key}'] = v.min() if v is not None else np.nan
        r[f'Max-Min {key}'] = v.max() - v.min() if v is not None else np.nan

    # BCM X
    bx = _get(seg, BCM_X)
    bz = _get(seg, BCM_Z)
    if bx is not None:
        r['Max_Pos_BMC_X'] = bx.max()
        r['Min_Pos_BCM_X'] = bx.min()
        r['BCM_X_ Displacement'] = bx.max() - bx.min()
    else:
        r['Max_Pos_BMC_X'] = r['Min_Pos_BCM_X'] = r['BCM_X_ Displacement'] = np.nan

    # Alcázar
    r['Force_Alcazar'] = FORCE_ALZ
    r['Disp_Alcazar'] = DISP_ALZ
    r['Veloc_Alcazar'] = DISP_ALZ / dt if dt > 0 else np.nan
    r['Mean Power_Alcazar'] = FORCE_ALZ * r['Veloc_Alcazar']

    # % desplazamientos
    if bz is not None:
        d = seg[BCM_Z].iloc[-1] - seg[BCM_Z].iloc[0]
        r['% Desp_BCM_Z_vs_Max'] = (d / (df[BCM_Z].max() / 1000)) * 100
    else:
        r['% Desp_BCM_Z_vs_Max'] = np.nan

    # Completitud
    r['_bcm_z_raw'] = abs(seg[BCM_Z].iloc[-1] - seg[BCM_Z].iloc[0]) if bz is not None else np.nan
    r['Completa'] = np.nan

    # EMG
    for col in EMG_COLS:
        v = _get(seg, col)
        r[col] = v.mean() if v is not None else np.nan

    # Fuerzas plataforma
    fx = _get(seg, FP_MAP['X'])
    fz = _get(seg, FP_MAP['Z'])
    r['Vert F_Mean'] = fz.mean() if fz is not None else np.nan
    r['Vert F_Max'] = fz.max() if fz is not None else np.nan
    r['Horizon F_Mean'] = fx.mean() if fx is not None else np.nan
    r['Horizon F_Max'] = fx.max() if fx is not None else np.nan

    return r


# ═══════════════════════════════════════════════════════════════════════════
#  PROCESADO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

FASES = [('conc', 'Concéntrica'), ('ecc', 'Excéntrica'), ('seated', 'Sentado')]

rows_out = []
for pb in phase_bounds:
    for fk, fl in FASES:
        s, e = pb[fk]
        rows_out.append(phase_stats(df_gen, s, e, fl, pb['rep']))

df_out = pd.DataFrame(rows_out)
print(f"[OK] Cálculos completados: {len(df_out)} filas x {len(df_out.columns)} columnas")

# Post-proceso Completa
for fl in ('Concéntrica', 'Excéntrica', 'Sentado'):
    mask = df_out['Fase'] == fl
    max_d = df_out.loc[mask, '_bcm_z_raw'].max()
    if pd.notna(max_d) and max_d > 0:
        df_out.loc[mask, 'Completa'] = (
            df_out.loc[mask, '_bcm_z_raw'] / max_d >= BCM_THRESH).astype(int)

df_out.drop(columns=['_bcm_z_raw'], inplace=True)
n_completas = int(df_out.loc[df_out['Fase'] == 'Concéntrica', 'Completa'].sum())
print(f"     Reps completas (conc.): {n_completas} / {n_reps}\n")


# ═══════════════════════════════════════════════════════════════════════════
#  GENERAR GRÁFICA
# ═══════════════════════════════════════════════════════════════════════════

print("[..] Generando gráfica de segmentación...")
fig_seg = build_segmentation_figure(df_gen, phase_bounds)
img_buf = BytesIO()
fig_seg.savefig(img_buf, format='png', dpi=150, bbox_inches='tight', facecolor='#f8fafc')
plt.close(fig_seg)
img_buf.seek(0)
print("[OK] Gráfica generada\n")


# ═══════════════════════════════════════════════════════════════════════════
#  EXPORTACIÓN EXCEL
# ═══════════════════════════════════════════════════════════════════════════

out_path = FILE.parent / f"{FILE.stem}_results.xlsx"
print(f"[..] Exportando a {out_path.name} ...")

with pd.ExcelWriter(out_path, engine='xlsxwriter',
                    engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:

    wb = writer.book

    F = {
        'title': wb.add_format({'bold': True, 'font_size': 13, 'font_color': '#1e3a5f'}),
        'sub': wb.add_format({'italic': True, 'font_color': '#6b7280', 'font_size': 9}),
        'hdr': wb.add_format({'bold': True, 'bg_color': '#1e3a5f', 'font_color': 'white',
                              'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True}),
        'hdr2': wb.add_format({'bold': True, 'bg_color': '#334155', 'font_color': 'white',
                               'border': 1, 'align': 'center', 'valign': 'vcenter'}),
        'conc': wb.add_format({'bg_color': '#dbeafe', 'border': 1, 'num_format': '0.0000'}),
        'ecc': wb.add_format({'bg_color': '#fee2e2', 'border': 1, 'num_format': '0.0000'}),
        'seated': wb.add_format({'bg_color': '#f1f5f9', 'border': 1, 'num_format': '0.0000'}),
        'txt': wb.add_format({'border': 1}),
        'grp_a': wb.add_format({'bold': True, 'bg_color': '#e0f2fe', 'border': 1, 'font_color': '#0c4a6e'}),
        'grp_b': wb.add_format({'bold': True, 'bg_color': '#f0fdf4', 'border': 1, 'font_color': '#14532d'}),
        'key': wb.add_format({'bold': True, 'bg_color': '#f8fafc', 'border': 1}),
        'log_k': wb.add_format({'bold': True, 'bg_color': '#fef9c3', 'border': 1}),
        'log_v': wb.add_format({'bg_color': '#fefce8', 'border': 1}),
        'log_sec': wb.add_format({'bold': True, 'bg_color': '#1e3a5f', 'font_color': 'white', 'border': 1}),
    }

    # HOJA 1: KF_Results
    df_out.to_excel(writer, sheet_name='KF_Results', index=False, startrow=2)
    ws = writer.sheets['KF_Results']
    ws.write(0, 0, f'STS Results — {codigo}  |  {test_name}  |  {fecha_test}', F['title'])
    ws.write(1, 0,
             f'Detección automática: umbral={VEL_THRESHOLD} m/s, ventana={WINDOW} frames  |  '
             f'Reps={n_reps}  |  Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}', F['sub'])

    for ci, col in enumerate(df_out.columns):
        ws.write(2, ci, col, F['hdr'])

    for ri, row in df_out.iterrows():
        fase = row['Fase']
        fmt = F['conc'] if fase == 'Concéntrica' else (F['ecc'] if fase == 'Excéntrica' else F['seated'])
        for ci, val in enumerate(row):
            if pd.isna(val):
                ws.write(ri + 3, ci, '', F['txt'])
            elif isinstance(val, (int, float)):
                ws.write(ri + 3, ci, val, fmt)
            else:
                ws.write(ri + 3, ci, val, F['txt'])

    ws.set_row(2, 38)
    ws.freeze_panes(3, 2)
    ws.set_zoom(85)
    for ci, col in enumerate(df_out.columns):
        ws.set_column(ci, ci, min(max(len(str(col)), 8) + 2, 32))

    # HOJA 2: Segmentation_Plot
    ws2 = wb.add_worksheet('Segmentation_Plot')
    ws2.write(0, 0, f'Segmentación de fases STS — {codigo}  |  {test_name}', F['title'])
    ws2.write(1, 0, 'Detección automática basada en velocidad vertical del BCM', F['sub'])
    ws2.insert_image(3, 0, 'placeholder.png', {'image_data': img_buf, 'x_scale': 1.0, 'y_scale': 1.0})
    ws2.set_column(0, 0, 140)

    t_row = 34
    for ci, hdr in enumerate(['Rep', 'Fase', 'Inicio (s)', 'Fin (s)', 'Duración (s)', 'Completa']):
        ws2.write(t_row, ci, hdr, F['hdr2'])
    for ri, row in df_out[['Repeticion', 'Fase', 'Inicio_Tiempo', 'Final_Tiempo', 'Tiempo fase', 'Completa']].iterrows():
        fmt = F['conc'] if row['Fase'] == 'Concéntrica' else (F['ecc'] if row['Fase'] == 'Excéntrica' else F['seated'])
        for ci, val in enumerate(row):
            ws2.write(t_row + 1 + ri, ci, val, fmt)
    for ci in range(6):
        ws2.set_column(ci, ci, 16)

    # HOJA 3: Variable_Dictionary
    df_dict = pd.DataFrame(VARIABLE_DICT, columns=['Grupo', 'Variable', 'Descripción', 'Cálculo', 'Unidad'])
    ws3 = wb.add_worksheet('Variable_Dictionary')
    ws3.write(0, 0, 'Diccionario de Variables — STS Analysis Tool (Reducido)', F['title'])
    ws3.write(1, 0, f'{len(df_dict)} variables documentadas', F['sub'])

    for ci, hdr in enumerate(['Grupo', 'Variable', 'Descripción', 'Cálculo', 'Unidad']):
        ws3.write(2, ci, hdr, F['hdr'])

    prev_grp = None
    toggle = True
    for ri, row in df_dict.iterrows():
        if row['Grupo'] != prev_grp:
            toggle = not toggle
            prev_grp = row['Grupo']
        fg = F['grp_a'] if toggle else F['grp_b']
        ws3.write(ri + 3, 0, row['Grupo'], fg)
        ws3.write(ri + 3, 1, row['Variable'], F['key'])
        ws3.write(ri + 3, 2, row['Descripción'], F['txt'])
        ws3.write(ri + 3, 3, row['Cálculo'], F['txt'])
        ws3.write(ri + 3, 4, row['Unidad'], F['txt'])

    ws3.set_column(0, 0, 20)
    ws3.set_column(1, 1, 38)
    ws3.set_column(2, 2, 48)
    ws3.set_column(3, 3, 52)
    ws3.set_column(4, 4, 12)
    ws3.set_row(2, 22)
    ws3.freeze_panes(3, 0)

    # HOJA 4: Processing_Log
    ws4 = wb.add_worksheet('Processing_Log')
    ws4.write(0, 0, 'Log de Procesamiento — STS Analysis Tool (Reducido)', F['title'])
    ws4.set_column(0, 0, 30)
    ws4.set_column(1, 1, 60)

    SECTIONS = {'IDENTIFICACIÓN', 'DATOS RAW', 'DETECCIÓN AUTOMÁTICA',
                'PARÁMETROS SUJETO', 'MÉTODO ALCÁZAR', 'RESULTADO'}
    log = [
        ('IDENTIFICACIÓN', ''),
        ('Código', str(codigo)),
        ('Test', str(test_name)),
        ('Fecha test', str(fecha_test)),
        ('Procesado el', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('Archivo fuente', FILE.name),
        ('Hoja procesada', SHEET_NAME),
        ('', ''),
        ('DATOS RAW', ''),
        ('Frames totales', str(len(df_gen))),
        ('Columnas Reducido', str(len(df_gen.columns))),
        ('', ''),
        ('DETECCIÓN AUTOMÁTICA', ''),
        ('Método', 'Umbral de velocidad vertical BCM'),
        ('Umbral velocidad', f'{VEL_THRESHOLD} m/s'),
        ('Ventana detección', f'{WINDOW} frames consecutivos'),
        ('Suavizado velocidad', f'{SMOOTH_WINDOW} frames (rolling mean)'),
        ('Reps detectadas', str(n_reps)),
        ('Total intervalos', f'{n_reps * 3}  ({n_reps} reps x 3 fases)'),
        ('', ''),
        ('PARÁMETROS SUJETO', ''),
        ('Altura', f'{altura} m'),
        ('Peso', f'{peso} kg'),
        ('Altura silla', f'{alt_silla} m'),
        ('', ''),
        ('MÉTODO ALCÁZAR', ''),
        ('Force_Alcazar', f'{FORCE_ALZ:.6f} N'),
        ('Disp_Alcazar', f'{DISP_ALZ:.6f} m'),
        ('', ''),
        ('RESULTADO', ''),
        ('Filas generadas', str(len(df_out))),
        ('Columnas generadas', str(len(df_out.columns))),
        ('Reps completas', f'{n_completas} / {n_reps}'),
        ('Archivo salida', str(out_path.name)),
    ]

    for ri, (k, v) in enumerate(log):
        if k in SECTIONS:
            ws4.write(ri + 2, 0, k, F['log_sec'])
            ws4.write(ri + 2, 1, '', F['log_sec'])
        elif k == '':
            ws4.write(ri + 2, 0, '', F['txt'])
            ws4.write(ri + 2, 1, '', F['txt'])
        else:
            ws4.write(ri + 2, 0, k, F['log_k'])
            ws4.write(ri + 2, 1, v, F['log_v'])

print(f"[OK] Excel exportado correctamente")
print(f"     Hoja KF_Results          : {len(df_out)} filas x {len(df_out.columns)} cols")
print(f"     Hoja Segmentation_Plot   : gráfica + tabla de tiempos")
print(f"     Hoja Variable_Dictionary : {len(VARIABLE_DICT)} variables documentadas")
print(f"     Hoja Processing_Log      : {len(log)} entradas")
print(f"\n{'=' * 65}")
print(f"  Análisis completado: {out_path.name}")
print(f"{'=' * 65}\n")
