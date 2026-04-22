import ast
from typing import List

from .rule_issue import RuleIssue


class NewDitOneRule:
    # [NUEVO] DIT = 1: clase con profundidad de herencia minima.
    # En Python, se aproxima como clases sin base explicita o solo object.
    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        if not self._is_dit_one(node):
            return []

        return [
            RuleIssue(
                rule_key="NEW-DIT-ONE",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' has inheritance depth equivalent to 1 "
                    "(root/object-level only)."
                ),
                symbol_name=node.name,
                metric_name="DIT = 1",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]

    def _is_dit_one(self, node: ast.ClassDef) -> bool:
        if not node.bases:
            return True
        if len(node.bases) == 1:
            base = node.bases[0]
            if isinstance(base, ast.Name):
                return base.id == "object"
            if isinstance(base, ast.Attribute):
                return base.attr == "object"
        return False
