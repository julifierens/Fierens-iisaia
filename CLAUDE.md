# CLAUDE.md

Repositorio de entregas de Julián Alejandro Fierens para la materia
**Introducción a la Ingeniería de Software Asistida por IA** (IISAIA, FIUBA, 2026).
Es público y lo corrige el docente.

Material y consignas oficiales: https://github.com/FIUBA-Posgrado-Inteligencia-Artificial/IISAIA
(`programa.md` y `semanas/NN/source_material/`). Ante una duda sobre qué pide
una entrega, la consigna oficial manda sobre cualquier suposición.

## Estructura

Una carpeta por entrega. Cada `README.md` de carpeta es el **informe** de esa
entrega, no documentación de uso. El `README.md` de la raíz es el índice.

| Carpeta | Entrega | Estado |
|---------|---------|--------|
| `TP1/` | Bad UI: selector astronómico de fecha (un solo HTML) | Entregado. **Congelado: no se modifica.** |
| `TP2/` | Contrato OpenAPI de una API para SPTERO | En curso |
| (a crear) | Trabajo final: SPTERO Web, individual, construido sobre el contrato del TP2 | Pendiente |

## Qué se evalúa, y por qué trabajamos así

Que funcione no alcanza. Se evalúa la **apropiación**: que Julián pueda explicar,
corregir y extender lo que se construyó, y que las decisiones sean suyas y no
las que el modelo eligió por defecto. De ahí salen las reglas de trabajo:

- Antes de crear o modificar archivos, proponer qué se va a hacer y esperar aprobación.
- Las decisiones de diseño (recursos, endpoints, campos, status codes, arquitectura)
  las toma Julián. Claude señala problemas, opciones y consecuencias, pero no
  elige por él ni corrige en silencio.
- Explicar qué hace cada cambio y para qué sirve. El objetivo es aprender a usar
  las herramientas, no solo obtener archivos.
- No hacer commit, push ni abrir PRs sin pedido explícito.

## Registro del proceso

El docente evalúa el proceso, así que se registra mientras ocurre y no al final.

- Los prompts relevantes de cada TP van al `prompts.md` de su carpeta: textuales,
  en orden, con "Qué buscaba" (lo redacta Julián) y "Qué devolvió".
- Si el modelo se equivoca o se desvía, avisarlo en el momento: es material para
  "Qué salió mal". Nunca inventar ni maquillar errores.
- Las decisiones y sus porqués van al `README.md` del TP. La memoria automática
  no sirve para esto: no está en el repositorio y no es evidencia.
- Cuando la consigna pide una sola conversación de IA, el TP se hace en una sola sesión.

## Git

GitHub Flow: rama `feature/<descripcion>` desde `main`, commits chicos (uno por
etapa cerrada), PR a `main`. Mensajes en español: `tipo: descripción en minúscula`
(`docs`, `feat`, `fix`, `chore`).

## Convenciones

- Documentos, comentarios y mensajes de commit en español.
- Los informes siguen la estructura de `TP1/README.md`: qué me propuse construir,
  decisiones que tomé yo, qué salió mal y cómo lo corregí, prompts.

<!-- Al crear TP2/CLAUDE.md, rules o skills, agregar acá una sección
     "Dónde seguir leyendo" con una tabla que apunte a cada uno. -->
