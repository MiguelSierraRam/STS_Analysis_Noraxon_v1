import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from pathlib import Path
from datetime import datetime

def bio_sts_tool(input_csv, output_xlsx):
    print(f"--- Iniciando Procesamiento: {Path(input_csv).name} ---")
    
    # 1. CARGA DE DATOS (Hoja Reducido)
    df = pd.read_csv(input_csv)
    dt = df['time'].diff().median()
    
    # 2 & 3. CÁLCULOS FÍSICOS (CINEMÁTICA Y CINÉTICA)
    # Columna objetivo para el Centro de Masas (BCM)
    col_z = 'Noraxon MyoMotion-Trajectories-Pelvis-z (mm)'
    
    # Derivadas cinemáticas
    df['V_BCM_m_s'] = (df[col_z].diff() / dt) / 1000.0  # mm a m/s
    df['A_BCM_m_s2'] = df['V_BCM_m_s'].diff() / dt
    
    # Cinética de plataformas
    fz_cols = [c for c in df.columns if 'Fz (N)' in c]
    df['Fuerza_Vertical_Total_N'] = df[fz_cols].sum(axis=1)
    
    # Potencia y Trabajo
    df['Potencia_W'] = df['Fuerza_Vertical_Total_N'] * df['V_BCM_m_s']
    df['Trabajo_J_Acumulado'] = (df['Potencia_W'] * dt).fillna(0).cumsum()

    # 5. LÓGICA DE DETECCIÓN DE FASES (REGLA DE LAS 30 CELDAS)
    N = 30
    umbral_v = 0.1
    diff_z = df[col_z].diff()

    # Marcador Concéntrico: 30 celdas posteriores positivas
    # Usamos shift(-N) para que la ventana "mire al futuro"
    df['win_pos'] = (diff_z > 0).iloc[::-1].rolling(N).sum().iloc[::-1]
    # Marcador Excéntrico: 30 celdas anteriores negativas
    df['win_neg'] = (diff_z < 0).rolling(N).sum()

    reps = []
    estado = "BUSCANDO_CONCENTRICA"
    tmp_rep = {}
    contador_rep = 1

    print("Detectando fases...")
    for i in range(len(df)):
        v = df.at[i, 'V_BCM_m_s']
        
        # Inicio Concéntrica: Vector + durante 30 celdas y Vel > 0.1
        if estado == "BUSCANDO_CONCENTRICA":
            if df.at[i, 'win_pos'] == N and v > umbral_v:
                tmp_rep = {
                    'Rep': contador_rep,
                    'idx_ini_con': i,
                    't_ini_con': df.at[i, 'time']
                }
                estado = "BUSCANDO_TRANSICION"
        
        # Transición: Máximo desplazamiento Z antes de que la velocidad sea negativa
        elif estado == "BUSCANDO_TRANSICION":
            if v < 0:
                idx_max = df.loc[tmp_rep['idx_ini_con']:i, col_z].idxmax()
                tmp_rep['idx_trans'] = idx_max
                tmp_rep['t_trans'] = df.at[idx_max, 'time']
                estado = "BUSCANDO_EXCENTRICA"
                
        # Fin Excéntrica: Vector - durante 30 celdas y Vel < -0.1
        elif estado == "BUSCANDO_EXCENTRICA":
            if df.at[i, 'win_neg'] == N and v < -umbral_v:
                tmp_rep['idx_fin_exc'] = i
                tmp_rep['t_fin_exc'] = df.at[i, 'time']
                reps.append(tmp_rep.copy())
                contador_rep += 1
                estado = "BUSCANDO_CONCENTRICA"

    # 6 & 7. EXTRACCIÓN DE MÉTRICAS (BLOQUE DE 360+ COLUMNAS)
    # Seleccionamos todas las señales de interés del archivo original
    cols_analisis = [c for c in df.columns if any(x in c for x in ['(%)', '(N)', '(m/s)', '(W)', '(deg)'])]
    
    resumen_fases = []
    for r in reps:
        for fase_tipo in ['CONCENTRICA', 'EXCENTRICA']:
            idx_a = r['idx_ini_con'] if fase_tipo == 'CONCENTRICA' else r['idx_trans']
            idx_b = r['idx_trans'] if fase_tipo == 'CONCENTRICA' else r['idx_end_ecc' if 'idx_end_ecc' in r else 'idx_fin_exc']
            
            segmento = df.loc[idx_a:idx_b]
            
            # Fila de datos para esta fase
            fila = {
                'Repeticion': r['Rep'],
                'Fase': fase_tipo,
                'T_Inicio': df.at[idx_a, 'time'],
                'T_Final': df.at[idx_b, 'time'],
                'Duracion_s': df.at[idx_b, 'time'] - df.at[idx_a, 'time'],
                'Trabajo_Mecanico_Fase_J': (segmento['Potencia_W'] * dt).sum()
            }
            
            # Cálculo masivo de Max, Media, Min para cada señal
            for col in cols_analisis:
                fila[f'{col}_Max'] = segmento[col].max()
                fila[f'{col}_Mean'] = segmento[col].mean()
                fila[f'{col}_Min'] = segmento[col].min()
                fila[f'{col}_CV'] = (segmento[col].std() / segmento[col].mean()) * 100 if segmento[col].mean() != 0 else 0
            
            resumen_fases.append(fila)

    df_out = pd.DataFrame(resumen_fases)

    # EXPORTACIÓN
    with pd.ExcelWriter(output_xlsx, engine='xlsxwriter') as writer:
        # HOJA 1: Datos Procesados (Raw + Física)
        df.drop(columns=['win_pos', 'win_neg']).to_excel(writer, sheet_name='PASO_1_PROCESADOS', index=False)
        
        # HOJA 2: Análisis por fase (Resultados para SPSS/R)
        df_out.to_excel(writer, sheet_name='PASO_2_ANALISIS', index=False)
        
        # HOJA 3: Log
        pd.DataFrame({
            'Metrica': ['Fecha', 'Reps Detectadas', 'Frecuencia Muestreo'],
            'Valor': [datetime.now().strftime("%Y-%m-%d"), len(reps), 1/dt]
        }).to_excel(writer, sheet_name='LOG')

    print(f"--- Proceso Finalizado. Archivo: {output_xlsx} ---")

# --- USO ---
# bio_sts_tool('2025-11-04-12-24_SMP011_D1_10STS_13REP_1.xlsx - Reducido.csv', 'STS_ANALYSIS_TOTAL.xlsx')