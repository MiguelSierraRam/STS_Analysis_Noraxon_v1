# Módulos de Análisis STS (Sit-to-Stand)

Estructura modular y profesional para análisis de datos de Sit-to-Stand. Incluye soporte para análisis básico y análisis avanzado con métricas de EMG, Hip Z y Centro de Presión.

## Organización de Módulos

### Core Modules (Análisis Básico)

#### `utils.py`
Funciones matemáticas básicas reutilizables:
- `centered_slope()` - Derivada mediante pendiente centrada (7 puntos)
- `cumulative_trapezoid()` - Integral acumulada por trapecios
- `detect_column()` - Búsqueda inteligente de columnas en DataFrames

#### `detection.py`
Lógica de detección de eventos y segmentación de fases:
- `compute_vector_displacements()` - Cálculo de vector de desplazamientos (cambios de signo)
- `compute_windows()` - Sumas acumuladas de ventanas futuras y previas
- `detect_conc_starts()` - Detección de inicio de fase concéntrica (Levantarse)
- `detect_peaks()` - Detección de picos (transición Concéntrica-Excéntrica)
- `detect_ecc_ends()` - Detección de fin de fase excéntrica (Sentarse)
- `pair_repetitions()` - Emparejar eventos de inicio, pico y fin en repeticiones
- `compute_phase_events()` - Detector principal que genera eventos y gráficas
- `compute_acc_phases()` - Marcadores acumulativos de fase **(NEW v2.0)**

**Dataclasses:**
- `PhaseEvent()` - Evento individual de una fase
- `RepEvents()` - Colección de eventos de una repetición **(NEW v2.0)**

#### `metrics.py`
Estructura de datos y cálculo de métricas básicas por repetición:
- `RepResult` - Dataclass con 21 campos de resultados por repetición
- `compute_metrics()` - Cálculo completo: amplitud, duración, velocidad, potencia, trabajo
- `mark_ok_repetitions()` - Marcar repeticiones como OK según umbral de amplitud

#### `plotting.py`
Generación de visualizaciones con matplotlib:
- `plot_general_segmentation()` - Gráfico general con desplazamiento y velocidad
- `plot_per_repetition()` - Gráficos detallados por repetición individual
- `generate_plots()` - Orquestador que genera todos los gráficos

#### `export.py`
Exportación de datos a múltiples formatos:
- `create_sheet1_variables()` - Crear DataFrame completo de variables (Hoja 1)
- `export_to_excel()` - Exportación a Excel con 3 hojas (Hoja1, Hoja2, Hoja3)
- `export_to_json()` - Exportación de parámetros a JSON
- `export_advanced_sheet3()` - Genera Hoja3 avanzada con métricas por fase **(NEW v2.0)**

### Advanced Modules (NEW v2.0)

#### `advanced_metrics.py` ⭐ NEW
Computador avanzado de estadísticos genéricos y detección de columnas Noraxon:

**Clase PhaseComputer:**
- Constructor: Recibe datos de referencia, columna y unidades
- `range_mm_to_m()` - Rango de desplazamiento convertido (mm → m)
- `stats()` - Media, máximo, mínimo en período especificado
- `power_work()` - Potencia media/máxima y trabajo acumulado
- `mean()` / `stdev()` - Media y desviación estándar por período
- `max_val()` / `min_val()` - Máximos y mínimos absolutos
- `_slice()` - Método privado de slicing temporal

**Funciones de Detección:**
- `trapz_manual()` - Integración trapezoidal (compatible NumPy 2.x sin scipy)
- `detect_emg_columns()` - Detecta 7 canales EMG específicos de Noraxon
- `detect_cop_columns()` - Detecta Centro de Presión pre-calculado o raw
- `detect_column_variants()` - Búsqueda genérica por keywords con fallbacks

**Compatibilidad:**
- Works with NumPy 2.x (sin scipy)
- Manejo automático de unidades (mm, m, mV, etc.)

#### `metadata.py` ⭐ NEW
Extractor de metadatos de files Noraxon:

**Función principal:**
- `read_metadata()` - Lee hoja 'MetaData_&_Parameters' de Excel

**Campos capturados:**
- Código / ID del sujeto
- Altura (cm)
- Peso (kg)
- Tipo de prueba
- Fecha de la prueba
- Altura de silla

## Uso Básico

```python
from src import run_tool

# Análisis básico (solo BCM Z)
excel, plot, json = run_tool(
    file_path='data/input/datos.xlsx',
    sheet_name='Reducido',
    mass_kg=75.0,
    window=30
)

# Retorna:
# - excel: Ruta al archivo Excel (3 hojas)
# - plot: Ruta a imagen PNG de gráficos
# - json: Ruta a parámetros JSON
```

## Uso Avanzado (v2.0 Enhanced)

```python
from sts_analysis_tool_enhanced import run_tool_enhanced

# Análisis completo con Hip Z, EMG, CoP_SD
excel, plot, json = run_tool_enhanced(
    file_path='data/input/datos_noraxon.xlsx',
    sheet_name='Reducido',
    mass_kg=75.0,
    window=30,
    close_last_seated_at_end=True  # Opcional: cerrar última fase
)

# Retorna 3-sheet Excel con:
# - Hoja1: Variables + Acc Phases
# - Hoja2: Parámetros y gráfico
# - Hoja3: Métricas por fase (Hip Z, EMG, CoP SD)
```

## Interfaz de Línea de Comandos

### Versión Básica
```bash
python sts_analysis_tool_exact.py \
  --input data/input/datos.xlsx \
  --sheet Reducido \
  --mass-kg 75 \
  --window 30 \
  --n-positive 30 \
  --vel-th 0.1 \
  --ok-th 0.85
```

### Versión Enhanced (v2.0)
```bash
python sts_analysis_tool_enhanced.py \
  --input data/input/datos_noraxon.xlsx \
  --sheet Reducido \
  --mass-kg 75 \
  --window 30
```

## Comparación: Versiones

| Característica | exact.py | enhanced.py v2.0 |
|---|---|---|
| **Core**: Detección de fases | ✅ | ✅ |
| **Core**: Métricas básicas | ✅ | ✅ |
| **Advanced**: Hip Z (desplazamiento/velocidad) | ❌ | ✅ NEW |
| **Advanced**: EMG (7 canales automáticos) | ❌ | ✅ NEW |
| **Advanced**: CoP SD (Centro presión) | ❌ | ✅ NEW |
| **Advanced**: Acc Phases (marcadores) | ❌ | ✅ NEW |
| **Advanced**: Metadatos Noraxon | ❌ | ✅ NEW |
| Líneas de código | ~280 | ~450 |
| Complejidad | Baja | Media |

## Ventajas Arquitectónicas

✅ **Modular** - Funciones independientes, cada módulo ≤350 líneas
✅ **Testeable** - Cada función tiene responsabilidad única
✅ **Documentado** - Docstrings completos en todas funciones
✅ **Mantenible** - Separación clara de responsabilidades
✅ **Extensible** - Fácil agregar nuevas columnas/métricas
✅ **Profesional** - Estándares OOP, type hints, error handling
✅ **Versionado** - Git-ready con .gitignore
✅ **Robusto** - Manejo de datos faltantes, columnas variantes
