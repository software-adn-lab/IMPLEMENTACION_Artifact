import ast
from typing import List

from .rule_issue import RuleIssue


class NewNmdVeryLowRule:
    # [NUEVO] NMD VERY_LOW: muy pocos metodos declarados.
    # Ajusta min_methods_threshold para controlar sensibilidad.
    def __init__(self, min_methods_threshold: int = 1, ignore_dunder: bool = True):
        self.min_methods_threshold = min_methods_threshold
        self.ignore_dunder = ignore_dunder

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        methods = [
            m
            for m in node.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            and (not self.ignore_dunder or not (m.name.startswith("__") and m.name.endswith("__")))
        ]

        methods_count = len(methods)
        if methods_count > self.min_methods_threshold:
            return []

        return [
            RuleIssue(
                rule_key="NEW-NMD-VERY-LOW",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' has only {methods_count} declared methods, "
                    f"which is at or below the threshold {self.min_methods_threshold}."
                ),
                symbol_name=node.name,
                metric_name="NMD VERY_LOW",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]
