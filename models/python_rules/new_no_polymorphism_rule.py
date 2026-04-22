import ast
from typing import List

from .rule_issue import RuleIssue


class NewNoPolymorphismRule:
    # [NUEVO] NO_POLYMORPHISM: sin uso de jerarquias/polimorfismo.
    # Ajusta require_method_overrides si quieres hacerlo mas estricto.
    def __init__(self, require_method_overrides: bool = False):
        self.require_method_overrides = require_method_overrides

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        has_non_object_base = any(not self._is_object_base(base) for base in node.bases)

        if has_non_object_base:
            return []

        if self.require_method_overrides:
            # Placeholder para futuras mejoras (deteccion de override real).
            return []

        return [
            RuleIssue(
                rule_key="NEW-NO-POLYMORPHISM",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' does not use inheritance-based polymorphism "
                    "(only root/object-level hierarchy detected)."
                ),
                symbol_name=node.name,
                metric_name="NO_POLYMORPHISM",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]

    def _is_object_base(self, base: ast.AST) -> bool:
        if isinstance(base, ast.Name):
            return base.id == "object"
        if isinstance(base, ast.Attribute):
            return base.attr == "object"
        return False
