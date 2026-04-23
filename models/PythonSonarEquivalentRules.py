import ast
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Tuple

from .python_rules import (
    NewDitOneRule,
    NewNaccVeryHighRule,
    NewNinterfVeryHighRule,
    NewNmdVeryLowRule,
    NewNmnoparamVeryHighRule,
    NewNoPolymorphismRule,
    NewNprivfieldHighRule,
    PYLX01LexicProceduralClassNameRule,
    RuleIssue,
    S100LexicMethodNameRule,
    S101LexicClassNameRule,
    S138MethodTooBigRule,
    S1444ClassAttributeFinalRule,
    S1448TooManyMethodsRule,
)


class PythonSonarEquivalentRules:
    """
    Orquestador de reglas locales para analisis de codigo Python.

    Reglas activas (una clase por archivo en models/python_rules):
    - S101: LEXIC CLASSNAME (Manager, Process, Control, Controller)
    - PY-LX01: LEXIC CLASSNAME PROCEDURAL (Make, Create, Exec, Compute)
    - S100: LEXIC METHODNAME (Manager, Process, Control, Controller)
    - S138: LOC_METHOD VERY_HIGH
    - S1444: USE_GLOBAL_VARIABLE
    - S1448: NMD VERY_HIGH
    - NEW-NACC-VERY-HIGH: NACC VERY_HIGH
    - NEW-NINTERF-VERY-HIGH: NINTERF VERY_HIGH
    - NEW-NPRIVFIELD-HIGH: NPRIVFIELD HIGH
    - NEW-NMD-VERY-LOW: NMD VERY_LOW
    - NEW-NO-POLYMORPHISM: NO_POLYMORPHISM
    - NEW-DIT-ONE: DIT = 1
    - NEW-NMNOPARAM-VERY-HIGH: NMNOPARAM VERY_HIGH

    [CAMBIO] Se retiro la validacion regex de class/method names, porque ahora
    la deteccion para S101 y S100 es 100% lexica.
    """

    def __init__(
        self,
        max_method_lines: int = 75,
        maximum_method_threshold: int = 35,
        count_non_public: bool = True,
        controller_class_terms: Tuple[str, ...] = (
            "manager",
            "process",
            "control",
            "controller",
        ),
        procedural_class_terms: Tuple[str, ...] = (
            "make",
            "create",
            "exec",
            "compute",
        ),
        controller_method_terms: Tuple[str, ...] = (
            "manager",
            "process",
            "control",
            "controller",
        ),
    ):
        # [NUEVO] Instancias de reglas separadas por archivo.
        self.rule_s101 = S101LexicClassNameRule(controller_class_terms)
        self.rule_py_lx01 = PYLX01LexicProceduralClassNameRule(procedural_class_terms)
        self.rule_s100 = S100LexicMethodNameRule(controller_method_terms)
        self.rule_s138 = S138MethodTooBigRule(max_method_lines)
        self.rule_s1444 = S1444ClassAttributeFinalRule()
        self.rule_s1448 = S1448TooManyMethodsRule(maximum_method_threshold, count_non_public)

        # [NUEVO] Reglas de metricas adicionales solicitadas.
        self.rule_new_nacc = NewNaccVeryHighRule()
        # [ACTUALIZACION 2026-04-23] Regla habilitada (antes estaba comentada por archivo vacio).
        self.rule_new_ninterf = NewNinterfVeryHighRule()
        self.rule_new_nprivfield = NewNprivfieldHighRule()
        self.rule_new_nmd_low = NewNmdVeryLowRule()
        self.rule_new_no_polymorphism = NewNoPolymorphismRule()
        self.rule_new_dit_one = NewDitOneRule()
        self.rule_new_nmnoparam = NewNmnoparamVeryHighRule()

    def analyze_repository(self, repo_path: str) -> Dict:
        root = Path(repo_path)
        if not root.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")

        issues: List[RuleIssue] = []
        metrics = {
            "python_files": 0,
            "classes": 0,
            "methods": 0,
            "lines": 0,
        }

        for py_file in self._iter_python_files(root):
            metrics["python_files"] += 1
            file_issues, file_metrics = self._analyze_file(py_file, root)
            issues.extend(file_issues)
            for key in metrics:
                if key in file_metrics:
                    metrics[key] += file_metrics[key]

        return {
            "metrics": metrics,
            "issues": [asdict(issue) for issue in issues],
            "issues_count": len(issues),
        }

    def _iter_python_files(self, root: Path):
        excluded_dirs = {
            ".git",
            ".venv",
            "venv",
            "env",
            "__pycache__",
            "node_modules",
        }

        for file_path in root.rglob("*.py"):
            relative_parts = file_path.relative_to(root).parts
            if any(part in excluded_dirs for part in relative_parts):
                continue
            yield file_path

    def _analyze_file(self, file_path: Path, repo_root: Path):
        relative_file = file_path.relative_to(repo_root).as_posix()
        source = file_path.read_text(encoding="utf-8", errors="ignore")
        source_lines = source.splitlines()

        file_metrics = {
            "classes": 0,
            "methods": 0,
            "lines": len(source_lines),
        }

        try:
            tree = ast.parse(source)
        except SyntaxError as error:
            return [
                RuleIssue(
                    rule_key="PY-SYNTAX",
                    file_path=relative_file,
                    line=error.lineno or 1,
                    message=f"Syntax error during analysis: {error.msg}",
                    severity="CRITICAL",
                    metric_name="SYNTAX_ERROR",
                    textRange={
                        "startLine": error.lineno or 1,
                        "endLine": error.lineno or 1,
                    },
                )
            ], file_metrics

        visitor = _RulesVisitor(
            file_path=relative_file,
            source_lines=source_lines,
            rule_s101=self.rule_s101,
            rule_py_lx01=self.rule_py_lx01,
            rule_s100=self.rule_s100,
            rule_s138=self.rule_s138,
            rule_s1444=self.rule_s1444,
            rule_s1448=self.rule_s1448,
            rule_new_nacc=self.rule_new_nacc,
            rule_new_ninterf=self.rule_new_ninterf,
            rule_new_nprivfield=self.rule_new_nprivfield,
            rule_new_nmd_low=self.rule_new_nmd_low,
            rule_new_no_polymorphism=self.rule_new_no_polymorphism,
            rule_new_dit_one=self.rule_new_dit_one,
            rule_new_nmnoparam=self.rule_new_nmnoparam,
        )
        visitor.visit(tree)

        file_metrics["classes"] = visitor.total_classes
        file_metrics["methods"] = visitor.total_methods

        return visitor.issues, file_metrics


class _RulesVisitor(ast.NodeVisitor):
    """Visitor de AST que delega cada verificacion a una clase-regla."""

    def __init__(
        self,
        file_path: str,
        source_lines: List[str],
        rule_s101: S101LexicClassNameRule,
        rule_py_lx01: PYLX01LexicProceduralClassNameRule,
        rule_s100: S100LexicMethodNameRule,
        rule_s138: S138MethodTooBigRule,
        rule_s1444: S1444ClassAttributeFinalRule,
        rule_s1448: S1448TooManyMethodsRule,
        rule_new_nacc: NewNaccVeryHighRule,
        rule_new_ninterf: NewNinterfVeryHighRule,
        rule_new_nprivfield: NewNprivfieldHighRule,
        rule_new_nmd_low: NewNmdVeryLowRule,
        rule_new_no_polymorphism: NewNoPolymorphismRule,
        rule_new_dit_one: NewDitOneRule,
        rule_new_nmnoparam: NewNmnoparamVeryHighRule,
    ):
        self.file_path = file_path
        self.source_lines = source_lines
        self.rule_s101 = rule_s101
        self.rule_py_lx01 = rule_py_lx01
        self.rule_s100 = rule_s100
        self.rule_s138 = rule_s138
        self.rule_s1444 = rule_s1444
        self.rule_s1448 = rule_s1448
        self.rule_new_nacc = rule_new_nacc
        self.rule_new_ninterf = rule_new_ninterf
        self.rule_new_nprivfield = rule_new_nprivfield
        self.rule_new_nmd_low = rule_new_nmd_low
        self.rule_new_no_polymorphism = rule_new_no_polymorphism
        self.rule_new_dit_one = rule_new_dit_one
        self.rule_new_nmnoparam = rule_new_nmnoparam

        self.issues: List[RuleIssue] = []
        self.total_classes = 0
        self.total_methods = 0
        self.class_depth = 0

    def visit_ClassDef(self, node: ast.ClassDef):
        self.class_depth += 1
        self.total_classes += 1

        self.issues.extend(self.rule_s101.check_class(node, self.file_path))
        self.issues.extend(self.rule_py_lx01.check_class(node, self.file_path))
        self.issues.extend(self.rule_new_nacc.check_class(node, self.file_path))
        self.issues.extend(self.rule_new_ninterf.check_class(node, self.file_path))
        self.issues.extend(self.rule_new_nprivfield.check_class(node, self.file_path))
        self.issues.extend(self.rule_new_nmd_low.check_class(node, self.file_path))
        self.issues.extend(self.rule_new_no_polymorphism.check_class(node, self.file_path))
        self.issues.extend(self.rule_new_dit_one.check_class(node, self.file_path))
        self.issues.extend(self.rule_new_nmnoparam.check_class(node, self.file_path))

        class_methods = [
            item
            for item in node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        self.total_methods += len(class_methods)

        self.issues.extend(self.rule_s1448.check_class(node, class_methods, self.file_path))

        for member in node.body:
            self.issues.extend(self.rule_s1444.check_member(member, self.file_path))

        for member in class_methods:
            self._check_callable_rules(member)

        self.generic_visit(node)
        self.class_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef):
        if self.class_depth == 0:
            self._check_callable_rules(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        if self.class_depth == 0:
            self._check_callable_rules(node)
        self.generic_visit(node)

    def _check_callable_rules(self, node: ast.AST):
        self.issues.extend(self.rule_s100.check_callable(node, self.file_path))
        self.issues.extend(self.rule_s138.check_callable(node, self.file_path, self.source_lines))
