import ast
from typing import List, Tuple

from .rule_issue import RuleIssue


class NewNinterfVeryHighRule:
    # [ACTUALIZACION 2026-04-23]
    # Regla creada para detectar NINTERF VERY_HIGH en Python mediante:
    # 1) Type-checking explicito (isinstance/type(...) is ...).
    # 2) Ramificacion por tipo en if/elif o match/case.
    # 3) Repeticion de estos bloques en 2 o mas metodos.
    def __init__(self, min_type_branches: int = 3, min_repeated_methods: int = 2):
        self.min_type_branches = min_type_branches
        self.min_repeated_methods = min_repeated_methods

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        methods = [
            m
            for m in node.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not (m.name.startswith("__") and m.name.endswith("__"))
        ]

        methods_with_type_switch = 0
        max_type_branches = 0

        for method in methods:
            has_type_check, type_branches = self._analyze_method(method)
            if has_type_check:
                methods_with_type_switch += 1
                max_type_branches = max(max_type_branches, type_branches)

        very_high_by_complexity = max_type_branches >= self.min_type_branches
        very_high_by_duplication = methods_with_type_switch >= self.min_repeated_methods

        if not (very_high_by_complexity and very_high_by_duplication):
            return []

        return [
            RuleIssue(
                rule_key="NEW-NINTERF-VERY-HIGH",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' relies on explicit type-checking across "
                    f"{methods_with_type_switch} methods; max type-branches={max_type_branches}. "
                    f"This indicates NINTERF VERY_HIGH (missing polymorphic dispatch)."
                ),
                symbol_name=node.name,
                metric_name="NINTERF VERY_HIGH",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]

    def _analyze_method(self, method: ast.AST) -> Tuple[bool, int]:
        type_check_nodes = 0
        type_branches = 0

        for stmt in ast.walk(method):
            if isinstance(stmt, ast.If):
                if self._contains_type_check(stmt.test):
                    type_check_nodes += 1
                    type_branches += self._count_if_chain_branches(stmt)
            elif isinstance(stmt, ast.Match):
                # match/case se considera switch por tipo/comportamiento.
                if len(stmt.cases) > 0:
                    type_check_nodes += 1
                    type_branches += len(stmt.cases)

        return type_check_nodes > 0, type_branches

    def _count_if_chain_branches(self, node: ast.If) -> int:
        count = 1
        current = node
        while (
            len(current.orelse) == 1
            and isinstance(current.orelse[0], ast.If)
            and self._contains_type_check(current.orelse[0].test)
        ):
            count += 1
            current = current.orelse[0]

        if current.orelse:
            count += 1
        return count

    def _contains_type_check(self, expr: ast.AST) -> bool:
        for part in ast.walk(expr):
            if isinstance(part, ast.Call):
                if isinstance(part.func, ast.Name) and part.func.id == "isinstance":
                    return True
                if isinstance(part.func, ast.Name) and part.func.id == "type":
                    return True
            if isinstance(part, ast.Compare):
                left = part.left
                if isinstance(left, ast.Call) and isinstance(left.func, ast.Name):
                    if left.func.id == "type":
                        return True
        return False
