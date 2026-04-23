# Flujo Backend

## Flujo principal de analisis

1. POST /api/test-connection recibe project_key y token.
2. main_controller invoca RepositoryStructureAnalyzer para preparar repo local.
3. PythonSonarEquivalentRules analiza AST y genera issues locales.
4. JSONReader obtiene issues CODE_SMELL de SonarCloud.
5. ExcelProcessor mapea Sonar rules a Moha smells.
6. main_controller mapea issues locales NEW-* a Moha smells.
7. Se unifican resultados y se ejecuta DetectAntipattern.
8. Se retorna antipattern_result para render en frontend.

## Entradas clave

- project_key: identificador del repositorio/proyecto.
- token: opcional para repos privados en SonarCloud.

## Salida clave

- antipattern_result:
  - condiciones_totales
  - condiciones_cumplidas
  - total_ocurrencias
  - detectado
  - detalle_smells
  - resumen_archivos
