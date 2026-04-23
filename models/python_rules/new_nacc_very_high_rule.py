import ast
from typing import List, Set

from .rule_issue import RuleIssue


class NewNaccVeryHighRule:
    # [ACTUALIZACION 2026-04-23]
    # Se ajusto la regla para alinearla con Lanza & Marinescu + DECOR/Moha:
    # 1) NACC (NOAM) significativo: al menos 5 accesores.
    # 2) WOC bajo: >= 66% de metodos accesores sobre el total de metodos.
    # Nota: el componente estadistico por percentiles (Q3/P80/P90) se deja para
    # una fase de agregacion global del repositorio.
    def __init__(self, min_accessor_methods: int = 5, min_accessor_ratio: float = 0.66):
        self.min_accessor_methods = min_accessor_methods
        self.min_accessor_ratio = min_accessor_ratio

    def check_class(self, node: ast.ClassDef, file_path: str) -> List[RuleIssue]:
        methods = [
            m
            for m in node.body
            if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not (m.name.startswith("__") and m.name.endswith("__"))
        ]
        if not methods:
            return []

        accessor_methods = [m for m in methods if self._is_accessor_like(m)]
        accessor_count = len(accessor_methods)
        accessor_ratio = accessor_count / len(methods)

        if accessor_count < self.min_accessor_methods or accessor_ratio < self.min_accessor_ratio:
            return []

        return [
            RuleIssue(
                rule_key="NEW-NACC-VERY-HIGH",
                file_path=file_path,
                line=node.lineno,
                message=(
                    f"Class '{node.name}' has NACC/NOAM={accessor_count} accessor methods "
                    f"over {len(methods)} declared methods "
                    f"(ratio={accessor_ratio:.2f}), meeting thresholds "
                    f"NACC>={self.min_accessor_methods} and accessor_ratio>={self.min_accessor_ratio:.2f}."
                ),
                symbol_name=node.name,
                metric_name="NACC VERY_HIGH",
                textRange={
                    "startLine": node.lineno,
                    "endLine": getattr(node, "end_lineno", node.lineno),
                },
            )
        ]

    def _is_accessor_like(self, method: ast.AST) -> bool:
        if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False

        lower_name = method.name.lower()
        if lower_name.startswith(("get_", "set_", "is_", "has_")):
            return True

        body = getattr(method, "body", [])
        if len(body) == 1 and isinstance(body[0], ast.Return):
            value = body[0].value
            if isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
                return value.value.id in {"self", "cls"}

        # Setter minimo: asigna a self.<attr> y no tiene mas logica.
        if len(body) == 1 and isinstance(body[0], ast.Assign):
            assign = body[0]
            if len(assign.targets) == 1 and isinstance(assign.targets[0], ast.Attribute):
                target = assign.targets[0]
                if isinstance(target.value, ast.Name) and target.value.id == "self":
                    return True

        return False

    def _collect_public_members(self, node: ast.ClassDef) -> Set[str]:
        members: Set[str] = set()

        for member in node.body:
            if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not member.name.startswith("_"):
                    members.add(member.name)
                for stmt in ast.walk(member):
                    if isinstance(stmt, ast.Attribute) and isinstance(stmt.value, ast.Name):
                        if stmt.value.id == "self" and not stmt.attr.startswith("_"):
                            members.add(stmt.attr)
            elif isinstance(member, ast.Assign):
                for target in member.targets:
                    if isinstance(target, ast.Name) and not target.id.startswith("_"):
                        members.add(target.id)
            elif isinstance(member, ast.AnnAssign) and isinstance(member.target, ast.Name):
                if not member.target.id.startswith("_"):
                    members.add(member.target.id)

        return members
