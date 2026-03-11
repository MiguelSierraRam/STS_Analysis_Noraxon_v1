# sts_analysis_tool_sencillo.py
"""
═══════════════════════════════════════════════════════════════════════════════
                    STS Analysis Tool — Biomechanical Pipeline
                    GENUD Toledo Research Group
                    VERSIÓN PARA ARCHIVOS *_Sencillo.xlsx
═══════════════════════════════════════════════════════════════════════════════

INPUT: Archivo *_Sencillo.xlsx con hoja "General" (217 columnas completas)
       incluyendo variables derivadas y marcadores de fase pre-calculados

OUTPUT: Excel con 4 hojas:
  · KF_Results: estadísticas por repetición × fase
  · Segmentation_Plot: gráfica de segmentación
  · Variable_Dictionary: documentación de variables
  · Processing_Log: log del procesamiento

DIFERENCIAS CON VERSIÓN "Reducido":
  · Lee marcadores de fase ya calculados (Conc Start, Conc-Exc, Ecc End)
  · Usa todas las 116 variables derivadas existentes
  · No necesita calcular velocidades/aceleraciones/fuerzas/potencias

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

FILE       = Path('2025-11-04-12-24_SMP011_D1_10STS_13REP_1.xlsx')
G          = 9.80
ALZ_FACTOR = 0.90
BCM_THRESH = 0.85


# ═══════════════════════════════════════════════════════════════════════════
#  DICCIONARIO DE VARIABLES
# ═══════════════════════════════════════════════════════════════════════════

VARIABLE_DICT = [
    # (Grupo, Variable, Descripción, Cálculo, Unidad)
    
    # ── IDENTIFICADORES ──────────────────────────────────────────────────
    ('Identificadores', 'Código',                 'ID del participante',                                   'Extraído de MetaData_&_Parameters',                        '—'),
    ('Identificadores', 'Altura',                 'Talla del participante',                                'Extraído de MetaData_&_Parameters',                        'm'),
    ('Identificadores', 'Peso_kg',                'Peso corporal',                                         'Extraído de MetaData_&_Parameters',                        'kg'),
    ('Identificadores', 'Altura de la silla',     'Altura del asiento utilizado',                          'Extraído de MetaData_&_Parameters',                        'm'),
    ('Identificadores', 'Test',                   'Nombre del protocolo (e.g., 10STS)',                    'Extraído de MetaData_&_Parameters',                        '—'),
    ('Identificadores', 'Fecha Test',             'Fecha y hora del test',                                 'Extraído de MetaData_&_Parameters',                        'YYYY-MM-DD-HH-MM'),
    ('Identificadores', 'Repeticion',             'Número de repetición STS',                              'Contador desde detección de fases (1 a N)',                 '—'),
    ('Identificadores', 'Fase',                   'Fase del movimiento',                                   'Concéntrica / Excéntrica / Sentado',                       '—'),

    # ── TIMING ───────────────────────────────────────────────────────────
    ('Timing', 'Inicio_Tiempo',  'Tiempo inicio de fase',   'time[índice_inicio_fase]',        's'),
    ('Timing', 'Final_Tiempo',   'Tiempo fin de fase',      'time[índice_fin_fase]',           's'),
    ('Timing', 'Tiempo fase',    'Duración de la fase',     'Final_Tiempo − Inicio_Tiempo',    's'),

    # ── TRAYECTORIAS ─────────────────────────────────────────────────────
    ('Trayectorias', 'Shoulder RT-x/z (mm)',       'Posición media hombro RT en X/Z',          'mean(columna) durante la fase', 'mm'),
    ('Trayectorias', 'Pelvis-x/z (mm)',            'Posición media pelvis en X/Z',             'mean(columna) durante la fase', 'mm'),
    ('Trayectorias', 'Hip RT-x/z (mm)',            'Posición media cadera RT en X/Z',          'mean(columna) durante la fase', 'mm'),
    ('Trayectorias', 'Knee RT-x/z (mm)',           'Posición media rodilla RT en X/Z',         'mean(columna) durante la fase', 'mm'),
    ('Trayectorias', 'Ankle RT-x/z (mm)',          'Posición media tobillo RT en X/Z',         'mean(columna) durante la fase', 'mm'),
    ('Trayectorias', 'Heel RT-x/z (mm)',           'Posición media talón RT en X/Z',           'mean(columna) durante la fase', 'mm'),
    ('Trayectorias', 'Heel back RT-x/z (mm)',      'Posición media talón posterior RT en X/Z', 'mean(columna) durante la fase', 'mm'),
    ('Trayectorias', 'Foot toe RT-x/z (mm)',       'Posición media punta del pie RT en X/Z',   'mean(columna) durante la fase', 'mm'),
    ('Trayectorias', '1st metatarsal RT-x/z (mm)', 'Posición media 1ª art. metatarsofalángica','mean(columna) durante la fase', 'mm'),
    ('Trayectorias', '5th metatarsal RT-x/z (mm)', 'Posición media 5ª art. metatarsofalángica','mean(columna) durante la fase', 'mm'),
    ('Trayectorias', 'BCM-x/z (mm)',               'Posición media BCM en X/Z',                'mean(columna) durante la fase', 'mm'),

    # ── ÁNGULOS ──────────────────────────────────────────────────────────
    ('Ángulos', 'Thoracic Flexion Fwd (deg)',       'Flexión torácica media',          'mean(col) durante la fase',   '°'),
    ('Ángulos', 'Max º Toracico',                   'Flexión torácica máxima',         'max(col) durante la fase',    '°'),
    ('Ángulos', 'Minº Toracico',                    'Flexión torácica mínima',         'min(col) durante la fase',    '°'),
    ('Ángulos', 'Max-Min_ºToracico',                'ROM torácico',                    'max − min durante la fase',   '°'),
    ('Ángulos', 'Lumbar Flexion Fwd (deg)',         'Flexión lumbar media',            'mean(col) durante la fase',   '°'),
    ('Ángulos', 'Max º Lumbar',                     'Flexión lumbar máxima',           'max(col) durante la fase',    '°'),
    ('Ángulos', 'Minº Lumbar',                      'Flexión lumbar mínima',           'min(col) durante la fase',    '°'),
    ('Ángulos', 'Max-Min_ºLumbar',                  'ROM lumbar',                      'max − min durante la fase',   '°'),
    ('Ángulos', 'Torso-Pelvic Flexion Fwd (deg)',   'Flexión torso-pelvis media',      'mean(col) durante la fase',   '°'),
    ('Ángulos', 'Max º Torso-Pelvis',               'Flexión torso-pelvis máxima',     'max(col) durante la fase',    '°'),
    ('Ángulos', 'Minº Torso-Pelvis',                'Flexión torso-pelvis mínima',     'min(col) durante la fase',    '°'),
    ('Ángulos', 'Max-Min_ºTorso-Pelvis',            'ROM torso-pelvis',                'max − min durante la fase',   '°'),
    ('Ángulos', 'RT Hip Flexion (deg)',             'Flexión cadera RT media',          'mean(col) durante la fase',   '°'),
    ('Ángulos', 'Max º Hip',                        'Flexión cadera máxima',           'max(col) durante la fase',    '°'),
    ('Ángulos', 'Minº Hip',                         'Flexión cadera mínima',           'min(col) durante la fase',    '°'),
    ('Ángulos', 'Max-Min_ºHip',                     'ROM cadera',                      'max − min durante la fase',   '°'),
    ('Ángulos', 'Start-Max_ºHip',  'Swing cadera inicio→máximo (solo conc.)',  'max(Hip) − Hip[primer_frame]',         '°'),
    ('Ángulos', 'Start-Min_ºHip',  'Swing cadera inicio→mínimo (solo exc.)',   'Hip[primer_frame] − min(Hip)',         '°'),
    ('Ángulos', 'RT Knee Flexion (deg)',            'Flexión rodilla RT media',        'mean(col) durante la fase',   '°'),
    ('Ángulos', 'RT Ankle Dorsiflexion (deg)',      'Dorsiflexión tobillo RT media',   'mean(col) durante la fase',   '°'),

    # ── IMU PITCH ────────────────────────────────────────────────────────
    ('IMU Pitch', 'Max Upp Spine',      'Pitch máx sensor col. superior', 'max(Upper spine Pitch)',  '°'),
    ('IMU Pitch', 'Min Pitch Upp Spine','Pitch mín sensor col. superior', 'min(Upper spine Pitch)',  '°'),
    ('IMU Pitch', 'Max-Min Upp Spine',  'Rango pitch col. superior',      'max − min',               '°'),
    ('IMU Pitch', 'Max Low Spine',      'Pitch máx sensor col. inferior', 'max(Lower spine Pitch)',  '°'),
    ('IMU Pitch', 'Min Pitch Low Spine','Pitch mín sensor col. inferior', 'min(Lower spine Pitch)',  '°'),
    ('IMU Pitch', 'Max-Min Low Spine',  'Rango pitch col. inferior',      'max − min',               '°'),
    ('IMU Pitch', 'Max Pelvis',         'Pitch máx sensor pelvis',        'max(Pelvis Pitch)',        '°'),
    ('IMU Pitch', 'Min Pitch Pelvis',   'Pitch mín sensor pelvis',        'min(Pelvis Pitch)',        '°'),
    ('IMU Pitch', 'Max-Min Pelvis',     'Rango pitch pelvis',             'max − min',               '°'),
    ('IMU Pitch', 'Max Object',         'Pitch máx sensor objeto',        'max(Object 1 Pitch)',      '°'),
    ('IMU Pitch', 'Min Pitch Object',   'Pitch mín sensor objeto',        'min(Object 1 Pitch)',      '°'),
    ('IMU Pitch', 'Max-Min Object',     'Rango pitch objeto',             'max − min',               '°'),

    # ── BCM POSICIÓN ─────────────────────────────────────────────────────
    ('BCM Posición', 'Max_Pos_BMC_X',          'Posición máxima BCM en X (AP)',                  'max(BCM_X) durante la fase',                               'mm'),
    ('BCM Posición', 'Min_Pos_BCM_X',          'Posición mínima BCM en X',                       'min(BCM_X) durante la fase',                               'mm'),
    ('BCM Posición', 'BCM_X_ Displacement',    'Desplazamiento total BCM en X',                  'max(BCM_X) − min(BCM_X)',                                  'mm'),
    ('BCM Posición', 'Time_Max_BCM_X',         'Timestamp del pico BCM en X',                    'time[idx donde BCM_X == max]',                             's'),
    ('BCM Posición', 'DisplBCMY_to_Max_BCM_X', 'Desplazamiento Z del BCM en el momento del pico X', 'BCM_Z[idx_maxX] − BCM_Z[inicio_fase]',                'mm'),
    ('BCM Posición', '% Desp_BCM_Z_vs_Max',    '% desplazamiento vertical BCM vs. máximo global','(BCM_Z[fin]−BCM_Z[ini]) / (max_global/1000) × 100',        '%'),
    ('BCM Posición', '% Desp_Hip_Z_vs_Max',    '% desplazamiento vertical cadera vs. máx global','(Hip_Z[fin]−Hip_Z[ini]) / (max_global/1000) × 100',        '%'),
    ('BCM Posición', '%Desp_Hip_Y_VS_Alcazar', '% desplazamiento cadera Z vs. Disp_Alcazar',     '(Hip_Z[fin]−Hip_Z[ini]) / 1000 / Disp_Alcazar × 100',     '%'),

    # ── CoP ──────────────────────────────────────────────────────────────
    ('CoP', 'CoP_Acc Displ_AP',     'Desplazamiento acumulado CoP AP',          'sum(CoP_Disp_X) durante la fase',   'mm'),
    ('CoP', 'CoP_Acc Displ_ML',     'Desplazamiento acumulado CoP ML',          'sum(CoP_Disp_Y) durante la fase',   'mm'),
    ('CoP', 'CoP_Acc Displ_Result', 'Desplazamiento acumulado CoP resultante',  'sum(CoP_Disp_XY) durante la fase',  'mm'),
    ('CoP', 'CoP_SD Displ_AP',      'SD desplazamiento CoP AP',                 'std(CoP_Disp_X) durante la fase',   'mm'),
    ('CoP', 'CoP_SD Displ_ML',      'SD desplazamiento CoP ML',                 'std(CoP_Disp_Y) durante la fase',   'mm'),
    ('CoP', 'CoP_SD Displ_Result',  'SD desplazamiento CoP resultante',         'std(CoP_Disp_XY) durante la fase',  'mm'),

    # ── ALCÁZAR ──────────────────────────────────────────────────────────
    ('Alcázar', 'Force_Alcazar',      'Fuerza estimada (Alcázar)',           '0.90 × peso_kg × 9.80',              'N'),
    ('Alcázar', 'Disp_Alcazar',       'Desplazamiento estimado (Alcázar)',   'altura × 0.5 − altura_silla',        'm'),
    ('Alcázar', 'Veloc_Alcazar',      'Velocidad media estimada (Alcázar)',  'Disp_Alcazar / Tiempo_fase',          'm/s'),
    ('Alcázar', 'Mean Power_Alcazar', 'Potencia media estimada (Alcázar)',   'Force_Alcazar × Veloc_Alcazar',       'W'),

    # ── COMPLETITUD ──────────────────────────────────────────────────────
    ('Completitud', 'Completa', 'Rep. considerada biomecánicamente completa',
     '1 si |BCM_Z_fin−BCM_Z_ini| >= 85% del max de esa fase; 0 si no', '0/1'),

    # ── EMG ──────────────────────────────────────────────────────────────
    ('EMG', 'RT TIB.ANT. (%)',    'Tibial anterior RT — media fase',          'mean(col) durante la fase', '% MVC'),
    ('EMG', 'RT VLO (%)',         'Vasto lateral RT — media fase',            'mean(col) durante la fase', '% MVC'),
    ('EMG', 'RT RECTUS FEM. (%)', 'Recto femoral RT — media fase',            'mean(col) durante la fase', '% MVC'),
    ('EMG', 'RT MED. GASTRO (%)', 'Gastrocnemio medial RT — media fase',      'mean(col) durante la fase', '% MVC'),
    ('EMG', 'RT SEMITEND. (%)',   'Semitendinoso RT — media fase',            'mean(col) durante la fase', '% MVC'),
    ('EMG', 'RT GLUT. MAX. (%)',  'Glúteo máximo RT — media fase',            'mean(col) durante la fase', '% MVC'),
    ('EMG', 'RT LUMBAR ES (%)',   'Erector espinal lumbar RT — media fase',   'mean(col) durante la fase', '% MVC'),

    # ── FUERZAS PLATAFORMA ───────────────────────────────────────────────
    ('Fuerzas FP', 'Vert F_Mean',            'Fuerza vertical media',                       'mean(Force Plates_Z)',                                       'N'),
    ('Fuerzas FP', 'Vert F_Max',             'Fuerza vertical máxima',                      'max(Force Plates_Z)',                                        'N'),
    ('Fuerzas FP', 'Time to Vert F_Max',     'Tiempo desde inicio hasta pico Fz',           'time[idx_max_Fz] − Inicio_Tiempo',                           's'),
    ('Fuerzas FP', 'Time to Vert F_Max_%',   'Tiempo al pico Fz (% fase)',                  '(time[idx_max_Fz] − Inicio_Tiempo) / Tiempo_fase × 100',    '%'),
    ('Fuerzas FP', 'Horizon F_Mean',         'Fuerza horizontal media',                     'mean(Force Plates_X)',                                       'N'),
    ('Fuerzas FP', 'Horizon F_Max',          'Fuerza horizontal máxima',                    'max(Force Plates_X)',                                        'N'),
    ('Fuerzas FP', 'Time to Horizon F_Max',  'Tiempo desde inicio hasta pico Fx',           'time[idx_max_Fx] − Inicio_Tiempo',                           's'),
    ('Fuerzas FP', 'Time to Horizon F_Max_%','Tiempo al pico Fx (% fase)',                  '(time[idx_max_Fx] − Inicio_Tiempo) / Tiempo_fase × 100',    '%'),
    ('Fuerzas FP', 'Result F_Mean',          'Fuerza resultante media',                     'mean(Force Plates_Resultante)',                              'N'),
    ('Fuerzas FP', 'Result F_Max',           'Fuerza resultante máxima',                    'max(Force Plates_Resultante)',                               'N'),
    ('Fuerzas FP', 'Time to Result F_Max',   'Tiempo desde inicio hasta pico Fresult',      'time[idx_max_Fres] − Inicio_Tiempo',                         's'),
    ('Fuerzas FP', 'Time to Result F_Max_%', 'Tiempo al pico Fresult (% fase)',             '(time[idx_max_Fres] − Inicio_Tiempo) / Tiempo_fase × 100',  '%'),

    # ── SEGMENTOS — Desplazamiento ────────────────────────────────────────
    ('Segmentos - Disp', 'Displac_[Seg]_X',  'Desplazamiento neto X',  'col_disp_X[fin] − col_disp_X[ini]  (acumulada)', 'mm'),
    ('Segmentos - Disp', 'Displac_[Seg]_Z',  'Desplazamiento neto Z',  'col_disp_Z[fin] − col_disp_Z[ini]  (acumulada)', 'mm'),
    ('Segmentos - Disp', 'Displac_[Seg]_XZ', 'Desplazamiento neto XZ', 'col_disp_XZ[fin] − col_disp_XZ[ini] (acumulada)','mm'),

    # ── SEGMENTOS — Velocidad ─────────────────────────────────────────────
    ('Segmentos - Vel', 'Veloc_[Seg]_X',    'Velocidad media X',          'mean(Vel_[Seg]_X)',    'mm/s'),
    ('Segmentos - Vel', 'Veloc_[Seg]_Z',    'Velocidad media Z',          'mean(Vel_[Seg]_Z)',    'mm/s'),
    ('Segmentos - Vel', 'Veloc_[Seg]_XZ',   'Velocidad media resultante', 'mean(Vel_[Seg]_XZ)',   'mm/s'),
    ('Segmentos - Vel', 'Veloc_[Seg]_X.1',  'Velocidad máxima abs. X',    'max(|Vel_[Seg]_X|)',   'mm/s'),
    ('Segmentos - Vel', 'Veloc_[Seg]_Z.1',  'Velocidad máxima abs. Z',    'max(|Vel_[Seg]_Z|)',   'mm/s'),
    ('Segmentos - Vel', 'Veloc_[Seg]_XZ.1', 'Velocidad máxima abs. XZ',   'max(|Vel_[Seg]_XZ|)', 'mm/s'),

    # ── SEGMENTOS — Potencia estimada ─────────────────────────────────────
    ('Segmentos - Pow E', 'Mean Power_[Seg]_X',  'Potencia media estimada X',  'mean(Power_Estimated_[Seg]_X)',  'W'),
    ('Segmentos - Pow E', 'Mean Power_[Seg]_Z',  'Potencia media estimada Z',  'mean(Power_Estimated_[Seg]_Z)',  'W'),
    ('Segmentos - Pow E', 'Mean Power_[Seg]_XZ', 'Potencia media estimada XZ', 'mean(Power_Estimated_[Seg]_XZ)','W'),
    ('Segmentos - Pow E', 'Max Power_[Seg]_X',   'Potencia máxima estimada X', 'max(Power_Estimated_[Seg]_X)',   'W'),
    ('Segmentos - Pow E', 'Max Power_[Seg]_Y',   'Potencia máxima estimada Z', 'max(Power_Estimated_[Seg]_Z)',   'W'),
    ('Segmentos - Pow E', 'Max Power_[Seg]_XY',  'Potencia máxima estimada XZ','max(Power_Estimated_[Seg]_XZ)', 'W'),

    # ── SEGMENTOS — Trabajo mecánico estimado ─────────────────────────────
    ('Segmentos - Work E', 'Mech Work_[Seg]_X',  'Trabajo mecánico estimado X',  'col_work_E_X[fin]  − col_work_E_X[ini]  (acumulada)', 'J'),
    ('Segmentos - Work E', 'Mech Work_[Seg]_Z',  'Trabajo mecánico estimado Z',  'col_work_E_Z[fin]  − col_work_E_Z[ini]  (acumulada)', 'J'),
    ('Segmentos - Work E', 'Mech Work_[Seg]_XZ', 'Trabajo mecánico estimado XZ', 'col_work_E_XZ[fin] − col_work_E_XZ[ini] (acumulada)', 'J'),

    # ── SEGMENTOS — Potencia con plataforma de fuerzas ────────────────────
    ('Segmentos - Pow FP', 'Mean Power_[Seg]_X.1',  'Potencia media con FP en X',  'mean(Power_[Seg]*Force Platform_X)',  'W'),
    ('Segmentos - Pow FP', 'Mean Power_[Seg]_Z.1',  'Potencia media con FP en Z',  'mean(Power_[Seg]*Force Platform_Z)',  'W'),
    ('Segmentos - Pow FP', 'Mean Power_[Seg]_XZ.1', 'Potencia media con FP en XZ', 'mean(Power_[Seg]*Force Platform_XZ)','W'),
    ('Segmentos - Pow FP', 'Max Power_[Seg]_X.1',   'Potencia máxima con FP en X', 'max(Power_[Seg]*Force Platform_X)',   'W'),
    ('Segmentos - Pow FP', 'Max Power_[Seg]_Z.1',   'Potencia máxima con FP en Z', 'max(Power_[Seg]*Force Platform_Z)',   'W'),
    ('Segmentos - Pow FP', 'Max Power_[Seg]_XZ.1',  'Potencia máxima con FP en XZ','max(Power_[Seg]*Force Platform_XZ)', 'W'),

    # ── SEGMENTOS — Trabajo mecánico con plataforma de fuerzas ───────────
    ('Segmentos - Work FP', 'Mech Work_[Seg]_X.1',  'Trabajo mecánico con FP en X',  'col_work_FP_X[fin]  − col_work_FP_X[ini]  (acumulada)', 'J'),
    ('Segmentos - Work FP', 'Mech Work_[Seg]_Z.1',  'Trabajo mecánico con FP en Z',  'col_work_FP_Z[fin]  − col_work_FP_Z[ini]  (acumulada)', 'J'),
    ('Segmentos - Work FP', 'Mech Work_[Seg]_XZ.1', 'Trabajo mecánico con FP en XZ', 'col_work_FP_XZ[fin] − col_work_FP_XZ[ini] (acumulada)', 'J'),
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

FP_FORCE = {
    'Vert':    'Force Plates_Z',
    'Horizon': 'Force Plates_X',
    'Result':  'Force Plates_Resultante',
}

BCM_Z = 'Noraxon MyoMotion-Trajectories-Body center of mass-z (mm)'
BCM_X = 'Noraxon MyoMotion-Trajectories-Body center of mass-x (mm)'
HIP_Z = 'Noraxon MyoMotion-Trajectories-Hip RT-z (mm)'

SEG_MAP = {
    'Shoulder': {
        'disp':    ('Disp_Shoulder_X',   'Disp_Shoulder_Z',   'Disp_Shoulder_XZ'),
        'vel':     ('Vel_Shoulder_X',    'Vel_Shoulder_Z',    'Vel_Shoulder_XZ'),
        'pow_e':   ('Power_Estimated_Shoulder_X',     'Power_Estimated_Shoulder_Z',     'Power_Estimated_Shoulder_XZ'),
        'work_e':  ('Mech Work_Estimated_Shoulder_X', 'Mech Work_Estimated_Shoulder_Z', 'Mech Work_Estimated_Shoulder_XZ'),
        'pow_fp':  ('Power_Shoulder*Force Platform_X',     'Power_Shoulder*Force Platform_Z',     'Power_Shoulder*Force Platform_XZ'),
        'work_fp': ('Mech Work_Shoulder*Force Platform_X', 'Mech Work_Shoulder*Force Platform_Z', 'Mech Work_Shoulder*Force Platform_XZ'),
    },
    'Pelvis': {
        'disp':    ('Disp_Pelvis_X',   'Disp_Pelvis_Z',   'Disp_Pelvis_XZ'),
        'vel':     ('Vel_Pelvis_X',    'Vel_Pelvis_Z',    'Vel_Pelvis_XZ'),
        'pow_e':   ('Power_Estimated_Pelvis_X',     'Power_Estimated_Pelvis_Z',     'Power_Estimated_Pelvis_XZ'),
        'work_e':  ('Mech Work_Estimated_Pelvis_X', 'Mech Work_Estimated_Pelvis_Z', 'Mech Work_Estimated_Pelvis_XZ'),
        'pow_fp':  ('Power_Pelvis*Force Platform_X',     'Power_Pelvis*Force Platform_Z',     'Power_Pelvis*Force Platform_XZ'),
        'work_fp': ('Mech Work_Pelvis*Force Platform_X', 'Mech Work_Pelvis*Force Platform_Z', 'Mech Work_Pelvis*Force Platform_XZ'),
    },
    'Hip': {
        'disp':    ('Disp_Hip_X',   'Disp_Hip_Z',   'Disp_Hip_XZ'),
        'vel':     ('Vel_Hip_X',    'Vel_Hip_Z',    'Vel_Hip_XZ'),
        'pow_e':   ('Power_Estimated_Hip_X',     'Power_Estimated_Hip_Z',     'Power_Estimated_Hip_XZ'),
        'work_e':  ('Mech Work_Estimated_Hip_X', 'Mech Work_Estimated_Hip_Z', 'Mech Work_Estimated_Hip_XZ'),
        'pow_fp':  ('Power_Hip*Force Platform_X',     'Power_Hip*Force Platform_Z',     'Power_Hip*Force Platform_XZ'),
        'work_fp': ('Mech Work_Hip*Force Platform_X', 'Mech Work_Hip*Force Platform_Z', 'Mech Work_Hip*Force Platform_XZ'),
    },
    'BMC': {
        'disp':    ('Disp_BCM_X',   'Disp_BCM_Z',   'Disp_BCM_XZ'),
        'vel':     ('Vel_BCM_X',    'Vel_BCM_Z',    'Vel_BCM_XZ'),
        'pow_e':   ('Power_Estimated Center of Mass_X',     'Power_Estimated Center of Mass_Z',     'Power_Estimated Center of Mass_XZ'),
        'work_e':  ('Mech Work_Estimated_BCM_X', 'Mech Work_Estimated_BCM_Z', 'Mech Work_Estimated_BCM_XZ'),
        'pow_fp':  ('Power_COM*Force Platform_X',     'Power_COM*Force Platform_Z',     'Power_COM*Force Platform_XZ'),
        'work_fp': ('Mech Work_BCM*Force Platform_X', 'Mech Work_BCM*Force Platform_Z', 'Mech Work_BCM*Force Platform_XZ'),
    },
}


# ═══════════════════════════════════════════════════════════════════════════
#  UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════

def _get(seg, col):
    """Devuelve la serie si la columna existe y tiene al menos un dato, sino None."""
    return seg[col] if (col in seg.columns and seg[col].notna().any()) else None


# ═══════════════════════════════════════════════════════════════════════════
#  CARGA DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

print(f"\n{'='*65}")
print(f"  STS Analysis Tool")
print(f"  Archivo : {FILE.name}")
print(f"  Fecha   : {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}")
print(f"{'='*65}\n")

xl      = pd.ExcelFile(FILE)
df_gen  = pd.read_excel(xl, 'General',               header=0)
df_meta = pd.read_excel(xl, 'MetaData_&_Parameters', header=None, index_col=0)

print(f"[OK] General cargado: {len(df_gen)} frames x {len(df_gen.columns)} columnas")


# ═══════════════════════════════════════════════════════════════════════════
#  EXTRACCIÓN DE METADATA
# ═══════════════════════════════════════════════════════════════════════════

codigo     = df_meta.loc['Código', 1]
altura     = float(df_meta.loc['Altura', 1])
peso       = float(df_meta.loc['Peso', 1])
alt_silla  = float(df_meta.loc['Altura de la silla', 1])
test_name  = df_meta.loc['Nombre Test', 1]
fecha_test = df_meta.loc['Fecha del test', 1]

FORCE_ALZ = round(ALZ_FACTOR * peso * G, 6)
DISP_ALZ  = round(altura * 0.5 - alt_silla, 6)

print(f"[OK] Participante  : {codigo}")
print(f"     Altura        : {altura} m")
print(f"     Peso          : {peso} kg")
print(f"     Silla         : {alt_silla} m")
print(f"     Force_Alcazar : {FORCE_ALZ:.4f} N   (0.9 x {peso} x {G})")
print(f"     Disp_Alcazar  : {DISP_ALZ:.4f} m   ({altura}x0.5 - {alt_silla})\n")


# ═══════════════════════════════════════════════════════════════════════════
#  DETECCIÓN DE FASES (desde marcadores Excel)
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════
# SEGMENTACIÓN AUTOMÁTICA DE FASES STS
# ═══════════════════════════════════════════════════════════════════

vel = df_gen['Vel_BCM_Z'].values
pos = df_gen[BCM_Z].values

cs_idx = []
ce_idx = []
ee_idx = []

i = WINDOW

while i < len(df_gen) - WINDOW:

    # -------------------------------------------------
    # DETECTAR INICIO CONCÉNTRICA
    # -------------------------------------------------

    if vel[i] > VEL_THRESH_POS:

        future_pos = pos[i:i+WINDOW]

        cond1 = np.all(np.diff(future_pos) > 0)

        if cond1:

            cs_idx.append(i)

            # -------------------------------------------------
            # DETECTAR TRANSICIÓN (MÁXIMO BCM_Z)
            # -------------------------------------------------

            search = pos[i:i+400]

            if len(search) == 0:
                break

            local_max = np.argmax(search)

            ce = i + local_max
            ce_idx.append(ce)

            # -------------------------------------------------
            # DETECTAR INICIO EXCÉNTRICA
            # -------------------------------------------------

            j = ce + WINDOW

            while j < len(df_gen) - WINDOW:

                if vel[j] < VEL_THRESH_NEG:

                    past_pos = pos[j-WINDOW:j]

                    cond2 = np.all(np.diff(past_pos) < 0)

                    if cond2:

                        ee_idx.append(j)

                        i = j + WINDOW
                        break

                j += 1

        else:
            i += 1

    else:
        i += 1


# -------------------------------------------------
# CONSTRUIR FASES
# -------------------------------------------------

n_reps = min(len(cs_idx), len(ce_idx), len(ee_idx))

phase_bounds = []

for k in range(n_reps):

    se = cs_idx[k+1] - 1 if k+1 < n_reps else len(df_gen)-1

    phase_bounds.append({
        'rep': k+1,
        'conc':   (cs_idx[k], ce_idx[k]),
        'ecc':    (ce_idx[k], ee_idx[k]),
        'seated': (ee_idx[k], se)
    })


print(f"[OK] Segmentación automática:")
print(f"     Conc start detectados: {len(cs_idx)}")
print(f"     Transiciones conc-ecc: {len(ce_idx)}")
print(f"     Inicios excéntrica:   {len(ee_idx)}")
print(f"     Repeticiones válidas: {n_reps}")

# ═══════════════════════════════════════════════════════════════════════════
#  GRÁFICA DE SEGMENTACIÓN
# ═══════════════════════════════════════════════════════════════════════════

def build_segmentation_figure(df, pb_list):
    """
    Genera figura con 2 subplots:
      Superior : BCM_Z — posición vertical del centro de masa corporal (mm)
      Inferior : Vel_BCM_Z — velocidad vertical del BCM (m/s)
    Sombreado por fase: azul=concéntrica, rojo=excéntrica, gris=sentado.
    Líneas discontinuas en cada transición. Número de rep sobre cada conc.
    """
    time      = df['time'].values
    bcm_z_arr = df[BCM_Z].values       if BCM_Z       in df.columns else np.full(len(df), np.nan)
    vel_arr   = df['Vel_BCM_Z'].values if 'Vel_BCM_Z' in df.columns else np.full(len(df), np.nan)

    t0   = df.loc[pb_list[0]['conc'][0],   'time'] - 0.3
    t1   = df.loc[pb_list[-1]['seated'][1],'time'] + 0.3
    mask = (time >= t0) & (time <= t1)
    t_c  = time[mask];  bcm_c = bcm_z_arr[mask];  vel_c = vel_arr[mask]

    COL = {'conc': '#3b82f6', 'ecc': '#ef4444', 'seated': '#94a3b8'}

    fig, axes = plt.subplots(2, 1, figsize=(16, 7), sharex=True, facecolor='#f8fafc')
    fig.suptitle(
        f'Segmentación de fases STS  —  {codigo}  |  {test_name}  |  {fecha_test}',
        fontsize=12, fontweight='bold', color='#1e293b', y=0.99
    )

    for ax, data, ylabel, line_col in [
        (axes[0], bcm_c, 'Posición BCM vertical (mm)',  '#1d4ed8'),
        (axes[1], vel_c, 'Velocidad BCM vertical (m/s)','#b91c1c'),
    ]:
        ax.set_facecolor('#f1f5f9')
        ax.grid(True, alpha=0.45, color='white', linewidth=1.2)
        ax.spines[['top', 'right']].set_visible(False)
        ax.set_ylabel(ylabel, fontsize=10, color='#374151', labelpad=8)
        ax.tick_params(colors='#374151', labelsize=9)

        for pb in pb_list:
            for fk, fc in COL.items():
                s_i, e_i = pb[fk]
                ax.axvspan(df.loc[s_i,'time'], df.loc[e_i,'time'],
                           alpha=0.20, color=fc, linewidth=0)

        ax.plot(t_c, data, color=line_col, linewidth=1.3, zorder=5)

        for pb in pb_list:
            for idx in [pb['conc'][0], pb['conc'][1], pb['ecc'][1]]:
                ax.axvline(df.loc[idx,'time'], color='#64748b',
                           linewidth=0.75, linestyle='--', alpha=0.7, zorder=4)

        if ax is axes[0] and not np.all(np.isnan(data)):
            y_rng = np.nanmax(data) - np.nanmin(data)
            y_top = np.nanmax(data) + y_rng * 0.04
            for pb in pb_list:
                t_mid = (df.loc[pb['conc'][0],'time'] + df.loc[pb['conc'][1],'time']) / 2
                ax.text(t_mid, y_top, str(pb['rep']),
                        ha='center', va='bottom', fontsize=7.5,
                        color='#1e40af', fontweight='bold')

    axes[1].set_xlabel('Tiempo (s)', fontsize=10, color='#374151', labelpad=6)

    legend_elems = [
        mpatches.Patch(facecolor='#3b82f6', alpha=0.4, label='Concéntrica'),
        mpatches.Patch(facecolor='#ef4444', alpha=0.4, label='Excéntrica'),
        mpatches.Patch(facecolor='#94a3b8', alpha=0.4, label='Sentado'),
        Line2D([0],[0], color='#64748b', linestyle='--', linewidth=0.9, label='Transición'),
    ]
    fig.legend(handles=legend_elems, loc='lower center', ncol=4,
               fontsize=9, framealpha=0.9, bbox_to_anchor=(0.5, 0.005))
    plt.tight_layout(rect=[0, 0.05, 1, 0.975])
    return fig


# ═══════════════════════════════════════════════════════════════════════════
#  CÁLCULO POR FASE
# ═══════════════════════════════════════════════════════════════════════════

def phase_stats(df, s, e, fase, rep):
    """Calcula todas las variables biomecánicas para un intervalo de fase."""
    seg = df.iloc[s:e + 1]
    r   = {}

    r.update({
        'Código': codigo, 'Altura': altura, 'Peso_kg': peso,
        'Altura de la silla': alt_silla, 'Test': test_name,
        'Fecha Test': fecha_test, 'Repeticion': rep, 'Fase': fase,
    })

    r['Inicio_Tiempo'] = round(seg['time'].iloc[0],  3)
    r['Final_Tiempo']  = round(seg['time'].iloc[-1], 3)
    dt                 = round(r['Final_Tiempo'] - r['Inicio_Tiempo'], 3)
    r['Tiempo fase']   = dt

    # Trayectorias — posición media durante la fase
    for cx, cz in TRAJ_PAIRS:
        r[cx] = seg[cx].mean() if cx in seg.columns else np.nan
        r[cz] = seg[cz].mean() if cz in seg.columns else np.nan

    # Ángulos — media, max, min, rango de movimiento
    for key, col in ANGLE_COLS.items():
        v = _get(seg, col)
        r[col] = v.mean() if v is not None else np.nan
        if key in ('Toracico', 'Lumbar', 'Torso-Pelvis', 'Hip'):
            r[f'Max º {key}']    = v.max()         if v is not None else np.nan
            r[f'Minº {key}']     = v.min()         if v is not None else np.nan
            r[f'Max-Min_º{key}'] = v.max()-v.min() if v is not None else np.nan

    # Hip Swing — diferencial desde el inicio de fase
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

    # IMU Pitch — max, min, rango
    for key, col in PITCH_COLS.items():
        v = _get(seg, col)
        r[f'Max {key}']       = v.max()         if v is not None else np.nan
        r[f'Min Pitch {key}'] = v.min()         if v is not None else np.nan
        r[f'Max-Min {key}']   = v.max()-v.min() if v is not None else np.nan

    # BCM X — posición, desplazamiento, tiempo al pico
    bx = _get(seg, BCM_X)
    bz = _get(seg, BCM_Z)
    if bx is not None:
        i_max = bx.idxmax()
        r['Max_Pos_BMC_X']          = bx.max()
        r['Min_Pos_BCM_X']          = bx.min()
        r['BCM_X_ Displacement']    = bx.max() - bx.min()
        r['Time_Max_BCM_X']         = df.loc[i_max, 'time']
        r['DisplBCMY_to_Max_BCM_X'] = seg.loc[i_max, BCM_Z] - seg[BCM_Z].iloc[0] if bz is not None else np.nan
    else:
        for k in ('Max_Pos_BMC_X','Min_Pos_BCM_X','BCM_X_ Displacement',
                  'Time_Max_BCM_X','DisplBCMY_to_Max_BCM_X'):
            r[k] = np.nan

    # CoP — desplazamiento acumulado y desviación estándar
    ap  = _get(seg, 'CoP_Disp_X')
    ml  = _get(seg, 'CoP_Disp_Y')
    res = _get(seg, 'CoP_Disp_XY')
    r['CoP_Acc Displ_AP']     = ap.sum()  if ap  is not None else np.nan
    r['CoP_Acc Displ_ML']     = ml.sum()  if ml  is not None else np.nan
    r['CoP_Acc Displ_Result'] = res.sum() if res is not None else np.nan
    r['CoP_SD Displ_AP']      = ap.std()  if ap  is not None else np.nan
    r['CoP_SD Displ_ML']      = ml.std()  if ml  is not None else np.nan
    r['CoP_SD Displ_Result']  = res.std() if res is not None else np.nan

    # Método Alcázar
    r['Force_Alcazar']      = FORCE_ALZ
    r['Disp_Alcazar']       = DISP_ALZ
    r['Veloc_Alcazar']      = DISP_ALZ / dt        if dt > 0 else np.nan
    r['Mean Power_Alcazar'] = FORCE_ALZ * r['Veloc_Alcazar']

    # % desplazamientos relativos
    if bz is not None:
        d = seg[BCM_Z].iloc[-1] - seg[BCM_Z].iloc[0]
        r['% Desp_BCM_Z_vs_Max'] = (d / (df[BCM_Z].max() / 1000)) * 100
    else:
        r['% Desp_BCM_Z_vs_Max'] = np.nan

    hz = _get(seg, HIP_Z)
    if hz is not None:
        dh = seg[HIP_Z].iloc[-1] - seg[HIP_Z].iloc[0]
        r['% Desp_Hip_Z_vs_Max']    = (dh / (df[HIP_Z].max() / 1000)) * 100
        r['%Desp_Hip_Y_VS_Alcazar'] = (dh / 1000 / DISP_ALZ) * 100
    else:
        r['% Desp_Hip_Z_vs_Max'] = r['%Desp_Hip_Y_VS_Alcazar'] = np.nan

    # Completitud — placeholder (se calcula en post-proceso)
    r['_bcm_z_raw'] = abs(seg[BCM_Z].iloc[-1] - seg[BCM_Z].iloc[0]) if bz is not None else np.nan
    r['Completa']   = np.nan

    # EMG — activación media durante la fase
    for col in EMG_COLS:
        v = _get(seg, col)
        r[col] = v.mean() if v is not None else np.nan

    # Fuerzas plataforma — media, máximo, tiempo al pico (absoluto y % fase)
    for label, col in FP_FORCE.items():
        v = _get(seg, col)
        if v is not None:
            r[f'{label} F_Mean']          = v.mean()
            r[f'{label} F_Max']           = v.max()
            t_pk                           = df.loc[v.idxmax(), 'time'] - r['Inicio_Tiempo']
            r[f'Time to {label} F_Max']   = round(t_pk, 3)
            r[f'Time to {label} F_Max_%'] = round(t_pk / dt * 100, 2) if dt > 0 else np.nan
        else:
            r[f'{label} F_Mean'] = r[f'{label} F_Max'] = np.nan
            r[f'Time to {label} F_Max'] = r[f'Time to {label} F_Max_%'] = np.nan

    # Segmentos biomecánicos: Shoulder, Pelvis, Hip, BMC
    for sn, cm in SEG_MAP.items():

        # Desplazamiento neto (columna acumulada: fin − inicio)
        for ax_, col in zip(('X','Z','XZ'), cm['disp']):
            v = _get(seg, col)
            r[f'Displac_{sn}_{ax_}'] = v.iloc[-1] - v.iloc[0] if v is not None else np.nan

        # Velocidad media y máxima absoluta
        for ax_, col in zip(('X','Z','XZ'), cm['vel']):
            v = _get(seg, col)
            r[f'Veloc_{sn}_{ax_}']   = v.mean()      if v is not None else np.nan
            r[f'Veloc_{sn}_{ax_}.1'] = v.abs().max() if v is not None else np.nan

        # Potencia media y máxima — estimada
        for ax_, col in zip(('X','Z','XZ'), cm['pow_e']):
            v = _get(seg, col)
            r[f'Mean Power_{sn}_{ax_}'] = v.mean() if v is not None else np.nan
            r[f'Max Power_{sn}_{ax_}']  = v.max()  if v is not None else np.nan

        # Trabajo mecánico estimado (columna acumulada: fin − inicio)
        for ax_, col in zip(('X','Z','XZ'), cm['work_e']):
            v = _get(seg, col)
            r[f'Mech Work_{sn}_{ax_}'] = v.iloc[-1] - v.iloc[0] if v is not None else np.nan

        # Potencia media y máxima — con plataforma de fuerzas
        for ax_, col in zip(('X','Z','XZ'), cm['pow_fp']):
            v = _get(seg, col)
            r[f'Mean Power_{sn}_{ax_}.1'] = v.mean() if v is not None else np.nan
            r[f'Max Power_{sn}_{ax_}.1']  = v.max()  if v is not None else np.nan

        # Trabajo mecánico con plataforma de fuerzas (columna acumulada: fin − inicio)
        for ax_, col in zip(('X','Z','XZ'), cm['work_fp']):
            v = _get(seg, col)
            r[f'Mech Work_{sn}_{ax_}.1'] = v.iloc[-1] - v.iloc[0] if v is not None else np.nan

    return r


# ═══════════════════════════════════════════════════════════════════════════
#  PROCESADO PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

FASES = [('conc','Concéntrica'), ('ecc','Excéntrica'), ('seated','Sentado')]

rows_out = []
for pb in phase_bounds:
    for fk, fl in FASES:
        s, e = pb[fk]
        rows_out.append(phase_stats(df_gen, s, e, fl, pb['rep']))

df_out = pd.DataFrame(rows_out)
print(f"[OK] Calculos completados: {len(df_out)} filas x {len(df_out.columns)} columnas")

# Post-proceso: columna Completa
# 1 si |BCM_Z_desplazamiento| >= 85% del máximo en ese tipo de fase
for fl in ('Concéntrica', 'Excéntrica', 'Sentado'):
    mask  = df_out['Fase'] == fl
    max_d = df_out.loc[mask, '_bcm_z_raw'].max()
    if pd.notna(max_d) and max_d > 0:
        df_out.loc[mask, 'Completa'] = (
            df_out.loc[mask, '_bcm_z_raw'] / max_d >= BCM_THRESH).astype(int)

df_out.drop(columns=['_bcm_z_raw'], inplace=True)
n_completas = int(df_out.loc[df_out['Fase'] == 'Concéntrica', 'Completa'].sum())
print(f"     Reps completas (conc.): {n_completas} / {n_reps}")


# ═══════════════════════════════════════════════════════════════════════════
#  GENERAR GRÁFICA
# ═══════════════════════════════════════════════════════════════════════════

print("[..] Generando grafica de segmentacion...")
fig_seg = build_segmentation_figure(df_gen, phase_bounds)
img_buf = BytesIO()
fig_seg.savefig(img_buf, format='png', dpi=150, bbox_inches='tight', facecolor='#f8fafc')
plt.close(fig_seg)
img_buf.seek(0)
print("[OK] Grafica generada\n")


# ═══════════════════════════════════════════════════════════════════════════
#  EXPORTACIÓN EXCEL MULTI-HOJA
# ═══════════════════════════════════════════════════════════════════════════

out_path = FILE.parent / f"{FILE.stem}_results.xlsx"
print(f"[..] Exportando a {out_path.name} ...")

with pd.ExcelWriter(out_path, engine='xlsxwriter',
                    engine_kwargs={'options': {'nan_inf_to_errors': True}}) as writer:
    wb = writer.book

    # ── Formatos ──────────────────────────────────────────────────────────
    F = {
        'title':   wb.add_format({'bold':True, 'font_size':13, 'font_color':'#1e3a5f'}),
        'sub':     wb.add_format({'italic':True, 'font_color':'#6b7280', 'font_size':9}),
        'hdr':     wb.add_format({'bold':True, 'bg_color':'#1e3a5f', 'font_color':'white',
                                  'border':1, 'align':'center', 'valign':'vcenter', 'text_wrap':True}),
        'hdr2':    wb.add_format({'bold':True, 'bg_color':'#334155', 'font_color':'white',
                                  'border':1, 'align':'center', 'valign':'vcenter'}),
        'conc':    wb.add_format({'bg_color':'#dbeafe', 'border':1, 'num_format':'0.0000'}),
        'ecc':     wb.add_format({'bg_color':'#fee2e2', 'border':1, 'num_format':'0.0000'}),
        'seated':  wb.add_format({'bg_color':'#f1f5f9', 'border':1, 'num_format':'0.0000'}),
        'txt':     wb.add_format({'border':1}),
        'grp_a':   wb.add_format({'bold':True, 'bg_color':'#e0f2fe', 'border':1, 'font_color':'#0c4a6e'}),
        'grp_b':   wb.add_format({'bold':True, 'bg_color':'#f0fdf4', 'border':1, 'font_color':'#14532d'}),
        'key':     wb.add_format({'bold':True, 'bg_color':'#f8fafc', 'border':1}),
        'log_k':   wb.add_format({'bold':True, 'bg_color':'#fef9c3', 'border':1}),
        'log_v':   wb.add_format({'bg_color':'#fefce8', 'border':1}),
        'log_sec': wb.add_format({'bold':True, 'bg_color':'#1e3a5f', 'font_color':'white', 'border':1}),
    }

    # ── HOJA 1: KF_Results ────────────────────────────────────────────────
    df_out.to_excel(writer, sheet_name='KF_Results', index=False, startrow=2)
    ws = writer.sheets['KF_Results']
    ws.write(0, 0, f'STS Results — {codigo}  |  {test_name}  |  {fecha_test}', F['title'])
    ws.write(1, 0,
             f'Force_Alcazar={FORCE_ALZ:.4f} N  |  Disp_Alcazar={DISP_ALZ:.4f} m  |  '
             f'BCM_Umbral={int(BCM_THRESH*100)}%  |  Reps={n_reps}  |  '
             f'Generado: {datetime.now().strftime("%Y-%m-%d %H:%M")}', F['sub'])

    for ci, col in enumerate(df_out.columns):
        ws.write(2, ci, col, F['hdr'])

    for ri, row in df_out.iterrows():
        fase = row['Fase']
        fmt  = F['conc'] if fase == 'Concéntrica' else (F['ecc'] if fase == 'Excéntrica' else F['seated'])
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

    # ── HOJA 2: Segmentation_Plot ──────────────────────────────────────────
    ws2 = wb.add_worksheet('Segmentation_Plot')
    ws2.write(0, 0, f'Segmentación de fases STS — {codigo}  |  {test_name}', F['title'])
    ws2.write(1, 0,
              'Azul = Concéntrica  ·  Rojo = Excéntrica  ·  Gris = Sentado  '
              '·  Líneas discontinuas = transición entre fases', F['sub'])
    ws2.insert_image(3, 0, 'placeholder.png', {'image_data': img_buf, 'x_scale': 1.0, 'y_scale': 1.0})
    ws2.set_column(0, 0, 140)

    t_row = 34
    for ci, hdr in enumerate(['Rep','Fase','Inicio (s)','Fin (s)','Duración (s)','Completa']):
        ws2.write(t_row, ci, hdr, F['hdr2'])
    for ri, row in df_out[['Repeticion','Fase','Inicio_Tiempo','Final_Tiempo','Tiempo fase','Completa']].iterrows():
        fmt = F['conc'] if row['Fase']=='Concéntrica' else (F['ecc'] if row['Fase']=='Excéntrica' else F['seated'])
        for ci, val in enumerate(row):
            ws2.write(t_row + 1 + ri, ci, val, fmt)
    for ci in range(6):
        ws2.set_column(ci, ci, 16)

    # ── HOJA 3: Variable_Dictionary ───────────────────────────────────────
    df_dict = pd.DataFrame(VARIABLE_DICT,
                           columns=['Grupo','Variable','Descripción','Cálculo','Unidad'])
    ws3 = wb.add_worksheet('Variable_Dictionary')
    ws3.write(0, 0, 'Diccionario de Variables — STS Analysis Tool', F['title'])
    ws3.write(1, 0, f'{len(df_dict)} variables documentadas con descripción, fórmula y unidad', F['sub'])

    for ci, hdr in enumerate(['Grupo','Variable','Descripción','Cálculo','Unidad']):
        ws3.write(2, ci, hdr, F['hdr'])

    prev_grp = None; toggle = True
    for ri, row in df_dict.iterrows():
        if row['Grupo'] != prev_grp:
            toggle = not toggle
            prev_grp = row['Grupo']
        fg = F['grp_a'] if toggle else F['grp_b']
        ws3.write(ri+3, 0, row['Grupo'],      fg)
        ws3.write(ri+3, 1, row['Variable'],   F['key'])
        ws3.write(ri+3, 2, row['Descripción'],F['txt'])
        ws3.write(ri+3, 3, row['Cálculo'],    F['txt'])
        ws3.write(ri+3, 4, row['Unidad'],     F['txt'])

    ws3.set_column(0, 0, 20)
    ws3.set_column(1, 1, 38)
    ws3.set_column(2, 2, 48)
    ws3.set_column(3, 3, 52)
    ws3.set_column(4, 4, 12)
    ws3.set_row(2, 22)
    ws3.freeze_panes(3, 0)

    # ── HOJA 4: Processing_Log ────────────────────────────────────────────
    ws4 = wb.add_worksheet('Processing_Log')
    ws4.write(0, 0, 'Log de Procesamiento — STS Analysis Tool', F['title'])
    ws4.set_column(0, 0, 30)
    ws4.set_column(1, 1, 60)

    SECTIONS = {'IDENTIFICACIÓN','DATOS RAW','PARÁMETROS SUJETO',
                'MÉTODO ALCÁZAR','SEGMENTACIÓN','CRITERIO COMPLETA',
                'TRABAJO MECÁNICO','RESULTADO'}
    log = [
        ('IDENTIFICACIÓN',     ''),
        ('Código',             str(codigo)),
        ('Test',               str(test_name)),
        ('Fecha test',         str(fecha_test)),
        ('Procesado el',       datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('Archivo fuente',     FILE.name),
        ('',                   ''),
        ('DATOS RAW',          ''),
        ('Frames totales',     str(len(df_gen))),
        ('Frecuencia muestreo','100 Hz'),
        ('Columnas General',   str(len(df_gen.columns))),
        ('',                   ''),
        ('PARÁMETROS SUJETO',  ''),
        ('Altura',             f'{altura} m'),
        ('Peso',               f'{peso} kg'),
        ('Altura silla',       f'{alt_silla} m'),
        ('',                   ''),
        ('MÉTODO ALCÁZAR',     ''),
        ('g utilizada',        f'{G} m/s2'),
        ('Factor BW',          f'{ALZ_FACTOR}  (90%)'),
        ('Force_Alcazar',      f'{FORCE_ALZ:.6f} N   = 0.9 x {peso} x {G}'),
        ('Disp_Alcazar',       f'{DISP_ALZ:.6f} m    = {altura}x0.5 - {alt_silla}'),
        ('',                   ''),
        ('SEGMENTACIÓN',       ''),
        ('Marcador inicio',    'Conc Start == 10000'),
        ('Marcador transición','Conc-Exc == 10000'),
        ('Marcador fin exc',   'Ecc End == 10000'),
        ('Reps detectadas',    str(n_reps)),
        ('Total intervalos',   f'{n_reps*3}  ({n_reps} reps x 3 fases)'),
        ('',                   ''),
        ('CRITERIO COMPLETA',  ''),
        ('Umbral',             f'{int(BCM_THRESH*100)}% del desplazamiento BCM_Z maximo'),
        ('Métrica',            '|BCM_Z[fin] - BCM_Z[ini]| por fase'),
        ('Evaluación',         'Independiente por tipo de fase'),
        ('Reps completas',     f'{n_completas} / {n_reps}  (fase concentrica)'),
        ('',                   ''),
        ('TRABAJO MECÁNICO',   ''),
        ('Método',             'Diferencia acumulado: col[fin] - col[ini]'),
        ('Fuente',             'Mech Work_Estimated_* y Mech Work_*Force Platform_*'),
        ('',                   ''),
        ('RESULTADO',          ''),
        ('Filas generadas',    str(len(df_out))),
        ('Columnas generadas', str(len(df_out.columns))),
        ('Archivo salida',     str(out_path.name)),
    ]

    for ri, (k, v) in enumerate(log):
        if k in SECTIONS:
            ws4.write(ri+2, 0, k,  F['log_sec'])
            ws4.write(ri+2, 1, '', F['log_sec'])
        elif k == '':
            ws4.write(ri+2, 0, '', F['txt'])
            ws4.write(ri+2, 1, '', F['txt'])
        else:
            ws4.write(ri+2, 0, k, F['log_k'])
            ws4.write(ri+2, 1, v, F['log_v'])

print(f"[OK] Excel exportado correctamente")
print(f"     Hoja KF_Results          : {len(df_out)} filas x {len(df_out.columns)} cols")
print(f"     Hoja Segmentation_Plot   : grafica + tabla de tiempos")
print(f"     Hoja Variable_Dictionary : {len(VARIABLE_DICT)} variables documentadas")
print(f"     Hoja Processing_Log      : {len(log)} entradas")
print(f"\n{'='*65}")
print(f"  Analisis completado: {out_path.name}")
print(f"{'='*65}\n")
