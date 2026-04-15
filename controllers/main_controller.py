from flask import Blueprint, render_template, request, jsonify
import traceback

from models.JSONReader import JSONReader
from models.ExcelProcessor import ExcelProcessor
from models.AntipatternDetector import DetectAntipattern
from models.RepositoryStructureAnalyzer import RepositoryStructureAnalyzer
from models.PythonSonarEquivalentRules import PythonSonarEquivalentRules

main_bp = Blueprint('main', __name__)


def _map_local_rule_issue_to_moha(rule_issue, project_key):
    """Translate local metric issues to Moha smells used by DetectAntipattern."""
    rule_key = (rule_issue.get("rule_key") or "").upper()

    # Mapping requested by the project:
    # S138 -> LOC_METHOD VERY_HIGH -> LM (Spaghetti Code)
    # S1448 -> NMD VERY_HIGH -> LCS (BLOB/Large Class)
    # S101 -> LEXIC CLASSNAME -> CC (BLOB) and PN (Functional Decomposition)
    # S100 -> LEXIC METHODNAME -> CM (BLOB)
    # S1444 -> USE_GLOBAL_VARIABLE -> CGV (Spaghetti Code)
    local_moha_by_rule = {
        "S138": ["LM"],
        "S1448": ["LCS"],
        "S101": ["CC", "PN"],
        "S100": ["CM"],
        "S1444": ["CGV"],
    }

    mapped_moha_smells = local_moha_by_rule.get(rule_key, [])
    if not mapped_moha_smells:
        return []

    mapped = []
    for moha_smell in mapped_moha_smells:
        mapped.append({
            "moha_smell": moha_smell,
            "sonar_rule": rule_issue.get("metric_name") or rule_key,
            "metric_name": rule_issue.get("metric_name"),
            "line": rule_issue.get("line"),
            "severity": rule_issue.get("severity", "MAJOR"),
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
    data = request.get_json() or {}

    dominio = data.get("project_key", "").strip()
    token = data.get("token", "").strip()

    if not dominio:
        return jsonify({
            "success": False,
            "message": "You must enter the project name."
        }), 400

    try:
        # Optional and non-blocking: clone and inspect Java repository structure from the same GUI field.
        repository_analyzer = RepositoryStructureAnalyzer()
        repository_analyzer.analyze_and_print(dominio)

        # Optional and non-blocking: execute Python equivalent checks and print results.
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

            for issue in python_rules_result.get("issues", []):
                python_related_smells.extend(_map_local_rule_issue_to_moha(issue, dominio))

            print(f"[PythonSonarEquivalentRules] Moha smells generated: {len(python_related_smells)}")
        except Exception as python_rules_error:
            print(f"[PythonSonarEquivalentRules] Warning: {python_rules_error}")

        reader = JSONReader(dominio, token if token else None)
        reader.GetReportCodeSmells()
        codeSmellsSonarQube = reader.extractCodeSmells()

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
        relatedSmellsMoha = excelProcessor.GetRelatedMohaSmell()
        relatedSmellsMoha.extend(python_related_smells)

        result = DetectAntipattern(relatedSmellsMoha)

        return jsonify({
            "success": True,
            "message": "Analysis completed successfully.",
            # "total_smells": len(codeSmellsSonarQube),
            # "code_smells_details": codeSmellsSonarQube,
            # "related_smells": relatedSmellsMoha,
            "antipattern_result": result
        })

    except Exception as e:
        print("\n[ERROR] Analysis failed:")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "message": f"Error during analysis: {str(e)}"
        })
