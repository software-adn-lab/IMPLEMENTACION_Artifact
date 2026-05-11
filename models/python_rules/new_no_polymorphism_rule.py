import ast
from typing import List

from .rule_issue import RuleIssue


class NewNoPolymorphismRule:
    # [NUEVO] NO_POLYMORPHISM: detectar duplicación de lógica de decisión por tipo
    # según Fowler: si el mismo bloque de `isinstance`/`type` aparece en 2 o más
    # lugares para los mismos tipos, se considera falta de polimorfismo.
    def __init__(self, min_repeated_blocks: int = 2):
        self.min_repeated_blocks = min_repeated_blocks

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        # Recolectar firmas de bloques de decisión por tipo en los métodos
        methods = [
            m
            for m in node.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not (m.name.startswith("__") and m.name.endswith("__"))
        ]

        signatures = []  # list of frozenset of type-names detected in a block

        for method in methods:
            for stmt in ast.walk(method):
                if isinstance(stmt, ast.If):
                    if self._contains_type_check(stmt.test):
                        types = self._extract_types_from_if_chain(stmt)
                        if types:
                            signatures.append(frozenset(types))
                elif isinstance(stmt, ast.Match):
                    # For match/case, use the set of literal type names used in patterns
                    types = self._extract_types_from_match(stmt)
                    if types:
                        signatures.append(frozenset(types))

        # Contar firmas repetidas
        counts = {}
        for sig in signatures:
            counts[sig] = counts.get(sig, 0) + 1

        duplicated = [sig for sig, c in counts.items() if c >= self.min_repeated_blocks]

        if not duplicated:
            return []

        return [
            RuleIssue(
                rule_key="NEW-NO-POLYMORPHISM",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' contains duplicated type-dispatch blocks "
                    f"(same type-sets repeated >= {self.min_repeated_blocks} times)."
                ),
                symbol_name=node.name,
                metric_name="NO_POLYMORPHISM",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]

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

    def _extract_types_from_if_chain(self, node: ast.If) -> List[str]:
        types = []
        current = node
        while True:
            extracted = self._extract_types_from_test(current.test)
            types.extend(extracted)
            # follow elif chain
            if (
                len(current.orelse) == 1
                and isinstance(current.orelse[0], ast.If)
            ):
                current = current.orelse[0]
                continue
            break
        # return unique type names
        return list({t for t in types if t})

    def _extract_types_from_test(self, expr: ast.AST) -> List[str]:
        results = []
        for part in ast.walk(expr):
            if isinstance(part, ast.Call) and isinstance(part.func, ast.Name) and part.func.id == "isinstance":
                # isinstance(obj, Type) or isinstance(obj, (T1, T2))
                if len(part.args) >= 2:
                    type_arg = part.args[1]
                    results.extend(self._resolve_type_node(type_arg))
            if isinstance(part, ast.Compare):
                left = part.left
                if isinstance(left, ast.Call) and isinstance(left.func, ast.Name) and left.func.id == "type":
                    for comp in part.comparators:
                        results.extend(self._resolve_type_node(comp))
        return results

    def _extract_types_from_match(self, node: ast.Match) -> List[str]:
        types = []
        for case in node.cases:
            # simple approach: if pattern contains Name or Attribute, capture its id/attr
            for pat in ast.walk(case.pattern):
                if isinstance(pat, ast.Name):
                    types.append(pat.id)
                if isinstance(pat, ast.Attribute):
                    types.append(pat.attr)
        return list({t for t in types if t})

    def _resolve_type_node(self, node: ast.AST) -> List[str]:
        # Resolve Name, Attribute, or Tuple of those
        results = []
        if isinstance(node, ast.Name):
            results.append(node.id)
        elif isinstance(node, ast.Attribute):
            results.append(node.attr)
        elif isinstance(node, ast.Tuple):
            for elt in node.elts:
                results.extend(self._resolve_type_node(elt))
        return results
