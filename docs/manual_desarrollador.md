# Manual de Desarrollador

## 1. Objetivo

Este manual describe la arquitectura del proyecto, el flujo de ejecucion, la responsabilidad de cada clase principal y ejemplos para extender o probar el sistema.

## 2. Flujo End-to-End

1. El usuario envia project_key y token opcional desde la interfaz web.
2. El backend en controllers/main_controller.py recibe la peticion en /api/test-connection.
3. Se prepara el repositorio objetivo con RepositoryStructureAnalyzer.
4. Se ejecutan reglas locales Python con PythonSonarEquivalentRules.
5. Se consulta SonarCloud con JSONReader.
6. Se transforma Sonar rule -> Moha smell con ExcelProcessor.
7. Se mapean tambien las reglas locales (NEW-*) a Moha smells en _map_local_rule_issue_to_moha.
8. Se unifican ambas fuentes y se evalua DetectAntipattern.
9. Se retorna la respuesta JSON al frontend para renderizar reportes.

## 3. Clases y Responsabilidades

### 3.1 Entrada de la aplicacion

- App.py
  - Crea la app Flask.
  - Registra el blueprint principal.
  - Gestiona limpieza de repositorios temporales al cerrar el proceso.

### 3.2 Controlador

- controllers/main_controller.py
  - _map_local_rule_issue_to_moha: traduce cada rule_key local a codigos Moha (por ejemplo NEW-NINTERF-VERY-HIGH -> MI).
  - analyze_project: orquesta todo el pipeline de analisis.
  - cleanup_session_repo: elimina repo temporal de la sesion actual.

### 3.3 Modelos de integracion y analisis

- models/RepositoryStructureAnalyzer.py
  - Normaliza entradas owner/repo, URL o owner_repo.
  - Clona/actualiza repositorios en cloned_repositories.
  - Analiza estructura Python con AST (clases, metodos, interfaces-like).

- models/JSONReader.py
  - Consulta SonarCloud para issues CODE_SMELL.
  - Maneja autenticacion, errores de red y errores 401/403/404.

- models/ExcelProcessor.py
  - Lee Mapeo.xlsx y convierte reglas Sonar a Moha smells.
  - Deduplica resultados para no repetir la misma evidencia.

- models/PythonSonarEquivalentRules.py
  - Recorre archivos .py y ejecuta reglas AST.
  - Devuelve metricas agregadas y lista de issues normalizados.

- models/AntipatternDetector.py
  - Evalua condiciones por antipatron con expresiones regulares.
  - Calcula estado detectado/probable/no detectado.
  - Genera resumen por archivo.

### 3.4 Reglas locales (models/python_rules)

- rule_s101_lexic_classname.py: nombres de clase con terminos de control.
- rule_py_lx01_lexic_classname_procedural.py: nombres de clase procedurales.
- rule_s100_lexic_methodname.py: nombres de metodo con terminos de control.
- rule_s138_method_too_big.py: metodos demasiado largos.
- rule_s1444_class_attribute_final.py: uso de atributo global/no final.
- rule_s1448_too_many_methods.py: exceso de metodos por clase.

Reglas new activas:

- new_nacc_very_high_rule.py: NACC VERY_HIGH con combinacion de numero de accesores y ratio de accesores.
- new_ninterf_very_high_rule.py: NINTERF VERY_HIGH por type-checking repetido y ramificacion alta.
- new_nprivfield_high_rule.py: NPRIVFIELD HIGH por cantidad de campos privados/protegidos.
- new_nmd_very_low_rule.py: NMD VERY_LOW por clases con muy pocos metodos.
- new_nmnoparam_very_high_rule.py: muchos metodos sin parametros explicitos.
- new_no_polymorphism_rule.py: ausencia de polimorfismo por herencia.
- new_dit_one_rule.py: profundidad de herencia equivalente a 1.

## 4. Ejemplos

### 4.1 Ejecutar aplicacion

```bash
flask run
```

### 4.2 Ejecutar pruebas unitarias

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### 4.3 Ejemplo de uso directo del analizador de reglas

```python
from models.PythonSonarEquivalentRules import PythonSonarEquivalentRules

analyzer = PythonSonarEquivalentRules()
result = analyzer.analyze_repository("cloned_repositories/owner_repo")
print(result["issues_count"])
```

### 4.4 Ejemplo de mapeo local a Moha

```python
from controllers.main_controller import _map_local_rule_issue_to_moha

issue = {
    "rule_key": "NEW-NINTERF-VERY-HIGH",
    "metric_name": "NINTERF VERY_HIGH",
    "line": 27,
    "file_path": "src/service.py",
}
print(_map_local_rule_issue_to_moha(issue, "owner_repo"))
```

## 5. Como agregar una nueva regla local

1. Crear archivo en models/python_rules/new_NOMBRE_METRICA_rule.py.
2. Implementar clase con metodo check_class o check_callable.
3. Exportar la clase en models/python_rules/__init__.py.
4. Instanciar y ejecutar la regla en models/PythonSonarEquivalentRules.py.
5. Mapear rule_key a Moha smell en controllers/main_controller.py.
6. Agregar pruebas unitarias en tests/unit.

## 6. Estructura de carpetas para desarrollo

- docs: documentacion funcional y tecnica.
- docs/architecture: notas de arquitectura y flujo.
- tests: pruebas automatizadas.
- tests/unit: pruebas unitarias por modulo.
- tests/fixtures: datos de prueba reutilizables.

## 7. Recomendaciones de mantenimiento

- Mantener consistencia entre:
  - Regla local implementada.
  - Export en __init__.py.
  - Uso en PythonSonarEquivalentRules.
  - Mapeo en main_controller.
  - Prueba unitaria correspondiente.
- Si se cambia un umbral de una regla NEW-*, actualizar tambien su test esperado.
