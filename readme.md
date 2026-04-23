# Detector de Antipatrones de Diseno Basado en Code Smells de SonarCloud

## 1. Descripcion General

Esta herramienta es una aplicacion web que analiza proyectos de SonarCloud, identifica Code Smells y detecta antipatrones de diseno de alto nivel, como BLOB y Spaghetti Code.

El sistema entrega una visualizacion clara y detallada de resultados para apoyar la mejora continua de la calidad de codigo.

## 1.1 Reestructuracion No Destructiva del Proyecto

Se realizo una reestructuracion por carpetas sin eliminar archivos existentes.

Nuevas carpetas:

- docs/: documentacion tecnica y manuales.
- docs/architecture/: espacio para artefactos de arquitectura.
- tests/: suite de pruebas automatizadas.
- tests/unit/: pruebas unitarias por modulo.
- tests/fixtures/: datos de prueba reutilizables.

Manual de desarrollador:

- docs/manual_desarrollador.md
- docs/guia_pruebas.md

## 2. Caracteristicas Principales

- Integracion con SonarCloud: consume la API de SonarCloud para obtener Code Smells de un proyecto especifico.
- Soporte para repositorios publicos y privados: permite autenticacion con token cuando es necesario.
- Mapeo de olores: traduce Code Smells de SonarCloud a una clasificacion intermedia (Moha Smells) con una matriz en Excel (Mapeo.xlsx).
- Deteccion de antipatrones: identifica 4 tipos (BLOB, Swiss Army Knife, Functional Decomposition y Spaghetti Code) en funcion de combinaciones de Moha Smells.
- Dashboard interactivo: muestra un reporte general con resumen visual por antipatron.
- Reportes detallados: ofrece vistas individuales por antipatron con condiciones cumplidas y olores relacionados.
- Filtros dinamicos: las tablas de detalle incluyen filtros por columna.
- Visor de codigo: resalta lineas de codigo relacionadas con cada olor (solo para repositorios publicos de GitHub).

## 3. Prerrequisitos

Antes de ejecutar la aplicacion, asegurate de contar con:

- Python 3.8 o superior.
- pip (gestor de paquetes de Python).
- Un proyecto previamente analizado en SonarCloud.
- Opcional: token de usuario de SonarCloud para analizar repositorios privados (My Account > Security > Generate Tokens).

## 4. Instalacion y Ejecucion

1. Clonar el repositorio:
  ```bash
  git clone <URL_DEL_REPOSITORIO>
  cd ArtefactoImplementacionDEMO
  ```

2. Crear entorno virtual e instalar dependencias:
  ```bash
  python -m venv venv

  # Windows
  venv\Scripts\activate

  # macOS/Linux
  source venv/bin/activate

  pip install -r requirements.txt
  ```

3. Ejecutar la aplicacion Flask:
  ```bash
  flask run
  ```

4. Abrir en navegador:
  ```text
  http://127.0.0.1:5000
  ```

### 4.1 Ejecutar Pruebas Unitarias

Desde la raiz del proyecto:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Resultado esperado actual: 23 pruebas en estado OK.

Suite incluida en esta version:

- tests/unit/test_antipattern_detector.py
- tests/unit/test_main_controller_mapping.py
- tests/unit/test_python_rules_new.py
- tests/unit/test_python_sonar_equivalent_rules.py
- tests/unit/test_json_reader.py
- tests/unit/test_excel_processor.py

## 5. Guia de Uso

### Paso 1: Pagina de Inicio (Analisis)

1. Project Name (Project Key): ingresa la clave del proyecto en SonarCloud.
2. Private repository: habilita esta opcion si el repositorio es privado.
3. Authorization token: si es privado, ingresa el token de SonarCloud.
4. Presiona Verify project para iniciar el analisis.

### Paso 2: Reporte General

Al finalizar el analisis, se muestra el tablero principal.

- Se visualiza una tarjeta por antipatron.
- Cada tarjeta muestra un grafico circular con condiciones cumplidas (Moha Smells).
- Colores:
  - Rojo: todas las condiciones cumplidas (antipatron detectado).
  - Amarillo: al menos la mitad de condiciones cumplidas (posible antipatron).
  - Verde: menos de la mitad de condiciones cumplidas (no detectado).

### Paso 3: Reporte Individual

Esta vista entrega el detalle de un antipatron especifico.

- Incluye resumen visual y conclusion textual.
- Muestra tabla detallada de olores contribuyentes.
- Columnas principales: Moha Smell, Sonar Rule, Line, Severity, Location, View in SonarCloud.
- Cada columna puede filtrarse.
- Enlaces:
  - Location: abre el visor de codigo (si el repositorio es publico).
  - View in SonarCloud: abre el issue correspondiente en SonarCloud.

### Paso 4: Visor de Codigo

- Se abre desde la columna Location en reportes de repositorios publicos.
- Muestra el archivo fuente desde GitHub.
- Resalta las lineas asociadas al Code Smell.

## 6. Arquitectura y Logica Interna

1. Frontend: HTML, CSS y JavaScript capturan entrada del usuario (index.js), invocan APIs del backend y renderizan reportes (results.js, individualReport.js) usando sessionStorage.
2. Backend (Flask):
  - controllers/main_controller.py: define rutas y orquesta el analisis en /api/test-connection.
  - models/JSONReader.py: consume SonarCloud, maneja autenticacion y extrae issues CODE_SMELL.
  - models/ExcelProcessor.py: lee Mapeo.xlsx y convierte reglas Sonar a Moha Smells.
  - models/PythonSonarEquivalentRules.py: ejecuta metricas locales para Python y emite issues normalizados tipo Sonar.
  - models/python_rules/: contiene una clase por regla local, incluyendo reglas new_* para nuevas metricas.
  - models/AntipatternDetector.py: evalua condiciones por antipatron y devuelve resultado final.

### Flujo Actual de Mapeo y Deteccion

Antes, el flujo dependia solo de:

- Rule ID de SonarCloud.
- Mapeo Excel (Mapeo.xlsx) hacia Moha Smells.

Ahora, el flujo tiene dos fuentes que convergen en el mismo detector:

1. Fuente SonarCloud:
  - JSONReader obtiene los issues.
  - ExcelProcessor transforma cada rule ID a uno o varios Moha Smells.

2. Fuente de metricas locales Python:
  - PythonSonarEquivalentRules recorre el repositorio y aplica reglas en models/python_rules.
  - Cada regla local genera un issue con rule_key y metric_name.
  - main_controller mapea cada rule_key local (incluyendo NEW-*) a Moha Smells.

3. Fase de unificacion:
  - El controlador concatena ambas salidas en una sola lista: relatedSmellsMoha.

4. Fase de decision de antipatron:
  - AntipatternDetector compara relatedSmellsMoha con condiciones regex por antipatron.
  - Reglas actuales:
    - BLOB: (LCH|LCS), (CC|CM), DC
    - SwissArmyKnife: MI
    - FunctionalDecomposition: FP, COM, PN, NP, NI
    - SpaghettiCode: LM, MNP, CGV, NI, NP
  - Criterio de salida:
    - Detectado: todas las condiciones cumplidas.
    - Probable: al menos la mitad de condiciones cumplidas.
    - No detectado: menos de la mitad de condiciones cumplidas.

En resumen, la logica del detector se mantiene, pero ahora recibe evidencia combinada de SonarCloud y metricas locales Python.

### Flujo por Clase (Paso a Paso)

A continuacion se describe el flujo interno de cada clase principal para entender exactamente como se llega a la decision final de antipatron.

1. controllers/main_controller.py
  - Entrada: project_key y token (opcional) desde la peticion HTTP.
  - Proceso:
    - Invoca RepositoryStructureAnalyzer para clonar/ubicar y analizar la estructura Python del repositorio.
    - Ejecuta PythonSonarEquivalentRules para obtener issues locales (reglas Sonar equivalentes y reglas NEW-*).
    - Ejecuta JSONReader + ExcelProcessor para obtener mapeo Sonar -> Moha.
    - Mapea issues locales con _map_local_rule_issue_to_moha.
    - Une todo en relatedSmellsMoha.
    - Llama a DetectAntipattern.
  - Salida: JSON final con antipattern_result.

2. models/RepositoryStructureAnalyzer.py
  - Entrada: project_key.
  - Proceso: resuelve URL de repositorio, realiza clonado local (si aplica) y analiza archivos .py con AST.
  - Salida: ruta local del repositorio y resumen de estructura Python.

3. models/JSONReader.py
  - Entrada: project_key y token (opcional).
  - Proceso:
    - Consulta la API de SonarCloud.
    - Gestiona autenticacion y errores (401/403/404/timeouts).
    - Normaliza fields relevantes de cada issue.
  - Salida: lista de issues de Sonar con regla, severidad, componente, linea, etc.

4. models/ExcelProcessor.py
  - Entrada: lista de issues Sonar y archivo Mapeo.xlsx.
  - Proceso:
    - Lee la matriz de equivalencias.
    - Convierte rule IDs de Sonar en moha_smell.
    - Evita duplicados por combinacion relevante.
  - Salida: lista relatedSmellsMoha de origen sonar.

5. models/PythonSonarEquivalentRules.py
  - Entrada: ruta del repositorio local.
  - Proceso:
    - Recorre archivos .py validos.
    - Parsea cada archivo con AST.
    - Aplica _RulesVisitor, que delega en clases de models/python_rules.
    - Acumula issues con rule_key, metric_name, line, textRange y symbol_name.
  - Salida: metrics agregadas + issues locales normalizados.

6. models/python_rules/rule_*.py (reglas base)
  - Entrada: nodos AST (clase, metodo o miembro), ruta archivo, y umbrales configurables.
  - Proceso: cada regla valida una condicion puntual (nomenclatura lexica, tamano metodo, atributos globales, etc.).
  - Salida: cero o mas RuleIssue.

7. models/python_rules/new_*.py (metricas nuevas)
  - Entrada: nodos AST de clase/metodo + umbrales editables.
  - Proceso: calcula metricas nuevas (NACC, NINTERF, NPRIVFIELD, NMD VERY_LOW, NO_POLYMORPHISM, DIT=1, NMNOPARAM VERY_HIGH).
  - Salida: issues NEW-* con metric_name estandar.
  - Nota: cada NEW-* se mapea en main_controller a un Moha Smell para que participe en la deteccion.

8. models/AntipatternDetector.py
  - Entrada: relatedSmellsMoha combinado (sonar + local).
  - Proceso:
    - Evalua por antipatron si se cumplen reglas regex definidas en AntiPatrones.
    - Calcula condiciones_totales, condiciones_cumplidas y total_ocurrencias.
    - Determina estado: detectado, probable o no detectado.
    - Genera resumen por archivo (resumen_archivos).
  - Salida: estructura final por antipatron con detalle de evidencia.

9. views/templates y views/static/js
  - Entrada: JSON de antipattern_result desde backend.
  - Proceso: renderiza tarjetas generales, tablas de detalle, filtros y navegacion a vistas individuales.
  - Salida: visualizacion final para el usuario.

### Cadena Completa en una Linea

Peticion usuario -> main_controller -> (JSONReader + ExcelProcessor) + (PythonSonarEquivalentRules + python_rules) -> relatedSmellsMoha unificado -> AntipatternDetector -> respuesta JSON -> vistas/reportes.

### Ejemplos del Nuevo Mapeo

Ejemplo 1: mapeo de regla local NEW-* a Moha Smell

```text
Issue local detectado:
rule_key = NEW-NACC-VERY-HIGH
metric_name = NACC VERY_HIGH

Mapeo en main_controller:
NEW-NACC-VERY-HIGH -> DC

Resultado en relatedSmellsMoha:
{ moha_smell: "DC", source: "local", metric_name: "NACC VERY_HIGH", ... }
```

Ejemplo 2: combinacion Sonar + local para BLOB

```text
Desde Sonar/Excel:
S1448 -> LCS

Desde reglas locales:
S101 -> CC
NEW-NACC-VERY-HIGH -> DC

Condiciones BLOB requeridas:
(LCH|LCS), (CC|CM), DC

Evaluacion:
LCS + CC + DC -> BLOB detectado
```

Ejemplo 3: combinacion local para Spaghetti Code

```text
Reglas locales mapeadas:
S138 -> LM
NEW-NMNOPARAM-VERY-HIGH -> MNP
S1444 -> CGV
NEW-DIT-ONE -> NI
NEW-NO-POLYMORPHISM -> NP

Condiciones SpaghettiCode:
LM, MNP, CGV, NI, NP

Evaluacion:
si estan las 5 -> detectado
si hay al menos 3 -> probable
si hay 0, 1 o 2 -> no detectado
```

## 7. Solucion de Problemas

- Error: Project not found in SonarCloud.
  - Causa: project key incorrecto.
  - Solucion: verifica el project key exactamente como aparece en SonarCloud.

- Error: The repository is private or the authorization token is invalid.
  - Causa: repositorio privado sin token o token invalido/expirado.
  - Solucion: habilita Private repository e ingresa un token valido.

- Error: Could not connect to the server.
  - Causa: el servidor Flask no esta ejecutandose.
  - Solucion: ejecuta flask run y confirma disponibilidad en http://127.0.0.1:5000.

- La columna Location no muestra enlaces.
  - Causa: analisis de repositorio privado.
  - Solucion: comportamiento esperado para no exponer rutas de codigo no publicas.