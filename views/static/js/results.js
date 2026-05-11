function obtenerClaseColor(condicionesCumplidas, condicionesTotales) {
  if (condicionesCumplidas === condicionesTotales) {
    return "circulo-rojo";
  }

  if (condicionesCumplidas >= condicionesTotales / 2) {
    return "circulo-amarillo";
  }

  return "circulo-verde";
}

function clonarTemplate(templateId) {
  const template = document.getElementById(templateId);
  if (!(template instanceof HTMLTemplateElement)) {
    return null;
  }

  const nodo = template.content.firstElementChild?.cloneNode(true);
  return nodo || null;
}

function construirTarjetaGrafico(nombre, grafico) {
  const condicionesCumplidas = Number(grafico.condiciones_cumplidas) || 0;
  const condicionesTotales = Math.max(Number(grafico.condiciones_totales) || 0, 1);
  const claseColor = obtenerClaseColor(condicionesCumplidas, condicionesTotales);

  const tarjeta = clonarTemplate("grafico-card-template");
  if (!(tarjeta instanceof HTMLElement)) {
    return null;
  }

  const redireccion = () => {
    if (typeof window.__markInternalNavigationForCleanup === "function") {
      window.__markInternalNavigationForCleanup();
    }
    window.location.href = `/individual-report?patron=${encodeURIComponent(nombre)}`;
  };

  tarjeta.addEventListener("click", redireccion);
  tarjeta.addEventListener("keydown", (evento) => {
    if (evento.key === "Enter" || evento.key === " ") {
      evento.preventDefault();
      redireccion();
    }
  });

  const svg = tarjeta.querySelector("svg");
  if (!(svg instanceof SVGElement)) {
    return tarjeta;
  }
  svg.setAttribute("aria-label", nombre);

  const circuloPintado = svg.querySelector(".circulo-pintado");
  if (!(circuloPintado instanceof SVGElement)) {
    return tarjeta;
  }

  circuloPintado.classList.remove("circulo-verde", "circulo-amarillo", "circulo-rojo");
  circuloPintado.classList.add(claseColor);
  circuloPintado.setAttribute("pathLength", String(condicionesTotales));
  circuloPintado.setAttribute("stroke-dasharray", `${condicionesCumplidas} ${condicionesTotales}`);
  circuloPintado.style.setProperty("--total", String(condicionesTotales));

  const valorCentro = svg.querySelector(".valor-centro");
  if (valorCentro instanceof SVGElement) {
  valorCentro.textContent = `${condicionesCumplidas}/${condicionesTotales}`;
  }

  const titulo = tarjeta.querySelector("h2");
  if (titulo instanceof HTMLElement) {
    titulo.textContent = nombre;
  }

  return tarjeta;
}

function generarGraficos(datos) {
  const contenedor = document.getElementById("contenedorGeneralGraficos");
  if (!contenedor) {
    return;
  }

  const tarjetas = Object.entries(datos)
    .map(([nombre, grafico]) => construirTarjetaGrafico(nombre, grafico))
    .filter(Boolean);

  if (!tarjetas.length) {
    contenedor.textContent = "No data to display.";
    return;
  }

  contenedor.replaceChildren(...tarjetas);
}

function copiarEstilosComputados(origen, destino, referencia = origen) {
  const estilos = window.getComputedStyle(referencia);
  const propiedades = [
    "fill",
    "stroke",
    "stroke-width",
    "stroke-dasharray",
    "stroke-linecap",
    "transform",
    "transform-origin",
    "font-size",
    "font-weight",
    "font-family",
    "text-anchor",
    "dominant-baseline",
    "letter-spacing",
    "opacity"
  ];

  propiedades.forEach((propiedad) => {
    const valor = estilos.getPropertyValue(propiedad);
    if (valor) {
      destino.style.setProperty(propiedad, valor);
    }
  });

  Array.from(origen.children).forEach((hijoOrigen, indice) => {
    const hijoDestino = destino.children[indice];
    const hijoReferencia = referencia.children[indice];
    if (hijoDestino) {
      copiarEstilosComputados(hijoOrigen, hijoDestino, hijoReferencia || hijoOrigen);
    }
  });
}

function convertirSvgAImagen(svg, svgReferencia = svg) {
  return new Promise((resolve, reject) => {
    const svgClonado = svg.cloneNode(true);
    copiarEstilosComputados(svg, svgClonado, svgReferencia);

    const viewBox = svg.viewBox && svg.viewBox.baseVal;
    const width = viewBox && viewBox.width ? viewBox.width : svg.clientWidth || 240;
    const height = viewBox && viewBox.height ? viewBox.height : svg.clientHeight || 240;

    svgClonado.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    svgClonado.setAttribute("width", width);
    svgClonado.setAttribute("height", height);

    const markup = new XMLSerializer().serializeToString(svgClonado);
    const dataUri = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(markup)}`;
    const img = new Image();

    img.onload = function () {
      img.className = "grafico-svg-exportado";
      img.width = width;
      img.height = height;
      resolve(img);
    };

    img.onerror = function () {
      reject(new Error("Could not convert SVG chart to image."));
    };

    img.src = dataUri;
  });
}

async function prepararContenedorParaPdf(elemento) {
  const clon = elemento.cloneNode(true);
  clon.classList.add("pdf-export-grid");

  clon.querySelectorAll(".grafico").forEach((grafico) => {
    grafico.classList.remove("grafico-interactivo");
    grafico.removeAttribute("tabindex");
    grafico.removeAttribute("role");
  });

  const svgsOriginales = Array.from(elemento.querySelectorAll("svg"));
  const svgs = Array.from(clon.querySelectorAll("svg"));

  await Promise.all(svgs.map(async (svg, indice) => {
    const imagen = await convertirSvgAImagen(svg, svgsOriginales[indice]);
    svg.replaceWith(imagen);
  }));

  return clon;
}

function normalizarValorTabla(valor, porDefecto = "N/A") {
  const limpio = String(valor ?? "")
    .replace(/\s+/g, " ")
    .trim();
  return limpio || porDefecto;
}

function construirResumenDeteccionArchivos(datos) {
  const bloque = document.createElement("div");
  bloque.className = "pdf-traceability-detection-summary";

  const titulo = document.createElement("p");
  titulo.textContent = "Files/Classes where the antipattern is detected or likely:";
  titulo.style.margin = "0 0 8px 0";
  titulo.style.fontWeight = "700";
  titulo.style.fontSize = "11px";
  bloque.appendChild(titulo);

  const detecciones = Object.entries(datos).flatMap(([antipatron, resultado]) => {
    const resumenArchivos = Array.isArray(resultado?.resumen_archivos)
      ? resultado.resumen_archivos
      : [];

    const detectados = resumenArchivos
      .filter((x) => x?.antipatron_detectado)
      .map((x) => normalizarValorTabla(x.archivo_clase));

    const probables = resumenArchivos
      .filter((x) => {
        const cumplidas = Number(x?.condiciones_cumplidas) || 0;
        const totales = Number(x?.condiciones_totales) || 0;
        return !x?.antipatron_detectado && totales > 0 && cumplidas >= totales / 2;
      })
      .map((x) => normalizarValorTabla(x.archivo_clase));

    if (!detectados.length && !probables.length) {
      return [];
    }

    return [{
      antipatron: normalizarValorTabla(antipatron),
      detectados: [...new Set(detectados)],
      probables: [...new Set(probables)]
    }];
  });

  if (!detecciones.length) {
    const sinDatos = document.createElement("p");
    sinDatos.textContent = "No files/classes were found with detected or likely antipatterns for the evaluated set.";
    sinDatos.style.margin = "0 0 12px 0";
    sinDatos.style.fontSize = "10px";
    bloque.appendChild(sinDatos);
    return bloque;
  }

  detecciones.forEach((item) => {
    const linea = document.createElement("p");
    const partes = [];
    if (item.detectados.length) {
      partes.push(`Detected in: ${item.detectados.join(", ")}`);
    }
    if (item.probables.length) {
      partes.push(`Likely in: ${item.probables.join(", ")}`);
    }
    linea.textContent = `${item.antipatron}: ${partes.join(" | ")}`;
    linea.style.margin = "0 0 6px 0";
    linea.style.fontSize = "10px";
    bloque.appendChild(linea);
  });

  bloque.style.margin = "0 0 14px 0";
  return bloque;
}

function construirTrazabilidadPdfElemento(datos) {
  const filas = extraerFilasTrazabilidad(datos);
  if (!filas.length) {
    return construirTrazabilidadPdfElementoDesdeFilas([], datos, true);
  }

  return construirTrazabilidadPdfElementoDesdeFilas(filas, datos, true);
}

function extraerFilasTrazabilidad(datos) {
  return Object.entries(datos).flatMap(([antipatron, resultado]) => {
    const detalles = Array.isArray(resultado?.detalle_smells)
      ? resultado.detalle_smells.filter((smell) => smell && smell.moha_smell)
      : [];

    return detalles.map((smell) => ({
      antipatron: normalizarValorTabla(antipatron),
      mohaSmell: normalizarValorTabla(smell.moha_smell),
      sonarRule: normalizarValorTabla(smell.sonar_rule),
      line: normalizarValorTabla(smell.line ?? "N/A"),
      severity: normalizarValorTabla(smell.severity),
      component: normalizarValorTabla(smell.component),
      project: smell.project,
      issue_key: smell.issue_key
    }));
  });
}

function construirTrazabilidadPdfElementoDesdeFilas(filas, datosOriginales, incluirResumen) {
  if (!Array.isArray(filas) || filas.length === 0) {
    const sectionVacia = clonarTemplate("pdf-traceability-empty-template");
    if (!(sectionVacia instanceof HTMLElement)) {
      return null;
    }

    if (incluirResumen) {
      const titulo = sectionVacia.querySelector("h2");
      const resumen = construirResumenDeteccionArchivos(datosOriginales || {});
      if (titulo instanceof HTMLElement) {
        titulo.insertAdjacentElement("afterend", resumen);
      }
    }

    return sectionVacia;
  }

  const section = clonarTemplate("pdf-traceability-table-template");
  if (!(section instanceof HTMLElement)) {
    return null;
  }

  const tbody = section.querySelector("tbody");
  if (!(tbody instanceof HTMLElement)) {
    return section;
  }

  if (incluirResumen) {
    const titulo = section.querySelector("h2");
    const resumen = construirResumenDeteccionArchivos(datosOriginales || {});
    if (titulo instanceof HTMLElement) {
      titulo.insertAdjacentElement("afterend", resumen);
    }
  }

  // Add header for the new column in the cloned template.
  const theadRow = section.querySelector("thead tr");
  if (theadRow) {
    const th = document.createElement("th");
    th.textContent = "View in SonarCloud";
    th.style.fontSize = "10px"; // PDF-friendly size.
    theadRow.appendChild(th);
  }

  filas.forEach((fila) => {
    const row = document.createElement("tr");

    const campos = [fila.antipatron, fila.mohaSmell, fila.sonarRule, fila.line, fila.severity, fila.component];
    campos.forEach((valor, index) => {
      const td = document.createElement("td");
      td.textContent = valor;
      td.style.fontSize = "10px";

      if (index === 5) {
        td.style.wordBreak = "break-all";
        td.style.maxWidth = "150px";
      }

      row.appendChild(td);
    });

    const tdLink = document.createElement("td");
    if (fila.project && fila.issue_key) {
      const link = document.createElement("a");
      link.href = `https://sonarcloud.io/project/issues?issueStatuses=OPEN%2CCONFIRMED&id=${fila.project}&open=${fila.issue_key}`;
      link.textContent = "View";
      link.target = "_blank";
      link.style.color = "#0000EE";
      tdLink.appendChild(link);
    }
    tdLink.style.fontSize = "10px";
    row.appendChild(tdLink);

    tbody.appendChild(row);
  });

  return section;
}

function obtenerWorkerHtml2pdf() {
  if (typeof window.html2pdf !== "function") {
    return null;
  }
  const worker = window.html2pdf();
  return worker && typeof worker.from === "function" ? worker : null;
}

function cargarGraficosDesdeSession() {
  const contenedor = document.getElementById("contenedorGeneralGraficos");
  if (!contenedor) {
    return;
  }

  const datosGuardados = sessionStorage.getItem("antipatternResult");
  if (!datosGuardados) {
    contenedor.textContent = "No data to display.";
    return;
  }

  try {
    const datos = JSON.parse(datosGuardados);
    generarGraficos(datos);
  } catch (error) {
    console.error("Error parseando antipatternResult:", error);
    contenedor.textContent = "Could not load analysis data.";
  }
}

function construirWrapperPdf(projectName, language) {
  const wrapper = clonarTemplate("pdf-export-template");
  if (!(wrapper instanceof HTMLElement)) {
    return null;
  }

  const proyecto = wrapper.querySelector(".pdf-project-name");
  if (proyecto instanceof HTMLElement) {
    proyecto.textContent = projectName || "PROJECT_NAME";
  }

  const lenguaje = wrapper.querySelector(".pdf-language");
  if (lenguaje instanceof HTMLElement) {
    lenguaje.textContent = language || "LANGUAGE";
  }

  return wrapper;
}

// exportContainerPdf: generate and download the PDF automatically using html2pdf.
async function exportContainerPdf(projectName, language) {
  const element = document.getElementById("contenedorGeneralGraficos");
  if (!element || !element.children.length) {
    alert("There is no content to export. Please ensure the graphs are loaded.");
    return;
  }

  const workerCheck = obtenerWorkerHtml2pdf();
  if (!workerCheck) {
    alert("html2pdf is not available. Ensure the html2pdf script is loaded.");
    return;
  }

  let datosTrazabilidad = {};
  const antipatternData = sessionStorage.getItem("antipatternResult");
  if (antipatternData) {
    try {
      datosTrazabilidad = JSON.parse(antipatternData);
    } catch (e) {
      console.error("Could not parse antipatternResult:", e);
      datosTrazabilidad = {};
    }
  }
  const filasTrazabilidad = extraerFilasTrazabilidad(datosTrazabilidad);

  const now = new Date();
  const dateStr = now.toISOString().slice(0, 10).replace(/-/g, "");
  const safeName = (projectName || "project").replace(/\s+/g, "_").replace(/[^\w\-]/g, "");
  const filename = `Report_${safeName}_${dateStr}.pdf`;

  // Mount off-screen to ensure styles/layout are computed.
  const mount = document.createElement("div");
  mount.style.position = "fixed";
  mount.style.left = "-10000px";
  mount.style.top = "0";
  mount.style.width = "794px"; // ~A4 at 96dpi
  mount.style.background = "#ffffff";
  mount.style.zIndex = "-1";
  document.body.appendChild(mount);

  const margin = 24;

  try {
    // Build static first-page content (header/legend + charts grid).
    const charts = await prepararContenedorParaPdf(element);

    // If there are many rows, render in chunks to avoid a single giant canvas.
    const rowsPerPage = 28;
    const totalChunks = Math.max(1, Math.ceil((filasTrazabilidad.length || 0) / rowsPerPage));

    let pdf = null;
    const addCanvasToPdf = (canvas) => {
      if (!pdf) {
        throw new Error("PDF is not initialized.");
      }

      const pageWidth = pdf.internal.pageSize.getWidth();
      const pageHeight = pdf.internal.pageSize.getHeight();
      const usableWidth = pageWidth - margin * 2;
      const usableHeight = pageHeight - margin * 2;

      const imgData = canvas.toDataURL("image/jpeg", 0.92);
      let imgWidth = usableWidth;
      let imgHeight = (canvas.height * imgWidth) / canvas.width;
      if (imgHeight > usableHeight) {
        const scale = usableHeight / imgHeight;
        imgHeight = usableHeight;
        imgWidth = imgWidth * scale;
      }

      pdf.addPage();
      const x = margin + (usableWidth - imgWidth) / 2;
      const y = margin;
      pdf.addImage(imgData, "JPEG", x, y, imgWidth, imgHeight);
    };

    for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
      mount.replaceChildren();

      const wrapper = construirWrapperPdf(projectName, language);
      if (!(wrapper instanceof HTMLElement)) {
        throw new Error("Could not build the PDF template.");
      }

      // For chunks after the first, remove the header/legend to keep pages lighter.
      if (chunkIndex > 0) {
        wrapper.querySelector(".pdf-export-header")?.remove();
        wrapper.querySelector(".pdf-legend")?.remove();
      }

      // Only include charts on the first chunk to reduce canvas size.
      if (chunkIndex === 0) {
        wrapper.appendChild(charts);
      }

      const start = chunkIndex * rowsPerPage;
      const end = start + rowsPerPage;
      const filasChunk = filasTrazabilidad.slice(start, end);

      const trazabilidad = construirTrazabilidadPdfElementoDesdeFilas(
        filasChunk,
        datosTrazabilidad,
        chunkIndex === 0
      );
      if (trazabilidad) {
        wrapper.appendChild(trazabilidad);
      }

      mount.appendChild(wrapper);

      // Let the browser flush layout before capture.
      await new Promise((r) => requestAnimationFrame(() => r()));

      if (chunkIndex === 0) {
        // Initialize PDF using html2pdf's internal jsPDF instance.
        // Using a small-ish first chunk avoids the giant-canvas blank PDF issue.
        pdf = await window
          .html2pdf()
          .set({
            margin,
            html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
            jsPDF: { unit: "pt", format: "a4", orientation: "portrait" },
            pagebreak: { mode: ["css", "legacy"] }
          })
          .from(wrapper)
          .toPdf()
          .get("pdf");
      } else {
        const canvas = await window
          .html2pdf()
          .set({
            html2canvas: { scale: 2, useCORS: true, backgroundColor: "#ffffff" },
            pagebreak: { mode: ["css", "legacy"] }
          })
          .from(wrapper)
          .toCanvas()
          .get("canvas");

        addCanvasToPdf(canvas);
      }
    }

    if (!pdf) {
      throw new Error("PDF could not be created.");
    }
    pdf.save(filename);
  } catch (err) {
    console.error("Error generating PDF:", err);
    alert("Error generating the PDF. Check the browser console for details.");
  } finally {
    mount.remove();
  }
}

// Export PDF button listener (uses data stored in sessionStorage).
document.addEventListener('DOMContentLoaded', function() {
  cargarGraficosDesdeSession();

  var btn = document.getElementById('exportPdfBtn');
  if (!btn) return;
  btn.addEventListener('click', async function() {
    var proyecto = sessionStorage.getItem("projectName") || 'PROJECT_NAME';
    var lenguaje = sessionStorage.getItem("language") || 'LANGUAGE';
    btn.disabled = true;
    btn.textContent = 'Generating PDF...';

    try {
      await exportContainerPdf(proyecto, lenguaje);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Export PDF';
    }
  });
});