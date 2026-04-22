import ast
from typing import List, Set

from .rule_issue import RuleIssue


class NewNprivfieldHighRule:
    # [NUEVO] NPRIVFIELD HIGH: muchas variables privadas/protegidas.
    # Ajusta private_field_threshold para controlar sensibilidad.
    def __init__(self, private_field_threshold: int = 6):
        self.private_field_threshold = private_field_threshold

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        private_fields = self._collect_private_instance_fields(node)
        count_private = len(private_fields)
        if count_private < self.private_field_threshold:
            return []

        return [
            RuleIssue(
                rule_key="NEW-NPRIVFIELD-HIGH",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' declares {count_private} private/protected instance fields, "
                    f"which is above the threshold {self.private_field_threshold}."
                ),
                symbol_name=node.name,
                metric_name="NPRIVFIELD HIGH",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]

    def _collect_private_instance_fields(self, node: ast.ClassDef) -> Set[str]:
        fields: Set[str] = set()
        for member in node.body:
            if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for stmt in ast.walk(member):
                if isinstance(stmt, ast.Attribute) and isinstance(stmt.value, ast.Name):
                    if stmt.value.id == "self" and stmt.attr.startswith("_"):
                        fields.add(stmt.attr)
        return fields
