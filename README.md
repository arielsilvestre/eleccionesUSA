# Análisis de Midterms 2026 (EE.UU.)

Proyecto de análisis electoral para evaluar si el Partido Republicano
retiene la mayoría en House y Senate en las elecciones de medio término
del 3 de noviembre de 2026.

El análisis se basa en **condiciones de fondo**: historial electoral
(MIT Election Lab) e indicadores económicos (BLS). No se usan encuestas
ni modelos de intención de voto directa.

---

## Pregunta central

> ¿Retiene el oficialismo (Partido Republicano / administración Trump)
> la mayoría en la Cámara de Representantes y/o el Senado?

La variable de resultado es **control de mayoría por cámara**, no net
seat change ni voto popular agregado.

---

## Fuentes de datos

| Fuente | Rol | Acceso |
|--------|-----|--------|
| MIT Election Lab (Harvard Dataverse) | Historial electoral 1976–2024 | CSV descarga manual |
| BLS API (LAUS + CPI) | Desempleo estatal e inflación | API REST gratuita |
| FEC | Resultados electorales certificados | Tabla de referencia |
| House.gov Election Statistics | Serie histórica 1920–presente | Tabla de referencia |

---

## Estructura

```
/analysis/          → scripts Python de procesamiento
/data/bls/          → datos BLS (JSON crudos + CSVs)
/data/mit-election-lab/ → CSVs MIT Election Lab
/data/fec/          → datos FEC (referencia)
/data/house-gov/    → datos House.gov (referencia)
/output/            → resultados del análisis
/docs/              → documentación metodológica y planes
```

---

## Stack técnico

- Python 3.11 · pandas · requests · python-dotenv
- PostgreSQL en Railway (Fase 4, pendiente)

---

## Outputs actuales

| Archivo | Descripción |
|---------|-------------|
| `output/house_swing_2026.csv` | 74 distritos House competitivos |
| `output/senate_swing_2026.csv` | 11 estados Senate swing (Class 2) |
| `output/bls_swing_context.csv` | Desempleo agosto 2026 por estado swing + cambio YoY |
| `data/bls/laus_swing_states.csv` | Serie mensual de desempleo 2022–2026, 28 estados |
| `data/bls/cpi_national.csv` | CPI-U nacional mensual 2022–2026 |

---

## Decisiones metodológicas

Documentadas en [`DECISIONES.md`](DECISIONES.md) (D-01 a D-08).
Progreso del proyecto en [`ROADMAP.md`](ROADMAP.md).
Registro de sesiones en [`BITACORA.md`](BITACORA.md).

---

## Declaración de uso de inteligencia artificial

Este proyecto utilizó **Claude Code (Anthropic)** como herramienta de
asistencia técnica a lo largo del desarrollo.

### Qué hizo el autor

- Definición del problema y la pregunta de investigación.
- Selección y evaluación de fuentes de datos (MIT Election Lab, BLS, FEC,
  House.gov).
- Todas las decisiones metodológicas: criterio de swing (D-01 a D-06),
  exclusión de encuestas, definición de la variable de resultado,
  alcance geográfico, rango temporal, elección de series BLS.
- Supervisión y revisión de cada output generado.
- Corrección de errores y validación de resultados.
- Dirección del análisis en cada etapa.

### Qué hizo la IA

- Redacción e iteración del código Python bajo instrucciones explícitas.
- Ejecución de pasos de implementación definidos en planes escritos por
  el autor.
- Organización y documentación del repositorio (ROADMAP, BITACORA,
  DECISIONES) siguiendo criterios definidos por el autor.
- Detección de algunos errores técnicos durante la implementación
  (manejo de valores faltantes en la API de BLS, casos edge en fusion
  tickets, etc.).

### Alcance y limitaciones

La IA no tomó ninguna decisión de diseño ni metodológica de forma
autónoma. Toda decisión no trivial fue consultada explícitamente y
aprobada por el autor antes de implementarse. El análisis, los criterios
y las interpretaciones son del autor; el código es el medio de
implementación.

---

*Proyecto en curso — elecciones: 3 de noviembre de 2026.*
