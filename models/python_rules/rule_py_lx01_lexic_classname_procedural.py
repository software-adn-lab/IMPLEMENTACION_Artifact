import ast
from typing import List, Tuple

from .rule_issue import RuleIssue


class PYLX01LexicProceduralClassNameRule:
    # [NUEVO] Detecta nombres de clase procedurales.
    def __init__(self, terms: Tuple[str, ...]):
        self.terms = tuple(term.lower() for term in terms)

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        if not self._contains_any_term(node.name):
            return []

        return [
            RuleIssue(
                rule_key="PY-LX01",
                file_path=file_path,
                line=node.lineno,
                message=(
                    "Procedural class name detected "
                    f"('{node.name}'). Avoid terms like "
                    "Make/Create/Exec/Compute in class names."
                ),
                symbol_name=node.name,
                metric_name="LEXIC CLASSNAME PROCEDURAL",
                textRange={
                    "startLine": node.lineno,
                    "endLine": node.lineno,
                },
            )
        ]

    def _contains_any_term(self, name: str) -> bool:
        normalized = (name or "").lower()
        return any(term in normalized for term in self.terms)
