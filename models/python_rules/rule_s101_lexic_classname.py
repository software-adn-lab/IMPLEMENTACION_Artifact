import ast
from typing import List, Tuple

from .rule_issue import RuleIssue


class S101LexicClassNameRule:
    # [NUEVO] Detecta nombres de clase tipo Controller.
    def __init__(self, terms: Tuple[str, ...]):
        self.terms = tuple(term.lower() for term in terms)

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        if not self._contains_any_term(node.name):
            return []

        return [
            RuleIssue(
                rule_key="S101",
                file_path=file_path,
                line=node.lineno,
                message=(
                    "Controller-like class name detected "
                    f"('{node.name}'). Avoid terms like "
                    "Manager/Process/Control/Controller in class names."
                ),
                symbol_name=node.name,
                metric_name="LEXIC CLASSNAME",
                textRange={
                    "startLine": node.lineno,
                    "endLine": node.lineno,
                },
            )
        ]

    def _contains_any_term(self, name: str) -> bool:
        normalized = (name or "").lower()
        return any(term in normalized for term in self.terms)
