# Test script for STS Analysis Tool
from src.analysis import run_sts_analysis
import pandas as pd
import numpy as np

print('🔬 Probando API de análisis STS...')

# Crear datos de ejemplo
t = np.linspace(0, 5, 500)
z = 600 + 100 * np.sin(2 * np.pi * 0.5 * t)
df = pd.DataFrame({'Tiempo': t, 'BCM Z': z})

print(f'Datos creados: {len(df)} muestras, {len(df.columns)} columnas')

# Ejecutar análisis
try:
    results = run_sts_analysis(df, time_col='Tiempo', disp_col='BCM Z', mass_kg=75.0)
    print('✅ Análisis completado exitosamente!')
    print(f'Repeticiones detectadas: {len(results.get("reps", []))}')
    print(f'Parámetros calculados: {len(results.get("params", {}))}')
except Exception as e:
    print(f'❌ Error en análisis: {e}')