# Guías de Casos de Uso Específicos - STS Analysis Tool

## Caso 1: Análisis de Pacientes con Parkinson

### Contexto Clínico
Los pacientes con Parkinson presentan alteraciones en el patrón STS caracterizado por:
- Mayor tiempo de ejecución
- Reducción en la velocidad máxima
- Pérdida de la fluidez del movimiento
- Mayor variabilidad entre repeticiones

### Protocolo de Análisis

```python
import pandas as pd
from src.validation import validate_sts_data, print_validation_report
from src.detection import compute_phase_events
from src.analysis import generate_phase_dataframe
from src.export import export_to_excel

# 1. Cargar y validar datos
df = pd.read_excel('data/input/paciente_parkinson.xlsx', sheet_name='Reducido')
validation = validate_sts_data(df, time_col='Tiempo')
print_validation_report(validation)

if not validation['is_valid']:
    print("❌ Datos inválidos - revisar antes de continuar")
    exit()

# 2. Detectar fases con parámetros específicos para Parkinson
events, figures = compute_phase_events(
    df,
    time_col='Tiempo',
    mass_kg=70.0,  # peso del paciente
    window=50,     # ventana más amplia para movimientos lentos
    vel_threshold=0.03,  # umbral más bajo para detectar fases lentas
    n_positive=50,
    n_negative=50
)

# 3. Análisis detallado por fases
z_mm = df['BCM Z'].values * 1000  # convertir a mm
phase_df = generate_phase_dataframe(
    df=df,
    time_col='Tiempo',
    rep_events=events['rep_events'],
    marker_to_time=events['marker_to_time'],
    z_mm=z_mm,
    vel_m_s=df['Velocidad'].values,
    acc_m_s2=df['Aceleración'].values,
    power_W=None,  # no disponible
    mass_kg=70.0,
    dt=0.01,
    half_window_derivative=10,
    close_last_seated_at_end=True
)

# 4. Análisis específico de Parkinson
print("📊 Métricas clave para Parkinson:")
for idx, row in phase_df.iterrows():
    if row['phase'] == 'concéntrica':  # fase de levantarse
        print(f"Rep {row['rep_idx']}: Duración={row['duration_s']:.2f}s, "
              f"Velocidad máx={row.get('BCM_Z_stats', [0,0,0])[2]:.3f}m/s")

# 5. Exportar resultados
excel_file, plots_file, json_file = export_to_excel(
    df, events, 'Tiempo', 70.0, 0.01,
    output_dir='output/parkinson_analysis/'
)
```

### Interpretación de Resultados
- **Duración total > 3.5s**: Indicativo de bradicinesia severa
- **Velocidad máxima < 0.8 m/s**: Movimiento significativamente lento
- **Coeficiente de variación > 25%**: Alta variabilidad entre repeticiones
- **Fase excéntrica prolongada**: Dificultad para controlar el descenso

---

## Caso 2: Evaluación de Rehabilitación Post-Artroplastia de Cadera

### Contexto Clínico
Después de reemplazo de cadera, los pacientes muestran:
- Asimetría en el patrón de movimiento
- Reducción temporal de la fuerza
- Mejora progresiva con rehabilitación
- Necesidad de monitoreo objetivo del progreso

### Análisis Comparativo

```python
import pandas as pd
from pathlib import Path
from src.analysis import generate_phase_dataframe
from src.metrics import mark_ok_repetitions

def analyze_rehabilitation_progress(patient_id: str, sessions: List[str]):
    """
    Analizar progreso de rehabilitación a través de múltiples sesiones.

    Args:
        patient_id: ID del paciente
        sessions: Lista de archivos de sesión ['pre_op.xlsx', '1_mes.xlsx', '3_meses.xlsx']
    """
    results = {}

    for session_file in sessions:
        # Cargar datos
        df = pd.read_excel(f'data/input/{patient_id}/{session_file}')
        events, _ = compute_phase_events(df, 'Tiempo', mass_kg=75.0)

        # Análisis por fases
        phase_df = generate_phase_dataframe(
            df=df, time_col='Tiempo', rep_events=events['rep_events'],
            marker_to_time=events['marker_to_time'],
            z_mm=df['BCM Z'].values * 1000,
            vel_m_s=df['Velocidad'].values,
            acc_m_s2=df['Aceleración'].values,
            power_W=None, mass_kg=75.0, dt=0.01,
            half_window_derivative=7, close_last_seated_at_end=True
        )

        # Calcular métricas de simetría
        symmetry_metrics = calculate_symmetry_metrics(phase_df)

        results[session_file] = {
            'phase_metrics': phase_df,
            'symmetry': symmetry_metrics,
            'quality_score': calculate_quality_score(phase_df)
        }

    return results

def calculate_symmetry_metrics(phase_df: pd.DataFrame) -> Dict[str, float]:
    """Calcular métricas de simetría entre repeticiones."""
    metrics = {}

    # Simetría de duración
    durations = phase_df.groupby('rep_idx')['duration_s'].sum()
    metrics['duration_cv'] = durations.std() / durations.mean() * 100

    # Simetría de velocidad máxima
    max_velocities = phase_df.groupby('rep_idx')['BCM_Z_stats'].apply(
        lambda x: max([stats[2] for stats in x if isinstance(stats, list)])
    )
    metrics['velocity_cv'] = max_velocities.std() / max_velocities.mean() * 100

    return metrics

def calculate_quality_score(phase_df: pd.DataFrame) -> float:
    """Calcular score de calidad del movimiento (0-100)."""
    # Basado en: simetría, velocidad, fluidez
    symmetry_penalty = min(phase_df.groupby('rep_idx')['duration_s'].std() * 10, 30)
    velocity_score = min(phase_df['BCM_Z_stats'].apply(
        lambda x: x[2] if isinstance(x, list) else 0
    ).mean() * 50, 50)

    quality = 100 - symmetry_penalty + velocity_score / 2
    return max(0, min(100, quality))

# Uso
sessions = ['pre_operatorio.xlsx', '1_mes_post.xlsx', '3_meses_post.xlsx']
progress = analyze_rehabilitation_progress('paciente_001', sessions)

# Mostrar progreso
for session, data in progress.items():
    print(f"{session}:")
    print(f"  Simetría duración: {data['symmetry']['duration_cv']:.1f}%")
    print(f"  Simetría velocidad: {data['symmetry']['velocity_cv']:.1f}%")
    print(f"  Score calidad: {data['quality_score']:.1f}/100")
```

### Seguimiento del Progreso
- **Pre-operatorio**: Baseline para comparación
- **1 mes post**: Evaluación inicial de recuperación
- **3 meses post**: Evaluación de recuperación completa
- **Mejora esperada**: Reducción de asimetría < 15%, score de calidad > 80

---

## Caso 3: Investigación - Efectos de la Fatiga en STS

### Diseño Experimental
Estudio de fatiga muscular durante protocolo STS prolongado:
- 50 repeticiones consecutivas
- Medición cada 10 repeticiones
- Análisis de decremento de performance

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

def analyze_fatigue_effects(data_files: List[str], mass_kg: float):
    """
    Analizar efectos de fatiga en protocolo STS prolongado.

    Args:
        data_files: Lista de archivos ['rep_1-10.xlsx', 'rep_11-20.xlsx', ...]
        mass_kg: Masa corporal del sujeto
    """
    fatigue_metrics = []

    for i, file in enumerate(data_files):
        df = pd.read_excel(file)
        events, _ = compute_phase_events(df, 'Tiempo', mass_kg=mass_kg)

        phase_df = generate_phase_dataframe(
            df=df, time_col='Tiempo', rep_events=events['rep_events'],
            marker_to_time=events['marker_to_time'],
            z_mm=df['BCM Z'].values * 1000,
            vel_m_s=df['Velocidad'].values,
            acc_m_s2=df['Aceleración'].values,
            power_W=None, mass_kg=mass_kg, dt=0.01,
            half_window_derivative=7, close_last_seated_at_end=False
        )

        # Métricas por bloque de 10 repeticiones
        block_metrics = {
            'block': i + 1,
            'mean_duration': phase_df['duration_s'].mean(),
            'mean_peak_velocity': phase_df['BCM_Z_stats'].apply(
                lambda x: x[2] if isinstance(x, list) else 0
            ).mean(),
            'mean_power': phase_df.get('work_J', pd.Series([0]*len(phase_df))).mean(),
            'fatigue_index': calculate_fatigue_index(phase_df)
        }

        fatigue_metrics.append(block_metrics)

    return pd.DataFrame(fatigue_metrics)

def calculate_fatigue_index(phase_df: pd.DataFrame) -> float:
    """Calcular índice de fatiga basado en variabilidad."""
    # Mayor variabilidad = mayor fatiga
    duration_cv = phase_df['duration_s'].std() / phase_df['duration_s'].mean()
    velocity_cv = phase_df['BCM_Z_stats'].apply(
        lambda x: x[2] if isinstance(x, list) else 0
    ).std() / phase_df['BCM_Z_stats'].apply(
        lambda x: x[2] if isinstance(x, list) else 0
    ).mean()

    return (duration_cv + velocity_cv) / 2 * 100

# Análisis de fatiga
files = [f'data/fatigue/rep_{(i*10)+1}-{(i+1)*10}.xlsx' for i in range(5)]
fatigue_df = analyze_fatigue_effects(files, mass_kg=70.0)

# Análisis estadístico
slope_duration, _, _, _, _ = stats.linregress(fatigue_df['block'], fatigue_df['mean_duration'])
slope_velocity, _, _, _, _ = stats.linregress(fatigue_df['block'], fatigue_df['mean_peak_velocity'])

print(f"Incremento duración: {slope_duration*100:.2f}% por bloque")
print(f"Decremento velocidad: {slope_velocity*100:.2f}% por bloque")

# Visualización
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ax1.plot(fatigue_df['block'], fatigue_df['mean_duration'], 'o-')
ax1.set_title('Duración por Bloque de Repeticiones')
ax1.set_xlabel('Bloque (10 reps)')
ax1.set_ylabel('Duración (s)')

ax2.plot(fatigue_df['block'], fatigue_df['mean_peak_velocity'], 'o-')
ax2.set_title('Velocidad Máxima por Bloque')
ax2.set_xlabel('Bloque (10 reps)')
ax2.set_ylabel('Velocidad (m/s)')

plt.tight_layout()
plt.savefig('output/fatigue_analysis.png', dpi=300, bbox_inches='tight')
```

### Interpretación
- **Incremento duración > 5%**: Fatiga significativa
- **Decremento velocidad > 10%**: Pérdida de potencia
- **Índice fatiga > 20%**: Alta variabilidad por fatiga

---

## Caso 4: Análisis EMG Integrado con Biomecánica

### Configuración de Análisis
Análisis simultáneo de señales EMG y biomecánicas:

```python
from src.advanced_metrics import detect_emg_columns, detect_cop_columns
from src.analysis import generate_phase_dataframe

def analyze_emg_biomecanical_integration(file_path: str, mass_kg: float):
    """
    Análisis integrado EMG + biomecánica.

    Args:
        file_path: Archivo Excel con datos Noraxon
        mass_kg: Masa corporal
    """
    # Cargar datos
    df = pd.read_excel(file_path, sheet_name='Reducido')

    # Detectar canales automáticamente
    emg_cols = detect_emg_columns(df)
    cop_cols = detect_cop_columns(df)

    print(f"EMG channels detected: {emg_cols}")
    print(f"CoP channels detected: {cop_cols}")

    # Validación de datos
    validation = validate_sts_data(df, time_col='Tiempo')
    if not validation['is_valid']:
        print("❌ Datos inválidos")
        return None

    # Detección de fases
    events, figures = compute_phase_events(df, 'Tiempo', mass_kg=mass_kg)

    # Análisis por fases con EMG y CoP
    phase_df = generate_phase_dataframe(
        df=df,
        time_col='Tiempo',
        rep_events=events['rep_events'],
        marker_to_time=events['marker_to_time'],
        z_mm=df['BCM Z'].values * 1000,
        vel_m_s=df['Velocidad'].values,
        acc_m_s2=df['Aceleración'].values,
        power_W=df.get('Potencia'),  # si disponible
        mass_kg=mass_kg,
        dt=0.01,
        half_window_derivative=7,
        close_last_seated_at_end=True
    )

    # Análisis EMG por fase
    emg_analysis = analyze_emg_by_phase(df, phase_df, emg_cols, events['marker_to_time'])

    # Análisis CoP por fase
    cop_analysis = analyze_cop_by_phase(df, phase_df, cop_cols, events['marker_to_time'])

    return {
        'biomechanical': phase_df,
        'emg': emg_analysis,
        'cop': cop_analysis,
        'validation': validation
    }

def analyze_emg_by_phase(df: pd.DataFrame, phase_df: pd.DataFrame,
                        emg_cols: List[str], marker_to_time: Dict) -> pd.DataFrame:
    """Analizar activación EMG por fase."""
    from src.advanced_metrics import PhaseComputer

    emg_results = []

    for _, phase_row in phase_df.iterrows():
        phase_start = phase_row['start_time']
        phase_end = phase_row['end_time']

        for emg_col in emg_cols:
            if emg_col in df.columns:
                pc = PhaseComputer(df, 'Tiempo')
                rms_value = pc.mean(emg_col, phase_start, phase_end)
                peak_value = pc.max_val(emg_col, phase_start, phase_end)

                emg_results.append({
                    'phase': phase_row['phase'],
                    'rep_idx': phase_row['rep_idx'],
                    'emg_channel': emg_col,
                    'rms_amplitude': rms_value,
                    'peak_amplitude': peak_value,
                    'duration_s': phase_end - phase_start
                })

    return pd.DataFrame(emg_results)

def analyze_cop_by_phase(df: pd.DataFrame, phase_df: pd.DataFrame,
                        cop_cols: List[str], marker_to_time: Dict) -> pd.DataFrame:
    """Analizar Centro de Presión por fase."""
    cop_results = []

    for _, phase_row in phase_df.iterrows():
        phase_start = phase_row['start_time']
        phase_end = phase_row['end_time']

        for cop_col in cop_cols:
            if cop_col in df.columns:
                pc = PhaseComputer(df, 'Tiempo')
                mean_pos = pc.mean(cop_col, phase_start, phase_end)
                range_pos = pc.range_mm_to_m(cop_col, phase_start, phase_end)

                cop_results.append({
                    'phase': phase_row['phase'],
                    'rep_idx': phase_row['rep_idx'],
                    'cop_channel': cop_col,
                    'mean_position': mean_pos,
                    'position_range': range_pos[2] if range_pos[2] else 0,  # range
                    'duration_s': phase_end - phase_start
                })

    return pd.DataFrame(cop_results)

# Ejemplo de uso
results = analyze_emg_biomecanical_integration(
    'data/input/datos_noraxon.xlsx',
    mass_kg=75.0
)

if results:
    # Exportar resultados integrados
    with pd.ExcelWriter('output/integrated_analysis.xlsx') as writer:
        results['biomechanical'].to_excel(writer, sheet_name='Biomecanica', index=False)
        results['emg'].to_excel(writer, sheet_name='EMG', index=False)
        results['cop'].to_excel(writer, sheet_name='CoP', index=False)

    print("✅ Análisis integrado completado")
```

### Aplicaciones Clínicas
- **Valoración muscular**: Actividad EMG durante fases específicas
- **Control postural**: Análisis CoP durante transiciones
- **Coordinación**: Sincronización EMG-force plate
- **Rehabilitación**: Feedback biofeedback EMG

---

## Caso 5: Batch Processing de Múltiples Sujetos

### Procesamiento Masivo
Análisis automatizado de cohortes grandes:

```python
import glob
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor
import pandas as pd

def batch_process_sts_analysis(input_dir: str, output_dir: str,
                              mass_kg: float = None, n_workers: int = 4):
    """
    Procesar múltiples archivos STS en paralelo.

    Args:
        input_dir: Directorio con archivos Excel
        output_dir: Directorio para resultados
        mass_kg: Masa corporal (si None, intentar extraer de metadatos)
        n_workers: Número de procesos paralelos
    """
    # Encontrar archivos
    pattern = f"{input_dir}/**/*.xlsx"
    files = glob.glob(pattern, recursive=True)

    print(f"📁 Encontrados {len(files)} archivos para procesar")

    # Crear directorio de salida
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Procesar en paralelo
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        futures = []

        for file_path in files:
            future = executor.submit(
                process_single_subject,
                file_path, output_dir, mass_kg
            )
            futures.append((file_path, future))

        # Recopilar resultados
        results_summary = []
        for file_path, future in futures:
            try:
                result = future.result(timeout=300)  # 5 min timeout
                results_summary.append({
                    'file': Path(file_path).name,
                    'status': 'success',
                    'excel_file': result.get('excel'),
                    'plots_file': result.get('plots'),
                    'error': None
                })
            except Exception as e:
                results_summary.append({
                    'file': Path(file_path).name,
                    'status': 'error',
                    'excel_file': None,
                    'plots_file': None,
                    'error': str(e)
                })

    # Resumen final
    success_count = sum(1 for r in results_summary if r['status'] == 'success')
    print(f"✅ Procesamiento completado: {success_count}/{len(files)} exitosos")

    # Guardar resumen
    summary_df = pd.DataFrame(results_summary)
    summary_df.to_excel(f"{output_dir}/batch_processing_summary.xlsx", index=False)

    return summary_df

def process_single_subject(file_path: str, output_dir: str, mass_kg: float = None):
    """Procesar un solo sujeto."""
    from src.metadata import read_metadata
    from sts_analysis_tool_enhanced import run_tool_enhanced

    subject_id = Path(file_path).stem

    # Intentar extraer masa de metadatos
    if mass_kg is None:
        try:
            metadata = read_metadata(file_path)
            mass_kg = metadata.get('weight_kg', 70.0)  # default 70kg
        except:
            mass_kg = 70.0  # fallback

    # Análisis completo
    excel, plots, json_data = run_tool_enhanced(
        file_path=file_path,
        sheet_name='Reducido',
        mass_kg=mass_kg,
        close_last_seated_at_end=True
    )

    # Mover archivos a directorio organizado
    subject_dir = f"{output_dir}/{subject_id}"
    Path(subject_dir).mkdir(exist_ok=True)

    # Renombrar archivos
    import shutil
    shutil.move(excel, f"{subject_dir}/{subject_id}_analysis.xlsx")
    shutil.move(plots, f"{subject_dir}/{subject_id}_plots.png")
    shutil.move(json_data, f"{subject_dir}/{subject_id}_params.json")

    return {
        'excel': f"{subject_dir}/{subject_id}_analysis.xlsx",
        'plots': f"{subject_dir}/{subject_id}_plots.png",
        'json': f"{subject_dir}/{subject_id}_params.json"
    }

# Ejemplo de uso
summary = batch_process_sts_analysis(
    input_dir='data/input/cohort_study',
    output_dir='output/cohort_analysis',
    mass_kg=None,  # extraer de metadatos
    n_workers=6    # usar 6 CPUs
)

# Análisis estadístico de cohorte
successful = summary[summary['status'] == 'success']
print(f"📊 Cohorte procesada: {len(successful)} sujetos válidos")
```

### Beneficios del Batch Processing
- **Eficiencia**: Procesamiento paralelo de múltiples sujetos
- **Consistencia**: Parámetros uniformes para toda la cohorte
- **Escalabilidad**: Manejo de estudios grandes (100+ sujetos)
- **Trazabilidad**: Logs detallados y resúmenes de procesamiento

---

## Mejores Prácticas Generales

### 1. Validación de Datos
```python
# Siempre validar antes del análisis
from src.validation import validate_sts_data, print_validation_report

validation = validate_sts_data(df, time_col='Tiempo')
print_validation_report(validation)

if not validation['is_valid']:
    # Corregir problemas antes de continuar
    pass
```

### 2. Manejo de Errores
```python
try:
    results = run_tool_enhanced(file_path, mass_kg=75.0)
except ValidationError as e:
    print(f"Error de validación: {e}")
    # Corregir datos
except Exception as e:
    print(f"Error inesperado: {e}")
    # Logging detallado
```

### 3. Optimización de Performance
```python
# Para datasets grandes
df = df.iloc[::2]  # Decimar datos (50% menos muestras)
# o
df = df[df['Tiempo'] <= 30.0]  # Limitar duración
```

### 4. Documentación de Resultados
```python
# Incluir metadatos en resultados
results_metadata = {
    'software_version': '2.1.0',
    'analysis_date': pd.Timestamp.now(),
    'parameters': {
        'mass_kg': mass_kg,
        'sampling_rate': 100,
        'filter_window': window
    },
    'validation_status': validation['is_valid']
}
```

### 5. Reproducibilidad
```python
# Fijar seeds para resultados reproducibles
np.random.seed(42)
# Documentar versiones de dependencias
import sys
print(f"Python: {sys.version}")
print(f"NumPy: {np.__version__}")
print(f"Pandas: {pd.__version__}")
```