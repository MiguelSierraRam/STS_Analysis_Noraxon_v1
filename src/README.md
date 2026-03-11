# Módulos de Análisis STS (Sit-to-Stand)

Estructura modular y profesional para análisis de datos de Sit-to-Stand.

## Módulos

### `utils.py`
Funciones matemáticas básicas reutilizables:
- `centered_slope()` - Derivada mediante pendiente centrada
- `cumulative_trapezoid()` - Integral acumulada por trapecios
- `detect_column()` - Búsqueda de columnas en DataFrames

### `detection.py`
Lógica de detección de eventos y fases:
- `compute_vector_displacements()` - Cálculo de vector de desplazamientos
- `compute_windows()` - Sumas de ventanas futuras y previas
- `detect_conc_starts()` - Detección de inicio de fase concéntrica
- `detect_peaks()` - Detección de picos (transición Conc-Exc)
- `detect_ecc_ends()` - Detección de fin de fase excéntrica
- `pair_repetitions()` - Emparejar eventos en repeticiones
- `compute_phase_events()` - Cálculo de eventos y gráficas

### `metrics.py`
Estructura de datos y cálculo de métricas:
- `RepResult` - Dataclass con resultados de una repetición
- `compute_metrics()` - Cálculo completo de todas las métricas
- `mark_ok_repetitions()` - Marcar repeticiones como OK

### `plotting.py`
Generación de visualizaciones:
- `plot_general_segmentation()` - Gráfico general de fases
- `plot_per_repetition()` - Gráficos individuales por repetición
- `generate_plots()` - Generador de todos los gráficos

### `export.py`
Exportación de datos:
- `create_sheet1_variables()` - Crear DataFrame completo de variables
- `export_to_excel()` - Exportación a Excel (3 hojas)
- `export_to_json()` - Exportación de parámetros a JSON

## Uso

```python
from sts_analysis_tool_exact import run_tool

# Ejecutar análisis
excel_path, plot_path, json_path = run_tool(
    file_path='datos.xlsx',
    sheet_name='Reducido',
    mass_kg=75.0,
    window=30,
    n_positive=30,
)

print(f"Excel: {excel_path}")
print(f"Gráfico: {plot_path}")
print(f"Parámetros: {json_path}")
```

## Línea de comandos

```bash
python sts_analysis_tool_exact.py \
  --input datos.xlsx \
  --sheet Reducido \
  --mass-kg 75 \
  --window 30 \
  --n-positive 30 \
  --vel-th 0.1 \
  --ok-th 0.85
```

## Ventajas de esta arquitectura

✅ **Modular** - Funciones independientes y reutilizables
✅ **Testeable** - Cada módulo puede probarse aisladamente
✅ **Documentado** - Docstrings en todas las funciones
✅ **Mantenible** - Separación clara de responsabilidades
✅ **Extensible** - Fácil agregar nuevas funcionalidades
