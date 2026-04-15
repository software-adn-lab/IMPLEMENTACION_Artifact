const datosGuardados = JSON.parse(sessionStorage.getItem("antipatternResult"));
const params = new URLSearchParams(window.location.search);
const projectName = sessionStorage.getItem("projectName");
const isRepoPrivate = sessionStorage.getItem("isRepoPrivate") === "true";
const antipatronSeleccionado = params.get("patron");
const tablaBody = document.getElementById("cuerpo-tabla");

const diccionarioSmells = {
    "LCH": "Low Cohesion",
    "LCS": "Large Class",
    "DC": "Data Class",
    "CC": "Controller Class",
    "CM": "Controller Method",
    "MI": "Multiple Interface",
    "FP": "Field Private",
    "COM": "Class One Method",
    "PN": "Procedural Names",
    "NI": "No Inheritance",
    "NP": "No Polymorphism",
    "LM": "Long Method",
    "MNP": "Method No Parameter",
    "CGV": "Class Global Variable"
};

// Add the header for the new column dynamically.
const tablaCabecera = document.querySelector("#tabla-detalles thead tr");
if (tablaCabecera) {
    const th = document.createElement("th");
    th.textContent = "View in SonarCloud";
    tablaCabecera.appendChild(th);
}

if (datosGuardados && datosGuardados[antipatronSeleccionado]) {
    const detallesIndividuales = datosGuardados[antipatronSeleccionado].detalle_smells;
    cargarGrafico(antipatronSeleccionado, datosGuardados[antipatronSeleccionado]);
    // Llenar la tabla recorriendo el arreglo
    detallesIndividuales.forEach((smell) => {
        // Create a new row (tr)
        const fila = document.createElement("tr");

        // Get full name, or fallback to abbreviation if missing from the dictionary.
        const nombreCompleto = diccionarioSmells[smell.moha_smell] || smell.moha_smell;
        const isSonarSmell = (smell.source || "sonar") === "sonar" && !!smell.issue_key && !!smell.project;
        const linkUrl = isSonarSmell
            ? `https://sonarcloud.io/project/issues?issueStatuses=OPEN%2CCONFIRMED&id=${smell.project}&open=${smell.issue_key}`
            : null;

        const textRange = smell.textRange || {};
        const startLine = textRange.startLine || smell.line;
        const endLine = textRange.endLine || startLine;

        const codeDetailsUrl = `/code-details?component=${encodeURIComponent(smell.component)}&startLine=${startLine}&endLine=${endLine}&projectName=${encodeURIComponent(projectName)}`;

        const componentCell = isRepoPrivate
            ? `<td>${smell.component || 'N/A'}</td>`
            : `<td><a href="${codeDetailsUrl}">${smell.component || 'N/A'}</a></td>`;

        const sonarCell = linkUrl
            ? `<td><a href="${linkUrl}" target="_blank">View</a></td>`
            : `<td>-</td>`;

        // Insert cells (td) with the information.
        fila.innerHTML = `
                    <td>${nombreCompleto}</td>
                    <td>${smell.sonar_rule}</td>
                    <td>${smell.line || 'N/A'}</td>
                    <td>${smell.severity}</td>
                    ${componentCell}
                    ${sonarCell}
                `;

        // Add row to table body.
        tablaBody.appendChild(fila);
    });
} else {
    // Message when there is no data.
    tablaBody.innerHTML = "<tr><td colspan='6'>No data found for this antipattern.</td></tr>";
}

// EXCEL-LIKE FILTERS


function agregarFiltros() {

    const tabla = document.getElementById("tabla-detalles");
    const headers = tabla.querySelectorAll("th");

    headers.forEach((header, colIndex) => {

        const select = document.createElement("select");


        const allOption = document.createElement("option");
        allOption.value = "";
        allOption.textContent = "All";
        select.appendChild(allOption);

        const valores = new Set();

        document.querySelectorAll("#cuerpo-tabla tr").forEach(fila => {
            const celda = fila.children[colIndex];
            if (celda) {
                valores.add(celda.textContent);
            }
        });

        valores.forEach(valor => {
            const opcion = document.createElement("option");
            opcion.value = valor;
            opcion.textContent = valor;
            select.appendChild(opcion);
        });

        select.addEventListener("change", function () {

            const filtro = this.value;
            const filas = document.querySelectorAll("#cuerpo-tabla tr");

            filas.forEach(fila => {

                const celda = fila.children[colIndex];
                if (!celda) return;

                if (filtro === "" || celda.textContent === filtro) {
                    fila.style.display = "";
                } else {
                    fila.style.display = "none";
                }

            });

        });

        header.appendChild(select);

    });

}
function cargarGrafico(nombre, datosGrafico) {

    const contenedorIndividual = document.getElementById("contenedorIndividual");

    let claseColor = "circulo-verde";

    if (datosGrafico.condiciones_cumplidas === datosGrafico.condiciones_totales) {
        claseColor = "circulo-rojo";
    } else if (datosGrafico.condiciones_cumplidas >= datosGrafico.condiciones_totales / 2) {
        claseColor = "circulo-amarillo";
    }

    const archivosConAntipatron = Array.isArray(datosGrafico.archivos_con_antipatron)
        ? datosGrafico.archivos_con_antipatron
        : [];
    const resumenArchivos = Array.isArray(datosGrafico.resumen_archivos) ? datosGrafico.resumen_archivos : [];
    const archivosProbables = resumenArchivos
        .filter((x) => {
            const cumplidas = Number(x?.condiciones_cumplidas) || 0;
            const totales = Number(x?.condiciones_totales) || 0;
            return !x?.antipatron_detectado && totales > 0 && cumplidas >= totales / 2;
        })
        .map((x) => x.archivo_clase)
        .filter(Boolean);
    const topResumen = resumenArchivos[0] || null;

    let mensajeArchivo = "";
    if (archivosConAntipatron.length > 0 && archivosProbables.length > 0) {
        mensajeArchivo = `<b>Detection by file/class:</b> Detected in ${archivosConAntipatron.join(", ")}. Likely in ${[...new Set(archivosProbables)].join(", ")}.`;
    } else if (archivosConAntipatron.length > 0) {
        mensajeArchivo = `<b>Detection by file/class:</b> This antipattern was detected in ${archivosConAntipatron.join(", ")}.`;
    } else if (archivosProbables.length > 0) {
        mensajeArchivo = `<b>Detection by file/class:</b> This antipattern is likely in ${[...new Set(archivosProbables)].join(", ")}.`;
    } else if (topResumen && topResumen.archivo_clase && topResumen.condiciones_cumplidas > 0) {
        mensajeArchivo = `<b>Detection by file/class:</b> The file/class with the highest match is ${topResumen.archivo_clase} (${topResumen.condiciones_cumplidas}/${topResumen.condiciones_totales} conditions).`;
    } else {
        mensajeArchivo = "<b>Detection by file/class:</b> There is not enough evidence to associate this antipattern with a specific file/class.";
    }

    contenedorIndividual.innerHTML = `
    
            <svg>
                <circle
                    class="circulo-fondo"
                    pathLength="${datosGrafico.condiciones_totales}"
                    stroke-dasharray="${datosGrafico.condiciones_totales} ${datosGrafico.condiciones_totales}">
                </circle>

                <circle
                    class="${claseColor} circulo-pintado"
                    pathLength="${datosGrafico.condiciones_totales}"
                    stroke-dasharray="${datosGrafico.condiciones_cumplidas} ${datosGrafico.condiciones_totales}"
                    style="--total:${datosGrafico.condiciones_totales}">
                </circle>

                <text x="50%" y="48%" class="valor-centro">
                    ${datosGrafico.condiciones_cumplidas}/${datosGrafico.condiciones_totales}
                </text>

                <text x="50%" y="62%" class="subtexto-centro">
                    met
                </text>
                </svg>
                
                <h2>${nombre}</h2>
                <div class="separadorTexto">
                <text class="conclusion">
                ${datosGrafico.detectado}
                </text>
                <text class="condicionesCumplidas">
                <b>The met conditions for this antipattern are: </b>${datosGrafico.detalle_condiciones_cumplidas
                    .map(smell => diccionarioSmells[smell] || smell)
                    .join(", ")
                }
                </text>
                <text class="condicionesCumplidas">
                ${mensajeArchivo}
                </text>
                </div>
    `;
}




// Execute after populating the table.
setTimeout(agregarFiltros, 0);