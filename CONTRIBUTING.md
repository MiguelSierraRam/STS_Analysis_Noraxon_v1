# Contributing to STS Analysis Tool

¡Gracias por tu interés en contribuir! Aquí hay las pautas para hacerlo.

## Desarrollo Local

### 1. Fork y clonar

```bash
git clone https://github.com/YOUR-USERNAME/STS_Analysis_Noraxon_v1.git
cd STS_Analysis_Noraxon_v1
```

### 2. Crear rama de feature

```bash
git checkout -b feature/mi-feature
```

### 3. Instalar en modo desarrollo

```bash
pip install -e .[dev]
```

## Desarrollo

### Tests
```bash
make test          # Ejecutar tests
make test-cov      # Con cobertura
```

### Linting y Format
```bash
make lint          # Validar código
make format        # Formatear automáticamente
```

### Build
```bash
make build         # Crear distribución
```

## Pautas de Código

1. **Type hints**: Todas las funciones deben tener anotaciones de tipo
2. **Docstrings**: Google style con descripción, Args, Returns, Raises
3. **Tests**: Cada función pública debe tener test
4. **Black**: Código formateado con `make format`
5. **Flake8**: Sin warnings de linting

## Proceso de PR

1. Escribe tests para tu feature
2. Asegúrate de que `make test` pasa
3. Asegúrate de que `make lint` pasa
4. Crea un Pull Request con descripción clara
5. Espera revisión

## Reportar Bugs

Por favor crea un Issue con:
- Título descriptivo
- Descripción del bug
- Pasos para reproducir
- Comportamiento esperado vs actual
- Versión de Python y dependencias

## Sugerencias de Features

Abre un Issue con:
- Descripción de la feature
- Caso de uso
- Ejemplos de uso deseado
