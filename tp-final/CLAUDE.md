# CLAUDE.md — TP final: SPTERO Web

Aplicación web para analizar ensayos Small Punch Test, construida sobre el
contrato del TP2 y reutilizando el motor científico de SPTERO. Trabajo individual.

Antes de tocar código, leer la spec:
`docs/superpowers/specs/2026-10-12-sptero-web-design.md`. Lo que diga la spec
manda sobre cualquier suposición; si hace falta cambiarla, se propone y se edita
en un commit propio.

## Mapa de carpetas

| Ruta | Qué hay |
|---|---|
| `sptero_core/` | Lógica científica pura (numpy). Copiada del script original sin cambiar fórmulas. No importa nada de `app/`, no imprime, no lee disco. |
| `app/` | FastAPI: `main.py` (rutas y handlers), `schemas.py` (Pydantic), `service.py` (casos de uso), `repository.py` (sqlite3). |
| `static/` | Interfaz: `index.html`, `styles.css`, `app.js` (JS vanilla + Plotly.js). |
| `tests/` | pytest: caracterización contra el original, core sintético, repositorio, API, contrato. |
| `openapi.yaml` | Contrato v1.1. Evoluciona desde `../TP2/openapi.yaml`, que no se toca. |
| `docs/superpowers/` | Spec y plan. |
| `data/` | Base SQLite local. No se versiona. |
| `README.md` | Informe de la entrega (no es documentación de uso). |
| `prompts.md` | Prompts relevantes, textuales y en orden. |

## Cómo se abre una sesión

Las sesiones de desarrollo arrancan con el directorio de trabajo en `tp-final/`
(`cd tp-final` y después `claude`). Desde la raíz del repo, Claude Code no lee
`.claude/settings.json` ni el subagente (verificado; ver spec, sección 10). La
primera vez hay que aceptar el diálogo de confianza del workspace: hasta entonces se
ignoran las reglas `allow` (las `deny` y `ask` aplican igual).

## Comandos

Desde `tp-final/`:

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python -m pytest
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Variables de entorno:
- `SPTERO_DB`: ruta de la base (por defecto `data/sptero.db`).
- `SPTERO_ORIGINAL`: ruta local a `Programa SPTERO.py`, para los tests de caracterización.
- `SPTERO_RAW_SAMPLE`: ruta local a un `.raw` real (por ejemplo `P3_304L_L.raw`).

Sin las dos últimas, los tests de caracterización se saltean.

## Reglas de trabajo

- El script original y los `.raw` experimentales **no se suben al repositorio**.
  Se usan desde rutas locales.
- Las fórmulas del core no se modifican. Los únicos cambios permitidos respecto del
  original son de entrada/salida, y cada uno lleva su test de caracterización.
- TDD: el test se ve fallar antes de escribir el código. "En verde" es la suite
  completa con su salida a la vista.
- La API respeta `openapi.yaml`. Si un endpoint, campo o código tiene que cambiar,
  primero cambia el contrato y Julián lo aprueba.
- Las decisiones de diseño las toma Julián. Si algo de la spec o del plan no cierra,
  se frena y se consulta, no se corrige en silencio.
- Si el agente se equivoca o se desvía, se avisa en el momento: es material para
  "Qué salió mal" del README.
- No commit, push ni PR sin pedido explícito.

## Convenciones

- Nombres de la API en inglés (heredados del TP2); código interno, comentarios,
  documentos y commits en español.
- Unidades en los nombres de campos (`thickness_mm`, `pm_n`).
- Commits: `tipo: descripción en minúscula` (`feat`, `fix`, `test`, `docs`, `chore`).
- Ramas: `feature/tp-final-<etapa>` desde `main`, un PR por etapa.

## Configuración del agente

- `.claude/settings.json`: permisos del proyecto.
- `.claude/rules/core.md` y `.claude/rules/api.md`: reglas con alcance por carpeta.
- `.claude/skills/registrar-prompt/`: `/registrar-prompt` agrega una entrada a `prompts.md`.
- `.claude/agents/verificador-cientifico.md`: compara el core con el original.

Las reglas de archivos usan `Edit(...)`, que cubre todas las herramientas que
escriben (una regla `Write(...)` con ruta nunca se aplica), y rutas `//…` para
alcanzar carpetas fuera de `tp-final/`.

## Decisiones cerradas que condicionan el código

- D1: cero por precarga solo con corrección de flexibilidad, como el original.
- D2: el espesor se corrige con `PATCH /tests/{id}` y recalcula sin versiones.
- D3: la comparación superpone dos curvas del mismo tipo (crudas o procesadas).
- D4: guardado automático con estado visible; eliminar pide confirmación.
- D5: configuración en `tp-final/.claude/`, sesiones desde `tp-final/`.

El detalle está en la spec; el porqué de cada una, en el README.
