# sts_analysis_from_raw.py
# Herramienta de análisis STS que emula la hoja Excel *Sencillo*
# a partir de los datos brutos (p. ej. 2025-11-04-12-24_SMP011_D1_10STS_13REP_1.xlsx)

import pandas as pd
import numpy as np
from pathlib import Path
from io import BytesIO
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

# Parámetros globales
G = 9.80
ALZ_FACTOR = 0.90
BCM_COMPLETENESS_THRESH = 0.85  # 85%
WIN = 30     # frames (a 100 Hz ~= 0.30 s)
VEL_POS = 0.1   # m/s
VEL_NEG = -0.1  # m/s

# Columnas esperadas
COL_TIME='time'
COL_BCM_Z='Noraxon MyoMotion-Trajectories-Body center of mass-z (mm)'
COL_BCM_X='Noraxon MyoMotion-Trajectories-Body center of mass-x (mm)'
COL_HIP_Z='Noraxon MyoMotion-Trajectories-Hip RT-z (mm)'
COL_VEL_BCM_Z='Vel_BCM_Z'
COL_FP_X='Force Plates_X'; COL_FP_Z='Force Plates_Z'; COL_FP_RES='Force Plates_Resultante'
COL_COP_X='CoP_Disp_X'; COL_COP_Y='CoP_Disp_Y'; COL_COP_R='CoP_Disp_XY'

SEG_MAP = {
    'Shoulder': {
        'disp': ('Disp_Shoulder_X', 'Disp_Shoulder_Z', 'Disp_Shoulder_XZ'),
        'vel':  ('Vel_Shoulder_X',  'Vel_Shoulder_Z',  'Vel_Shoulder_XZ'),
        'pow_e':('Power_Estimated_Shoulder_X','Power_Estimated_Shoulder_Z','Power_Estimated_Shoulder_XZ'),
        'work_e':('Mech Work_Estimated_Shoulder_X','Mech Work_Estimated_Shoulder_Z','Mech Work_Estimated_Shoulder_XZ'),
        'pow_fp':('Power_Shoulder*Force Platform_X','Power_Shoulder*Force Platform_Z','Power_Shoulder*Force Platform_XZ'),
        'work_fp':('Mech Work_Shoulder*Force Platform_X','Mech Work_Shoulder*Force Platform_Z','Mech Work_Shoulder*Force Platform_XZ'),
    },
    'Pelvis': {
        'disp': ('Disp_Pelvis_X', 'Disp_Pelvis_Z', 'Disp_Pelvis_XZ'),
        'vel':  ('Vel_Pelvis_X',  'Vel_Pelvis_Z',  'Vel_Pelvis_XZ'),
        'pow_e':('Power_Estimated_Pelvis_X','Power_Estimated_Pelvis_Z','Power_Estimated_Pelvis_XZ'),
        'work_e':('Mech Work_Estimated_Pelvis_X','Mech Work_Estimated_Pelvis_Z','Mech Work_Estimated_Pelvis_XZ'),
        'pow_fp':('Power_Pelvis*Force Platform_X','Power_Pelvis*Force Platform_Z','Power_Pelvis*Force Platform_XZ'),
        'work_fp':('Mech Work_Pelvis*Force Platform_X','Mech Work_Pelvis*Force Platform_Z','Mech Work_Pelvis*Force Platform_XZ'),
    },
    'Hip': {
        'disp': ('Disp_Hip_X', 'Disp_Hip_Z', 'Disp_Hip_XZ'),
        'vel':  ('Vel_Hip_X',  'Vel_Hip_Z',  'Vel_Hip_XZ'),
        'pow_e':('Power_Estimated_Hip_X','Power_Estimated_Hip_Z','Power_Estimated_Hip_XZ'),
        'work_e':('Mech Work_Estimated_Hip_X','Mech Work_Estimated_Hip_Z','Mech Work_Estimated_Hip_XZ'),
        'pow_fp':('Power_Hip*Force Platform_X','Power_Hip*Force Platform_Z','Power_Hip*Force Platform_XZ'),
        'work_fp':('Mech Work_Hip*Force Platform_X','Mech Work_Hip*Force Platform_Z','Mech Work_Hip*Force Platform_XZ'),
    },
    'BMC': {
        'disp': ('Disp_BCM_X', 'Disp_BCM_Z', 'Disp_BCM_XZ'),
        'vel':  ('Vel_BCM_X',  'Vel_BCM_Z',  'Vel_BCM_XZ'),
        'pow_e':('Power_Estimated Center of Mass_X','Power_Estimated Center of Mass_Z','Power_Estimated Center of Mass_XZ'),
        'work_e':('Mech Work_Estimated_BCM_X','Mech Work_Estimated_BCM_Z','Mech Work_Estimated_BCM_XZ'),
        'pow_fp':('Power_COM*Force Platform_X','Power_COM*Force Platform_Z','Power_COM*Force Platform_XZ'),
        'work_fp':('Mech Work_BCM*Force Platform_X','Mech Work_BCM*Force Platform_Z','Mech Work_BCM*Force Platform_XZ'),
    }
}

ANGLE_COLS = {
    'Thoracic Flexion Fwd (deg)': 'Thoracic Flexion Fwd (deg)',
    'Lumbar Flexion Fwd (deg)': 'Lumbar Flexion Fwd (deg)',
    'Torso-Pelvic Flexion Fwd (deg)': 'Torso-Pelvic Flexion Fwd (deg)',
    'RT Hip Flexion (deg)': 'RT Hip Flexion (deg)',
    'RT Knee Flexion (deg)': 'RT Knee Flexion (deg)',
    'RT Ankle Dorsiflexion (deg)': 'RT Ankle Dorsiflexion (deg)'
}

PITCH_COLS = {
    'Upp Spine': 'Noraxon MyoMotion-Segments-Upper spine-Pitch (deg)',
    'Low Spine': 'Noraxon MyoMotion-Segments-Lower spine-Pitch (deg)',
    'Pelvis': 'Noraxon MyoMotion-Segments-Pelvis-Pitch (deg)',
    'Object': 'Object 1-Pitch (deg)'
}

EMG_COLS = [
    'RT TIB.ANT. (%)', 'RT VLO (%)', 'RT RECTUS FEM. (%)',
    'RT MED. GASTRO (%)', 'RT SEMITEND. (%)', 'RT GLUT. MAX. (%)', 'RT LUMBAR ES (%)'
]


def _get(DF, c):
    return DF[c] if (c in DF.columns and DF[c].notna().any()) else None


# Segmentación Conc->CE->Ecc con reglas pedidas
def segment(df, win=WIN, vpos=VEL_POS, vneg=VEL_NEG):
    pos = df[COL_BCM_Z].values/1000.0
    vel = df[COL_VEL_BCM_Z].values
    n=len(df)
    conc, peak, ecc=[],[],[]
    i=win
    while i<n-win:
        if vel[i]>vpos and np.all(np.diff(pos[i:i+win])>0):
            cs=i
            j=cs+win
            peak_idx=cs+int(np.argmax(pos[cs:j]))
            found=False
            while j<n-win:
                if pos[j]>pos[peak_idx]:
                    peak_idx=j
                if vel[j]<vneg and np.all(np.diff(pos[j-win:j])<0):
                    conc.append(cs); peak.append(peak_idx); ecc.append(j)
                    i=j+win
                    found=True
                    break
                j+=1
            if not found:
                break
            continue
        i+=1
    reps=[]
    m=min(len(conc),len(peak),len(ecc))
    for k in range(m):
        se = conc[k+1]-1 if k+1<m else n-1
        reps.append({'rep':k+1,'conc':(conc[k],peak[k]),'ecc':(peak[k],ecc[k]),'seated':(ecc[k],se)})
    return reps


def run(input_xlsx: Path):
    xl = pd.ExcelFile(input_xlsx)
    sheet = 'General' if 'General' in xl.sheet_names else xl.sheet_names[0]
    df = pd.read_excel(xl, sheet, engine='openpyxl')
    meta = pd.read_excel(xl, 'MetaData_&_Parameters', header=None, index_col=0, engine='openpyxl') if 'MetaData_&_Parameters' in xl.sheet_names else None

    # Velocidad (m/s) desde BCM_Z (mm)
    t = df[COL_TIME].values
    pos_m = df[COL_BCM_Z].values/1000.0
    df[COL_VEL_BCM_Z] = np.gradient(pos_m, t)

    # Meta
    try:
        codigo = str(meta.loc['Código', 1]) if meta is not None and 'Código' in meta.index else ''
    except Exception:
        codigo = str(meta.loc['Codigo', 1]) if meta is not None and 'Codigo' in meta.index else ''
    altura = float(meta.loc['Altura', 1]) if meta is not None and 'Altura' in meta.index else np.nan
    peso = float(meta.loc['Peso', 1]) if meta is not None and 'Peso' in meta.index else np.nan
    alt_silla = float(meta.loc['Altura de la silla', 1]) if meta is not None and 'Altura de la silla' in meta.index else np.nan
    test_name = meta.loc['Nombre Test', 1] if meta is not None and 'Nombre Test' in meta.index else ''
    fecha_test = meta.loc['Fecha del test', 1] if meta is not None and 'Fecha del test' in meta.index else ''
    FORCE_ALZ = ALZ_FACTOR * peso * G if not np.isnan(peso) else np.nan
    DISP_ALZ = (altura*0.5 - alt_silla) if (not np.isnan(altura) and not np.isnan(alt_silla)) else np.nan

    reps = segment(df)

    def phase_stats(s, e, fase, rep):
        seg = df.iloc[s:e+1]
        r = {
            'Código': codigo, 'Altura': altura, 'Peso_kg': peso,
            'Altura de la silla': alt_silla, 'Test': test_name, 'Fecha Test': fecha_test,
            'Repeticion': rep, 'Fase': fase,
            'Inicio_Tiempo': round(float(seg[COL_TIME].iloc[0]), 3),
            'Final_Tiempo': round(float(seg[COL_TIME].iloc[-1]), 3),
        }
        r['Tiempo fase'] = round(r['Final_Tiempo'] - r['Inicio_Tiempo'], 3)

        # Ángulos
        for nice, col in ANGLE_COLS.items():
            v = _get(seg, col)
            if v is not None:
                r[col] = float(v.mean())
                r[f'Max_{nice}'] = float(v.max())
                r[f'Min_{nice}'] = float(v.min())
                r[f'ROM_{nice}'] = float(v.max()-v.min())
            else:
                r[col] = r[f'Max_{nice}'] = r[f'Min_{nice}'] = r[f'ROM_{nice}'] = np.nan

        # Hip swing
        vhip = _get(seg, 'RT Hip Flexion (deg)')
        if vhip is not None:
            if fase == 'Concéntrica':
                r['Start-Max_°Hip'] = float(vhip.max() - vhip.iloc[0])
                r['Start-Min_°Hip'] = np.nan
            elif fase == 'Excéntrica':
                r['Start-Max_°Hip'] = np.nan
                r['Start-Min_°Hip'] = float(vhip.iloc[0] - vhip.min())
            else:
                r['Start-Max_°Hip'] = r['Start-Min_°Hip'] = np.nan
        else:
            r['Start-Max_°Hip'] = r['Start-Min_°Hip'] = np.nan

        # IMU Pitch
        for label, col in PITCH_COLS.items():
            v = _get(seg, col)
            r[f'Max Pitch {label}'] = float(v.max()) if v is not None else np.nan
            r[f'Min Pitch {label}'] = float(v.min()) if v is not None else np.nan
            r[f'Rango Pitch {label}'] = float(v.max()-v.min()) if v is not None else np.nan

        # BCM X
        bx = _get(seg, COL_BCM_X)
        bz = _get(seg, COL_BCM_Z)
        if bx is not None:
            idx_max = bx.idxmax()
            r['Max_Pos_BCM_X'] = float(bx.max())
            r['Min_Pos_BCM_X'] = float(bx.min())
            r['BCM_X_Displacement'] = float(bx.max() - bx.min())
            r['Time_Max_BCM_X'] = float(df.loc[idx_max, COL_TIME])
            r['DisplBCMZ_at_MaxBCM_X'] = float(seg.loc[idx_max, COL_BCM_Z] - seg[COL_BCM_Z].iloc[0]) if bz is not None else np.nan
        else:
            r.update({'Max_Pos_BCM_X': np.nan, 'Min_Pos_BCM_X': np.nan, 'BCM_X_Displacement': np.nan,
                      'Time_Max_BCM_X': np.nan, 'DisplBCMZ_at_MaxBCM_X': np.nan})

        # CoP
        for key, col in [('AP', COL_COP_X), ('ML', COL_COP_Y), ('Result', COL_COP_R)]:
            v = _get(seg, col)
            r[f'CoP_Acc Displ_{key}'] = float(v.sum()) if v is not None else np.nan
            r[f'CoP_SD Displ_{key}'] = float(v.std()) if v is not None else np.nan

        # Alcázar
        if not np.isnan(FORCE_ALZ) and not np.isnan(DISP_ALZ) and r['Tiempo fase']>0:
            r['Force_Alcazar'] = float(FORCE_ALZ)
            r['Disp_Alcazar'] = float(DISP_ALZ)
            vel_alz = DISP_ALZ / r['Tiempo fase']
            r['Veloc_Alcazar'] = float(vel_alz)
            r['Mean Power_Alcazar'] = float(FORCE_ALZ * vel_alz)
        else:
            r.update({'Force_Alcazar': np.nan, 'Disp_Alcazar': np.nan, 'Veloc_Alcazar': np.nan, 'Mean Power_Alcazar': np.nan})

        # % desplazamientos relativos
        if bz is not None:
            d = float(seg[COL_BCM_Z].iloc[-1] - seg[COL_BCM_Z].iloc[0])
            max_global = float(df[COL_BCM_Z].max())
            r['% Desp_BCM_Z_vs_Max'] = (d / (max_global/1000.0)) * 100.0 if max_global not in (0, np.nan) else np.nan
        else:
            r['% Desp_BCM_Z_vs_Max'] = np.nan
        hz = _get(seg, COL_HIP_Z)
        if hz is not None:
            dh = float(seg[COL_HIP_Z].iloc[-1] - seg[COL_HIP_Z].iloc[0])
            max_hip = float(df[COL_HIP_Z].max())
            r['% Desp_Hip_Z_vs_Max'] = (dh / (max_hip/1000.0)) * 100.0 if max_hip not in (0, np.nan) else np.nan
            r['% Desp_Hip_Z_vs_Alcazar'] = (dh/1000.0 / DISP_ALZ) * 100.0 if (DISP_ALZ not in (0, None, np.nan)) else np.nan
        else:
            r['% Desp_Hip_Z_vs_Max'] = r['% Desp_Hip_Z_vs_Alcazar'] = np.nan

        # Guardar desplazamiento bruto para completitud
        r['_bcm_z_raw'] = abs(float(seg[COL_BCM_Z].iloc[-1] - seg[COL_BCM_Z].iloc[0])) if bz is not None else np.nan

        # EMG medios
        for col in EMG_COLS:
            v = _get(seg, col)
            r[col] = float(v.mean()) if v is not None else np.nan

        # Fuerzas PF
        for label, col in [('Vert', COL_FP_Z), ('Horizon', COL_FP_X), ('Result', COL_FP_RES)]:
            v = _get(seg, col)
            if v is not None:
                r[f'{label} F_Mean'] = float(v.mean())
                r[f'{label} F_Max'] = float(v.max())
                t_pk = float(df.loc[v.idxmax(), COL_TIME]) - r['Inicio_Tiempo']
                r[f'Time to {label} F_Max'] = round(t_pk, 3)
                r[f'Time to {label} F_Max_%'] = round((t_pk / r['Tiempo fase']) * 100.0, 2) if r['Tiempo fase'] > 0 else np.nan
            else:
                r[f'{label} F_Mean'] = r[f'{label} F_Max'] = np.nan
                r[f'Time to {label} F_Max'] = r[f'Time to {label} F_Max_%'] = np.nan

        # Segmentos
        for sn, cm in SEG_MAP.items():
            for ax_, col in zip(('X','Z','XZ'), cm['disp']):
                v = _get(seg, col)
                r[f'Displac_{sn}_{ax_}'] = float(v.iloc[-1] - v.iloc[0]) if v is not None else np.nan
            for ax_, col in zip(('X','Z','XZ'), cm['vel']):
                v = _get(seg, col)
                r[f'Veloc_{sn}_{ax_}'] = float(v.mean()) if v is not None else np.nan
                r[f'Veloc_{sn}_{ax_}_MaxAbs'] = float(v.abs().max()) if v is not None else np.nan
            for ax_, col in zip(('X','Z','XZ'), cm['pow_e']):
                v = _get(seg, col)
                r[f'Mean Power_{sn}_{ax_}'] = float(v.mean()) if v is not None else np.nan
                r[f'Max Power_{sn}_{ax_}'] = float(v.max()) if v is not None else np.nan
            for ax_, col in zip(('X','Z','XZ'), cm['work_e']):
                v = _get(seg, col)
                r[f'Mech Work_{sn}_{ax_}'] = float(v.iloc[-1] - v.iloc[0]) if v is not None else np.nan
            for ax_, col in zip(('X','Z','XZ'), cm['pow_fp']):
                v = _get(seg, col)
                r[f'Mean Power_{sn}_{ax_}_FP'] = float(v.mean()) if v is not None else np.nan
                r[f'Max Power_{sn}_{ax_}_FP'] = float(v.max()) if v is not None else np.nan
            for ax_, col in zip(('X','Z','XZ'), cm['work_fp']):
                v = _get(seg, col)
                r[f'Mech Work_{sn}_{ax_}_FP'] = float(v.iloc[-1] - v.iloc[0]) if v is not None else np.nan

        return r

    rows=[]
    for pb in reps:
        for key, label in [('conc','Concéntrica'),('ecc','Excéntrica'),('seated','Sentado')]:
            s,e = pb[key]
            rows.append(phase_stats(s,e,label,pb['rep']))
    out = pd.DataFrame(rows)

    for label in ('Concéntrica','Excéntrica','Sentado'):
        m = out['Fase']==label
        mx = out.loc[m,'_bcm_z_raw'].max()
        if pd.notna(mx) and mx>0:
            out.loc[m,'Completa'] = (out.loc[m,'_bcm_z_raw']/mx >= BCM_COMPLETENESS_THRESH).astype(int)
        else:
            out.loc[m,'Completa'] = np.nan
    out.drop(columns=['_bcm_z_raw'], inplace=True)

    # Figura
    fig, axes = plt.subplots(2,1,figsize=(14,6), sharex=True)
    axes[0].plot(df[COL_TIME], df[COL_BCM_Z], color='#1d4ed8', lw=1.2)
    axes[0].set_ylabel('BCM Z (mm)')
    axes[1].plot(df[COL_TIME], df[COL_VEL_BCM_Z], color='#b91c1c', lw=1.2)
    axes[1].set_ylabel('Vel BCM Z (m/s)'); axes[1].set_xlabel('Tiempo (s)')
    COLS={'conc':'#3b82f6','ecc':'#ef4444','seated':'#94a3b8'}
    for pb in reps:
        for key, c in COLS.items():
            s,e = pb[key]
            t0,t1 = df.loc[s,COL_TIME], df.loc[e,COL_TIME]
            axes[0].axvspan(t0,t1,color=c,alpha=0.18)
            axes[1].axvspan(t0,t1,color=c,alpha=0.18)
        for idx in (pb['conc'][0], pb['conc'][1], pb['ecc'][1]):
            axes[0].axvline(df.loc[idx,COL_TIME], ls='--', lw=0.8, color='#64748b')
    plt.tight_layout()
    img = BytesIO(); fig.savefig(img, format='png', dpi=150, bbox_inches='tight'); plt.close(fig); img.seek(0)

    out_path = input_xlsx.parent / f"{input_xlsx.stem}_results.xlsx"
    with pd.ExcelWriter(out_path, engine='xlsxwriter') as writer:
        out.to_excel(writer, sheet_name='KF_Results', index=False)
        wb = writer.book
        ws_plot = wb.add_worksheet('Segmentation_Plot')
        ws_plot.insert_image(1,0,'seg.png',{'image_data':img})
        ws_log = wb.add_worksheet('Processing_Log')
        lines = [
            ['Archivo', input_xlsx.name],
            ['Fecha', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Sheet origen', sheet],
            ['Reps detectadas', str(len(reps))],
            ['Ventana (frames)', str(WIN)],
            ['Umbral vel +', f'{VEL_POS} m/s'],
            ['Umbral vel -', f'{VEL_NEG} m/s'],
            ['Criterio transición', 'Max(BCM_Z) entre inicio conc y inicio exc'],
        ]
        for r,(k,v) in enumerate(lines):
            ws_log.write(r,0,k); ws_log.write(r,1,v)

    return out_path

if __name__ == "__main__":
    print('Procesando...')
    p = run(Path('2025-11-04-12-24_SMP011_D1_10STS_13REP_1.xlsx'))
    print('OK ->', p)