"use strict";

// SPTERO Web: interfaz en JS sin frameworks. Habla solo con la API del contrato v1.1.
// Los datos del usuario (archivo, material) se insertan siempre con textContent.

const PLOTLY_CONFIG = { responsive: true, displaylogo: false };
const COLORES = ["#187e77", "#b5643e"];
const estado = { ensayo: null, archivo: null, ensayos: [], seleccion: [] };
const $ = (id) => document.getElementById(id);

async function pedir(metodo, url, cuerpo) {
  const opciones = { method: metodo, headers: {} };
  if (cuerpo instanceof FormData) {
    opciones.body = cuerpo;
  } else if (cuerpo !== undefined) {
    opciones.body = JSON.stringify(cuerpo);
    opciones.headers["Content-Type"] = "application/json";
  }
  const respuesta = await fetch(url, opciones);
  if (respuesta.status === 204) return null;
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const error = new Error(datos && datos.message ? datos.message : `Error ${respuesta.status}`);
    error.code = datos && datos.code;
    throw error;
  }
  return datos;
}

function leerNumero(id, nombre) {
  const texto = $(id).value.trim().replace(",", ".");
  const valor = Number(texto);
  if (texto === "" || !Number.isFinite(valor) || valor <= 0) {
    throw new Error(`${nombre} tiene que ser un número mayor que cero.`);
  }
  return valor;
}

function formato(valor, decimales) {
  if (valor === null || valor === undefined) return "—";
  return valor.toLocaleString("es-AR", { minimumFractionDigits: decimales, maximumFractionDigits: decimales });
}

function mostrarEstado(clave, texto) {
  const insignia = $("estado");
  insignia.dataset.estado = clave;
  insignia.textContent = texto;
}

function mostrarAviso(texto) {
  const aviso = $("aviso-formulario");
  aviso.textContent = texto || "";
  aviso.hidden = !texto;
}

function mostrarChip(nombre, detalle) {
  $("nombre-archivo").textContent = nombre;
  $("detalle-archivo").textContent = detalle;
  $("chip-archivo").hidden = false;
}

function layoutBase() {
  return {
    margin: { l: 64, r: 20, t: 10, b: 50 },
    xaxis: { title: { text: "Desplazamiento [mm]" }, zeroline: false },
    yaxis: { title: { text: "Carga [N]" }, zeroline: false },
    hovermode: "closest",
    legend: { orientation: "h", y: -0.22 },
  };
}

function graficar(divId, trazas) {
  const div = $(divId);
  if (typeof Plotly === "undefined") {
    div.textContent = "No se pudo cargar Plotly.js (hace falta conexión a internet para el gráfico).";
    div.className = "chart-wrap sin-grafico";
    return;
  }
  Plotly.react(div, trazas, layoutBase(), PLOTLY_CONFIG);
}

function leerParametros() {
  return {
    apply_compliance_correction: $("corregir").checked,
    compliance_mm_per_n: leerNumero("cp", "C_P"),
    beta: leerNumero("beta", "β"),
  };
}

async function alEnviar(evento) {
  evento.preventDefault();
  mostrarAviso("");
  let espesor;
  let parametros;
  try {
    espesor = leerNumero("espesor", "El espesor");
    parametros = leerParametros();
  } catch (error) {
    mostrarAviso(error.message);
    return;
  }
  // Evita dobles envíos mientras la petición está en vuelo.
  const botones = [$("boton-analizar"), $("boton-eliminar")];
  botones.forEach((boton) => { boton.disabled = true; });
  try {
    if (estado.ensayo) {
      await recalcular(espesor, parametros);
    } else {
      await analizarNuevo(espesor, parametros);
    }
  } finally {
    botones.forEach((boton) => { boton.disabled = false; });
  }
}

async function analizarNuevo(espesor, parametros) {
  const material = $("material").value.trim();
  if (!estado.archivo) { mostrarAviso("Elegí un archivo .raw."); return; }
  if (!material) { mostrarAviso("Indicá el material."); return; }
  const datos = new FormData();
  datos.append("file", estado.archivo);
  datos.append("material", material);
  datos.append("thickness_mm", String(espesor));
  mostrarEstado("guardando", "Guardando…");
  let creado;
  try {
    creado = await pedir("POST", "/tests", datos);
  } catch (error) {
    mostrarEstado("error", "Error al guardar");
    mostrarAviso(error.message);
    return;
  }
  try {
    await pedir("PUT", `/tests/${creado.id}/result`, parametros);
  } catch (error) {
    mostrarAviso(`El ensayo se guardó, pero no se pudo procesar: ${error.message}`);
  }
  await abrirEnsayo(creado.id);
  await cargarHistorial();
}

async function recalcular(espesor, parametros) {
  const id = estado.ensayo.id;
  mostrarEstado("guardando", "Guardando…");
  try {
    if (espesor !== estado.ensayo.thickness_mm) {
      await pedir("PATCH", `/tests/${id}`, { thickness_mm: espesor });
    }
    const actual = estado.ensayo.result && estado.ensayo.result.parameters;
    const cambiaron = !actual
      || actual.apply_compliance_correction !== parametros.apply_compliance_correction
      || actual.beta !== parametros.beta
      || (parametros.apply_compliance_correction && actual.compliance_mm_per_n !== parametros.compliance_mm_per_n);
    if (cambiaron) await pedir("PUT", `/tests/${id}/result`, parametros);
  } catch (error) {
    mostrarAviso(error.message);
  }
  await abrirEnsayo(id);
  await cargarHistorial();
}

async function abrirEnsayo(id) {
  let ensayo;
  try {
    ensayo = await pedir("GET", `/tests/${id}`);
  } catch (error) {
    mostrarAviso(error.message);
    return;
  }
  estado.ensayo = ensayo;
  estado.archivo = null;
  $("titulo").textContent = `Ensayo ${ensayo.filename}`;
  $("material").value = ensayo.material;
  $("material").readOnly = true;
  $("espesor").value = String(ensayo.thickness_mm);
  $("archivo").disabled = true;
  $("zona-carga").classList.add("bloqueada");
  mostrarChip(ensayo.filename, `${ensayo.point_count} puntos · guardado`);
  $("boton-analizar").textContent = "Recalcular";
  $("boton-eliminar").hidden = false;
  if (ensayo.result) {
    const p = ensayo.result.parameters;
    $("beta").value = String(p.beta);
    $("corregir").checked = p.apply_compliance_correction;
    if (p.compliance_mm_per_n !== null) $("cp").value = String(p.compliance_mm_per_n);
    mostrarEstado("procesado", "Guardado · procesado");
  } else {
    mostrarEstado("sin-procesar", "Guardado · sin procesar");
  }
  mostrarResultado(ensayo.result);
  await graficarEnsayo(ensayo);
}

function mostrarResultado(resultado) {
  $("m-pm").textContent = resultado ? formato(resultado.pm_n, 1) : "—";
  $("m-dm").textContent = resultado ? formato(resultado.dm_mm, 4) : "—";
  $("m-rm").textContent = resultado ? formato(resultado.rm_mpa, 1) : "—";
  $("m-py").textContent = resultado ? formato(resultado.py_t10_n, 1) : "—";
  $("m-sigma").textContent = resultado ? formato(resultado.sigma_y_t10_mpa, 1) : "—";
  if (!resultado) {
    $("parametros-usados").textContent = "—";
    return;
  }
  const p = resultado.parameters;
  const correccion = p.apply_compliance_correction ? `con corrección C_P = ${p.compliance_mm_per_n} mm/N` : "sin corrección de flexibilidad";
  $("parametros-usados").textContent = `t = ${estado.ensayo.thickness_mm} mm · β = ${p.beta} · ${correccion}`;
}

async function graficarEnsayo(ensayo) {
  const fuente = ensayo.result ? "processed" : "raw";
  let curva;
  try {
    curva = await pedir("GET", `/tests/${ensayo.id}/curve?source=${fuente}`);
  } catch (error) {
    mostrarAviso(error.message);
    return;
  }
  const trazas = [{
    x: curva.displacement_mm, y: curva.load_n, mode: "lines", name: "Curva SPT",
    line: { color: COLORES[0], width: 2 },
    hovertemplate: "%{x:.4f} mm<br>%{y:.1f} N<extra></extra>",
  }];
  const r = ensayo.result;
  if (r) {
    trazas.push({
      x: [r.dm_mm], y: [r.pm_n], mode: "markers", name: "Pm",
      marker: { size: 12, color: "white", line: { color: "#b53e47", width: 3 } },
      hovertemplate: "Pm = %{y:.1f} N<br>dm = %{x:.4f} mm<extra></extra>",
    });
    if (r.py_t10_n !== null) {
      trazas.push({
        x: [r.py_t10_displacement_mm], y: [r.py_t10_n], mode: "markers", name: "Py t/10",
        marker: { size: 10, symbol: "square", color: "#17384d" },
        hovertemplate: "Py t/10 = %{y:.1f} N<br>%{x:.4f} mm<extra></extra>",
      });
    }
  }
  $("subtitulo-grafico").textContent = fuente === "processed"
    ? "Curva procesada: la que se usó para calcular los resultados."
    : "Curva cruda: el ensayo todavía no se procesó.";
  graficar("grafico", trazas);
}

async function eliminarEnsayo(ensayo) {
  const confirmado = window.confirm(`¿Eliminar ${ensayo.filename} y su resultado? No se puede deshacer.`);
  if (!confirmado) return;
  const botones = [$("boton-analizar"), $("boton-eliminar")];
  botones.forEach((boton) => { boton.disabled = true; });
  try {
    await pedir("DELETE", `/tests/${ensayo.id}`);
  } catch (error) {
    mostrarAviso(error.message);
    return;
  } finally {
    botones.forEach((boton) => { boton.disabled = false; });
  }
  estado.seleccion = estado.seleccion.filter((id) => id !== ensayo.id);
  if (estado.ensayo && estado.ensayo.id === ensayo.id) nuevoAnalisis();
  await cargarHistorial();
}

function nuevoAnalisis() {
  estado.ensayo = null;
  estado.archivo = null;
  $("formulario").reset();
  $("material").readOnly = false;
  $("archivo").disabled = false;
  $("zona-carga").classList.remove("bloqueada");
  $("chip-archivo").hidden = true;
  $("titulo").textContent = "Nuevo análisis SPT";
  $("boton-analizar").textContent = "Analizar ensayo";
  $("boton-eliminar").hidden = true;
  $("subtitulo-grafico").textContent = "Todavía no hay un ensayo analizado.";
  mostrarAviso("");
  mostrarEstado("vacio", "Sin ensayo abierto");
  mostrarResultado(null);
  if (typeof Plotly !== "undefined") Plotly.purge("grafico");
}

function elegirArchivo(archivo) {
  if (!archivo || estado.ensayo) return;
  estado.archivo = archivo;
  mostrarChip(archivo.name, "Listo para analizar");
  mostrarAviso("");
}

function celda(contenido) {
  const td = document.createElement("td");
  if (contenido instanceof Node) td.append(contenido);
  else td.textContent = contenido;
  return td;
}

function boton(texto, clase, alHacerClic) {
  const b = document.createElement("button");
  b.type = "button";
  b.className = clase;
  b.textContent = texto;
  b.addEventListener("click", alHacerClic);
  return b;
}

function alternarSeleccion(id, casilla) {
  if (casilla.checked) {
    if (estado.seleccion.length >= 2) {
      casilla.checked = false;
      $("ayuda-comparacion").textContent = "Solo se pueden comparar dos ensayos a la vez.";
      return;
    }
    estado.seleccion.push(id);
  } else {
    estado.seleccion = estado.seleccion.filter((otro) => otro !== id);
  }
  actualizarComparacion();
}

async function cargarHistorial() {
  let ensayos;
  try {
    ensayos = await pedir("GET", "/tests");
  } catch (error) {
    mostrarAviso(error.message);
    return;
  }
  estado.ensayos = ensayos;
  estado.seleccion = estado.seleccion.filter((id) => ensayos.some((e) => e.id === id));
  const cuerpo = $("filas-historial");
  cuerpo.replaceChildren();
  if (ensayos.length === 0) {
    const fila = document.createElement("tr");
    const vacia = celda("Todavía no hay ensayos guardados.");
    vacia.colSpan = 9;
    fila.append(vacia);
    cuerpo.append(fila);
  }
  for (const ensayo of ensayos) {
    const casilla = document.createElement("input");
    casilla.type = "checkbox";
    casilla.checked = estado.seleccion.includes(ensayo.id);
    casilla.setAttribute("aria-label", `Comparar ${ensayo.filename}`);
    casilla.addEventListener("change", () => alternarSeleccion(ensayo.id, casilla));

    const nombre = document.createElement("b");
    nombre.textContent = ensayo.filename;
    const insignia = document.createElement("span");
    insignia.className = ensayo.result ? "status" : "status pendiente";
    insignia.textContent = ensayo.result ? "Procesado" : "Sin procesar";
    const acciones = document.createElement("span");
    acciones.append(
      boton("Abrir", "boton-fila", () => { abrirEnsayo(ensayo.id); $("analisis").scrollIntoView({ behavior: "smooth" }); }),
      boton("Eliminar", "boton-fila danger", () => eliminarEnsayo(ensayo)),
    );

    const fila = document.createElement("tr");
    fila.append(
      celda(casilla),
      celda(nombre),
      celda(ensayo.material),
      celda(formato(ensayo.thickness_mm, 3)),
      celda(ensayo.result ? `${formato(ensayo.result.pm_n, 0)} N` : "—"),
      celda(ensayo.result ? `${formato(ensayo.result.rm_mpa, 0)} MPa` : "—"),
      celda(new Date(ensayo.uploaded_at).toLocaleDateString("es-AR")),
      celda(insignia),
      celda(acciones),
    );
    cuerpo.append(fila);
  }
  actualizarComparacion();
}

function actualizarComparacion() {
  // Se completa en la Task 11.
}

function iniciar() {
  $("formulario").addEventListener("submit", alEnviar);
  $("boton-nuevo").addEventListener("click", nuevoAnalisis);
  $("boton-eliminar").addEventListener("click", () => estado.ensayo && eliminarEnsayo(estado.ensayo));
  $("archivo").addEventListener("change", (e) => elegirArchivo(e.target.files[0]));
  const zona = $("zona-carga");
  zona.addEventListener("dragover", (e) => { e.preventDefault(); if (!estado.ensayo) zona.classList.add("arrastrando"); });
  zona.addEventListener("dragleave", () => zona.classList.remove("arrastrando"));
  zona.addEventListener("drop", (e) => {
    e.preventDefault();
    zona.classList.remove("arrastrando");
    elegirArchivo(e.dataTransfer.files[0]);
  });
  cargarHistorial();
}

iniciar();
