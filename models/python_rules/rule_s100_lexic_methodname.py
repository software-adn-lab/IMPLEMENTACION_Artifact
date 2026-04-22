import ast
from typing import List, Tuple

from .rule_issue import RuleIssue


class S100LexicMethodNameRule:
    # [NUEVO] Detecta nombres de metodo/funcion tipo Controller.
    def __init__(self, terms: Tuple[str, ...]):
        self.terms = tuple(term.lower() for term in terms)

    def check_callable(self, node: ast.AST, file_path: str) -> List[RuleIssue]:
        name = getattr(node, "name", "")
        lineno = getattr(node, "lineno", 1)

        if name.startswith("__") and name.endswith("__"):
            return []

        if not self._contains_any_term(name):
            return []

        return [
            RuleIssue(
                rule_key="S100",
                file_path=file_path,
                line=lineno,
                message=(
                    "Controller-like method/function name detected "
                    f"('{name}'). Avoid terms like "
                    "Manager/Process/Control/Controller in method names."
                ),
                symbol_name=name,
                metric_name="LEXIC METHODNAME",
                textRange={
                    "startLine": lineno,
                    "endLine": lineno,
                },
            )
        ]

    def _contains_any_term(self, name: str) -> bool:
        normalized = (name or "").lower()
        return any(term in normalized for term in self.terms)
