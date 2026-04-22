from flask import Blueprint, render_template, request, jsonify
import traceback

from models.JSONReader import JSONReader
from models.ExcelProcessor import ExcelProcessor
from models.AntipatternDetector import DetectAntipattern
from models.RepositoryStructureAnalyzer import RepositoryStructureAnalyzer
from models.PythonSonarEquivalentRules import PythonSonarEquivalentRules

main_bp = Blueprint('main', __name__)


def _map_local_rule_issue_to_moha(rule_issue, project_key):
    """Traduce un issue local a uno o varios Moha smells.

    Flujo:
    1) Lee el rule_key local emitido por PythonSonarEquivalentRules.
    2) Resuelve los codigos de Moha smell esperados por DetectAntipattern.
    3) Normaliza la estructura para que coincida con entradas mapeadas desde Sonar.
    """
    rule_key = (rule_issue.get("rule_key") or "").upper()

    # [CAMBIO] Mapeo solicitado por el proyecto:
    # S138 -> LOC_METHOD VERY_HIGH -> LM (Spaghetti Code)
    # S1448 -> NMD VERY_HIGH -> LCS (BLOB/Clase Grande)
    # S101 -> LEXIC CLASSNAME -> CC (BLOB)
    # PY-LX01 -> LEXIC CLASSNAME PROCEDURAL -> PN (Functional Decomposition)
    # S100 -> LEXIC METHODNAME -> CM (BLOB)
    # S1444 -> USE_GLOBAL_VARIABLE -> CGV (Spaghetti Code)
    # NEW-NACC-VERY-HIGH -> NACC VERY_HIGH -> DC (BLOB)
    # NEW-NINTERF-VERY-HIGH -> NINTERF VERY_HIGH -> MI (Swiss Army Knife)
    # NEW-NPRIVFIELD-HIGH -> NPRIVFIELD HIGH -> FP (Functional Decomposition)
    # NEW-NMD-VERY-LOW -> NMD VERY_LOW -> COM (Functional Decomposition)
    # NEW-NO-POLYMORPHISM -> NO_POLYMORPHISM -> NP (FD/Spaghetti Code)
    # NEW-DIT-ONE -> DIT = 1 -> NI (FD/Spaghetti Code)
    # NEW-NMNOPARAM-VERY-HIGH -> NMNOPARAM VERY_HIGH -> MNP (Spaghetti Code)
    local_moha_by_rule = {
        "S138": ["LM"],
        "S1448": ["LCS"],
        "S101": ["CC"],
        "PY-LX01": ["PN"],  # [NUEVO] Clase procedural -> Functional Decomposition.
        "S100": ["CM"],
        "S1444": ["CGV"],
        "NEW-NACC-VERY-HIGH": ["DC"],
        "NEW-NINTERF-VERY-HIGH": ["MI"],
        "NEW-NPRIVFIELD-HIGH": ["FP"],
        "NEW-NMD-VERY-LOW": ["COM"],
        "NEW-NO-POLYMORPHISM": ["NP"],
        "NEW-DIT-ONE": ["NI"],
        "NEW-NMNOPARAM-VERY-HIGH": ["MNP"],
    }

    # Si una regla local no existe en el mapeo, se ignora para mantener resiliencia.
    mapped_moha_smells = local_moha_by_rule.get(rule_key, [])
    if not mapped_moha_smells:
        return []

    mapped = []
    for moha_smell in mapped_moha_smells:
        # Mantiene el mismo esquema que usa AntipatternDetector y las tablas del frontend.
        mapped.append({
            "moha_smell": moha_smell,
            "sonar_rule": rule_issue.get("metric_name") or rule_key,
            "metric_name": rule_issue.get("metric_name"),
            "line": rule_issue.get("line"),
            "severity": rule_issue.get("severity", "not specified"),
            "component": rule_issue.get("file_path"),
            "issue_key": None,
            "project": project_key,
            "textRange": rule_issue.get("textRange"),
            "source": "local",
        })

    return mapped

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/results")
def results():
    return render_template("generalReport.html")

@main_bp.route("/general-report")
def general_report():
    return render_template("generalReport.html")

@main_bp.route("/individual-report")
def individual_report():
    return render_template("individualReport.html")

@main_bp.route("/code-details")
def code_details():
    return render_template("codeDetails.html")

@main_bp.route("/api/test-connection", methods=["POST"])
def analyze_project():
    """Endpoint principal de orquestacion para detectar antipatrones.

    Flujo completo:
    1) Valida la entrada de la peticion (project_key/token).
    2) Ejecuta analisis local de metricas Python y lo mapea a Moha smells.
    3) Consulta issues en SonarCloud y los mapea con matriz Excel.
    4) Une ambas fuentes de smells en una sola lista.
    5) Ejecuta DetectAntipattern y retorna el resultado JSON.
    """
    # 1) Lee la entrada enviada por el formulario del frontend.
    data = request.get_json() or {}

    dominio = data.get("project_key", "").strip()
    token = data.get("token", "").strip()

    # project_key es obligatorio para consultar SonarCloud y el contexto local.
    if not dominio:
        return jsonify({
            "success": False,
            "message": "You must enter the project name."
        }), 400

    try:
        # 2) Prepara contexto local del repositorio (mejor esfuerzo, no bloqueante).
        repository_analyzer = RepositoryStructureAnalyzer()
        repository_analyzer.analyze_and_print(dominio)

        # 3) Flujo local: reglas Python -> issues locales -> Moha smells.
        python_related_smells = []
        try:
            local_repo_path = repository_analyzer.clone_repository(dominio)
            python_rules = PythonSonarEquivalentRules()
            python_rules_result = python_rules.analyze_repository(str(local_repo_path))

            print("\n[PythonSonarEquivalentRules] Analysis summary")
            print(f"Repository path: {local_repo_path}")
            print(f"Metrics: {python_rules_result.get('metrics', {})}")
            print(f"Total issues: {python_rules_result.get('issues_count', 0)}")

            for issue in python_rules_result.get("issues", [])[:20]:
                print(
                    f"- {issue.get('rule_key')} | {issue.get('file_path')}:{issue.get('line')} | {issue.get('message')}"
                )

            if python_rules_result.get("issues_count", 0) > 20:
                print("- ...")

            # Convierte cada issue local (rule_key) a Moha smells listos para el detector.
            for issue in python_rules_result.get("issues", []):
                python_related_smells.extend(_map_local_rule_issue_to_moha(issue, dominio))

            print(f"[PythonSonarEquivalentRules] Moha smells generated: {len(python_related_smells)}")
        except Exception as python_rules_error:
            # Errores locales se registran, pero no detienen el analisis basado en Sonar.
            print(f"[PythonSonarEquivalentRules] Warning: {python_rules_error}")

        # 4) Flujo Sonar: obtiene issues y los mapea mediante la matriz Excel.
        reader = JSONReader(dominio, token if token else None)
        reader.GetReportCodeSmells()
        codeSmellsSonarQube = reader.extractCodeSmells()

        # Si no hay token y no se obtienen smells, guia al usuario sobre repos privados.
        if not token and len(codeSmellsSonarQube) == 0:
            return jsonify({
                "success": False,
                "message": (
                    "No code smells were found. "
                    "If the repository is private, enable the "
                    "'Private repository' option and enter your authorization token."
                )
            })

        excelProcessor = ExcelProcessor("Mapeo.xlsx", codeSmellsSonarQube)
        # 5) Une ambas fuentes de smells en una lista unificada.
        relatedSmellsMoha = excelProcessor.GetRelatedMohaSmell()
        relatedSmellsMoha.extend(python_related_smells)

        # 6) Motor de decision final: evalua condiciones de antipatrones.
        result = DetectAntipattern(relatedSmellsMoha)

        # 7) Retorna payload consumido por los reportes del frontend.
        return jsonify({
            "success": True,
            "message": "Analysis completed successfully.",
            # "total_smells": len(codeSmellsSonarQube),
            # "code_smells_details": codeSmellsSonarQube,
            # "related_smells": relatedSmellsMoha,
            "antipattern_result": result
        })

    except Exception as e:
        # Cualquier error no controlado aqui se considera fallo total del punto de entrada.
        print("\n[ERROR] Analysis failed:")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Error during analysis: {str(e)}"
        })


@main_bp.route("/api/cleanup-session-repo", methods=["POST"])
def cleanup_session_repo():
    """Elimina la clonacion temporal asociada a la sesion del navegador."""
    data = request.get_json(silent=True) or {}
    project_key = (data.get("project_key") or data.get("projectName") or "").strip()

    if not project_key:
        return jsonify({
            "success": False,
            "message": "No project key provided for cleanup."
        }), 400

    try:
        repository_analyzer = RepositoryStructureAnalyzer()
        removed = repository_analyzer.delete_repository(project_key)
        return jsonify({
            "success": True,
            "removed": removed,
            "message": "Temporary repository removed." if removed else "Temporary repository not found."
        })
    except Exception as cleanup_error:
        print(f"[CLEANUP] Error removing temporary repository: {cleanup_error}")
        return jsonify({
            "success": False,
            "message": f"Cleanup error: {cleanup_error}"
        }), 500
