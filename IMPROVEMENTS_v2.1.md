# STS Analysis Tool v2.1 - Mejoras profesionales (Logging + Config)

## 🎯 Cambios principales en v2.1

### ✨ 1. Sistema de Configuración Centralizado (config.yaml)

Ahora puedes configurar todos los parámetros sin usar CLI:

```yaml
# config.yaml
window: 30
n_positive: 30
vel_th_m_s: 0.1
ok_th: 0.85
mass_kg: null
output_directory: 'data/output'
log_directory: 'data/logs'
make_plot: true
csv_export: false
```

**Uso:**
```bash
# Usar configuración por defecto
python sts_analysis_tool_enhanced_v2.py --input file.xlsx

# Con configuración custom
python sts_analysis_tool_enhanced_v2.py --config mi_config.yaml --input file.xlsx

# Ver configuración actual
python sts_analysis_tool_enhanced_v2.py --show-config
```

**Ventajas:**
- ✅ No repetir parámetros CLI en cada ejecución
- ✅ Fácil mantener presets diferentes por proyecto
- ✅ CLI y config.yaml se complementan (CLI override config.yaml)

---

### 📊 2. Logging Profesional y Centralizado

Sistema de logging completo con:
- **File + Console**: Logs en archivo `data/logs/sts_analysis.log` Y en consola
- **Niveles**: DEBUG | INFO | WARNING | ERROR | CRITICAL
- **Rotacion automática**: Los logs se rotan cada 10MB (manteniendo 5 backups)
- **Timestamps**: Cada log incluye fecha, hora, módulo y nivel

**Ejemplo de logs:**
```
2026-03-11 14:35:22,123 - src.logger - INFO - STS Analysis Tool inicializado
2026-03-11 14:35:22,124 - src.logger - INFO - Nivel de logging: INFO
2026-03-11 14:35:22,125 - src.logger - INFO - Logs guardados en: data/logs/sts_analysis.log
2026-03-11 14:35:23,456 - sts_analysis_tool_enhanced_v2 - INFO - Iniciando análisis: data/input/file.xlsx
2026-03-11 14:35:23,457 - sts_analysis_tool_enhanced_v2 - DEBUG - Leyendo datos de Excel...
2026-03-11 14:35:25,789 - sts_analysis_tool_enhanced_v2 - INFO - ✓ Análisis completado correctamente
```

**Uso:**
```bash
# DEBUG (detallado)
python sts_analysis_tool_enhanced_v2.py --input file.xlsx --log-level DEBUG

# INFO (normal)
python sts_analysis_tool_enhanced_v2.py --input file.xlsx --log-level INFO

# WARNING (solo advertencias)
python sts_analysis_tool_enhanced_v2.py --input file.xlsx --log-level WARNING

# Custom log directory
python sts_analysis_tool_enhanced_v2.py --input file.xlsx --log-dir /path/to/logs
```

---

### 📦 Nuevos módulos internos

#### `src/config.py` - Gestor de Configuración
```python
from src.config import get_config, load_config

# Cargar configuración por defecto
config = get_config()
print(config.get('window'))  # 30
print(config.get('logging.level'))  # INFO

# Cargar configuración custom
config = load_config('mi_config.yaml')
```

**Características:**
- Singleton pattern (una única instancia)
- Notación de puntos para rutas nested: `config.get('logging.level')`
- Defaults automáticos si falta clave

#### `src/logger.py` - Logging Centralizado
```python
from src.logger import get_logger, LoggerManager

# Configurar logging (automático en __main__)
LoggerManager.configure()

# Obtener logger para un módulo
logger = get_logger(__name__)
logger.info("Mensaje informativo")
logger.debug("Mensaje de debug")
logger.error("Error encontrado", exc_info=True)
```

**Características:**
- RotatingFileHandler (logs rotan por tamaño)
- Consola + archivo simultáneamente
- Formato personalizable
- Inicialización automática

---

## 🚀 Ejemplos de uso completo

### Ejemplo 1: Análisis individual con configuración por defecto
```bash
python sts_analysis_tool_enhanced_v2.py --input data/input/patient01.xlsx --mass-kg 75
```

Log esperado:
```
2026-03-11 14:35:23 - sts_analysis_tool_enhanced_v2 - INFO - Iniciando análisis: data/input/patient01.xlsx
2026-03-11 14:35:23 - sts_analysis_tool_enhanced_v2 - INFO - Parámetros de análisis:
2026-03-11 14:35:23 - sts_analysis_tool_enhanced_v2 - INFO -   - window: 30
2026-03-11 14:35:23 - sts_analysis_tool_enhanced_v2 - INFO - ✓ ANÁLISIS COMPLETADO
```

### Ejemplo 2: Batch processing con logs detallados
```bash
python sts_analysis_tool_enhanced_v2.py \
  --batch data/input \
  --out data/output \
  --mass-kg 75 \
  --csv \
  --log-level DEBUG
```

Log esperado:
```
2026-03-11 14:35:23 - sts_analysis_tool_enhanced_v2 - INFO - STS Analysis Tool iniciado
2026-03-11 14:35:23 - sts_analysis_tool_enhanced_v2 - INFO - Iniciando batch processing: data/input → data/output
2026-03-11 14:35:24 - sts_analysis_tool_enhanced_v2 - INFO - Processing: patient01.xlsx
2026-03-11 14:35:24 - sts_analysis_tool_enhanced_v2 - DEBUG - Leyendo datos de Excel...
2026-03-11 14:35:25 - sts_analysis_tool_enhanced_v2 - DEBUG - Datos cargados: 1000 muestras
2026-03-11 14:35:30 - sts_analysis_tool_enhanced_v2 - INFO - ✓ Análisis completado correctamente
2026-03-11 14:35:30 - sts_analysis_tool_enhanced_v2 - DEBUG -   Excel: data/output/patient01_analysis_enhanced.xlsx
2026-03-11 14:35:30 - sts_analysis_tool_enhanced_v2 - DEBUG -   Plot: data/output/patient01_analysis_enhanced.png
... (continúa con otros archivos)
2026-03-11 14:36:15 - sts_analysis_tool_enhanced_v2 - INFO - ✓ BATCH COMPLETADO
2026-03-11 14:36:15 - sts_analysis_tool_enhanced_v2 - INFO -   Total: 5, Éxito: 5, Fallos: 0
```

### Ejemplo 3: Configuración custom
```bash
# Crear config_strict.yaml
cat > config_strict.yaml << EOF
window: 20
n_positive: 40
vel_th_m_s: 0.15
ok_th: 0.9
mass_kg: 70
strict_mode: true
logging:
  level: 'DEBUG'
  console_output: true
EOF

# Usar configuración custom
python sts_analysis_tool_enhanced_v2.py --config config_strict.yaml --input file.xlsx

# Ver configuración antes de ejecutar
python sts_analysis_tool_enhanced_v2.py --config config_strict.yaml --show-config
```

---

## 📝 Estructura de logs

Logs se guardan en: `data/logs/sts_analysis.log`

Rotacion automática:
- Máximo 10 MB por archivo
- Se mantienen 5 backups:
  - `sts_analysis.log` (actual)
  - `sts_analysis.log.1` (backup 1)
  - `sts_analysis.log.2` (backup 2)
  - etc.

---

## 🔧 Configuración de logging en config.yaml

```yaml
logging:
  level: 'INFO'           # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  file_size_mb: 10        # Rotar cuando archivo > 10MB
  backup_count: 5         # Mantener 5 backups
  console_output: true    # Mostrar logs en consola además de archivo
```

---

## ✅ Checklist: Cómo usar v2.1

- [ ] Revisar `config.yaml` y personalizar si necesario
- [ ] Ejecutar con `--show-config` para ver valores actuales
- [ ] Usar `--log-level DEBUG` para troubleshooting
- [ ] Revisar `data/logs/sts_analysis.log` después de ejecución
- [ ] Crear `config_custom.yaml` para proyectos específicos
- [ ] Usar `--config` para cargar presets diferentes

---

## 🎓 Comparación: v2.0 vs v2.1

| Aspecto | v2.0 | v2.1 |
|---------|------|------|
| CLI parameters | ✅ | ✅ |
| Config file (YAML) | ❌ | ✅ NEW |
| Logging + Rotation | ❌ | ✅ NEW |
| Config precedence | - | CLI > config.yaml |
| Module: config.py | ❌ | ✅ NEW |
| Module: logger.py | ❌ | ✅ NEW |
| Log directory | - | `data/logs/` |
| Default log level | - | INFO (configurable) |

---

**Versión mejorada**: v2.1.0
**Modulos actualizado**: sts_analysis_tool_enhanced_v2.py
**Dependencias nuevas**: pyyaml (para parsing YAML)
