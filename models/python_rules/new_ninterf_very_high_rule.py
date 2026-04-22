import ast
from typing import List

from .rule_issue import RuleIssue


class NewNinterfVeryHighRule:
    # [NUEVO] NINTERF VERY_HIGH: demasiadas interfaces/bases.
    # Ajusta interfaces_threshold para controlar sensibilidad.
    def __init__(self, interfaces_threshold: int = 4):
        self.interfaces_threshold = interfaces_threshold

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        interfaces_count = len(node.bases)
        if interfaces_count < self.interfaces_threshold:
            return []

        return [
            RuleIssue(
                rule_key="NEW-NINTERF-VERY-HIGH",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' has {interfaces_count} base/interface types, "
                    f"which is above the threshold {self.interfaces_threshold}."
                ),
                symbol_name=node.name,
                metric_name="NINTERF VERY_HIGH",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]
