# Guia de Pruebas

## 1. Objetivo

Este documento explica como ejecutar las pruebas del proyecto y que valida cada una.

## 2. Prerrequisitos

- Tener Python disponible en el entorno virtual del proyecto.
- Estar ubicado en la raiz del proyecto.
- Haber activado el entorno virtual.

## 3. Activar entorno virtual

### Git Bash

```bash
source .venv/Scripts/activate
```

### PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### CMD

```bat
.venv\Scripts\activate.bat
```

## 4. Ejecutar todas las pruebas

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Resultado esperado actual:

- Total aproximado: 23 pruebas.
- Estado esperado: OK.

## 5. Ejecutar pruebas por archivo

### Antipattern detector

```bash
python -m unittest tests.unit.test_antipattern_detector -v
```

### Mapeo del controlador

```bash
python -m unittest tests.unit.test_main_controller_mapping -v
```

### Reglas nuevas

```bash
python -m unittest tests.unit.test_python_rules_new -v
```

### Orquestador de reglas

```bash
python -m unittest tests.unit.test_python_sonar_equivalent_rules -v
```

### Lector de SonarCloud

```bash
python -m unittest tests.unit.test_json_reader -v
```

### Procesador de Excel

```bash
python -m unittest tests.unit.test_excel_processor -v
```

## 6. Ejecutar una sola prueba especifica

Ejemplo:

```bash
python -m unittest tests.unit.test_python_rules_new.TestNewRules.test_new_nacc_very_high_positive -v
```

## 7. Detalle de cada archivo de prueba

### tests/unit/test_antipattern_detector.py

Pruebas incluidas:

1. test_detect_blob_when_all_conditions_present
- Entrada: smells LCS, CC y DC para un mismo archivo.
- Esperado: BLOB con 3 condiciones cumplidas, estado detectado y 1 archivo en archivos_con_antipatron.

2. test_no_detection_when_input_is_empty
- Entrada: lista vacia de smells.
- Esperado: para todos los antipatrones, 0 condiciones cumplidas y estado not detected.

3. test_blob_likely_when_half_or_more_conditions
- Entrada: 2 de 3 condiciones de BLOB (LCS y CC).
- Esperado: estado likely en BLOB.

4. test_blob_not_detected_when_less_than_half_conditions
- Entrada: solo 1 condicion de BLOB (CC).
- Esperado: estado not detected en BLOB.

### tests/unit/test_main_controller_mapping.py

Prueba incluida:

1. test_map_new_ninterf_rule_to_mi
- Entrada: issue local NEW-NINTERF-VERY-HIGH.
- Esperado: mapeo a un smell MI, source local y project owner_repo.

2. test_ignore_unknown_rule_key
- Entrada: rule_key no registrado en el mapeo.
- Esperado: lista vacia, sin conversion a Moha smells.

### tests/unit/test_python_rules_new.py

Pruebas incluidas:

1. test_new_nacc_very_high_positive
- Entrada: clase con 5 getters y una alta proporcion de accesores.
- Esperado: 1 issue con rule_key NEW-NACC-VERY-HIGH.

2. test_new_nacc_very_high_negative_when_ratio_is_low
- Entrada: clase con metodos accesores insuficientes en proporcion.
- Esperado: 0 issues para NEW-NACC-VERY-HIGH.

3. test_new_nprivfield_high_positive
- Entrada: clase con 8 campos privados en __init__.
- Esperado: 1 issue con rule_key NEW-NPRIVFIELD-HIGH.

4. test_new_nprivfield_high_negative_below_threshold
- Entrada: clase con 7 campos privados.
- Esperado: 0 issues para NEW-NPRIVFIELD-HIGH.

5. test_new_nmd_very_low_positive
- Entrada: clase con 2 metodos.
- Esperado: 1 issue con rule_key NEW-NMD-VERY-LOW.

6. test_new_nmd_very_low_negative_above_threshold
- Entrada: clase con 4 metodos.
- Esperado: 0 issues para NEW-NMD-VERY-LOW.

7. test_new_ninterf_very_high_positive
- Entrada: clase con 2 metodos que usan type-checking con if/elif/else.
- Esperado: 1 issue con rule_key NEW-NINTERF-VERY-HIGH.

8. test_new_ninterf_very_high_negative_when_only_one_method_has_type_checks
- Entrada: solo 1 metodo con type-checking y otro metodo sin ramificacion por tipo.
- Esperado: 0 issues para NEW-NINTERF-VERY-HIGH.

### tests/unit/test_python_sonar_equivalent_rules.py

Prueba incluida:

1. test_analyze_repository_generates_expected_issue
- Entrada: repositorio temporal con un archivo y una clase minima.
- Esperado: include NEW-NMD-VERY-LOW en los rule_keys y metricas minimas correctas.

2. test_analyze_repository_raises_value_error_for_missing_path
- Entrada: ruta inexistente.
- Esperado: ValueError.

3. test_analyze_repository_reports_syntax_errors
- Entrada: archivo temporal con error de sintaxis Python.
- Esperado: issue con rule_key PY-SYNTAX.

### tests/unit/test_json_reader.py

Pruebas incluidas:

1. test_get_report_code_smells_success
- Entrada: requests.get mockeado con respuesta 200 y un issue.
- Esperado: extractCodeSmells retorna 1 issue, regla python:S100 y componente normalizado src/file.py.

2. test_get_report_code_smells_private_repo_error
- Entrada: requests.get mockeado con status 401.
- Esperado: GetReportCodeSmells lanza excepcion con mensaje asociado a repositorio privado.

3. test_get_report_code_smells_project_not_found_error
- Entrada: requests.get mockeado con status 404.
- Esperado: GetReportCodeSmells lanza excepcion de proyecto no encontrado.

4. test_extract_code_smells_raises_when_no_data_loaded
- Entrada: invocacion de extractCodeSmells sin dataJson cargado.
- Esperado: excepcion controlada.

### tests/unit/test_excel_processor.py

Prueba incluida:

1. test_related_moha_smells_with_deduplication
- Entrada: archivo Excel temporal con filas de mapeo repetidas y lista de smells duplicados.
- Esperado: resultado deduplicado de longitud 1, moha_smell CC y source sonar.

2. test_related_moha_smells_returns_empty_when_no_rule_matches
- Entrada: rules de Sonar que no coinciden con el archivo de mapeo.
- Esperado: lista vacia.

## 8. Datos de soporte

- tests/fixtures/sample_module.py se incluye como fixture inicial para escenarios de prueba y extensiones futuras.

## 9. Recomendaciones al extender pruebas

- Mantener el nombre de archivo con prefijo test_.
- Mantener test por modulo para trazabilidad.
- Si cambias umbrales de reglas NEW-*, actualizar sus expectativas en test_python_rules_new.py.
- Preferir datos de entrada pequenos y deterministas para pruebas de valor esperado.
