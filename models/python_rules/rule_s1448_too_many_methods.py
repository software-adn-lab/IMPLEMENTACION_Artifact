import ast
from typing import List

from .rule_issue import RuleIssue


class S1448TooManyMethodsRule:
    # [NUEVO] Detecta clases con demasiados metodos.
    def __init__(self, maximum_method_threshold: int, count_non_public: bool):
        self.maximum_method_threshold = maximum_method_threshold
        self.count_non_public = count_non_public

    def check_class(self, node: ast.ClassDef, class_methods: List[ast.AST], file_path: str) -> List[RuleIssue]:
        methods_for_count = class_methods
        if not self.count_non_public:
            methods_for_count = [m for m in class_methods if not getattr(m, "name", "").startswith("_")]

        if len(methods_for_count) <= self.maximum_method_threshold:
            return []

        visibility_text = "" if self.count_non_public else " public"
        return [
            RuleIssue(
                rule_key="S1448",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' has {len(methods_for_count)}{visibility_text} methods, "
                    f"which is greater than the {self.maximum_method_threshold} authorized. "
                    "Split it into smaller classes."
                ),
                symbol_name=node.name,
                metric_name="NMD VERY_HIGH",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]
