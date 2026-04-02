from flask import Blueprint, render_template, request, jsonify
import traceback

from models.JSONReader import JSONReader
from models.ExcelProcessor import ExcelProcessor
from models.AntipatternDetector import DetectAntipattern

main_bp = Blueprint('main', __name__)

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
