# STS Analysis Tool - Análisis Sit-to-Stand Profesional

[![Test Suite](https://img.shields.io/badge/tests-44%20passing-brightgreen)]() 
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()

**Herramienta profesional para análisis biomecánico de pruebas Sit-to-Stand (STS).**

Estructura modular y extensible que captura automáticamente:
- 📊 **Métricas básicas**: amplitud, duración, velocidad, potencia, trabajo
- 📈 **Hip Z avanzado**: desplazamiento y velocidad del centro de masa por fase
- 🔌 **EMG automático**: detección de 7 canales de electromiografía Noraxon
- 🎯 **Centro de Presión**: métricas COP pre-calculadas o derivadas
- 📋 **Metadatos**: extracción automática de sujeto, peso, altura, tipo de prueba

Estructura modular y extensible que captura automáticamente:
- 📊 **Métricas básicas**: amplitud, duración, velocidad, potencia, trabajo
- 📈 **Hip Z avanzado**: desplazamiento y velocidad del centro de masa por fase
- 🔌 **EMG automático**: detección de 7 canales de electromiografía Noraxon
- 🎯 **Centro de Presión**: métricas COP pre-calculadas o derivadas
- 📋 **Metadatos**: extracción automática de sujeto, peso, altura, tipo de prueba

---

## ⚡ Quick Start (5 minutos)

### 1. Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd Prueba\ 2

# Opción A: Instalación rápida (desarrollo)
pip install -r requirements.txt

# Opción B: Instalación como paquete
pip install -e .

# Verificar instalación
python -c "import src; print('✅ STS Analysis Tool instalado')"
```

### 2. Análisis Básico (2 líneas)

```python
from sts_analysis_tool_enhanced import run_tool_enhanced

# Análisis con datos locales
excel_file, plots_file, json_params = run_tool_enhanced(
    file_path='data/input/tu_archivo.xlsx',
    sheet_name='Reducido',
    mass_kg=75.0  # peso del sujeto en kg
)
print(f"✅ Resultados en: {excel_file}")
```

**Salida generada:**
- 📄 `output/YYYY-MM-DD-HH-MM_<ID>_analysis_enhanced_params.json` - Parámetros
- 📊 `output/YYYY-MM-DD-HH-MM_<ID>_analysis_enhanced.png` - 4 gráficos
- 📑 `output/YYYY-MM-DD-HH-MM_<ID>_analysis_enhanced.xlsx` - 3 hojas (datos, params, métricas por fase)

---

## 📥 Instalación Detallada

### Requisitos Previos
- **Python 3.9+** (probado en 3.9, 3.10, 3.11, 3.12, 3.14)
- **pip** o **conda**
- [Descargar Python](https://www.python.org/downloads/)

### Instalación Paso a Paso

**Windows:**
```bash
# 1. Abrir PowerShell en la carpeta del proyecto
cd C:\ruta\a\Prueba\ 2

# 2. Crear entorno virtual (recomendado)
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar
python -m pytest --version  # debería mostrar pytest 7.x+
```

**macOS/Linux:**
```bash
# 1. Navegar a la carpeta
cd ~/ruta/a/Prueba\ 2

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar
pip install -r requirements.txt

# 4. Verificar
python -m pytest --version
```

### Dependencias

| Paquete | Versión | Uso |
|---------|---------|-----|
| NumPy | 2.0+ | Computación numérica |
| pandas | 2.0+ | Manejo de DataFrames |
| matplotlib | 3.7+ | Visualización |
| openpyxl | 3.1+ | Excel I/O |
| PyYAML | 6.0+ | Configuración |
| pytest | 7.4+ | Testing (dev) |
| pytest-cov | 4.1+ | Coverage reports (dev) |

---

## 💻 Uso Práctico

### Ejemplo 1: Análisis Simple (BCM Z)

```python
from sts_analysis_tool_exact import run_tool

excel, plots, json_data = run_tool(
    file_path='data/input/sujeto_001.xlsx',
    sheet_name='Reducido',
    mass_kg=75.0,        # peso del sujeto
    window=30,           # ventana de suavizado
    vel_threshold=0.05,  # umbral de velocidad (m/s)
    ok_repetitions_threshold=0.85
)

print(f"📊 Excel guardado en: {excel}")
print(f"📈 Gráficos en: {plots}")
```

### Ejemplo 2: Análisis Completo con EMG/CoP (v2.0)

```python
from sts_analysis_tool_enhanced import run_tool_enhanced

# Análisis con soporte para canales Noraxon
excel, plots, json_data = run_tool_enhanced(
    file_path='data/input/sujeto_noraxon.xlsx',
    sheet_name='Reducido',
    mass_kg=75.0,
    height_cm=175.0,  # opcional: para cálculos avanzados
    close_last_seated_at_end=True  # cerrar última fase al final
)

# Genera automáticamente:
# - Hoja1: Variables (BCM Z, Hip Z, EMG x7, CoP SD, etc)
# - Hoja2: Parámetros (por repetición)
# - Hoja3: Métricas por fase (concéntrica, excéntrica, sentado)
```

### Ejemplo 3: Uso Programático Avanzado

```python
import pandas as pd
from src.detection import compute_phase_events
from src.analysis import generate_phase_dataframe
from src.advanced_metrics import detect_emg_columns, detect_cop_columns

# Cargar datos
df = pd.read_excel('data/input/datos.xlsx', sheet_name='Reducido')
time_col = 'Tiempo'  # o auto-detect

# Paso 1: Detectar fases (stand, sit, vel, aceleración)
events, figures = compute_phase_events(
    df, time_col, mass_kg=75.0, window=30
)

# Paso 2: Generar métricas por fase
z_mm = df['BCM Z'].values
phase_df = generate_phase_dataframe(
    df=df,
    time_col=time_col,
    rep_events=events['rep_events'],
    marker_to_time=events['marker_to_time'],
    z_mm=z_mm * 1000,  # convertir a mm
    vel_m_s=df['Velocidad'].values,
    acc_m_s2=df['Aceleración'].values,
    power_W=df.get('Potencia', 0),
    mass_kg=75.0,
    dt=0.01  # 100 Hz sampling
)

# Paso 3: Exportar
phase_df.to_excel('output/fases_detalladas.xlsx')
```

### Ejemplo 4: Obtener Metadatos de Excel Noraxon

```python
from src.metadata import read_metadata

# Extrae metadatos de la hoja 'MetaData_&_Parameters'
metadata = read_metadata('data/input/datos_noraxon.xlsx')

print(f"Sujeto ID: {metadata.get('subject_code')}")
print(f"Peso: {metadata.get('weight_kg')} kg")
print(f"Altura: {metadata.get('height_cm')} cm")
print(f"Tipo prueba: {metadata.get('test_type')}")
```

---

## 🔧 Configuración

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

## 🧪 Testing & Calidad de Código

### Ejecutar Tests

```bash
# Test básico (todos los tests)
python -m pytest

# Test con verbosidad
python -m pytest -v

# Test de un módulo específico
python -m pytest tests/test_detection.py

# Test con salida de cobertura
python -m pytest --cov=src tests/
```

### Cobertura de Código

```bash
# Generar reporte de cobertura detallado
python -m pytest --cov=src --cov-report=term-missing --cov-report=html tests/

# Abrir reporte HTML (se abrirá htmlcov/index.html)
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
firefox htmlcov/index.html  # Linux
```

**Estado Actual:**
- ✅ **80% cobertura** general del proyecto
- ✅ **44 tests** pasando
- ✅ Módulos más críticos: 85-97% cobertura
  - detection.py: 95%
  - plotting.py: 97%
  - logger.py: 96%
  - metadata.py: 91%
  - advanced_metrics.py: 80%

### Integración Continua (CI/CD)

El proyecto incluye GitHub Actions que:
- Ejecuta tests automáticamente en cada push (3 OS × 4 Python versions)
- Genera reportes de cobertura
- Valida que no haya regresiones

---

## ❓ Troubleshooting & FAQ

### P: "ModuleNotFoundError: No module named 'src'"
**R:** Instala el paquete en modo desarrollo:
```bash
pip install -e .
```
O ejecuta scripts desde la raíz del proyecto:
```bash
python -m pytest  # en lugar de cd tests && pytest
```

### P: "FileNotFoundError: data/input/archivo.xlsx"
**R:** El archivo debe existir. Opciones:
```bash
# 1. Verificar ruta
ls data/input/  # o dir data\input en Windows

# 2. Usar ruta absoluta
excel, plots, json = run_tool_enhanced(
    file_path='C:/Users/PC/Desktop/Prueba 2/data/input/archivo.xlsx',
    ...
)

# 3. Copiar archivo a data/input/
cp /ruta/al/archivo.xlsx data/input/
```

### P: "ValueError: Sheet 'Reducido' not found" o "KeyError: 'BCM Z'"
**R:** El nombre de la hoja o columna es incorrecto. Verifica:
```python
import openpyxl
wb = openpyxl.load_workbook('data/input/archivo.xlsx')
print(wb.sheetnames)  # ver nombres de hojas

import pandas as pd
df = pd.read_excel('data/input/archivo.xlsx', sheet_name='Reducido')
print(df.columns)  # ver nombres de columnas
```

### P: "MemoryError" con archivos grandes
**R:** Procesa en chunks o reduce la frecuencia de muestreo:
```python
# Leer solo columnas necesarias
df = pd.read_excel(file_path, sheet_name=sheet_name, 
                   usecols=['Tiempo', 'BCM Z', 'Velocidad'])

# O decimar datos (usar cada 2ª muestra)
df = df.iloc[::2, :]  # reduce 50%
```

### P: "EMG columns not found" (análisis Enhanced)
**R:** Verifica que el archivo tenga canales EMG correctos:
```python
from src.advanced_metrics import detect_emg_columns
cols = detect_emg_columns(df)  # retorna lista de EMG encontrados
print(f"Canales EMG detectados: {cols}")
```

Noraxon standard channel names:
- `EMG1 Quad`, `EMG2 Glut`, `EMG3 Tibialis`, etc.
- Variantes: `Ch 1`, `Channel 1`, `EMG 1`

### P: "Gráficos no se generan" o "Imagen pequeña/ilegible"
**R:** Ajusta parámetros de matplotlib:
```python
import matplotlib
matplotlib.rcParams['figure.figsize'] = (14, 10)  # más grande
matplotlib.rcParams['font.size'] = 12  # letra más grande
```

### P: "¿Cómo reportar un bug?"
**R:** Abre un issue en GitHub con:
1. Versión de Python: `python --version`
2. Versión del paquete: `pip show -f stsanalysis`
3. Comando/código que falló (completo)
4. Mensaje de error (completo) y traceback
5. Archivo de ejemplo (si es posible)

---

## 📂 Estructura del Proyecto

```
Prueba 2/
├── src/                          # Módulos principales
│   ├── __init__.py              # Entry points (run_tool, run_tool_enhanced)
│   ├── analysis.py              # Análisis por fases ⭐
│   ├── advanced_metrics.py      # PhaseComputer, EMG/CoP detection ⭐
│   ├── detection.py             # Detección de eventos (95% coverage)
│   ├── metrics.py               # RepResult dataclass (87% coverage)
│   ├── plotting.py              # Visualización (97% coverage)
│   ├── export.py                # Excel/JSON export
│   ├── metadata.py              # Metadatos Noraxon
│   ├── config.py                # Configuración (84% coverage)
│   ├── logger.py                # Logging (96% coverage)
│   └── utils.py                 # Utilidades matemáticas (79% coverage)
│
├── tests/                        # Suite de tests (44 tests, 80% coverage)
│   ├── test_analysis.py         # 19 tests para analysis.py
│   ├── test_advanced_metrics.py # 11 tests para advanced_metrics.py
│   ├── test_detection.py        # Detection, event pairing
│   ├── test_export_plotting_metadata.py
│   ├── test_config.py, test_logger.py, test_utils.py, test_metrics.py
│   └── __pycache__/
│
├── data/                         # Datos de entrada/salida
│   ├── input/                   # Tus archivos .xlsx
│   ├── output/                  # Resultados generados
│   └── logs/                    # Archivos de log
│
├── docs/                         # Documentación
│   ├── README.md                # Este archivo
│   ├── IMPROVEMENTS_v2.1.md     # Cambios y mejoras recientes
│   ├── PHASE_4_SUMMARY.md       # Resumen de fase de desarrollo
│   └── CONTRIBUTING.md          # Directrices de contribución
│
├── htmlcov/                      # Reportes de cobertura (generado)
├── config.yaml                   # Configuración defaults
├── requirements.txt              # Dependencias Python
├── setup.py                      # Configuración de paquete
├── Makefile                      # Tareas de desarrollo
├── sts_analysis_tool_enhanced_v2.py  # Script principal (v2.0)
├── sts_analysis_tool_exact.py        # Script básico
├── pytest.ini                    # Configuración pytest
├── LICENSE                       # MIT License
└── CONTRIBUTING.md              # Guía de contribución
```

---

## 🚀 Desarrollo Avanzado

### Extender con Nuevas Columnas/Métricas

1. **Agregar detección de columnas** en `advanced_metrics.py`:

```python
def detect_force_columns(df: pd.DataFrame) -> List[str]:
    """Detecta canales de fuerza/presión."""
    keywords = ['force', 'fuerza', 'N/kg', 'normalizado']
    return detect_column_variants(df, keywords)
```

2. **Usar en análisis**:

```python
force = detect_force_columns(df)
computer = PhaseComputer(df, force[0], 'N')
stats = computer.stats(t_start, t_end)
```

### Agregar Nuevos Test

```bash
# 1. Crear archivo test_myfeature.py en tests/
# 2. Escribir tests con pytest
# 3. Ejecutar
python -m pytest tests/test_myfeature.py -v
```

### Modificar Configuración

Editar `config.yaml`:
```yaml
sampling_rate: 100  # Hz
velocity_threshold: 0.05  # m/s
ok_reps_threshold: 0.85
```

---

## 📊 Características por Versión

## 🤝 Contribuir

¿Ideas de mejora? Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para:
- Estructura de código de conducta
- Proceso de PR
- Estándares de código
- Cómo reportar bugs

---

## 📝 Licencia

MIT License - Libre para uso académico y comercial.
Ver [LICENSE](../LICENSE) para detalles.

---

## 🔗 Referencias Útiles

- [GitHub](https://github.com/tu-repo)
- [Documentación de Módulos](README.md#organización-de-módulos)
- [CI/CD Status](https://github.com/tu-repo/actions)
- [Coverage Report](htmlcov/index.html)

---

**Última actualización:** Marzo 2026
**Versión:** 2.1 (80% code coverage, 44 tests passing)


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
