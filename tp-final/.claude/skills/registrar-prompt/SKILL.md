---
name: registrar-prompt
description: Agrega una entrada al prompts.md del TP final con un prompt de Julián copiado textual, en el formato del repositorio. Usar solo cuando Julián lo pide con /registrar-prompt.
argument-hint: "[título corto de la entrada]"
disable-model-invocation: true
---

# Registrar un prompt en `prompts.md`

Qué prompt es relevante lo decide Julián; por eso esta skill se invoca solo a mano.

## Dónde está el archivo

El archivo es el `prompts.md` que está **al lado de la carpeta `.claude/` que
contiene esta skill**, es decir, en la raíz del TP final. Las sesiones de
desarrollo arrancan en `tp-final/`, así que normalmente la ruta es `./prompts.md`.
Si el directorio de trabajo es la raíz del repositorio, es `tp-final/prompts.md`.
Antes de escribir, confirmá que el archivo existe y empieza con
`# Prompts — TP final`; si no, frená y preguntá. Nunca crees un `prompts.md` nuevo.

## Pasos

1. Leé ese `prompts.md` y tomá el número de la última entrada. La nueva es la siguiente.
2. Identificá el prompt a registrar: por defecto, el último mensaje de Julián
   anterior a la invocación de la skill. Si hay dudas sobre cuál es, preguntá.
3. Copiá el prompt **textual**: sin corregir ortografía, sin resumir y sin
   reordenar. Si tenía archivos adjuntos, listalos en una línea `Adjuntos:`.
4. Agregá la entrada al final del archivo con este formato exacto:

   ````markdown
   ---

   ## N — <título del argumento, o uno corto propuesto por vos>

   Sesión <n> (<fecha dd/mm/aaaa>). Adjuntos: `archivo1`, `archivo2`   ← adjuntos solo si hubo

   ```
   <prompt textual>
   ```

   **Qué buscaba:** _(completa Julián)_

   **Qué devolvió:** <resumen honesto de lo que hizo el modelo en respuesta>
   ````

5. En **Qué devolvió**, contá lo que pasó de verdad: qué archivos creó o cambió,
   qué decisiones dejó pendientes y, si el modelo se equivocó o se desvió, decilo
   explícitamente. No maquilles errores ni inventes aciertos.
6. **No escribas "Qué buscaba"**: es de Julián. Dejá el marcador `_(completa Julián)_`.
7. No modifiques entradas anteriores, ni hagas commit. Avisale a Julián que la
   entrada está lista para que complete su parte.
