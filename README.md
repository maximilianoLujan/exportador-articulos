## Qué es esta app

Esta API recibe un PDF, extrae texto y detecta entidades bibliográficas (hoy: artículos; mañana: libros, partes de libro, etc.).

## Concepto clave: "proceso"

Un **proceso** es simplemente _una ejecución del pipeline_ sobre un PDF.

- Subes un PDF → se crea un proceso
- Ese proceso guarda: el PDF, el texto extraído (opcional), y una lista de **ítems extraídos** (artículos/libros/…)
- Si un ítem no se puede parsear, el proceso **no falla entero**: el ítem se guarda con `parse_error` para depurar.

Esto te permite:

- Repetir importaciones y comparar resultados.
- Mejorar el parser sin perder trazabilidad.
- Extender a nuevos tipos (libro/parte) sin rehacer la base.

## Base de datos

Por defecto usa SQLite en `./nodexl.db`.

Ejemplo PostgreSQL:

`DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/nodexl`

## Endpoints

- `POST /import/pdf` → devuelve artículos detectados (y guarda proceso/ítems en BBDD)
- `GET /procesos` → lista últimos procesos
- `GET /procesos/{id}` → detalle de un proceso
- `GET /procesos/{id}/items` → ítems extraídos (con `data` y `parse_error`)

## Grafo (para el frontend)

Para dibujar un grafo estilo NodeXL en el frontend, la API te devuelve **vertices** y **edges** a partir de los ítems parseados de un proceso.

- `GET /grafo/procesos` → grafo global (incluye nodos `process`)
- `GET /grafo/procesos/{id}` → devuelve `{ vertices, edges, summary }` para un proceso
- `GET /grafo/procesos/{id}/vertices` → sólo vertices
- `GET /grafo/procesos/{id}/edges` → sólo edges
- `GET /grafo/procesos/{id}/metricas` → métricas estándar (centralidades, clustering, k-core, HITS, Louvain, etc.)
- `GET /grafo/metricas` → métricas del grafo global (desde BBDD, usando `limit`)

Formato:

- `vertices[]`: nodos con `id`, `type` y `label`
  - `type = person` (autor)
  - `type = publication` (artículo)
- `edges[]`: aristas con `source`, `target`, `type`
  - `type = authored` (autor → artículo)

El frontend normalmente:

1. llama a `GET /procesos` para elegir un proceso
2. llama a `GET /grafo/procesos/{id}`
3. pinta `vertices` y `edges` en tu librería (Cytoscape, vis-network, d3, etc.)

## Clasificación de artículos

La app intenta asignar una categoría por artículo:

- `Articulos Congresos Internacionales`
- `Articulos Congresos Nacionales`
- `Articulos Revistas Internacionales`
- `Articulos Revistas Nacionales`

Si el PDF trae encabezados de sección, se usan como fuente principal. Si no, se infiere con heurísticas:

- **Revistas**: presencia de `ISSN`/`vol.` en el texto del ítem.
- **Nacional/Internacional**: patrón `LUGAR: EDITORIAL, AÑO` (ej. `AMSTERDAM: ELSEVIER..., 2018`).

En este proyecto, **"nacional" = Argentina** (sin usar APIs externas).

La categoría queda guardada en `data.category` de cada ítem y también aparece en el vertex `publication` del grafo.
